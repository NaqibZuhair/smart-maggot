let grafikSensor = null;

function getEl(id) {
    return document.getElementById(id);
}

function setText(id, value) {
    const element = getEl(id);
    if (element) {
        element.innerText = value;
    }
}

function setClass(id, className) {
    const element = getEl(id);
    if (element) {
        element.className = className;
    }
}

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '-';
    }

    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#039;');
}

async function fetchJson(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const result = await response.json();

        if (!response.ok || result.success === false) {
            throw new Error(result.message || 'Terjadi kesalahan saat mengambil data.');
        }

        return result;
    } catch (error) {
        console.error(error);
        tampilkanPeringatan('Gagal memuat data: ' + error.message);
        return null;
    }
}

function tampilkanPeringatan(pesan) {
    setClass('alertKondisi', 'alert-kondisi alert-warning');
    setText('alertText', pesan);
}

async function ambilDataTerbaru() {
    const result = await fetchJson('/api/sensor/latest');

    if (!result || !result.data) {
        setText('suhu', '-');
        setText('kelembaban', '-');
        setText('status', 'Belum Ada Data');
        setText('keterangan', 'Belum ada data sensor yang tersimpan.');
        setText('waktuTerakhir', '-');

        setClass('status', 'status-warning');
        setClass('alertKondisi', 'alert-kondisi alert-warning');
        setText('alertText', 'Belum ada data sensor. Silakan buat data simulasi terlebih dahulu.');
        return;
    }

    const data = result.data;
    const status = data.status_kondisi || '-';
    const keterangan = data.keterangan || '-';

    setText('suhu', `${data.suhu} °C`);
    setText('kelembaban', `${data.kelembaban} %`);
    setText('status', status);
    setText('keterangan', keterangan);
    setText('waktuTerakhir', formatWaktuLengkap(data.created_at));

    if (status === 'Normal') {
        setClass('status', 'status-normal');
        setClass('alertKondisi', 'alert-kondisi alert-normal');
        setText('alertText', 'Kondisi kandang maggot berada dalam batas normal.');
    } else {
        setClass('status', 'status-warning');
        setClass('alertKondisi', 'alert-kondisi alert-warning');
        setText('alertText', `${status}. ${keterangan}`);
    }
}

async function ambilRiwayatData() {
    const result = await fetchJson('/api/sensor/history');

    const tabel = getEl('tabelRiwayat');

    if (!result || !result.data || result.data.length === 0) {
        if (tabel) {
            tabel.innerHTML = '<tr><td colspan="5">Belum ada data.</td></tr>';
        }

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

    if (tabel) {
        tabel.innerHTML = '';

        result.data.slice().reverse().forEach(function(item) {
            const badgeClass = item.status_kondisi === 'Normal'
                ? 'badge-normal'
                : 'badge-warning';

            tabel.innerHTML += `
                <tr>
                    <td>${escapeHtml(formatWaktuLengkap(item.created_at))}</td>
                    <td>${escapeHtml(item.suhu)} °C</td>
                    <td>${escapeHtml(item.kelembaban)} %</td>
                    <td>
                        <span class="badge ${badgeClass}">
                            ${escapeHtml(item.status_kondisi)}
                        </span>
                    </td>
                    <td>${escapeHtml(item.keterangan)}</td>
                </tr>
            `;
        });
    }

    updateGrafik(labels, dataSuhu, dataKelembaban);
}

function updateGrafik(labels, dataSuhu, dataKelembaban) {
    const canvas = getEl('grafikSensor');

    if (!canvas || typeof Chart === 'undefined') {
        return;
    }

    const ctx = canvas.getContext('2d');

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
                },
                tooltip: {
                    enabled: true
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
    const result = await fetchJson('/api/sensor/statistics');

    if (!result || !result.data) {
        return;
    }

    const data = result.data;

    const totalData = data.total_data ?? 0;
    const rataSuhu = data.rata_suhu ?? 0;
    const rataKelembaban = data.rata_kelembaban ?? 0;
    const suhuTertinggi = data.suhu_tertinggi ?? 0;
    const suhuTerendah = data.suhu_terendah ?? 0;
    const kelembabanTertinggi = data.kelembaban_tertinggi ?? 0;
    const kelembabanTerendah = data.kelembaban_terendah ?? 0;

    const totalNormal = data.total_normal ?? 0;
    const totalPeringatan = data.total_peringatan ?? 0;
    const totalTerlaluPanas = data.total_terlalu_panas ?? 0;
    const totalTerlaluDingin = data.total_terlalu_dingin ?? 0;
    const totalTerlaluLembab = data.total_terlalu_lembab ?? 0;
    const totalTerlaluKering = data.total_terlalu_kering ?? 0;

    const persentaseNormal = data.persentase_normal ?? 0;
    const persentasePeringatan = data.persentase_peringatan ?? 0;

    setText('totalData', totalData);
    setText('rataSuhu', `${rataSuhu} °C`);
    setText('rataKelembaban', `${rataKelembaban} %`);
    setText('suhuTertinggi', `${suhuTertinggi} °C`);
    setText('suhuTerendah', `${suhuTerendah} °C`);
    setText('kelembabanTertinggi', `${kelembabanTertinggi} %`);
    setText('kelembabanTerendah', `${kelembabanTerendah} %`);

    setText('totalNormal', totalNormal);
    setText('totalPeringatan', totalPeringatan);
    setText('totalTerlaluPanas', totalTerlaluPanas);
    setText('totalTerlaluDingin', totalTerlaluDingin);
    setText('totalTerlaluLembab', totalTerlaluLembab);
    setText('totalTerlaluKering', totalTerlaluKering);

    setText('persentaseNormal', `${persentaseNormal} %`);
    setText('persentasePeringatan', `${persentasePeringatan} %`);

    setText('kesimpulanAnalisis', data.kesimpulan || buatKesimpulanCadangan(data));
    setText('rekomendasiAnalisis', data.rekomendasi || 'Belum ada rekomendasi.');
    setText('ringkasanPengujian', buatRingkasanPengujian(data));
}

function buatKesimpulanCadangan(data) {
    const totalData = data.total_data ?? 0;
    const rataSuhu = data.rata_suhu ?? 0;
    const rataKelembaban = data.rata_kelembaban ?? 0;
    const totalNormal = data.total_normal ?? 0;
    const totalPeringatan = data.total_peringatan ?? 0;

    if (totalData === 0) {
        return 'Belum ada data sensor yang tersimpan. Sistem masih perlu menerima data dari simulasi atau perangkat ESP32.';
    }

    if (totalNormal >= totalPeringatan) {
        return `Berdasarkan ${totalData} data sensor, rata-rata suhu kandang adalah ${rataSuhu} °C dan rata-rata kelembaban adalah ${rataKelembaban}%. Sebagian besar kondisi kandang berada dalam status normal, sehingga lingkungan budidaya maggot masih cukup stabil.`;
    }

    return `Berdasarkan ${totalData} data sensor, rata-rata suhu kandang adalah ${rataSuhu} °C dan rata-rata kelembaban adalah ${rataKelembaban}%. Jumlah kondisi peringatan lebih banyak daripada kondisi normal, sehingga kandang perlu diperiksa, terutama pada aspek suhu, kelembaban media, dan ventilasi.`;
}

function buatRingkasanPengujian(data) {
    const totalData = data.total_data ?? 0;
    const totalNormal = data.total_normal ?? 0;
    const totalPeringatan = data.total_peringatan ?? 0;
    const persentaseNormal = data.persentase_normal ?? 0;
    const persentasePeringatan = data.persentase_peringatan ?? 0;

    if (totalData === 0) {
        return 'Belum ada data pengujian. Silakan gunakan data simulasi terlebih dahulu sampai perangkat ESP32 tersedia.';
    }

    return `Pengujian sementara menggunakan ${totalData} data sensor. Dari jumlah tersebut, ${totalNormal} data berada pada kondisi normal dan ${totalPeringatan} data berada pada kondisi peringatan. Persentase kondisi normal sebesar ${persentaseNormal}%, sedangkan kondisi peringatan sebesar ${persentasePeringatan}%. Data ini dapat digunakan sebagai dasar analisis awal terhadap kestabilan suhu dan kelembaban kandang maggot.`;
}

async function buatSimulasi() {
    const result = await fetchJson('/api/sensor/simulate');

    if (result && result.success) {
        await refreshDashboard();
    }
}

function bukaModalReset() {
    const modal = getEl('modalReset');

    if (modal) {
        modal.classList.add('show');
    }
}

function tutupModalReset() {
    const modal = getEl('modalReset');

    if (modal) {
        modal.classList.remove('show');
    }
}

async function resetData() {
    const result = await fetchJson('/api/sensor/reset', {
        method: 'POST'
    });

    if (result && result.success) {
        tutupModalReset();
        window.location.reload();
        return;
    }

    tutupModalReset();
}

async function refreshDashboard() {
    await ambilDataTerbaru();
    await ambilRiwayatData();
    await ambilStatistikData();
}

function formatWaktu(waktu) {
    if (!waktu) {
        return '-';
    }

    const teks = String(waktu);

    if (teks.includes(' ')) {
        const bagian = teks.split(' ');
        return bagian[1].substring(0, 5);
    }

    return teks;
}

function formatWaktuLengkap(waktu) {
    if (!waktu) {
        return '-';
    }

    const teks = String(waktu);

    if (teks.includes(' ')) {
        const bagian = teks.split(' ');
        const tanggal = bagian[0].split('-');
        const jam = bagian[1].substring(0, 5);

        if (tanggal.length === 3) {
            return `${tanggal[2]}/${tanggal[1]}/${tanggal[0]}\n${jam} WIB`;
        }
    }

    return teks;
}

refreshDashboard();
setInterval(refreshDashboard, 5000);