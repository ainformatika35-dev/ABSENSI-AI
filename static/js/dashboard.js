/**
 * ABSENSI-AI - Dashboard Client Utilities
 */

// Jam Digital Realtime
function initDigitalClock(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;

    function update() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        el.textContent = `${hours}:${minutes}:${seconds} WIB`;
    }

    update();
    setInterval(update, 1000);
}

// Format Tanggal Indonesia
function formatDateIndo(dateStr) {
    if (!dateStr) return '-';
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString('id-ID', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (e) {
        return dateStr;
    }
}
