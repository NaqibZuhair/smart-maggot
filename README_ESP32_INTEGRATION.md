# Smart Maggot Dashboard

Panduan ini digunakan untuk menjalankan dashboard Smart Maggot dan menghubungkan data sensor dari ESP32.

## 1. Kebutuhan Sistem

Pastikan laptop sudah memiliki:

* Python 3
* MySQL atau Laragon
* Git, jika project diambil dari GitHub
* Browser
* Koneksi WiFi yang sama antara laptop dan ESP32

## 2. Setup Project

Masuk ke folder project, lalu install dependency:

```bash
pip install -r requirements.txt
```

Buat file `.env` dari contoh konfigurasi:

```bash
copy .env.example .env
```

Isi file `.env` sesuai konfigurasi lokal.

Contoh:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=smart_maggot
DB_PORT=3306

SECRET_KEY=smart-maggot-local-secret-2026
IOT_API_KEY=smart-maggot-esp32-key-2026

FLASK_ENV=development
FLASK_DEBUG=1
ALLOWED_ORIGIN=*
PORT=5000
```

Catatan:

* `SECRET_KEY` digunakan untuk session login dashboard.
* `IOT_API_KEY` digunakan ESP32 untuk mengirim data sensor.
* Jangan upload file `.env` ke GitHub.

## 3. Setup Database dan Admin

Jalankan file berikut:

```bash
python create_admin.py
```

Isi nama, email, dan password admin sesuai kebutuhan.

File ini akan membuat database, tabel `users`, tabel `sensor_data`, dan akun admin.

## 4. Menjalankan Dashboard

Jalankan Flask:

```bash
python app.py
```

Buka dashboard di browser laptop:

```text
http://127.0.0.1:5000
```

Login menggunakan akun admin yang sudah dibuat.

## 5. Endpoint untuk ESP32

ESP32 mengirim data sensor ke endpoint berikut:

```text
POST http://SERVER_HOST:5000/api/sensor/store
```

Ganti `SERVER_HOST` dengan alamat laptop yang menjalankan Flask.

Contoh:

```text
POST http://192.168.1.10:5000/api/sensor/store
```

Catatan penting:

* Browser di laptop boleh membuka `http://127.0.0.1:5000`.
* ESP32 tidak boleh memakai `127.0.0.1`.
* Dari sisi ESP32, `127.0.0.1` berarti ESP32 itu sendiri, bukan laptop.
* ESP32 harus memakai IP laptop yang menjalankan Flask.
* Laptop dan ESP32 harus berada di jaringan WiFi yang sama.

## 6. Header Request ESP32

Setiap request dari ESP32 wajib membawa header:

```text
Content-Type: application/json
X-API-Key: isi_sesuai_IOT_API_KEY_di_file_env
```

Contoh:

```text
Content-Type: application/json
X-API-Key: smart-maggot-esp32-key-2026
```

## 7. Body JSON

Format data yang dikirim ESP32:

```json
{
  "suhu": 29.5,
  "kelembaban": 72.4
}
```

Field wajib:

* `suhu`
* `kelembaban`

Tipe data harus angka.

## 8. Response Jika Berhasil

Jika data berhasil masuk, server akan mengirim response:

```json
{
  "success": true,
  "message": "Data sensor berhasil disimpan."
}
```

Setelah data berhasil masuk:

* Suhu terbaru akan berubah.
* Kelembaban terbaru akan berubah.
* Grafik akan bertambah.
* Riwayat data akan bertambah.
* Status ESP32 akan menjadi Online.

## 9. Response Jika API Key Salah

Jika `X-API-Key` salah atau tidak dikirim, server akan mengirim response:

```json
{
  "success": false,
  "message": "API key tidak valid."
}
```

atau:

```json
{
  "success": false,
  "message": "Header X-API-Key wajib dikirim."
}
```

## 10. Tes Manual dengan Curl

Tes endpoint tanpa ESP32:

```bash
curl -X POST http://127.0.0.1:5000/api/sensor/store -H "Content-Type: application/json" -H "X-API-Key: smart-maggot-esp32-key-2026" -d "{\"suhu\":29.5,\"kelembaban\":72.4}"
```

Jika memakai Git Bash, Linux, atau Mac:

```bash
curl -X POST http://127.0.0.1:5000/api/sensor/store \
-H "Content-Type: application/json" \
-H "X-API-Key: smart-maggot-esp32-key-2026" \
-d '{"suhu":29.5,"kelembaban":72.4}'
```

## 11. Logika Analisis Dashboard

Dashboard memakai batas berikut:

```text
Suhu > 32°C = Terlalu Panas
Suhu < 25°C = Terlalu Dingin
Kelembaban > 80% = Terlalu Lembab
Kelembaban < 60% = Terlalu Kering
Selain itu = Normal
```

## 12. Status Koneksi ESP32

Dashboard menampilkan status koneksi ESP32.

```text
Online = data terakhir masuk kurang dari atau sama dengan 60 detik
Offline = lebih dari 60 detik belum ada data baru
```

## 13. Troubleshooting

### Data tidak masuk ke dashboard

Cek hal berikut:

1. Flask sudah berjalan dengan `python app.py`.
2. Endpoint yang dipakai ESP32 sudah benar.
3. ESP32 dan laptop berada di WiFi yang sama.
4. Header `X-API-Key` sudah sesuai dengan `IOT_API_KEY`.
5. Firewall laptop tidak memblokir port `5000`.
6. Body JSON sudah memakai field `suhu` dan `kelembaban`.

### Dashboard bisa dibuka, tapi ESP32 gagal kirim data

Kemungkinan besar ESP32 masih memakai:

```text
http://127.0.0.1:5000
```

Ganti dengan IP laptop yang menjalankan Flask.

### Login gagal

Jalankan ulang:

```bash
python create_admin.py
```

Lalu buat atau update akun admin.

## 14. Format Integrasi Singkat

Gunakan format berikut di program ESP32:

```text
URL:
http://SERVER_HOST:5000/api/sensor/store

Method:
POST

Headers:
Content-Type: application/json
X-API-Key: isi_sesuai_IOT_API_KEY

Body:
{
  "suhu": nilai_suhu,
  "kelembaban": nilai_kelembaban
}
```
