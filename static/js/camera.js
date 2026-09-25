/**
 * ABSENSI-AI - Camera & Media Handler
 */

let videoStream = null;

async function initCamera() {
    const video = document.getElementById('webcamVideo');
    const errorBox = document.getElementById('cameraErrorBox');
    const errorMsg = document.getElementById('cameraErrorMessage');

    if (!video) return;

    if (errorBox) errorBox.classList.add('d-none');

    // Cek apakah browser mendukung getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        if (errorBox && errorMsg) {
            errorMsg.textContent = "Browser Anda tidak mendukung akses kamera HTML5 / Webcam API.";
            errorBox.classList.remove('d-none');
            errorBox.classList.add('d-flex');
        }
        showToast("Browser tidak mendukung akses kamera.", "danger");
        return;
    }

    try {
        if (videoStream) {
            videoStream.getTracks().forEach(track => track.stop());
        }

        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            },
            audio: false
        });

        videoStream = stream;
        video.srcObject = stream;
        await video.play();

        if (errorBox) {
            errorBox.classList.add('d-none');
            errorBox.classList.remove('d-flex');
        }
    } catch (err) {
        console.error("Camera access error:", err);
        if (errorBox && errorMsg) {
            errorMsg.textContent = "Kamera tidak dapat diakses. Pastikan browser memiliki izin menggunakan kamera dan perangkat terhubung.";
            errorBox.classList.remove('d-none');
            errorBox.classList.add('d-flex');
        }
        showToast("Kamera tidak dapat diakses. Periksa izin kamera browser.", "danger");
    }
}

function captureFrameBase64(format = 'image/jpeg', quality = 0.85) {
    const video = document.getElementById('webcamVideo');
    const canvas = document.getElementById('captureCanvas') || document.createElement('canvas');

    if (!video || !video.videoWidth) {
        return null;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL(format, quality);
}

function stopCamera() {
    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }
}

window.addEventListener('beforeunload', stopCamera);
