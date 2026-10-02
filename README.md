<div align="center">

<img src="static/images/logo.svg" alt="ABSENSI-AI Logo" width="100"/>

# 🎓 ABSENSI-AI

### Sistem Presensi Cerdas Berbasis Pengenalan Wajah & Firebase

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Realtime_DB-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**ABSENSI-AI** adalah aplikasi presensi modern untuk sekolah yang menggunakan teknologi **AI pengenalan wajah** (Face Recognition) secara real-time melalui kamera, dengan penyimpanan data berbasis **Firebase Realtime Database**.

</div>

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🤖 **Face Recognition AI** | Pengenalan wajah real-time menggunakan model SFace 128-dimensi (OpenCV Zoo) |
| 📷 **Registrasi Wajah** | Admin dapat mendaftarkan wajah siswa langsung melalui kamera web |
| ⏰ **Deteksi Keterlambatan** | Sistem otomatis menandai status Hadir / Terlambat berdasarkan jam yang dikonfigurasi |
| 🔐 **Multi-Role Auth** | Sistem login terpisah untuk Admin dan Siswa |
| 📊 **Dashboard Analitik** | Dashboard real-time untuk admin dan siswa |
| 📄 **Laporan Excel** | Export laporan kehadiran ke format `.xlsx` menggunakan openpyxl |
| ☁️ **Firebase Realtime** | Semua data tersinkronisasi secara real-time via Firebase |
| 🌐 **Antarmuka Responsif** | Tampilan web yang bersih dan responsif |

---

## 🧠 Teknologi AI

Aplikasi ini menggunakan dua model **ONNX** dari [OpenCV Zoo](https://github.com/opencv/opencv_zoo):

| Model | Fungsi |
|-------|--------|
| `face_detection_yunet_2023mar.onnx` | Deteksi lokasi wajah dalam frame kamera |
| `face_recognition_sface_2021dec.onnx` | Ekstraksi embedding vektor 128-dimensi untuk pengenalan wajah |

Kecocokan wajah dihitung menggunakan **Cosine Similarity**. Model diunduh otomatis saat pertama kali dijalankan jika belum tersedia.

---

## 🗂️ Struktur Proyek

```
ABSENSI-AI/
├── app.py                      # Entry point aplikasi Flask
├── config.py                   # Konfigurasi aplikasi (env vars)
├── requirements.txt            # Dependensi Python
├── database.rules.json         # Aturan keamanan Firebase
├── .env.example                # Contoh file konfigurasi environment
│
├── ai/                         # Modul Kecerdasan Buatan
│   ├── face_detector.py        # Deteksi wajah (YuNet)
│   ├── face_recognition.py     # Pengenalan & pencocokan wajah (SFace)
│   ├── face_utils.py           # Utilitas: cosine similarity, liveness
│   └── models/                 # Model ONNX (diunduh otomatis / tidak di-commit)
│
├── firebase/                   # Modul Koneksi Firebase
│   └── firebase_config.py      # Inisialisasi Firebase Admin SDK
│
├── routes/                     # Blueprint Rute Flask
│   ├── auth.py                 # Login, logout, dekorator role
│   ├── attendance.py           # API absensi & pengenalan wajah
│   ├── students.py             # CRUD data siswa & registrasi wajah
│   └── reports.py              # Laporan & export Excel
│
├── templates/                  # Template HTML (Jinja2)
│   ├── base.html               # Layout utama
│   ├── login.html              # Halaman login
│   ├── admin/                  # Halaman khusus Admin
│   │   ├── dashboard.html
│   │   ├── students.html
│   │   ├── face_registration.html
│   │   └── reports.html
│   └── siswa/                  # Halaman khusus Siswa
│       ├── dashboard.html
│       ├── attendance.html
│       └── history.html
│
└── static/                     # Aset Statis
    ├── css/style.css           # Stylesheet
    ├── js/                     # JavaScript (kamera, absensi, dashboard)
    └── images/logo.svg         # Logo aplikasi
```

---

## ⚙️ Instalasi & Menjalankan

### Prasyarat

- **Python 3.11+**
- **Git**
- Akun **Firebase** dengan proyek aktif
- **Service Account Key** dari Firebase Console

### 1. Clone Repositori

```bash
git clone https://github.com/ainformatika35-dev/ABSENSI-AI.git
cd ABSENSI-AI
```

### 2. Buat & Aktifkan Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependensi

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment

Salin file `.env.example` menjadi `.env` dan sesuaikan nilainya:

```bash
cp .env.example .env
```

Isi file `.env`:

```env
# Flask
FLASK_SECRET_KEY=ganti_dengan_kunci_rahasia_anda
DEBUG=True
PORT=5000
HOST=0.0.0.0

# Firebase
FIREBASE_DATABASE_URL=https://<project-id>-default-rtdb.firebaseio.com/
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json

# Pengenalan Wajah
FACE_RECOGNITION_THRESHOLD=0.50

# Jam Absensi
ATTENDANCE_START_TIME=07:00
ATTENDANCE_LATE_TIME=07:15
```

### 5. Setup Firebase

1. Buka [Firebase Console](https://console.firebase.google.com/) → pilih proyek Anda
2. Masuk ke **Project Settings** → **Service Accounts** → **Generate new private key**
3. Simpan file yang diunduh sebagai `serviceAccountKey.json` di root proyek
4. Aktifkan **Realtime Database** di Firebase Console
5. Terapkan aturan keamanan dari file `database.rules.json`

> ⚠️ **PENTING:** Jangan pernah commit file `serviceAccountKey.json` atau `.env` ke repositori publik!

### 6. Jalankan Aplikasi

```bash
python app.py
```

Akses aplikasi di browser: **[http://localhost:5000](http://localhost:5000)**

---

## 🔑 Akun Default

| Role | Username / NIS | Password |
|------|----------------|----------|
| **Admin** | `admin` | `admin123` |
| **Siswa** | `1001` | `siswa123` |

> 💡 Ubah password default segera setelah login pertama.

---

## 📱 Alur Penggunaan

```
[Admin Login]
    │
    ├── Tambah Data Siswa (Nama, NIS, Kelas)
    │
    ├── Registrasi Wajah Siswa (via Kamera)
    │       └── Sistem simpan embedding 128D ke Firebase
    │
    └── Monitor Dashboard (Statistik Kehadiran)
            └── Export Laporan ke Excel

[Siswa Login]
    │
    ├── Lakukan Absensi (via Kamera)
    │       └── AI cocokkan wajah → catat Hadir / Terlambat
    │
    └── Lihat Riwayat Kehadiran Pribadi
```

---

## 🚦 Status Kehadiran

| Status | Kondisi |
|--------|---------|
| ✅ **Hadir** | Check-in sebelum batas waktu terlambat (`ATTENDANCE_LATE_TIME`) |
| ⚠️ **Terlambat** | Check-in setelah batas waktu terlambat |
| ❌ **Tidak Hadir** | Tidak ada check-in sama sekali |

---

## 🔧 Konfigurasi Lanjutan

### Threshold Pengenalan Wajah

Nilai `FACE_RECOGNITION_THRESHOLD` (0.0 – 1.0) mengontrol tingkat keketatan pengenalan:

- **0.4** → Ketat (hanya cocok jika sangat mirip)
- **0.5** → Seimbang *(default)*
- **0.6** → Longgar (lebih mudah cocok)

### Model AI

Model ONNX akan **diunduh otomatis** dari OpenCV Zoo saat pertama dijalankan jika belum ada di folder `ai/models/`. Untuk instalasi offline, unduh secara manual:

- [YuNet (Deteksi)](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
- [SFace (Pengenalan)](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)

---

## 📦 Dependensi

| Library | Versi Minimum | Fungsi |
|---------|---------------|--------|
| `Flask` | 3.0.0 | Web framework |
| `firebase-admin` | 6.5.0 | Koneksi Firebase (Admin SDK) |
| `opencv-python` | 4.8.0 | Pemrosesan gambar & AI |
| `numpy` | 1.24.0 | Komputasi numerik |
| `python-dotenv` | 1.0.0 | Manajemen environment variables |
| `openpyxl` | 3.1.0 | Export laporan Excel |
| `Pillow` | 10.0.0 | Manipulasi gambar |
| `requests` | 2.31.0 | HTTP client |
| `Werkzeug` | 3.0.0 | Utilitas WSGI Flask |

---

## 🤝 Kontribusi

Kontribusi sangat disambut! Silakan ikuti langkah berikut:

1. **Fork** repositori ini
2. Buat branch fitur baru: `git checkout -b fitur/nama-fitur`
3. Commit perubahan: `git commit -m 'feat: tambah fitur X'`
4. Push ke branch: `git push origin fitur/nama-fitur`
5. Buat **Pull Request**

---

## 📜 Lisensi

Proyek ini dilisensikan di bawah **MIT License** — bebas digunakan, dimodifikasi, dan didistribusikan.

---

<div align="center">

Dibuat dengan ❤️ oleh **ainformatika35-dev**

⭐ Jangan lupa beri bintang jika proyek ini bermanfaat!

</div>
