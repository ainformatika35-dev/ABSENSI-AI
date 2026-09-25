from functools import wraps
from flask import Blueprint, request, jsonify, session, redirect, url_for
from werkzeug.security import check_password_hash
from firebase.firebase_config import get_user_by_username_or_nis, get_user

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Autentikasi diperlukan. Silakan login."}), 401
            return redirect(url_for("page_login"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Autentikasi diperlukan. Silakan login."}), 401
            return redirect(url_for("page_login"))
        if session["user"].get("role") != "admin":
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Akses ditolak. Memerlukan role admin."}), 403
            return redirect(url_for("page_siswa_dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def siswa_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Autentikasi diperlukan. Silakan login."}), 401
            return redirect(url_for("page_login"))
        if session["user"].get("role") != "siswa":
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "message": "Akses khusus siswa."}), 403
            return redirect(url_for("page_admin_dashboard"))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    identifier = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not identifier or not password:
        return jsonify({"success": False, "message": "Username/NIS dan password harus diisi."}), 400

    user = get_user_by_username_or_nis(identifier)
    if not user:
        return jsonify({"success": False, "message": "User dengan NIS/Username tersebut tidak ditemukan."}), 404

    # Cek status user
    if user.get("status") == "inactive":
        return jsonify({"success": False, "message": "Akun ini telah dinonaktifkan oleh administrator."}), 403

    # Verifikasi password
    stored_password = user.get("password", "")
    is_valid = False
    if stored_password.startswith("pbkdf2:") or stored_password.startswith("scrypt:"):
        is_valid = check_password_hash(stored_password, password)
    else:
        # Fallback jika password lama berupa plain text
        is_valid = (stored_password == password)

    if not is_valid:
        return jsonify({"success": False, "message": "Password yang dimasukkan salah."}), 401

    # Set user session
    session["user"] = {
        "uid": user.get("uid"),
        "nis": user.get("nis", ""),
        "nama": user.get("nama", "User"),
        "role": user.get("role", "siswa"),
        "kelas": user.get("kelas", "")
    }

    redirect_url = "/admin/dashboard" if user.get("role") == "admin" else "/siswa/dashboard"
    return jsonify({
        "success": True,
        "message": f"Login berhasil sebagai {user.get('nama')}",
        "user": session["user"],
        "redirect": redirect_url
    })

@auth_bp.route("/logout", methods=["POST", "GET"])
def api_logout():
    session.clear()
    if request.method == "GET":
        return redirect(url_for("page_login"))
    return jsonify({"success": True, "message": "Berhasil logout."})

@auth_bp.route("/me", methods=["GET"])
def api_me():
    user = session.get("user")
    if not user:
        return jsonify({"success": False, "authenticated": False}), 401
    return jsonify({"success": True, "authenticated": True, "user": user})
