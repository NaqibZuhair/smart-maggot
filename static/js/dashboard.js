let grafikSensor = null;

async function ambilDataTerbaru() {
    const response = await fetch('/api/sensor/latest');
    const result = await response.json();

    if (result.data) {
        const data = result.data;

        document.getElementById('suhu').innerText = data.suhu + ' °C';
        document.getElementById('kelembaban').innerText = data.kelembaban + ' %';
        document.getElementById('status').innerText = data.status_kondisi;
        document.getElementById('keterangan').innerText = data.keterangan;
        document.getElementById('waktuTerakhir').innerText = formatWaktuLengkap(data.created_at);

        const statusElement = document.getElementById('status');

        if (data.status_kondisi === 'Normal') {
            statusElement.className = 'status-normal';
        } else {
            statusElement.className = 'status-warning';
        }

        const alertKondisi = document.getElementById('alertKondisi');
        const alertText = document.getElementById('alertText');

        if (data.status_kondisi === 'Normal') {
            alertKondisi.className = 'alert-kondisi alert-normal';
            alertText.innerText = 'Kondisi kandang maggot berada dalam batas normal.';
        } else {
            alertKondisi.className = 'alert-kondisi alert-warning';
            alertText.innerText = data.status_kondisi + '. ' + data.keterangan;
        }
    }
}

async function ambilRiwayatData() {
    const response = await fetch('/api/sensor/history');
    const result = await response.json();

    const tabel = document.getElementById('tabelRiwayat');
    tabel.innerHTML = '';

    if (!result.data || result.data.length === 0) {
        tabel.innerHTML = '<tr><td colspan="5">Belum ada data.</td></tr>';
        updateGrafik([], [], []);
        return;
    }

    const labels = [];
    const dataSuhu = [];
    const dataKelembaban = [];

    result.data.forEach(function(item) {
        labels.push(formatWaktu(item.created_at));
        dataSuhu.push(parseFloat(item.suhu));
        dataKelembaban.push(parseFloat(item.kelembaban));
    });

    result.data.slice().reverse().forEach(function(item) {
        const badgeClass = item.status_kondisi === 'Normal'
            ? 'badge-normal'
            : 'badge-warning';

        tabel.innerHTML += `
            <tr>
                <td>${formatWaktuLengkap(item.created_at)}</td>
                <td>${item.suhu} °C</td>
                <td>${item.kelembaban} %</td>
                <td>
                    <span class="badge ${badgeClass}">
                        ${item.status_kondisi}
                    </span>
                </td>
                <td>${item.keterangan}</td>
            </tr>
        `;
    });

    updateGrafik(labels, dataSuhu, dataKelembaban);
}

function updateGrafik(labels, dataSuhu, dataKelembaban) {
    const ctx = document.getElementById('grafikSensor').getContext('2d');

    if (grafikSensor !== null) {
        grafikSensor.destroy();
    }

    grafikSensor = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Suhu (°C)',
                    data: dataSuhu,
                    borderWidth: 2,
                    tension: 0.3
                },
                {
                    label: 'Kelembaban (%)',
                    data: dataKelembaban,
                    borderWidth: 2,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

async function ambilStatistikData() {
    const response = await fetch('/api/sensor/statistics');
    const result = await response.json();

    if (result.data) {
        const data = result.data;

        document.getElementById('totalData').innerText = data.total_data ?? 0;
        document.getElementById('rataSuhu').innerText = (data.rata_suhu ?? 0) + ' °C';
        document.getElementById('rataKelembaban').innerText = (data.rata_kelembaban ?? 0) + ' %';
        document.getElementById('suhuTertinggi').innerText = (data.suhu_tertinggi ?? 0) + ' °C';
        document.getElementById('kelembabanTertinggi').innerText = (data.kelembaban_tertinggi ?? 0) + ' %';
        document.getElementById('totalNormal').innerText = data.total_normal ?? 0;
        document.getElementById('totalPeringatan').innerText = data.total_peringatan ?? 0;

        let kesimpulan = '';

        const totalData = data.total_data ?? 0;
        const rataSuhu = data.rata_suhu ?? 0;
        const rataKelembaban = data.rata_kelembaban ?? 0;
        const totalNormal = data.total_normal ?? 0;
        const totalPeringatan = data.total_peringatan ?? 0;

        if (totalData === 0) {
            kesimpulan = 'Belum ada data sensor yang tersimpan. Sistem masih perlu menerima data dari simulasi atau perangkat ESP32.';
        } else if (totalNormal >= totalPeringatan) {
            kesimpulan = `Berdasarkan ${totalData} data sensor, rata-rata suhu kandang adalah ${rataSuhu} °C dan rata-rata kelembaban adalah ${rataKelembaban}%. Sebagian besar kondisi kandang berada dalam status normal, sehingga lingkungan budidaya maggot masih cukup stabil.`;
        } else {
            kesimpulan = `Berdasarkan ${totalData} data sensor, rata-rata suhu kandang adalah ${rataSuhu} °C dan rata-rata kelembaban adalah ${rataKelembaban}%. Jumlah kondisi peringatan lebih banyak daripada kondisi normal, sehingga kandang perlu diperiksa, terutama pada aspek suhu, kelembaban media, dan ventilasi.`;
        }

        document.getElementById('kesimpulanAnalisis').innerText = kesimpulan;
    }
}

async function buatSimulasi() {
    await fetch('/api/sensor/simulate');
    await refreshDashboard();
}

function bukaModalReset() {
    document.getElementById('modalReset').classList.add('show');
}

function tutupModalReset() {
    document.getElementById('modalReset').classList.remove('show');
}

async function resetData() {
    const response = await fetch('/api/sensor/reset', {
        method: 'POST'
    });

    const result = await response.json();

    if (result.success) {
        tutupModalReset();
        window.location.reload();
    } else {
        document.getElementById('alertKondisi').className = 'alert-kondisi alert-warning';
        document.getElementById('alertText').innerText = 'Reset data gagal: ' + result.message;
        tutupModalReset();
    }
}

async function refreshDashboard() {
    await ambilDataTerbaru();
    await ambilRiwayatData();
    await ambilStatistikData();
}

function formatWaktu(waktu) {
    if (!waktu) return '-';

    const date = new Date(waktu);

    if (isNaN(date.getTime())) {
        return waktu;
    }

    return date.toLocaleTimeString('id-ID', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatWaktuLengkap(waktu) {
    if (!waktu) return '-';

    const date = new Date(waktu);

    if (isNaN(date.getTime())) {
        return waktu;
    }

    return date.toLocaleString('id-ID');
}

refreshDashboard();
setInterval(refreshDashboard, 5000);