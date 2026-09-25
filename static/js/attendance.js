/**
 * ABSENSI-AI - Face Recognition Attendance Client
 */

let isProcessingAttendance = false;

async function performAttendanceCheckIn() {
    if (isProcessingAttendance) return;

    const btnCapture = document.getElementById('btnCapture');
    const scannerLine = document.getElementById('scannerLine');
    const resultCard = document.getElementById('attendanceResultCard');
    const resultBody = document.getElementById('resultCardBody');

    // 1. Tangkap frame webcam
    const b64Image = captureFrameBase64();
    if (!b64Image) {
        showToast("Kamera tidak dapat diakses. Pastikan browser memiliki izin menggunakan kamera.", "danger");
        return;
    }

    isProcessingAttendance = true;
    if (btnCapture) {
        btnCapture.disabled = true;
        btnCapture.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span> Memindai Wajah...`;
    }
    if (scannerLine) scannerLine.classList.remove('d-none');
    if (resultCard) resultCard.classList.add('d-none');

    try {
        const response = await fetch('/api/attendance/check-in', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: b64Image })
        });
        const data = await response.json();

        if (scannerLine) scannerLine.classList.add('d-none');

        if (response.ok && data.success) {
            // Berhasil presensi
            const rec = data.data;
            const isLate = (rec.status || '').toLowerCase() === 'terlambat';
            const statusBadge = isLate 
                ? '<span class="badge bg-warning text-dark px-3 py-1 rounded-pill fs-6"><i class="bi bi-alarm me-1"></i> TERLAMBAT</span>'
                : '<span class="badge bg-success px-3 py-1 rounded-pill fs-6"><i class="bi bi-check-circle me-1"></i> HADIR</span>';

            resultCard.className = 'card border-0 rounded-4 mt-4 shadow-sm bg-success-subtle border-success-subtle';
            resultBody.innerHTML = `
                <div class="text-success fs-1 mb-2"><i class="bi bi-check-circle-fill"></i></div>
                <h4 class="fw-bold text-dark mb-1">Absensi Berhasil!</h4>
                <p class="text-secondary mb-3">${data.message}</p>
                <div class="p-3 bg-white rounded-3 shadow-sm d-inline-block text-start" style="min-width: 280px;">
                    <div class="row g-2 small">
                        <div class="col-4 text-muted">Nama:</div>
                        <div class="col-8 fw-bold text-dark">${rec.nama}</div>
                        <div class="col-4 text-muted">NIS / Kelas:</div>
                        <div class="col-8 fw-semibold">${rec.nis} &bull; ${rec.kelas}</div>
                        <div class="col-4 text-muted">Waktu:</div>
                        <div class="col-8">${rec.jam} WIB (${rec.tanggal})</div>
                        <div class="col-4 text-muted">Status:</div>
                        <div class="col-8">${statusBadge}</div>
                    </div>
                </div>
                <div class="mt-4">
                    <a href="/siswa/dashboard" class="btn btn-success rounded-pill px-4 fw-semibold">
                        Lihat Dashboard Siswa
                    </a>
                </div>
            `;
            resultCard.classList.remove('d-none');
            showToast(data.message, 'success');

            // Play success chime
            playAudioFeedback(true);
        } else {
            // Gagal atau sudah absen
            const isAlreadyAttended = (data.message || '').includes('sudah melakukan absensi');
            resultCard.className = `card border-0 rounded-4 mt-4 shadow-sm ${isAlreadyAttended ? 'bg-info-subtle border-info-subtle' : 'bg-danger-subtle border-danger-subtle'}`;
            resultBody.innerHTML = `
                <div class="${isAlreadyAttended ? 'text-info' : 'text-danger'} fs-1 mb-2">
                    <i class="bi ${isAlreadyAttended ? 'bi-info-circle-fill' : 'bi-x-circle-fill'}"></i>
                </div>
                <h5 class="fw-bold text-dark mb-2">${data.message || "Gagal melakukan presensi"}</h5>
                <p class="small text-muted mb-3">
                    ${isAlreadyAttended ? 'Catatan kehadiran Anda sudah tersimpan untuk hari ini.' : 'Posisikan wajah Anda tegak lurus dan pastikan ruangan memiliki pencahayaan cukup.'}
                </p>
                ${isAlreadyAttended ? `
                    <a href="/siswa/dashboard" class="btn btn-outline-primary rounded-pill px-4 btn-sm">Ke Dashboard</a>
                ` : `
                    <button type="button" class="btn btn-danger rounded-pill px-4 btn-sm" onclick="performAttendanceCheckIn()">
                        <i class="bi bi-arrow-clockwise me-1"></i> Coba Lagi
                    </button>
                `}
            `;
            resultCard.classList.remove('d-none');
            showToast(data.message || 'Verifikasi wajah gagal', isAlreadyAttended ? 'info' : 'error');

            playAudioFeedback(false);
        }
    } catch (err) {
        console.error("Attendance API error:", err);
        if (scannerLine) scannerLine.classList.add('d-none');
        showToast("Terjadi gangguan saat memproses absensi ke server.", "danger");
    } finally {
        isProcessingAttendance = false;
        if (btnCapture) {
            btnCapture.disabled = false;
            btnCapture.innerHTML = `<i class="bi bi-camera-fill me-2"></i> Scan & Verifikasi Wajah`;
        }
    }
}

// Suara notifikasi sederhana Web Audio API
function playAudioFeedback(isSuccess) {
    try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();

        osc.connect(gain);
        gain.connect(audioCtx.destination);

        if (isSuccess) {
            osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
            osc.frequency.setValueAtTime(880, audioCtx.currentTime + 0.12); // A5
            gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
            osc.start(audioCtx.currentTime);
            osc.stop(audioCtx.currentTime + 0.35);
        } else {
            osc.frequency.setValueAtTime(320, audioCtx.currentTime);
            osc.frequency.setValueAtTime(240, audioCtx.currentTime + 0.15);
            gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
            osc.start(audioCtx.currentTime);
            osc.stop(audioCtx.currentTime + 0.35);
        }
    } catch (e) {
        // Audio API not supported or user blocked, safe to ignore
    }
}
