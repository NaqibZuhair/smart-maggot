# Smart Maggot Monitoring

Smart Maggot Monitoring adalah aplikasi web berbasis Python Flask yang digunakan untuk memantau suhu dan kelembaban kandang maggot. Sistem ini dirancang sebagai project UAS mata kuliah Mobile Computing berdasarkan konsep Smart Maggot Farming berbasis IoT.

Pada tahap awal, sistem menggunakan data simulasi untuk menguji API, database, dashboard, grafik, riwayat data, dan analisis sensor. Setelah perangkat tersedia, sistem akan diintegrasikan dengan ESP32 dan sensor DHT11/DHT22 agar data yang masuk berasal dari pembacaan sensor secara langsung.

## Fitur Utama

* Dashboard monitoring suhu dan kelembaban kandang maggot
* API untuk menerima data sensor
* Penyimpanan data sensor ke database MySQL
* Tombol generate data simulasi
* Tampilan data terbaru
* Riwayat data sensor
* Grafik suhu dan kelembaban menggunakan Chart.js
* Analisis statistik data sensor
* Kesimpulan sementara otomatis berdasarkan data sensor

## Teknologi yang Digunakan

* Python
* Flask
* Flask-CORS
* PyMySQL
* Python Dotenv
* MySQL
* HTML
* CSS
* JavaScript
* Chart.js
* Laragon

## Struktur Project

```text
```text
smart-maggot/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── database.sql
├── README.md
│
├── templates/
│   └── dashboard.html
│
├── static/
│   ├── css/
│   │   └── dashboard.css
│   │
│   ├── js/
│   │   └── dashboard.js
│   │
│   └── vendor/
│       └── chartjs/
│           └── chart.umd.min.js
│
└── venv/
```

Catatan: folder `venv/` dan file `.env` tidak perlu dipush ke GitHub.

```

Catatan: folder `venv/` dan file `.env` tidak perlu dipush ke GitHub.

## Persiapan Project

### 1. Clone atau salin project

Simpan project di folder Laragon:

```text
C:\laragon\www\smart-maggot
```

### 2. Buat virtual environment

```bash
python -m venv venv
```

### 3. Aktifkan virtual environment

Untuk Windows PowerShell:

```bash
.\venv\Scripts\activate
```

### 4. Install library

```bash
pip install -r requirements.txt
```

### 5. Buat file konfigurasi environment

Copy file:

```text
.env.example
```

menjadi:

```text
.env
```

Isi konfigurasi database:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=smart_maggot
DB_PORT=3306
```

Sesuaikan `DB_USER`, `DB_PASSWORD`, dan `DB_PORT` jika konfigurasi MySQL di laptop berbeda.

## Setup Database

Buka database manager Laragon, misalnya HeidiSQL, lalu import file:

```text
database.sql
```

Database yang digunakan:

```text
smart_maggot
```

Tabel utama:

```text
sensor_data
```

## Menjalankan Aplikasi

Aktifkan virtual environment:

```bash
.\venv\Scripts\activate
```

Jalankan Flask:

```bash
python app.py
```

Buka aplikasi di browser:

```text
http://127.0.0.1:5000
```

## Endpoint API

### Test API

```text
GET /api/test
```

Digunakan untuk mengecek apakah API Flask aktif.

### Test Database

```text
GET /api/db-test
```

Digunakan untuk mengecek koneksi Flask ke database MySQL.

### Simulasi Data Sensor

```text
GET /api/sensor/simulate
```

Digunakan untuk membuat data simulasi suhu dan kelembaban.

### Data Sensor Terbaru

```text
GET /api/sensor/latest
```

Digunakan untuk mengambil data sensor terbaru.

### Riwayat Data Sensor

```text
GET /api/sensor/history
```

Digunakan untuk mengambil 20 data sensor terbaru.

### Statistik Data Sensor

```text
GET /api/sensor/statistics
```

Digunakan untuk mengambil ringkasan analisis data sensor.

### Simpan Data Sensor

```text
POST /api/sensor/store
```

Endpoint ini akan digunakan oleh ESP32 untuk mengirim data sensor.

Format JSON:

```json
{
  "suhu": 30.5,
  "kelembaban": 75
}
```

Contoh respons:

```json
{
  "success": true,
  "message": "Data sensor berhasil disimpan.",
  "data": {
    "id": 1,
    "suhu": 30.5,
    "kelembaban": 75,
    "status_kondisi": "Normal",
    "keterangan": "Kondisi suhu dan kelembaban kandang maggot berada dalam batas normal."
  }
}
```

### Export Data Sensor CSV

```text
GET /api/sensor/export-csv
```

Digunakan untuk mengunduh seluruh data sensor dalam format CSV. File ini dapat dipakai untuk laporan, pengujian, atau analisis lanjutan di Excel.

### Reset Data Sensor

```text
POST /api/sensor/reset
```

Digunakan untuk menghapus seluruh data sensor dari database. Fitur ini membantu saat demo karena sistem dapat dikembalikan ke kondisi awal sebelum melakukan simulasi ulang.


## Aturan Status Kondisi

Sistem menentukan status kondisi berdasarkan suhu dan kelembaban.

| Kondisi                    | Status         |
| -------------------------- | -------------- |
| Suhu lebih dari 32°C       | Terlalu Panas  |
| Suhu kurang dari 25°C      | Terlalu Dingin |
| Kelembaban lebih dari 80%  | Terlalu Lembab |
| Kelembaban kurang dari 60% | Terlalu Kering |
| Selain kondisi di atas     | Normal         |

## Alur Kerja Sistem

```text
ESP32 + Sensor DHT11/DHT22
        ↓
Mengirim data suhu dan kelembaban melalui WiFi
        ↓
REST API Python Flask
        ↓
Database MySQL
        ↓
Dashboard Web
        ↓
Grafik, riwayat data, statistik, dan kesimpulan sementara
```

## Status Pengembangan

Fitur yang sudah selesai:

* Backend Flask
* Koneksi MySQL
* Database sensor_data
* API sensor
* Data simulasi
* Dashboard awal
* Riwayat data
* Grafik suhu dan kelembaban
* Statistik data sensor
* Kesimpulan otomatis

Fitur berikutnya:

* Pemisahan file HTML, CSS, dan JavaScript
* Perapian tampilan dashboard
* Export data
* Dokumentasi integrasi ESP32
* Integrasi ESP32 dengan sensor DHT11/DHT22
* Penambahan LCD, LED, dan buzzer

## Anggota Kelompok


| No | Nama                  | Peran                   | NIM         |
| -- | --------------------- | ----------------------- | ----------- |
| 1  | Naqib Zuhair Al-Hudri | Backend/API             | 2407411042  |
| 2  | Diandra Bagustri      | Dashboard               | 2407411000  |
| 3  | Muhammad Reza Arifin  | Database                | 2407411000  |
| 4  | Sulthon Fabian        | Hardware ESP32          | 2407411000  |

## Catatan

Project ini masih dalam tahap pengembangan. Data simulasi digunakan sementara sampai perangkat ESP32 dan sensor DHT11/DHT22 tersedia.
