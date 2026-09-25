import os
import json
import logging
from datetime import datetime
from werkzeug.security import generate_password_hash
from config import Config

logger = logging.getLogger(__name__)

# Status koneksi Firebase
_firebase_app = None
_firebase_connected = False

# Fallback store (digunakan sebelum serviceAccountKey.json diunggah agar aplikasi dapat dijalankan)
_fallback_data = {
    "users": {},
    "face_data": {},
    "attendance": {}
}

def init_firebase():
    """
    Inisialisasi Firebase Admin SDK menggunakan serviceAccountKey.json dan Database URL.
    Jika file credential belum ada, sistem mengaktifkan mode fallback dengan notifikasi jelas.
    """
    global _firebase_app, _firebase_connected
    if _firebase_app is not None:
        return _firebase_connected

    cred_path = Config.FIREBASE_CREDENTIALS_PATH
    db_url = Config.FIREBASE_DATABASE_URL

    if os.path.exists(cred_path):
        try:
            import firebase_admin
            from firebase_admin import credentials, db

            # Cek apakah firebase_admin sudah pernah diinisialisasi
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_path)
                _firebase_app = firebase_admin.initialize_app(cred, {
                    'databaseURL': db_url
                })
            else:
                _firebase_app = firebase_admin.get_app()

            _firebase_connected = True
            logger.info(f"Firebase Admin SDK berhasil terhubung ke Realtime Database: {db_url}")
            print(f"[FIREBASE] Berhasil terhubung ke Firebase Realtime Database: {db_url}")
        except Exception as e:
            logger.error(f"Gagal menghubungkan Firebase: {e}")
            print(f"[FIREBASE WARNING] Gagal menghubungkan Firebase Admin: {e}")
            _firebase_connected = False
    else:
        _firebase_connected = False
        print("=" * 70)
        print("[PERHATIAN KONFIGURASI FIREBASE]")
        print(f"File credential '{cred_path}' belum ditemukan.")
        print("Sistem berjalan dalam mode transisi (Firebase Placeholder / Local Buffer).")
        print("Untuk menghubungkan ke Firebase Realtime Database asli:")
        print("1. Buka Firebase Console: https://console.firebase.google.com/project/absensi-ai-6cced")
        print("2. Pilih Project Settings > Service accounts > Generate new private key")
        print("3. Simpan file tersebut sebagai 'serviceAccountKey.json' di root direktori project ini.")
        print("=" * 70)

    # Seed admin default
    seed_default_admin()
    return _firebase_connected

def is_firebase_connected():
    return _firebase_connected

def get_db():
    if _firebase_connected:
        from firebase_admin import db
        return db
    return None

# =========================================================================
# USERS CRUD
# =========================================================================

def get_user(user_id):
    if _firebase_connected:
        try:
            from firebase_admin import db
            ref = db.reference(f'users/{user_id}')
            return ref.get()
        except Exception as e:
            logger.error(f"Firebase get_user error: {e}")
    return _fallback_data["users"].get(user_id)

def get_user_by_username_or_nis(identifier):
    """Mencari user berdasarkan NIS atau username."""
    identifier_str = str(identifier).strip()
    if _firebase_connected:
        try:
            from firebase_admin import db
            ref = db.reference('users')
            users = ref.get() or {}
            for uid, user in users.items():
                if str(user.get("nis", "")).strip() == identifier_str:
                    return user
                if str(user.get("username", "")).strip().lower() == identifier_str.lower():
                    return user
                if uid == identifier_str:
                    return user
            return None
        except Exception as e:
            logger.error(f"Firebase find user error: {e}")

    for uid, user in _fallback_data["users"].items():
        if str(user.get("nis", "")).strip() == identifier_str:
            return user
        if str(user.get("username", "")).strip().lower() == identifier_str.lower():
            return user
        if uid == identifier_str:
            return user
    return None

def create_or_update_user(user_id, data):
    data["updatedAt"] = datetime.now().isoformat()
    if "createdAt" not in data:
        data["createdAt"] = datetime.now().isoformat()

    if _firebase_connected:
        try:
            from firebase_admin import db
            ref = db.reference(f'users/{user_id}')
            ref.set(data)
            _fallback_data["users"][user_id] = data
            return True
        except Exception as e:
            logger.error(f"Firebase create_or_update_user error: {e}")

    _fallback_data["users"][user_id] = data
    return True

def delete_user(user_id):
    if _firebase_connected:
        try:
            from firebase_admin import db
            db.reference(f'users/{user_id}').delete()
            db.reference(f'face_data/{user_id}').delete()
        except Exception as e:
            logger.error(f"Firebase delete_user error: {e}")

    _fallback_data["users"].pop(user_id, None)
    _fallback_data["face_data"].pop(user_id, None)
    return True

def get_all_students():
    result = []
    if _firebase_connected:
        try:
            from firebase_admin import db
            users = db.reference('users').get() or {}
            for uid, user in users.items():
                if user and user.get("role") == "siswa":
                    user_dict = dict(user)
                    user_dict["uid"] = uid
                    result.append(user_dict)
            return sorted(result, key=lambda x: x.get("nama", "").lower())
        except Exception as e:
            logger.error(f"Firebase get_all_students error: {e}")

    for uid, user in _fallback_data["users"].items():
        if user and user.get("role") == "siswa":
            user_dict = dict(user)
            user_dict["uid"] = uid
            result.append(user_dict)
    return sorted(result, key=lambda x: x.get("nama", "").lower())

# =========================================================================
# FACE DATA
# =========================================================================

def get_face_data(user_id):
    if _firebase_connected:
        try:
            from firebase_admin import db
            return db.reference(f'face_data/{user_id}').get()
        except Exception as e:
            logger.error(f"Firebase get_face_data error: {e}")
    return _fallback_data["face_data"].get(user_id)

def save_face_embeddings(user_id, embeddings_list):
    """
    Menyimpan face embeddings siswa ke Firebase Realtime Database
    Struktur: face_data / USER_ID / embeddings / { embedding1: [...], embedding2: [...] }
    """
    embeddings_dict = {}
    for idx, emb in enumerate(embeddings_list, start=1):
        embeddings_dict[f"embedding{idx}"] = emb

    payload = {
        "embeddings": embeddings_dict,
        "updatedAt": datetime.now().isoformat()
    }

    if _firebase_connected:
        try:
            from firebase_admin import db
            ref = db.reference(f'face_data/{user_id}')
            ref.set(payload)
            _fallback_data["face_data"][user_id] = payload
            return True
        except Exception as e:
            logger.error(f"Firebase save_face_embeddings error: {e}")

    _fallback_data["face_data"][user_id] = payload
    return True

def reset_face_data(user_id):
    if _firebase_connected:
        try:
            from firebase_admin import db
            db.reference(f'face_data/{user_id}').delete()
        except Exception as e:
            logger.error(f"Firebase reset_face_data error: {e}")
    _fallback_data["face_data"].pop(user_id, None)
    return True

def get_all_face_data():
    """Mengambil seluruh data face embedding untuk pencocokan AI."""
    if _firebase_connected:
        try:
            from firebase_admin import db
            return db.reference('face_data').get() or {}
        except Exception as e:
            logger.error(f"Firebase get_all_face_data error: {e}")
    return _fallback_data["face_data"]

# =========================================================================
# ATTENDANCE
# =========================================================================

def save_attendance(date_str, user_id, record):
    """
    Menyimpan absensi ke Firebase Realtime Database:
    Struktur: attendance / {YYYY-MM-DD} / {USER_ID}
    """
    if _firebase_connected:
        try:
            from firebase_admin import db
            ref = db.reference(f'attendance/{date_str}/{user_id}')
            ref.set(record)
            if date_str not in _fallback_data["attendance"]:
                _fallback_data["attendance"][date_str] = {}
            _fallback_data["attendance"][date_str][user_id] = record
            return True
        except Exception as e:
            logger.error(f"Firebase save_attendance error: {e}")

    if date_str not in _fallback_data["attendance"]:
        _fallback_data["attendance"][date_str] = {}
    _fallback_data["attendance"][date_str][user_id] = record
    return True

def get_attendance_by_date(date_str):
    if _firebase_connected:
        try:
            from firebase_admin import db
            return db.reference(f'attendance/{date_str}').get() or {}
        except Exception as e:
            logger.error(f"Firebase get_attendance_by_date error: {e}")
    return _fallback_data["attendance"].get(date_str, {})

def get_attendance_for_user_today(date_str, user_id):
    if _firebase_connected:
        try:
            from firebase_admin import db
            return db.reference(f'attendance/{date_str}/{user_id}').get()
        except Exception as e:
            logger.error(f"Firebase get_attendance_for_user_today error: {e}")
    return _fallback_data["attendance"].get(date_str, {}).get(user_id)

def get_attendance_history_for_user(user_id):
    """Mengambil riwayat absensi seorang siswa diurutkan dari terbaru."""
    records = []
    all_data = {}
    if _firebase_connected:
        try:
            from firebase_admin import db
            all_data = db.reference('attendance').get() or {}
        except Exception as e:
            logger.error(f"Firebase get history error: {e}")
            all_data = _fallback_data["attendance"]
    else:
        all_data = _fallback_data["attendance"]

    for date_key, day_records in (all_data or {}).items():
        if isinstance(day_records, dict) and user_id in day_records:
            item = dict(day_records[user_id])
            if "tanggal" not in item:
                item["tanggal"] = date_key
            records.append(item)

    # Urutkan berdasarkan tanggal descending
    records.sort(key=lambda x: x.get("tanggal", ""), reverse=True)
    return records

def get_all_attendance_records():
    """Mengambil seluruh data absensi untuk laporan dan statistik admin."""
    records = []
    all_data = {}
    if _firebase_connected:
        try:
            from firebase_admin import db
            all_data = db.reference('attendance').get() or {}
        except Exception as e:
            logger.error(f"Firebase get all attendance error: {e}")
            all_data = _fallback_data["attendance"]
    else:
        all_data = _fallback_data["attendance"]

    for date_key, day_records in (all_data or {}).items():
        if isinstance(day_records, dict):
            for uid, item in day_records.items():
                if isinstance(item, dict):
                    rec = dict(item)
                    if "tanggal" not in rec:
                        rec["tanggal"] = date_key
                    if "userId" not in rec:
                        rec["userId"] = uid
                    records.append(rec)

    records.sort(key=lambda x: (x.get("tanggal", ""), x.get("jam", "")), reverse=True)
    return records

# =========================================================================
# INITIAL SEEDING
# =========================================================================

def seed_default_admin():
    """Membuat akun default admin dan beberapa siswa sampel jika database kosong."""
    admin_user = get_user("admin_user")
    if not admin_user:
        admin_data = {
            "uid": "admin_user",
            "username": "admin",
            "password": generate_password_hash("admin123"),
            "nama": "Administrator",
            "role": "admin",
            "status": "active",
            "createdAt": datetime.now().isoformat()
        }
        create_or_update_user("admin_user", admin_data)

    # Cek apakah ada siswa sampel
    students = get_all_students()
    if len(students) == 0:
        sample_students = [
            {
                "uid": "siswa_1001",
                "nis": "1001",
                "username": "1001",
                "password": generate_password_hash("siswa123"),
                "nama": "Budi Santoso",
                "kelas": "XI IPA 1",
                "gender": "Laki-laki",
                "role": "siswa",
                "status": "active",
                "createdAt": datetime.now().isoformat()
            },
            {
                "uid": "siswa_1002",
                "nis": "1002",
                "username": "1002",
                "password": generate_password_hash("siswa123"),
                "nama": "Siti Nurhaliza",
                "kelas": "XI IPS 1",
                "gender": "Perempuan",
                "role": "siswa",
                "status": "active",
                "createdAt": datetime.now().isoformat()
            },
            {
                "uid": "siswa_1003",
                "nis": "1003",
                "username": "1003",
                "password": generate_password_hash("siswa123"),
                "nama": "Ahmad Fauzi",
                "kelas": "XI IPA 2",
                "gender": "Laki-laki",
                "role": "siswa",
                "status": "active",
                "createdAt": datetime.now().isoformat()
            }
        ]
        for s in sample_students:
            create_or_update_user(s["uid"], s)
