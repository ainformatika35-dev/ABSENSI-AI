from datetime import datetime
from flask import Blueprint, request, jsonify, session
from config import Config
from routes.auth import login_required, admin_required
from ai.face_recognition import get_face_recognizer
from ai.face_utils import base64_to_cv2, check_liveness
from firebase.firebase_config import (
    get_user,
    get_all_face_data,
    save_face_embeddings,
    save_attendance,
    get_attendance_by_date,
    get_attendance_for_user_today,
    get_attendance_history_for_user,
    get_all_attendance_records
)

attendance_bp = Blueprint("attendance", __name__)

# =========================================================================
# FACE REGISTRATION
# =========================================================================

@attendance_bp.route("/api/face/register", methods=["POST"])
@admin_required
def register_face():
    """
    Pendaftaran wajah siswa:
    Menerima user_id dan list foto (base64) wajah (minimal 1, direkomendasikan 3 sampel).
    Mengekstrak embedding vektor 128-D untuk setiap foto dan menyimpannya ke Firebase.
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    images_base64 = data.get("images", [])

    if not user_id:
        return jsonify({"success": False, "message": "ID Siswa harus disertakan."}), 400

    student = get_user(user_id)
    if not student:
        return jsonify({"success": False, "message": "Data siswa tidak ditemukan."}), 404

    if not images_base64 or not isinstance(images_base64, list):
        # Coba ambil single image jika ada
        single_img = data.get("image")
        if single_img:
            images_base64 = [single_img]
        else:
            return jsonify({"success": False, "message": "Sampel foto wajah belum disertakan."}), 400

    recognizer = get_face_recognizer()
    extracted_embeddings = []
    errors = []

    for idx, b64_img in enumerate(images_base64, start=1):
        cv_img = base64_to_cv2(b64_img)
        if cv_img is None:
            errors.append(f"Sampel #{idx}: Gambar tidak valid.")
            continue

        emb, box, err = recognizer.extract_embedding(cv_img)
        if err or emb is None:
            errors.append(f"Sampel #{idx}: {err or 'Wajah tidak dapat diproses'}")
            continue

        extracted_embeddings.append(emb)

    if not extracted_embeddings:
        return jsonify({
            "success": False,
            "message": "Gagal mendeteksi wajah yang valid dari sampel yang diberikan.",
            "details": errors
        }), 400

    # Simpan embeddings ke Firebase Realtime Database
    save_face_embeddings(user_id, extracted_embeddings)

    return jsonify({
        "success": True,
        "message": f"Berhasil mendaftarkan {len(extracted_embeddings)} sampel wajah untuk siswa {student.get('nama')}.",
        "samples_registered": len(extracted_embeddings),
        "warnings": errors if errors else None
    })

# =========================================================================
# FACE RECOGNITION TESTING
# =========================================================================

@attendance_bp.route("/api/face/recognize", methods=["POST"])
def recognize_face():
    """
    Endpoint pengujian kamera & pengenalan wajah:
    Menerima frame kamera, mendeteksi wajah, dan mengidentifikasi siswa.
    """
    data = request.get_json() or {}
    b64_img = data.get("image")

    if not b64_img:
        return jsonify({"success": False, "message": "Gambar tidak disertakan."}), 400

    cv_img = base64_to_cv2(b64_img)
    if cv_img is None:
        return jsonify({"success": False, "message": "Format gambar tidak valid."}), 400

    recognizer = get_face_recognizer()

    # Ekstrak embedding frame input
    query_emb, box, err = recognizer.extract_embedding(cv_img)
    if err or query_emb is None:
        return jsonify({"success": False, "message": err or "Wajah tidak terdeteksi."}), 400

    # Cek liveness sederhana
    is_live, live_msg, live_score = check_liveness(cv_img, box)
    if not is_live:
        return jsonify({
            "success": False,
            "message": live_msg,
            "liveness_passed": False
        }), 400

    # Cocokkan dengan data wajah di Firebase
    all_face_data = get_all_face_data()
    if not all_face_data:
        return jsonify({
            "success": False,
            "message": "Belum ada data wajah siswa yang terdaftar di sistem."
        }), 404

    matched_user_id, sim_score, is_match = recognizer.match_face(query_emb, all_face_data)

    if not is_match or not matched_user_id:
        return jsonify({
            "success": False,
            "message": "Wajah tidak dikenali. Silakan coba lagi.",
            "similarity": round(sim_score, 4)
        }), 404

    matched_user = get_user(matched_user_id)
    if not matched_user:
        return jsonify({"success": False, "message": "Data siswa pemilik wajah tidak ditemukan."}), 404

    return jsonify({
        "success": True,
        "message": f"Wajah teridentifikasi sebagai {matched_user.get('nama')}",
        "similarity": round(sim_score, 4),
        "student": {
            "uid": matched_user_id,
            "nis": matched_user.get("nis", ""),
            "nama": matched_user.get("nama", ""),
            "kelas": matched_user.get("kelas", "")
        }
    })

# =========================================================================
# ATTENDANCE CHECK-IN
# =========================================================================

@attendance_bp.route("/api/attendance/check-in", methods=["POST"])
def check_in():
    """
    Alur absensi siswa via face recognition:
    1. Ambil frame kamera base64.
    2. Backend mendeteksi wajah dan mengekstrak embedding.
    3. Backend mencocokkan dengan data wajah di Firebase.
    4. Cek aturan jam (Hadir / Terlambat).
    5. Cek absensi ganda (jika sudah absen hari ini, cegah duplikasi).
    6. Simpan absensi ke Firebase Realtime Database.
    """
    data = request.get_json() or {}
    b64_img = data.get("image")

    if not b64_img:
        return jsonify({
            "success": False,
            "message": "Kamera tidak dapat diakses atau frame tidak diterima. Pastikan browser memiliki izin kamera."
        }), 400

    cv_img = base64_to_cv2(b64_img)
    if cv_img is None:
        return jsonify({"success": False, "message": "Format gambar tidak valid."}), 400

    recognizer = get_face_recognizer()

    # Deteksi wajah & ekstrak embedding
    query_emb, box, err = recognizer.extract_embedding(cv_img)
    if err or query_emb is None:
        return jsonify({
            "success": False,
            "message": "Wajah belum terdeteksi. Posisikan wajah di depan kamera."
        }), 400

    # Liveness check
    is_live, live_msg, live_score = check_liveness(cv_img, box)
    if not is_live:
        return jsonify({
            "success": False,
            "message": live_msg
        }), 400

    # Pencocokan identitas wajah di backend
    all_face_data = get_all_face_data()
    if not all_face_data:
        return jsonify({
            "success": False,
            "message": "Belum ada siswa yang mendaftarkan wajah. Hubungi admin."
        }), 404

    matched_user_id, sim_score, is_match = recognizer.match_face(query_emb, all_face_data)

    if not is_match or not matched_user_id:
        return jsonify({
            "success": False,
            "message": "Wajah tidak dikenali. Silakan coba lagi.",
            "similarity": round(sim_score, 4)
        }), 404

    student = get_user(matched_user_id)
    if not student:
        return jsonify({"success": False, "message": "Data siswa tidak ditemukan."}), 404

    # Jika session aktif adalah siswa, pastikan wajah sesuai dengan siswa yang sedang login
    # (Kecuali jika aplikasi dibuka dalam mode Kios umum sekolah)
    current_session_user = session.get("user")
    if current_session_user and current_session_user.get("role") == "siswa":
        if current_session_user.get("uid") != matched_user_id:
            return jsonify({
                "success": False,
                "message": f"Wajah terdeteksi sebagai {student.get('nama')}, tidak sesuai dengan akun login ({current_session_user.get('nama')})."
            }), 403

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_time_str = now.strftime("%H:%M:%S")
    current_hm = now.strftime("%H:%M")

    # 1. Cek apakah sudah absen hari ini
    existing_attendance = get_attendance_for_user_today(today_str, matched_user_id)
    if existing_attendance:
        return jsonify({
            "success": False,
            "message": "Anda sudah melakukan absensi hari ini.",
            "data": existing_attendance
        }), 400

    # 2. Tentukan status kehadiran berdasarkan waktu batas
    late_time = Config.ATTENDANCE_LATE_TIME  # e.g. "07:15"
    if current_hm <= late_time:
        status_kehadiran = "Hadir"
    else:
        status_kehadiran = "Terlambat"

    record = {
        "userId": matched_user_id,
        "nis": student.get("nis", ""),
        "nama": student.get("nama", ""),
        "kelas": student.get("kelas", ""),
        "tanggal": today_str,
        "jam": current_time_str,
        "status": status_kehadiran,
        "method": "face_recognition",
        "confidence": round(sim_score, 4)
    }

    # Simpan ke Firebase Realtime Database
    save_attendance(today_str, matched_user_id, record)

    return jsonify({
        "success": True,
        "message": f"Absensi berhasil. Selamat datang, {student.get('nama')}.",
        "data": record
    })

# =========================================================================
# ATTENDANCE INQUIRY
# =========================================================================

@attendance_bp.route("/api/attendance/today", methods=["GET"])
@login_required
def get_today_attendance():
    today_str = datetime.now().strftime("%Y-%m-%d")
    current_user = session.get("user")

    if current_user.get("role") == "siswa":
        rec = get_attendance_for_user_today(today_str, current_user.get("uid"))
        return jsonify({
            "success": True,
            "today": today_str,
            "has_attended": rec is not None,
            "record": rec
        })
    else:
        # Admin: lihat seluruh absensi hari ini
        day_records = get_attendance_by_date(today_str)
        items = list(day_records.values()) if isinstance(day_records, dict) else []
        return jsonify({
            "success": True,
            "today": today_str,
            "count": len(items),
            "records": items
        })

@attendance_bp.route("/api/attendance/history", methods=["GET"])
@login_required
def get_attendance_history():
    current_user = session.get("user")
    target_user_id = request.args.get("user_id")

    # Siswa hanya boleh melihat riwayat absensi dirinya sendiri
    if current_user.get("role") == "siswa":
        target_user_id = current_user.get("uid")
    elif not target_user_id:
        target_user_id = current_user.get("uid")

    history = get_attendance_history_for_user(target_user_id)
    return jsonify({
        "success": True,
        "user_id": target_user_id,
        "history": history
    })

@attendance_bp.route("/api/attendance/manual", methods=["POST"])
@admin_required
def mark_attendance_manual():
    """Admin menandai absensi manual (Izin, Sakit, Alpa, Hadir, Terlambat)."""
    data = request.get_json() or {}
    user_id = data.get("user_id")
    tanggal = data.get("tanggal", datetime.now().strftime("%Y-%m-%d"))
    status = data.get("status", "Izin")
    keterangan = data.get("keterangan", "")

    student = get_user(user_id)
    if not student:
        return jsonify({"success": False, "message": "Siswa tidak ditemukan."}), 404

    record = {
        "userId": user_id,
        "nis": student.get("nis", ""),
        "nama": student.get("nama", ""),
        "kelas": student.get("kelas", ""),
        "tanggal": tanggal,
        "jam": datetime.now().strftime("%H:%M:%S"),
        "status": status,
        "method": "manual_admin",
        "keterangan": keterangan
    }

    save_attendance(tanggal, user_id, record)
    return jsonify({
        "success": True,
        "message": f"Status absensi {student.get('nama')} berhasil disimpan sebagai '{status}'.",
        "record": record
    })
