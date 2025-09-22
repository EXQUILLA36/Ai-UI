import os
import json
from flask import Flask, request, jsonify #type: ignore 
from flask_cors import CORS #type: ignore
from utils.LLM_model import AIAnalyst
from utils.Security import collect_data
from newRBAC import create_student_account, verify_password, load_students, decrypt_data
from urllib.parse import unquote
from pathlib import Path
import threading

app = Flask(__name__)
CORS(app)  # allow frontend to talk to backend

# configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
collections = {}

UPLOAD_FOLDER_LIST = os.path.join(os.path.dirname(__file__), 'uploads')
data_dir = Path(__file__).resolve().parent / 'database' / 'chroma_store'
api_mode = 'online'

# === Allowed extensions
ALLOWED_EXTENSIONS = {".xlsx", ".json", ".pdf"}
def is_allowed(filename):
    # function to store files that ends with allowed extensions
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

@app.route("/files", methods=["GET"])
def list_files():
    base = os.path.join(os.getcwd(), "uploads")
    result = {"faculty": [], "students": [], "admin": []}
    for folder in result.keys():
        folder_path = os.path.join(base, folder)
        if os.path.exists(folder_path):
            result[folder] = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return jsonify({"files": result})

@app.route("/student/<student_id>", methods=["GET"])
def get_student(student_id):
    try:
        students = load_students()
        student = students.get(student_id)

        if not student:
            return jsonify({"error": "Student not found"}), 404

        # Decrypt the studentName field and split into components
        decrypted_name = decrypt_data(student.get("studentName", ""))
        name_parts = decrypted_name.split(" ")
        
        # Handle cases where middle name might be missing
        if len(name_parts) >= 3:
            firstName = name_parts[0]
            middleName = name_parts[1]
            lastName = " ".join(name_parts[2:])
        elif len(name_parts) == 2:
            firstName = name_parts[0]
            middleName = ""
            lastName = name_parts[1]
        else:
            firstName = decrypted_name
            middleName = ""
            lastName = ""

        decrypted_student = {
            "studentId": student_id,
            "firstName": firstName,
            "middleName": middleName,
            "lastName": lastName,
            "email": decrypt_data(student.get("email", "")),
            "year": decrypt_data(student.get("year", "")),
            "course": decrypt_data(student.get("course", "")),
            "role": student.get("role", ""),  # role is not encrypted
        }

        return jsonify(decrypted_student), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    folder = request.form.get('folder', '').lower()

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    if folder not in ["faculty", "students", "admin"]:
        return jsonify({"message": "❌ Invalid folder. Must be faculty, students, or admin."}), 400

    target_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder)
    os.makedirs(target_folder, exist_ok=True)

    filepath = os.path.join(target_folder, file.filename)

    # Check duplicate
    if os.path.exists(filepath) and request.form.get("overwrite") != "true":
        return jsonify({
            "message": f"⚠️ File '{file.filename}' already exists in {folder}/. Overwrite?",
            "duplicate": True
        }), 409

    file.save(filepath)
    
    global collections, ai
    collections = collect_data(data_dir, role, assign, load= True)
    ai = AIAnalyst(collections, llm_config=full_config, execution_mode=api_mode)
    
    return jsonify({"message": "File uploaded successfully!", "filename": file.filename}), 200
    
@app.route("/delete_upload/<category>/<filename>", methods=["DELETE"])
def delete_upload(category, filename):
    if category not in ["faculty", "students", "admin"]:
        return jsonify({"error": "Invalid category"}), 400
    folder_path = os.path.join(app.config["UPLOAD_FOLDER"], category)
    file_path = os.path.join(folder_path, filename)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    try:
        os.remove(file_path)
        return jsonify({"message": "File deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/chatprompt", methods=["POST"])
def ChatPrompt():
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query"})
    
    user_query = data['query']
    final_answer = ai.web_start_ai_analyst(user_query=user_query)
    return jsonify({"response": final_answer})

# Store last logged-in role and assign in a file for main block to read
ROLE_ASSIGN_FILE = os.path.join(os.path.dirname(__file__), "config/last_role_assign.json")

def map_student_role(student_role):
    # Map student role string to role and assign
    mapping = {
        "student CS": ("teaching_faculty", ["BSCS"]),
        "student IT": ("teaching_faculty", ["BSIT"]),
        "student HM": ("teaching_faculty", ["BSHM"]),
        "student TM": ("teaching_faculty", ["BSTM"]),
        "student OAd": ("teaching_faculty", ["BSOAd"]),
        "student ECED": ("teaching_faculty", ["BECEd"]),
        "student TLEd": ("teaching_faculty", ["BTLEd"]),
        "faculty": ("Faculty", ["Faculty"]),
        "Guest": ("Guest", ["Guest"]),
        "student": ("Student", []), # fallback
    }
    return mapping.get(student_role, ("Student", []))

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    student_id = data.get("studentId")
    email = data.get("email")
    password = data.get("password")

    # Guest login special case
    if student_id == "PDM-0000-000000":
        guest_file = os.path.join(os.path.dirname(__file__), "accounts", "guest.json")
        try:
            with open(guest_file, "r", encoding="utf-8") as f:
                guest_data = json.load(f)
            guest = guest_data.get(student_id)
            if not guest:
                return jsonify({"error": "Guest account not found"}), 404
            # Save role and assign for main block to use
            with open(ROLE_ASSIGN_FILE, "w", encoding="utf-8") as f:
                json.dump({"role": "Guest", "assign": ["Guest"]}, f)
            return jsonify({"message": "Login successful", "studentId": student_id, "role": "Guest"})
        except Exception as e:
            return jsonify({"error": f"Guest login error: {str(e)}"}), 500

    students = load_students()
    if student_id not in students:
        return jsonify({"error": "Student ID not found"}), 404

    # Decrypt and compare email
    stored_email = decrypt_data(students[student_id].get("email", ""))
    if email != stored_email:
        return jsonify({"error": "Email does not match"}), 401

    # Verify password
    if not verify_password(student_id, password):
        return jsonify({"error": "Incorrect password"}), 401

    # Check for admin role
    student_role = students[student_id].get("role", "student")
    if student_role.lower() == "admin":
        with open(ROLE_ASSIGN_FILE, "w", encoding="utf-8") as f:
            json.dump({"role": "admin", "assign": [""]}, f)
        return jsonify({"message": "Login successful", "studentId": student_id, "role": "admin"})

    # Get role and assign mapping
    role, assign = map_student_role(student_role)

    # Save role and assign for main block to use
    with open(ROLE_ASSIGN_FILE, "w", encoding="utf-8") as f:
        json.dump({"role": role, "assign": assign}, f)

    return jsonify({"message": "Login successful", "studentId": student_id, "role": student_role})

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    required_fields = [
        "studentId",
        "firstName",
        "middleName",
        "lastName",
        "email", 
        "year",
        "course",
        "password"
    ]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    # Map short course code to full course name for role assignment
    course_map = {
        "BSCS": "Bachelor of Science in Computer Science (BSCS)",
        "BSIT": "Bachelor of Science in Information Technology (BSIT)",
        "BSHM": "Bachelor of Science in Hospitality Management (BSHM)",
        "BSTM": "Bachelor of Science in Tourism Management (BSTM)",
        "BSOAd": "Bachelor of Science in Office Administration (BSOAd)",
        "BECEd": "Bachelor of Early Childhood Education (BECEd)",
        "BTLEd": "Bachelor of Technology in Livelihood Education (BTLEd)",
    }
    course_full = course_map.get(data["course"], data["course"])

    result = create_student_account(
        student_id=data["studentId"],
        first_name=data["firstName"],
        middle_name=data["middleName"],
        last_name=data["lastName"],
        year=data["year"],
        course=course_full,
        password=data["password"],
        email=data["email"]
    )

    if "error" in result:
        return jsonify(result), 409
    return jsonify(result)

# === Health check
@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200

# === Course management 
COURSES_FILE = os.path.join(os.path.dirname(__file__), "config/courses.json")

def load_courses():
    if not os.path.exists(COURSES_FILE):
        return []
    with open(COURSES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def save_courses(courses):
    with open(COURSES_FILE, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2, ensure_ascii=False)

@app.route("/courses", methods=["GET"])
def get_courses():
    return jsonify(load_courses())

@app.route("/courses", methods=["POST"])
def add_course():
    data = request.json
    required = ["department", "program", "description"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing fields"}), 400
    courses = load_courses()
    courses.append(data)
    save_courses(courses)
    return jsonify({"message": "Course added"}), 201

@app.route("/refresh_collections", methods=["POST"])
def refresh_collections():
    global collections, ai, role, assign
    # Clear previous collections
    collections = {}
    try:
        with open(ROLE_ASSIGN_FILE, "r", encoding="utf-8") as f:
            last_role_assign = json.load(f)
            role = last_role_assign.get("role", "Admin")
            assign = last_role_assign.get("assign", [])
    except Exception:
        role = "Admin"
        assign = []

    # If last login was guest, set role and assign to Guest
    if role == "Guest":
        assign = ["Guest"]

    collections = collect_data(data_dir, role, assign)
    
    try:
        with open("config/config.json", "r", encoding="utf-8") as f:
            full_config = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "config.json not found"}), 500

    ai = AIAnalyst(collections=collections, llm_config=full_config, execution_mode=api_mode)
    return jsonify({"message": "Collections refreshed", "role": role, "assign": assign}), 200

if __name__ == "__main__":
    # Load role and assign from file if exists, else use default
    try:
        with open("config/config.json", "r", encoding="utf-8") as f:
            full_config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found! Cannot start AI Analyst.")
        
    app.run(debug=True, port=5000)
