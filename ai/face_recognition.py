import os
import cv2
import numpy as np
from config import Config
from ai.face_detector import FaceDetector
from ai.face_utils import cosine_similarity, check_liveness

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
SFACE_PATH = os.path.join(MODEL_DIR, "face_recognition_sface_2021dec.onnx")

class FaceRecognizer:
    def __init__(self, threshold=None):
        self.threshold = threshold if threshold is not None else Config.FACE_RECOGNITION_THRESHOLD
        self.detector = FaceDetector()
        self.sface = None

        if not os.path.exists(SFACE_PATH):
            try:
                import urllib.request
                os.makedirs(MODEL_DIR, exist_ok=True)
                print("[FaceRecognizer] Mengunduh model SFace...")
                urllib.request.urlretrieve(
                    "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
                    SFACE_PATH
                )
            except Exception as e:
                print(f"[FaceRecognizer] Gagal download SFace: {e}")

        if os.path.exists(SFACE_PATH):
            try:
                self.sface = cv2.FaceRecognizerSF.create(SFACE_PATH, "")
                print(f"[FaceRecognizer] SFace 128D Deep Learning Recognizer aktif (Threshold: {self.threshold})")
            except Exception as e:
                print(f"[FaceRecognizer] Gagal inisialisasi SFace: {e}")
                self.sface = None

    def extract_embedding(self, image, face_info=None):
        """
        Mengekstrak embedding vektor 128-dimensi dari gambar wajah.
        Jika face_info tidak diberikan, detector akan mendeteksi wajah terlebih dahulu.
        Mengembalikan (embedding_list, face_box, error_message).
        """
        if image is None or image.size == 0:
            return None, None, "Gambar kosong atau tidak valid"

        if face_info is None:
            face_info = self.detector.get_largest_face(image)

        if not face_info:
            return None, None, "Wajah tidak terdeteksi. Posisikan wajah di depan kamera."

        box = face_info["box"]
        raw_det = face_info.get("raw_detection")
        face_crop = face_info.get("raw_face")

        if self.sface is not None:
            try:
                aligned = None
                if raw_det is not None:
                    # Gunakan alignCrop bawaan SFace jika deteksi dari YuNet
                    aligned = self.sface.alignCrop(image, raw_det)
                elif face_crop is not None and face_crop.size > 0:
                    aligned = cv2.resize(face_crop, (112, 112))

                if aligned is not None:
                    feature = self.sface.feature(aligned)
                    # Normalisasi L2
                    feat_norm = feature / np.linalg.norm(feature)
                    embedding_list = [float(x) for x in feat_norm.flatten()]
                    return embedding_list, box, None
            except Exception as e:
                print(f"[FaceRecognizer] Error ekstraksi SFace: {e}")

        # Fallback embedding jika SFace gagal
        if face_crop is not None and face_crop.size > 0:
            try:
                resized = cv2.resize(face_crop, (64, 64))
                gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
                # Standarisasi dan L2 norm
                norm = (gray.astype(np.float32) - np.mean(gray)) / (np.std(gray) + 1e-5)
                # Resample ke 128 dimensi
                hist = cv2.calcHist([gray], [0], None, [128], [0, 256]).flatten()
                hist = hist / (np.linalg.norm(hist) + 1e-5)
                return [float(x) for x in hist], box, None
            except Exception as e:
                return None, None, f"Gagal mengekstrak fitur wajah: {e}"

        return None, None, "Gagal memproses potongan wajah"

    def match_face(self, query_embedding, all_face_data, threshold=None):
        """
        Mencocokkan embedding wajah input dengan seluruh data embedding yang terdaftar.
        all_face_data struktur dari Firebase:
        {
            "USER_ID": {
                "embeddings": {
                    "embedding1": [...],
                    "embedding2": [...]
                }
            }
        }
        Mengembalikan (matched_user_id, best_score, is_match)
        """
        active_threshold = threshold if threshold is not None else self.threshold

        if not query_embedding or not all_face_data:
            return None, 0.0, False

        best_user_id = None
        best_similarity = -1.0

        for user_id, data in all_face_data.items():
            if not data or not isinstance(data, dict):
                continue

            embeddings_group = data.get("embeddings", {})
            if not isinstance(embeddings_group, dict):
                continue

            # Periksa terhadap setiap sampel embedding siswa
            for emb_key, stored_emb in embeddings_group.items():
                if not stored_emb or not isinstance(stored_emb, list):
                    continue

                sim = cosine_similarity(query_embedding, stored_emb)
                if sim > best_similarity:
                    best_similarity = sim
                    best_user_id = user_id

        # Cek apakah skor memenuhi threshold kemiripan
        is_match = best_similarity >= active_threshold
        return best_user_id, float(best_similarity), is_match

# Singleton instance
recognizer_instance = None

def get_face_recognizer():
    global recognizer_instance
    if recognizer_instance is None:
        recognizer_instance = FaceRecognizer()
    return recognizer_instance
