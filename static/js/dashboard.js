let sensorChart = null;

const elements = {
    latestTime: document.getElementById("latestTime"),
    latestStatus: document.getElementById("latestStatus"),
    latestDescription: document.getElementById("latestDescription"),
    deviceStatusBadge: document.getElementById("deviceStatusBadge"),
    deviceStatusMessage: document.getElementById("deviceStatusMessage"),
    latestTemperature: document.getElementById("latestTemperature"),
    latestHumidity: document.getElementById("latestHumidity"),
    statusIndicator: document.getElementById("statusIndicator"),

    totalData: document.getElementById("totalData"),
    averageTemperature: document.getElementById("averageTemperature"),
    averageHumidity: document.getElementById("averageHumidity"),
    temperatureRange: document.getElementById("temperatureRange"),
    humidityRange: document.getElementById("humidityRange"),
    normalPercentage: document.getElementById("normalPercentage"),
    warningPercentage: document.getElementById("warningPercentage"),
    normalCount: document.getElementById("normalCount"),
    warningCount: document.getElementById("warningCount"),

    hotCount: document.getElementById("hotCount"),
    coldCount: document.getElementById("coldCount"),
    wetCount: document.getElementById("wetCount"),
    dryCount: document.getElementById("dryCount"),

    analysisConclusion: document.getElementById("analysisConclusion"),
    analysisRecommendation: document.getElementById("analysisRecommendation"),

    historyTableBody: document.getElementById("historyTableBody"),

    btnRefresh: document.getElementById("btnRefresh"),
    btnSimulate: document.getElementById("btnSimulate"),
    btnExport: document.getElementById("btnExport"),
    btnReset: document.getElementById("btnReset"),

    toast: document.getElementById("toast"),
    toastMessage: document.getElementById("toastMessage"),
};

function formatNumber(value, digit = 2) {
    const number = Number(value);

    if (Number.isNaN(number)) {
        return "0";
    }

    return number.toFixed(digit);
}

function getStatusClass(status) {
    if (!status) {
        return "warning";
    }

    if (status === "Normal") {
        return "normal";
    }

    if (status === "Terlalu Panas" || status === "Terlalu Dingin") {
        return "danger";
    }

    return "warning";
}

function showToast(message, type = "success") {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast show ${type}`;

    setTimeout(() => {
        elements.toast.className = "toast";
    }, 3000);
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, {
        credentials: "same-origin",
        ...options,
    });

    if (response.status === 401) {
        window.location.href = "/login";
        return null;
    }

    const result = await response.json();

    if (!response.ok || result.success === false) {
        throw new Error(result.message || "Terjadi kesalahan pada server.");
    }

    return result;
}

function updateLatestSensor(data) {
    if (!data) {
        elements.latestTime.textContent = "Belum ada data";
        elements.latestStatus.textContent = "Belum ada data sensor";
        elements.latestDescription.textContent = "Silakan kirim data dari ESP32 atau gunakan fitur simulasi data.";
        elements.latestTemperature.textContent = "0";
        elements.latestHumidity.textContent = "0";
        elements.statusIndicator.className = "status-indicator warning";

        if (elements.deviceStatusBadge) {
            elements.deviceStatusBadge.textContent = "Offline";
            elements.deviceStatusBadge.className = "device-badge offline";
        }

        if (elements.deviceStatusMessage) {
            elements.deviceStatusMessage.textContent = "Belum ada data dari ESP32.";
        }

        return;
    }

    elements.latestTime.textContent = data.created_at || "Waktu tidak tersedia";
    elements.latestStatus.textContent = data.status_kondisi || "Tidak diketahui";
    elements.latestDescription.textContent = data.keterangan || "Tidak ada keterangan.";
    elements.latestTemperature.textContent = formatNumber(data.suhu);
    elements.latestHumidity.textContent = formatNumber(data.kelembaban);

    const statusClass = getStatusClass(data.status_kondisi);
    elements.statusIndicator.className = `status-indicator ${statusClass}`;

    if (elements.deviceStatusBadge) {
        const koneksi = data.koneksi_perangkat || "offline";
        const statusPerangkat = data.status_perangkat || "Offline";

        elements.deviceStatusBadge.textContent = statusPerangkat;
        elements.deviceStatusBadge.className = `device-badge ${koneksi}`;
    }

    if (elements.deviceStatusMessage) {
        elements.deviceStatusMessage.textContent = data.pesan_perangkat || "Status perangkat tidak tersedia.";
    }
}

function updateStatistics(data) {
    if (!data) {
        return;
    }

    elements.totalData.textContent = data.total_data || 0;

    elements.averageTemperature.textContent = formatNumber(data.rata_suhu);
    elements.averageHumidity.textContent = formatNumber(data.rata_kelembaban);

    elements.temperatureRange.textContent = `Min ${formatNumber(data.suhu_terendah)} °C | Max ${formatNumber(data.suhu_tertinggi)} °C`;
    elements.humidityRange.textContent = `Min ${formatNumber(data.kelembaban_terendah)}% | Max ${formatNumber(data.kelembaban_tertinggi)}%`;

    elements.normalPercentage.textContent = formatNumber(data.persentase_normal);
    elements.warningPercentage.textContent = formatNumber(data.persentase_peringatan);

    elements.normalCount.textContent = data.total_normal || 0;
    elements.warningCount.textContent = data.total_peringatan || 0;

    elements.hotCount.textContent = data.total_terlalu_panas || 0;
    elements.coldCount.textContent = data.total_terlalu_dingin || 0;
    elements.wetCount.textContent = data.total_terlalu_lembab || 0;
    elements.dryCount.textContent = data.total_terlalu_kering || 0;

    elements.analysisConclusion.textContent = data.kesimpulan || "Belum ada kesimpulan.";
    elements.analysisRecommendation.textContent = data.rekomendasi || "Belum ada rekomendasi.";
}

function renderHistoryTable(data) {
    if (!data || data.length === 0) {
        elements.historyTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-row">
                    Belum ada data sensor.
                </td>
            </tr>
        `;
        return;
    }

    const rows = data
        .slice()
        .reverse()
        .map((item) => {
            const statusClass = getStatusClass(item.status_kondisi);

            return `
                <tr>
                    <td>${item.created_at || "-"}</td>
                    <td>${formatNumber(item.suhu)} °C</td>
                    <td>${formatNumber(item.kelembaban)}%</td>
                    <td>
                        <span class="badge ${statusClass}">
                            ${item.status_kondisi || "-"}
                        </span>
                    </td>
                    <td>${item.keterangan || "-"}</td>
                </tr>
            `;
        })
        .join("");

    elements.historyTableBody.innerHTML = rows;
}

function renderChart(data) {
    const canvas = document.getElementById("sensorChart");

    if (!canvas) {
        return;
    }

    const labels = data.map((item) => item.created_at || "-");
    const temperatureData = data.map((item) => Number(item.suhu || 0));
    const humidityData = data.map((item) => Number(item.kelembaban || 0));

    if (sensorChart) {
        sensorChart.data.labels = labels;
        sensorChart.data.datasets[0].data = temperatureData;
        sensorChart.data.datasets[1].data = humidityData;
        sensorChart.update();
        return;
    }

    sensorChart = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Suhu (°C)",
                    data: temperatureData,
                    borderColor: "#dc2626",
                    backgroundColor: "rgba(220, 38, 38, 0.12)",
                    tension: 0.35,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: "Kelembaban (%)",
                    data: humidityData,
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37, 99, 235, 0.12)",
                    tension: 0.35,
                    fill: true,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false,
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        padding: 18,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || "";
                            const value = context.parsed.y || 0;
                            return `${label}: ${value}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 0,
                        autoSkip: true,
                        maxTicksLimit: 6,
                    },
                    grid: {
                        display: false,
                    },
                },
                y: {
                    beginAtZero: false,
                    grid: {
                        color: "rgba(148, 163, 184, 0.22)",
                    },
                },
            },
        },
    });
}

async function loadLatestSensor() {
    const result = await requestJson("/api/sensor/latest");
    updateLatestSensor(result.data);
}

async function loadStatistics() {
    const result = await requestJson("/api/sensor/statistics");
    updateStatistics(result.data);
}

async function loadHistory() {
    const result = await requestJson("/api/sensor/history");
    renderHistoryTable(result.data || []);
    renderChart(result.data || []);
}

async function loadDashboard(showSuccessToast = false) {
    try {
        await Promise.all([
            loadLatestSensor(),
            loadStatistics(),
            loadHistory(),
        ]);

        if (showSuccessToast) {
            showToast("Dashboard berhasil diperbarui.", "success");
        }
    } catch (error) {
        showToast(error.message, "error");
    }
}

async function simulateSensorData() {
    try {
        elements.btnSimulate.disabled = true;
        elements.btnSimulate.textContent = "Memproses...";

        const result = await requestJson("/api/sensor/simulate");

        showToast(result.message || "Data simulasi berhasil dibuat.", "success");
        await loadDashboard();

    } catch (error) {
        showToast(error.message, "error");

    } finally {
        elements.btnSimulate.disabled = false;
        elements.btnSimulate.textContent = "Simulasi Data";
    }
}

async function resetSensorData() {
    const confirmReset = confirm("Yakin ingin menghapus semua data sensor?");

    if (!confirmReset) {
        return;
    }

    try {
        const result = await requestJson("/api/sensor/reset", {
            method: "POST",
        });

        showToast(result.message || "Data sensor berhasil dihapus.", "success");
        await loadDashboard();

    } catch (error) {
        showToast(error.message, "error");
    }
}

function exportCsv() {
    window.location.href = "/api/sensor/export-csv";
}

function activateSidebarMenu() {
    const menuItems = document.querySelectorAll(".menu-item");

    menuItems.forEach((item) => {
        item.addEventListener("click", () => {
            menuItems.forEach((menu) => menu.classList.remove("active"));
            item.classList.add("active");
        });
    });
}

function registerEventListeners() {
    if (elements.btnRefresh) {
        elements.btnRefresh.addEventListener("click", () => loadDashboard(true));
    }

    if (elements.btnSimulate) {
        elements.btnSimulate.addEventListener("click", simulateSensorData);
    }

    if (elements.btnExport) {
        elements.btnExport.addEventListener("click", exportCsv);
    }

    if (elements.btnReset) {
        elements.btnReset.addEventListener("click", resetSensorData);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    registerEventListeners();
    activateSidebarMenu();
    loadDashboard();

    setInterval(() => {
        loadDashboard(false);
    }, 10000);
});