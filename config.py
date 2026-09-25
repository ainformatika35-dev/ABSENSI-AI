import os
from dotenv import load_dotenv

# Muat file .env jika ada
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "absensi-ai-default-secret-key-2026")
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")

    # Firebase Admin Configuration
    FIREBASE_DATABASE_URL = os.getenv(
        "FIREBASE_DATABASE_URL",
        "https://absensi-ai-6cced-default-rtdb.firebaseio.com/"
    )
    FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
    if not os.path.isabs(FIREBASE_CREDENTIALS_PATH):
        FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, FIREBASE_CREDENTIALS_PATH)

    # Firebase Web Configuration (untuk frontend modular SDK)
    FIREBASE_WEB_CONFIG = {
        "apiKey": "AIzaSyA4-L0W2ecqPH3T5gh3j7diNUbx1RrMfyY",
        "authDomain": "absensi-ai-6cced.firebaseapp.com",
        "projectId": "absensi-ai-6cced",
        "storageBucket": "absensi-ai-6cced.firebasestorage.app",
        "messagingSenderId": "822149982282",
        "appId": "1:822149982282:web:bf27020e110e5273dedeb3",
        "measurementId": "G-GL0WEQZEC4",
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "https://absensi-ai-6cced-default-rtdb.firebaseio.com/")
    }

    # Aturan Waktu Absensi
    ATTENDANCE_START_TIME = os.getenv("ATTENDANCE_START_TIME", "07:00")
    ATTENDANCE_LATE_TIME = os.getenv("ATTENDANCE_LATE_TIME", "07:15")

    # Threshold Pengenalan Wajah
    # Nilai jarak Euclidean / Cosine (default 0.50)
    FACE_RECOGNITION_THRESHOLD = float(os.getenv("FACE_RECOGNITION_THRESHOLD", "0.50"))
