import os
import json
from flask import Flask, request, jsonify #type: ignore 
from flask_cors import CORS #type: ignore
from utils.LLM_model import AIAnalyst
from utils.Security import collect_data
from newRBAC import create_student_account, verify_password, load_students, decrypt_data
from urllib.parse import unquote
import json

app = Flask(__name__)
CORS(app)  # allow frontend to talk to backend

# configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

UPLOAD_FOLDER_LIST = os.path.join(os.path.dirname(__file__), 'uploads')

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
    collections = collect_data()
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

# @app.route("/login", methods=["POST"])
# def login():
#     data = request.json
#     student_id = data.get("studentId")
#     student_name = data.get("studentName")
#     password = data.get("password")

#     import json
#     from werkzeug.security import check_password_hash #type: ignore

#     try:
#         with open("students.json", "r") as f:
#             students = json.load(f)
#     except FileNotFoundError:
#         return jsonify({"error": "No registered users yet."}), 404

#     if student_id not in students:
#         return jsonify({"error": "Invalid Student ID."}), 401

#     student = students[student_id]

#     # Decrypt studentName here if needed; for now, assume plain text
#     # If encrypted, you'd need to decrypt it similarly to your register process
#     # For this demo, just check hashed password
    # if not check_password_hash(student["password"], password):
    #     return jsonify({"error": "Incorrect password."}), 401

#     # Optional name validation (if stored as plain text or decrypted)
    # if student_name != student["studentName"]:
    #     return jsonify({"error": "Name does not match our records."}), 401

    # return jsonify({"message": "Login successful", "student": student}), 200


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

    result = create_student_account(
        student_id=data["studentId"],
        first_name=data["firstName"],
        middle_name=data["middleName"],
        last_name=data["lastName"],
        year=data["year"],
        course=data["course"],
        password=data["password"],
        role="student",
        email=data["email"]  # <-- FIXED
    )

    if "error" in result:
        return jsonify(result), 409
    return jsonify(result)

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    student_id = data.get("studentId")
    email = data.get("email")
    password = data.get("password")

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

    return jsonify({"message": "Login successful", "studentId": student_id})

@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "ok"}, 200

# === Course management 
COURSES_FILE = os.path.join(os.path.dirname(__file__), "courses.json")

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




if __name__ == "__main__":
    collections = collect_data()
    api_mode = 'online'
    
    try:
        with open("config/config.json", "r", encoding="utf-8") as f:
            full_config = json.load(f)
    except FileNotFoundError:
        print("❌ config.json not found! Cannot start AI Analyst.")
    
    ai = AIAnalyst(collections=collections, llm_config=full_config, execution_mode=api_mode)
    app.run(debug=True, port=5000)
