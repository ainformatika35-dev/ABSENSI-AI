import os
from flask import Flask, render_template, redirect, url_for, session, request
from config import Config
from firebase.firebase_config import init_firebase, is_firebase_connected
from routes.auth import auth_bp, login_required, admin_required, siswa_required
from routes.attendance import attendance_bp
from routes.students import students_bp
from routes.reports import reports_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inisialisasi Firebase
    with app.app_context():
        init_firebase()

    # Daftarkan Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(reports_bp)

    # Template Context Processor (Menyediakan user dan status firebase ke seluruh template)
    @app.context_processor
    def inject_global_data():
        return {
            "current_user": session.get("user"),
            "firebase_connected": is_firebase_connected(),
            "firebase_web_config": Config.FIREBASE_WEB_CONFIG,
            "late_time": Config.ATTENDANCE_LATE_TIME
        }

    # =========================================================================
    # PAGE ROUTES
    # =========================================================================

    @app.route("/")
    def index():
        user = session.get("user")
        if not user:
            return redirect(url_for("page_login"))
        if user.get("role") == "admin":
            return redirect(url_for("page_admin_dashboard"))
        return redirect(url_for("page_siswa_dashboard"))

    @app.route("/login")
    def page_login():
        user = session.get("user")
        if user:
            if user.get("role") == "admin":
                return redirect(url_for("page_admin_dashboard"))
            return redirect(url_for("page_siswa_dashboard"))
        return render_template("login.html")

    # =========================================================================
    # SISWA PAGES
    # =========================================================================

    @app.route("/siswa/dashboard")
    @siswa_required
    def page_siswa_dashboard():
        return render_template("siswa/dashboard.html")

    @app.route("/siswa/attendance")
    @siswa_required
    def page_siswa_attendance():
        return render_template("siswa/attendance.html")

    @app.route("/siswa/history")
    @siswa_required
    def page_siswa_history():
        return render_template("siswa/history.html")

    # =========================================================================
    # ADMIN PAGES
    # =========================================================================

    @app.route("/admin/dashboard")
    @admin_required
    def page_admin_dashboard():
        return render_template("admin/dashboard.html")

    @app.route("/admin/students")
    @admin_required
    def page_admin_students():
        return render_template("admin/students.html")

    @app.route("/admin/face-registration")
    @admin_required
    def page_admin_face_registration():
        return render_template("admin/face_registration.html")

    @app.route("/admin/reports")
    @admin_required
    def page_admin_reports():
        return render_template("admin/reports.html")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("login.html", error_msg="Halaman tidak ditemukan"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("login.html", error_msg="Terjadi kesalahan pada server"), 500

    return app

app = create_app()

if __name__ == "__main__":
    print("=" * 65)
    print("  ABSENSI-AI: Aplikasi Presensi Wajah Berbasis AI & Firebase  ")
    print("=" * 65)
    print(f"  * Mode        : {'Development' if Config.DEBUG else 'Production'}")
    print(f"  * Alamat Server: http://localhost:{Config.PORT}")
    print(f"  * Akun Default Admin : admin / admin123")
    print(f"  * Akun Default Siswa : 1001 / siswa123")
    print("=" * 65)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
