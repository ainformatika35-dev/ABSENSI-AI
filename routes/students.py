import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from routes.auth import admin_required
from firebase.firebase_config import (
    get_all_students,
    get_user,
    create_or_update_user,
    delete_user,
    get_face_data,
    reset_face_data,
    get_user_by_username_or_nis
)

students_bp = Blueprint("students", __name__, url_prefix="/api/students")

@students_bp.route("", methods=["GET"])
@admin_required
def list_students():
    students = get_all_students()
    enhanced_students = []
    for s in students:
        uid = s.get("uid")
        face_info = get_face_data(uid)
        embeddings = face_info.get("embeddings", {}) if face_info else {}
        sample_count = len(embeddings)

        s_copy = dict(s)
        # Hapus hash password dari response
        s_copy.pop("password", None)
        s_copy["face_registered"] = sample_count > 0
        s_copy["face_samples_count"] = sample_count
        enhanced_students.append(s_copy)

    return jsonify({"success": True, "students": enhanced_students})

@students_bp.route("", methods=["POST"])
@admin_required
def add_student():
    data = request.get_json() or {}
    nis = str(data.get("nis", "")).strip()
    nama = str(data.get("nama", "")).strip()
    kelas = str(data.get("kelas", "")).strip()
    gender = str(data.get("gender", "Laki-laki")).strip()
    password = str(data.get("password", "siswa123")).strip()

    if not nis or not nama or not kelas:
        return jsonify({"success": False, "message": "NIS, Nama, dan Kelas wajib diisi."}), 400

    # Cek apakah NIS sudah digunakan
    existing = get_user_by_username_or_nis(nis)
    if existing:
        return jsonify({"success": False, "message": f"Siswa dengan NIS {nis} sudah terdaftar."}), 400

    new_uid = f"siswa_{nis}_{uuid.uuid4().hex[:6]}"
    student_data = {
        "uid": new_uid,
        "nis": nis,
        "username": nis,
        "password": generate_password_hash(password),
        "nama": nama,
        "kelas": kelas,
        "gender": gender,
        "role": "siswa",
        "status": "active",
        "createdAt": datetime.now().isoformat()
    }

    create_or_update_user(new_uid, student_data)
    student_data.pop("password", None)
    return jsonify({
        "success": True,
        "message": f"Siswa {nama} berhasil didaftarkan.",
        "student": student_data
    }), 201

@students_bp.route("/<user_id>", methods=["GET"])
@admin_required
def get_student_detail(user_id):
    student = get_user(user_id)
    if not student or student.get("role") != "siswa":
        return jsonify({"success": False, "message": "Siswa tidak ditemukan."}), 404

    s_copy = dict(student)
    s_copy.pop("password", None)
    face_info = get_face_data(user_id)
    embeddings = face_info.get("embeddings", {}) if face_info else {}
    s_copy["face_registered"] = len(embeddings) > 0
    s_copy["face_samples_count"] = len(embeddings)
    return jsonify({"success": True, "student": s_copy})

@students_bp.route("/<user_id>", methods=["PUT"])
@admin_required
def update_student(user_id):
    student = get_user(user_id)
    if not student or student.get("role") != "siswa":
        return jsonify({"success": False, "message": "Siswa tidak ditemukan."}), 404

    data = request.get_json() or {}
    nama = str(data.get("nama", student.get("nama"))).strip()
    kelas = str(data.get("kelas", student.get("kelas"))).strip()
    gender = str(data.get("gender", student.get("gender", "Laki-laki"))).strip()
    status = str(data.get("status", student.get("status", "active"))).strip()
    new_password = data.get("password")

    student["nama"] = nama
    student["kelas"] = kelas
    student["gender"] = gender
    student["status"] = status
    if new_password and str(new_password).strip():
        student["password"] = generate_password_hash(str(new_password).strip())

    create_or_update_user(user_id, student)
    return jsonify({"success": True, "message": f"Data siswa {nama} berhasil diperbarui."})

@students_bp.route("/<user_id>", methods=["DELETE"])
@admin_required
def remove_student(user_id):
    student = get_user(user_id)
    if not student:
        return jsonify({"success": False, "message": "Siswa tidak ditemukan."}), 404

    nama = student.get("nama", "Siswa")
    delete_user(user_id)
    return jsonify({"success": True, "message": f"Data siswa {nama} dan data wajahnya berhasil dihapus."})

@students_bp.route("/<user_id>/reset-face", methods=["POST"])
@admin_required
def reset_student_face(user_id):
    student = get_user(user_id)
    if not student:
        return jsonify({"success": False, "message": "Siswa tidak ditemukan."}), 404

    reset_face_data(user_id)
    return jsonify({
        "success": True,
        "message": f"Data wajah siswa {student.get('nama')} berhasil di-reset. Silakan daftarkan ulang wajah siswa."
    })
