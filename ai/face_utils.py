import cv2
import numpy as np
import base64
import re

def base64_to_cv2(b64_string):
    """
    Mengonversi string base64 (termasuk data URL seperti data:image/jpeg;base64,...)
    menjadi gambar OpenCV (BGR ndarray).
    """
    if not b64_string:
        return None

    # Hapus prefix header data:image/xxx;base64, jika ada
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[face_utils] Error decode base64: {e}")
        return None

def cv2_to_base64(img, format=".jpg"):
    """Mengonversi gambar OpenCV ke string base64 dengan header JPEG."""
    try:
        success, encoded_img = cv2.imencode(format, img)
        if not success:
            return None
        b64_bytes = base64.b64encode(encoded_img).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_bytes}"
    except Exception as e:
        print(f"[face_utils] Error encode base64: {e}")
        return None

def check_blur(img, min_variance=40.0):
    """
    Mengecek apakah gambar kabur menggunakan Laplacian variance.
    Mengembalikan (is_clear: bool, variance: float).
    """
    if img is None or img.size == 0:
        return False, 0.0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance >= min_variance, variance

def check_liveness(img, face_box=None):
    """
    Deteksi keaslian wajah (liveness sederhana) untuk mencegah spoofing foto cetak/layar hp:
    1. Cek ketajaman (blur / laplacian variance)
    2. Cek variasi kecerahan dan kontras alami kulit
    3. Cek ukuran wajah memadai
    Mengembalikan (is_live: bool, message: str, score: float)
    """
    if img is None or img.size == 0:
        return False, "Gambar kosong", 0.0

    is_clear, variance = check_blur(img, min_variance=35.0)
    if not is_clear:
        return False, "Wajah buram atau pencahayaan kurang. Posisikan wajah dengan tenang dan terang.", variance

    # Cek kontras dan distribusi histogram
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    std_dev = np.std(gray)
    if std_dev < 18.0:
        return False, "Kontras wajah terlalu rendah atau layar silau.", float(std_dev)

    # Jika face box ada, periksa rasio area wajah terhadap frame
    if face_box is not None:
        x, y, w, h = face_box
        if w < 70 or h < 70:
            return False, "Posisikan wajah lebih dekat ke kamera.", float(min(w, h))

    return True, "Wajah valid dan jelas", variance

def cosine_similarity(v1, v2):
    """Menghitung cosine similarity antara dua embedding 1D (skor 0 - 1)."""
    a = np.array(v1, dtype=np.float32).flatten()
    b = np.array(v2, dtype=np.float32).flatten()
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def l2_distance(v1, v2):
    """Menghitung Euclidean (L2) distance antara dua embedding 1D."""
    a = np.array(v1, dtype=np.float32).flatten()
    b = np.array(v2, dtype=np.float32).flatten()
    return float(np.linalg.norm(a - b))
