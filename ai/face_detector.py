import os
import cv2
import numpy as np

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
YUNET_PATH = os.path.join(MODEL_DIR, "face_detection_yunet_2023mar.onnx")

class FaceDetector:
    def __init__(self, confidence_threshold=0.6, nms_threshold=0.3):
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.yunet = None
        self.haar_cascade = None

        # Coba inisialisasi YuNet ONNX
        if not os.path.exists(YUNET_PATH):
            try:
                import urllib.request
                os.makedirs(MODEL_DIR, exist_ok=True)
                print("[FaceDetector] Mengunduh model YuNet...")
                urllib.request.urlretrieve(
                    "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
                    YUNET_PATH
                )
            except Exception as e:
                print(f"[FaceDetector] Gagal download YuNet: {e}")

        if os.path.exists(YUNET_PATH):
            try:
                self.yunet = cv2.FaceDetectorYN.create(
                    model=YUNET_PATH,
                    config="",
                    input_size=(320, 320),
                    score_threshold=self.confidence_threshold,
                    nms_threshold=self.nms_threshold,
                    top_k=5000
                )
                print("[FaceDetector] Menggunakan OpenCV YuNet Deep Learning Detector")
            except Exception as e:
                print(f"[FaceDetector] Warning YuNet: {e}, beralih ke Haar Cascade")
                self.yunet = None

        # Fallback Haar Cascade bawaan OpenCV
        if self.yunet is None:
            haar_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.haar_cascade = cv2.CascadeClassifier(haar_path)
            print("[FaceDetector] Menggunakan OpenCV Haar Cascade Detector")

    def detect_faces(self, image):
        """
        Mendeteksi wajah pada gambar BGR.
        Mengembalikan list objek:
        [
            {
                "box": (x, y, w, h),
                "confidence": float,
                "landmarks": array/None,
                "raw_face": face_crop_img,
                "aligned_face": aligned_img
            }
        ]
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        faces = []

        if self.yunet is not None:
            try:
                self.yunet.setInputSize((w, h))
                _, detections = self.yunet.detect(image)
                if detections is not None:
                    for det in detections:
                        score = float(det[-1])
                        if score >= self.confidence_threshold:
                            # Box: x, y, w, h
                            bx = int(max(0, det[0]))
                            by = int(max(0, det[1]))
                            bw = int(min(w - bx, det[2]))
                            bh = int(min(h - by, det[3]))

                            if bw > 20 and bh > 20:
                                face_crop = image[by:by+bh, bx:bx+bw]
                                faces.append({
                                    "box": (bx, by, bw, bh),
                                    "confidence": score,
                                    "raw_detection": det,
                                    "raw_face": face_crop
                                })
                    return faces
            except Exception as e:
                print(f"[FaceDetector] Error deteksi YuNet: {e}")

        # Fallback ke Haar Cascade jika YuNet gagal atau tidak ada
        if self.haar_cascade is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            detected = self.haar_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60)
            )
            for (bx, by, bw, bh) in detected:
                face_crop = image[by:by+bh, bx:bx+bw]
                faces.append({
                    "box": (int(bx), int(by), int(bw), int(bh)),
                    "confidence": 0.85,
                    "raw_detection": None,
                    "raw_face": face_crop
                })

        return faces

    def get_largest_face(self, image):
        """Mengambil satu wajah terbesar di dalam frame."""
        faces = self.detect_faces(image)
        if not faces:
            return None
        # Pilih berdasarkan area terbesar (w * h)
        return max(faces, key=lambda f: f["box"][2] * f["box"][3])
