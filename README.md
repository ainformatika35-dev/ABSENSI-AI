# ABSENSI-AI: Aplikasi Presensi Wajah Berbasis AI & Firebase

Aplikasi web modern untuk presensi/absensi siswa menggunakan deteksi dan pengenalan wajah (*Face Recognition AI*) berbasis Python (Flask + OpenCV Deep Learning) dan terintegrasi dengan **Firebase Realtime Database**.

---

## 🌟 Fitur Utama

1. **Pengenalan Wajah AI Mendalam**:
   - Deteksi wajah akurat menggunakan model **YuNet**.
   - Ekstraksi fitur embedding 128-dimensi menggunakan **SFace** (OpenCV DNN).
   - Validasi ketajaman (*Laplacian Variance*) dan deteksi keaslian (*Liveness Detection*) untuk mencegah kecurangan menggunakan foto cetak atau layar ponsel.
   - Threshold kemiripan dapat disesuaikan via `.env`.

2. **Aturan Presensi Otomatis**:
   - Pembagian status otomatis: **Hadir** (sebelum/pada batas waktu) atau **Terlambat** (melewati batas waktu).
   - Pencegahan absensi ganda (siswa tidak dapat melakukan absensi berulang pada hari yang sama).

3. **Peran & Akses Pengguna (Role-Based)**:
   - **Siswa**:
     - Login menggunakan NIS atau username.
     - Dashboard status kehadiran hari ini.
     - Presensi mandiri via kamera webcam laptop/komputer.
     - Riwayat kehadiran pribadi.
   - **Admin**:
     - Dashboard statistik harian (Total Siswa, Hadir, Terlambat, Izin, Sakit, Alpa).
     - Grafik tren kehadiran 7 hari, distribusi status, dan rekap per kelas (Chart.js).
     - Manajemen siswa lengkap (Tambah, Edit, Hapus/Nonaktifkan).
     - Pendaftaran sampel wajah siswa (3 sampel: lurus, senyum, sudut berbeda) beserta fitur uji kamera live.
     - Laporan presensi lengkap dengan filter tanggal, kelas, nama/NIS, dan status.
     - Ekspor laporan ke format **CSV** dan **Excel (.xlsx)**.
     - Input presensi manual untuk izin, sakit, dan alpa.

4. **Integrasi Firebase Realtime Database**:
   - Backend terhubung melalui **Firebase Admin SDK**.
   - Dilengkapi aturan keamanan role-based (`database.rules.json`).
   - Mode transisi / buffer otomatis jika `serviceAccountKey.json` belum diunggah sehingga aplikasi tetap dapat langsung dijalankan dan diuji.

---

## 📁 Struktur Direktori

```text
ABSENSI AI RAYA/
├── app.py                     # Entry point server Flask
├── config.py                  # Konfigurasi aplikasi & environment
├── database.rules.json        # Firebase Realtime Database Security Rules
├── requirements.txt           # Dependensi Python
├── .env                       # File konfigurasi lokal
├── .env.example               # Template environment variable
├── .gitignore
├── firebase/
│   ├── __init__.py
│   └── firebase_config.py     # Konektor & handler Firebase Realtime Database
├── ai/
│   ├── __init__.py
│   ├── face_detector.py       # OpenCV YuNet & Haar Cascade Detector
│   ├── face_recognition.py    # OpenCV SFace 128D Embedding Recognizer
│   ├── face_utils.py          # Utilitas gambar, base64 & liveness check
│   └── models/
│       ├── face_detection_yunet_2023mar.onnx
│       └── face_recognition_sface_2021dec.onnx
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Autentikasi & kontrol sesi
│   ├── attendance.py          # Presensi wajah & check-in AI
│   ├── students.py            # Manajemen data siswa
│   └── reports.py             # Laporan, statistik & ekspor CSV/Excel
├── templates/
│   ├── base.html              # Layout master & navbar
│   ├── login.html             # Halaman login modern
│   ├── siswa/
│   │   ├── dashboard.html     # Dashboard siswa & status harian
│   │   ├── attendance.html    # Halaman scan wajah AI
│   │   └── history.html       # Riwayat kehadiran siswa
│   └── admin/
│       ├── dashboard.html     # Dashboard analytics & grafik admin
│       ├── students.html      # Kelola data siswa
│       ├── face_registration.html # Pendaftaran wajah & uji kamera
│       └── reports.html       # Laporan, filter & ekspor data
├── static/
│   ├── css/style.css          # Tema modern bernuansa sekolah
│   ├── js/
│   │   ├── camera.js          # Web API kamera browser
│   │   ├── attendance.js      # Client check-in AI & feedback audio
│   │   └── dashboard.js       # Jam digital & format tanggal
│   └── images/
│       └── logo.svg           # Logo vektor aplikasi
└── README.md
```

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

### 1. Persyaratan Sistem
- Python versi 3.10 atau 3.11.
- Webcam / kamera laptop yang berfungsi.
- Browser modern (Google Chrome, Microsoft Edge, atau Mozilla Firefox).

### 2. Membuat Virtual Environment

Buka Command Prompt atau PowerShell di folder project:

```bash
python -m venv venv
```

Aktifkan virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (Command Prompt)**:
  ```cmd
  venv\Scripts\activate.bat
  ```

### 3. Menginstall Dependensi

```bash
pip install -r requirements.txt
```

### 4. Konfigurasi Environment (`.env`)

File `.env` sudah disediakan secara otomatis. Anda dapat menyesuaikan konfigurasi sesuai kebutuhan:

```env
FLASK_SECRET_KEY=absensi_ai_super_secret_key_2026_xyz
PORT=5000
HOST=0.0.0.0

# Firebase Database URL
FIREBASE_DATABASE_URL=https://absensi-ai-6cced-default-rtdb.firebaseio.com/
FIREBASE_CREDENTIALS_PATH=serviceAccountKey.json

# Ambang batas kemiripan wajah (0.0 - 1.0)
FACE_RECOGNITION_THRESHOLD=0.50

# Aturan batas waktu presensi
ATTENDANCE_START_TIME=07:00
ATTENDANCE_LATE_TIME=07:15
```

### 5. Memasukkan Firebase Service Account

1. Buka [Firebase Console](https://console.firebase.google.com/project/absensi-ai-6cced).
2. Masuk ke **Project Settings** (ikon gerigi) > tab **Service accounts**.
3. Klik tombol **Generate new private key** dan simpan file JSON tersebut.
4. Ubah nama file tersebut menjadi `serviceAccountKey.json` dan letakkan di **root folder project** (sejajar dengan `app.py`).

> *Catatan:* Jika file tersebut belum diletakkan, aplikasi tetap berjalan dalam mode transisi lokal agar Anda dapat menguji seluruh fungsi tanpa hambatan.

### 6. Menjalankan Aplikasi

```bash
python app.py
```

Buka browser dan akses:
```
http://localhost:5000
```

---

## 🔑 Akun Bawaan Sistem (Demo)

Sistem telah menyediakan akun awal secara otomatis:

| Role | Username / NIS | Password | Keterangan |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Akses penuh dashboard, siswa, pendaftaran wajah, dan laporan |
| **Siswa** | `1001` | `siswa123` | Akun Siswa: Budi Santoso (XI IPA 1) |
| **Siswa** | `1002` | `siswa123` | Akun Siswa: Siti Nurhaliza (XI IPS 1) |
| **Siswa** | `1003` | `siswa123` | Akun Siswa: Ahmad Fauzi (XI IPA 2) |

---

## 📖 Alur Penggunaan Aplikasi

### A. Pendaftaran Wajah Siswa (Admin)
1. Login sebagai Admin (`admin` / `admin123`).
2. Masuk ke menu **Daftar Wajah** (`/admin/face-registration`).
3. Pilih siswa pada dropdown.
4. Izinkan browser mengakses kamera.
5. Posisikan wajah siswa di dalam oval pemandu.
6. Klik tombol **Ambil Foto Sampel** sebanyak 3 kali (posisi netral, senyum, sedikit sudut berbeda).
7. Klik **Simpan ke Firebase Database**. Sistem AI akan mengekstrak vektor embedding 128-dimensi dan menyimpannya.
8. Gunakan tombol **Uji Kamera** untuk memastikan sistem mengenali wajah siswa tersebut secara akurat.

### B. Melakukan Presensi Wajah (Siswa)
1. Login sebagai Siswa (misal `1001` / `siswa123`).
2. Di halaman Dashboard Siswa, klik tombol **ABSENSI SEKARANG** (`/siswa/attendance`).
3. Berdiri/duduk tegak menghadap webcam.
4. Klik **Scan & Verifikasi Wajah**.
5. Sistem AI backend akan mendeteksi wajah, mencocokkan embedding, menentukan status (*Hadir* jika <= 07:15, *Terlambat* jika > 07:15), dan menyimpan presensi ke Firebase.
6. Notifikasi berhasil dan bunyi konfirmasi akan muncul. Siswa tidak dapat absen lagi pada hari yang sama.

### C. Melihat & Mengekspor Laporan (Admin)
1. Buka menu **Laporan** (`/admin/reports`).
2. Gunakan saringan berdasarkan tanggal mulai, tanggal akhir, kelas, nama/NIS, atau status kehadiran.
3. Klik tombol **Export CSV** untuk mengunduh laporan format `.csv`.
4. Klik tombol **Export Excel** untuk mengunduh laporan format `.xlsx` dengan format tabel rapi.

### D. Menjalankan di Jaringan Lokal (Komputer / Laptop Sekolah)
Aplikasi sudah diset untuk mendengarkan host `0.0.0.0`.
Untuk membukanya dari komputer lain yang terhubung ke satu jaringan Wi-Fi/LAN sekolah:
1. Temukan IP lokal laptop server (misal melalui perintah `ipconfig`, contoh: `192.168.1.15`).
2. Buka browser di komputer lain dengan alamat: `http://192.168.1.15:5000`.

---

## 🔒 Keamanan & Kebijakan
- Password disimpan menggunakan hashing `scrypt` / `pbkdf2` via Werkzeug Security (tidak ada plaintext).
- Foto mentah tidak disimpan ke database untuk menjaga privasi; hanya representasi matematis embedding wajah yang disimpan.
- Validasi identitas siswa diproses murni dari algoritma pengenalan wajah di server backend.
