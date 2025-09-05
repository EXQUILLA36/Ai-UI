import json
import os
from werkzeug.security import generate_password_hash, check_password_hash #type: ignore
from cryptography.fernet import Fernet #type: ignore
from utils.System import SmartStudentDataSystem

# ======== Setup Encryption ========
KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fernet.key")

def get_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key

secret_key = get_or_create_key()
cipher = Fernet(secret_key)

# ======== Database Path ========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # current folder
DB_FILE = os.path.join(BASE_DIR, "accounts", "students.json")  # point to subfolder

# ======== Encryption / Decryption ========
def encrypt_data(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()

def decrypt_data(token: str) -> str:
    return cipher.decrypt(token.encode()).decode()

# ======== File I/O Helpers ========
def load_students():
    """Load students from JSON file into dict."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_students(students):
    """Save students dict to JSON file."""
    with open(DB_FILE, "w") as f:
        json.dump(students, f, indent=4)

# ======== RBAC Core ========
def create_student_account(student_id, first_name, middle_name, last_name, year, course, password, email, role="student"):
    students = load_students()

    if student_id in students:
        return {"error": "Student ID already exists"}

    hashed_password = generate_password_hash(password)
    encrypted_name = encrypt_data(f"{first_name} {middle_name} {last_name}")
    encrypted_year = encrypt_data(year)
    encrypted_course = encrypt_data(course)
    encrypted_email = encrypt_data(email)

    students[student_id] = {
        "studentName": encrypted_name,
        "year": encrypted_year,
        "course": encrypted_course,
        "email": encrypted_email,
        "password": hashed_password,
        "role": role
    }

    save_students(students)
    return {"message": "Student account created successfully", "studentId": student_id, "role": role}

def verify_password(student_id, password):
    students = load_students()
    if student_id not in students:
        return False
    return check_password_hash(students[student_id]["password"], password)

def get_student_info(student_id):
    students = load_students()
    if student_id not in students:
        return {"error": "Student not found"}

    student = students[student_id]
    return {
        "studentId": student_id,
        "studentName": decrypt_data(student["studentName"]),
        "year": decrypt_data(student["year"]),
        "course": decrypt_data(student["course"]),
        "role": student["role"]
        # Do NOT return password
    }

def get_all_students(requesting_user_id):
    """Admins only: list all students."""
    students = load_students()

    if requesting_user_id not in students:
        return {"error": "Requesting user not found"}

    if students[requesting_user_id]["role"] != "admin":
        return {"error": "Unauthorized access"}

    result = []
    for sid, data in students.items():
        result.append({
            "studentId": sid,
            "studentName": decrypt_data(data["studentName"]),
            "year": decrypt_data(data["year"]),
            "course": decrypt_data(data["course"]),
            "role": data["role"]
        })
    return result