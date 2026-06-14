import os
import random
import secrets
from functools import wraps

import pymysql
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from werkzeug.security import check_password_hash

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY belum diatur di file .env")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("FLASK_ENV") == "production"

allowed_origin = os.getenv("ALLOWED_ORIGIN", "*")
CORS(app, resources={r"/api/*": {"origins": allowed_origin}})

BATAS_SUHU_PANAS = 32
BATAS_SUHU_DINGIN = 25
BATAS_KELEMBABAN_LEMBAB = 80
BATAS_KELEMBABAN_KERING = 60
BATAS_OFFLINE_DETIK = 60


def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "smart_maggot"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def to_float(value):
    if value is None:
        return 0
    return float(value)


def to_int(value):
    if value is None:
        return 0
    return int(value)


def json_error(message, status_code=400, error=None):
    payload = {
        "success": False,
        "message": message,
    }

    if error and os.getenv("FLASK_ENV") != "production":
        payload["error"] = str(error)

    return jsonify(payload), status_code


def tentukan_status(suhu, kelembaban):
    if suhu > BATAS_SUHU_PANAS:
        return (
            "Terlalu Panas",
            "Suhu kandang terlalu tinggi. Periksa ventilasi, kurangi paparan panas langsung, dan tambahkan peneduh.",
        )

    if suhu < BATAS_SUHU_DINGIN:
        return (
            "Terlalu Dingin",
            "Suhu kandang terlalu rendah. Periksa posisi kandang dan pastikan lingkungan tidak terlalu dingin.",
        )

    if kelembaban > BATAS_KELEMBABAN_LEMBAB:
        return (
            "Terlalu Lembab",
            "Kelembaban terlalu tinggi. Kurangi kadar air pada media dan perbaiki sirkulasi udara.",
        )

    if kelembaban < BATAS_KELEMBABAN_KERING:
        return (
            "Terlalu Kering",
            "Kelembaban terlalu rendah. Jaga kelembaban media agar kondisi maggot tetap stabil.",
        )

    return (
        "Normal",
        "Kondisi suhu dan kelembaban kandang maggot berada dalam batas normal.",
    )


def buat_kesimpulan_dan_rekomendasi(data):
    total_data = to_int(data.get("total_data"))
    total_normal = to_int(data.get("total_normal"))
    total_peringatan = to_int(data.get("total_peringatan"))

    total_panas = to_int(data.get("total_terlalu_panas"))
    total_dingin = to_int(data.get("total_terlalu_dingin"))
    total_lembab = to_int(data.get("total_terlalu_lembab"))
    total_kering = to_int(data.get("total_terlalu_kering"))

    if total_data == 0:
        return {
            "persentase_normal": 0,
            "persentase_peringatan": 0,
            "kesimpulan": "Belum ada data sensor yang tersimpan. Silakan buat data simulasi atau kirim data dari perangkat ESP32.",
            "rekomendasi": "Lakukan pengambilan data terlebih dahulu agar sistem dapat memberikan analisis kondisi kandang maggot.",
        }

    persentase_normal = round((total_normal / total_data) * 100, 2)
    persentase_peringatan = round((total_peringatan / total_data) * 100, 2)

    if persentase_normal >= 80:
        kondisi_umum = "stabil"
    elif persentase_normal >= 60:
        kondisi_umum = "cukup stabil"
    else:
        kondisi_umum = "kurang stabil"

    kesimpulan = (
        f"Berdasarkan {total_data} data sensor, kondisi kandang maggot tergolong {kondisi_umum}. "
        f"Sebanyak {persentase_normal}% data berada pada kondisi normal, sedangkan "
        f"{persentase_peringatan}% data berada pada kondisi peringatan."
    )

    daftar_masalah = {
        "suhu terlalu panas": total_panas,
        "suhu terlalu dingin": total_dingin,
        "kelembaban terlalu tinggi": total_lembab,
        "kelembaban terlalu rendah": total_kering,
    }

    masalah_dominan = max(daftar_masalah, key=daftar_masalah.get)
    jumlah_masalah_dominan = daftar_masalah[masalah_dominan]

    if total_peringatan == 0:
        rekomendasi = (
            "Kondisi kandang sudah baik. Tetap lakukan monitoring berkala agar suhu dan kelembaban "
            "tetap berada pada batas ideal."
        )
    elif masalah_dominan == "suhu terlalu panas" and jumlah_masalah_dominan > 0:
        rekomendasi = (
            "Masalah yang paling sering muncul adalah suhu terlalu panas. Disarankan mengecek ventilasi, "
            "mengurangi paparan sinar matahari langsung, dan menambahkan peneduh pada area kandang."
        )
    elif masalah_dominan == "suhu terlalu dingin" and jumlah_masalah_dominan > 0:
        rekomendasi = (
            "Masalah yang paling sering muncul adalah suhu terlalu dingin. Disarankan menempatkan kandang "
            "di area yang lebih stabil dan menghindari lokasi yang terlalu lembab atau terlalu terbuka pada malam hari."
        )
    elif masalah_dominan == "kelembaban terlalu tinggi" and jumlah_masalah_dominan > 0:
        rekomendasi = (
            "Masalah yang paling sering muncul adalah kelembaban terlalu tinggi. Disarankan mengurangi kadar air "
            "pada media, memperbaiki sirkulasi udara, dan memastikan media tidak terlalu basah."
        )
    elif masalah_dominan == "kelembaban terlalu rendah" and jumlah_masalah_dominan > 0:
        rekomendasi = (
            "Masalah yang paling sering muncul adalah kelembaban terlalu rendah. Disarankan menjaga kelembaban media "
            "agar tidak terlalu kering dan melakukan pengecekan kondisi media secara rutin."
        )
    else:
        rekomendasi = (
            "Terdapat beberapa kondisi peringatan. Disarankan melakukan pengecekan rutin pada ventilasi, posisi kandang, "
            "dan kelembaban media maggot."
        )

    return {
        "persentase_normal": persentase_normal,
        "persentase_peringatan": persentase_peringatan,
        "kesimpulan": kesimpulan,
        "rekomendasi": rekomendasi,
    }


def simpan_data_sensor(suhu, kelembaban):
    status, keterangan = tentukan_status(suhu, kelembaban)
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO sensor_data
                (suhu, kelembaban, status_kondisi, keterangan)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (suhu, kelembaban, status, keterangan))
            connection.commit()

            return {
                "id": cursor.lastrowid,
                "suhu": suhu,
                "kelembaban": kelembaban,
                "status_kondisi": status,
                "keterangan": keterangan,
            }

    finally:
        connection.close()


def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return json_error("Akses ditolak. Silakan login terlebih dahulu.", 401)
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return json_error("Akses ditolak. Silakan login terlebih dahulu.", 401)
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            if request.path.startswith("/api/"):
                return json_error("Akses ditolak. Hanya admin yang boleh melakukan aksi ini.", 403)
            return "Akses ditolak. Hanya admin yang boleh melakukan aksi ini.", 403

        return function(*args, **kwargs)

    return wrapper


def validasi_api_key_esp32():
    expected_api_key = os.getenv("IOT_API_KEY")
    api_key = request.headers.get("X-API-Key")

    if not expected_api_key:
        return False, "IOT_API_KEY belum diatur di server."

    if not api_key:
        return False, "Header X-API-Key wajib dikirim."

    if not secrets.compare_digest(api_key, expected_api_key):
        return False, "API key tidak valid."

    return True, None


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Email dan password wajib diisi."
            return render_template("login.html", error=error)

        connection = None

        try:
            connection = get_db_connection()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, nama, email, password, role FROM users WHERE email = %s LIMIT 1",
                    (email,),
                )
                user = cursor.fetchone()

            if user and check_password_hash(user["password"], password):
                session.clear()
                session["user_id"] = user["id"]
                session["nama"] = user["nama"]
                session["email"] = user["email"]
                session["role"] = user["role"]

                return redirect(url_for("home"))

            error = "Email atau password salah."

        except Exception as e:
            error = f"Terjadi kesalahan: {str(e)}"

        finally:
            if connection:
                connection.close()

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    return render_template(
        "dashboard.html",
        nama=session.get("nama"),
        role=session.get("role"),
    )


@app.route("/api/test")
def api_test():
    return jsonify({
        "success": True,
        "message": "API Flask berhasil aktif.",
        "project": "Smart Maggot Monitoring",
    })


@app.route("/api/db-test")
@login_required
def db_test():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total_data FROM sensor_data")
            result = cursor.fetchone()

        return jsonify({
            "success": True,
            "message": "Koneksi database berhasil.",
            "total_data_sensor": result["total_data"],
        })

    except Exception as e:
        return json_error("Koneksi database gagal.", 500, e)

    finally:
        if connection:
            connection.close()


@app.route("/api/sensor/store", methods=["POST"])
def sensor_store():
    api_key_valid, api_key_message = validasi_api_key_esp32()

    if not api_key_valid:
        return json_error(api_key_message, 401)

    data = request.get_json(silent=True)

    if data:
        suhu = data.get("suhu")
        kelembaban = data.get("kelembaban")
    else:
        suhu = request.form.get("suhu")
        kelembaban = request.form.get("kelembaban")

    if suhu is None or kelembaban is None:
        return json_error("Data suhu dan kelembaban wajib dikirim.", 400)

    try:
        suhu = round(float(suhu), 2)
        kelembaban = round(float(kelembaban), 2)
    except ValueError:
        return json_error("Suhu dan kelembaban harus berupa angka.", 400)

    if suhu < 0 or suhu > 80:
        return json_error("Nilai suhu tidak valid. Masukkan suhu antara 0 sampai 80 derajat Celsius.", 400)

    if kelembaban < 0 or kelembaban > 100:
        return json_error("Nilai kelembaban tidak valid. Masukkan kelembaban antara 0 sampai 100 persen.", 400)

    try:
        data_sensor = simpan_data_sensor(suhu, kelembaban)
    except Exception as e:
        return json_error("Data sensor gagal disimpan.", 500, e)

    return jsonify({
        "success": True,
        "message": "Data sensor berhasil disimpan.",
        "data": data_sensor,
    })


@app.route("/api/sensor/simulate")
@login_required
def sensor_simulate():
    suhu = round(random.uniform(24, 36), 2)
    kelembaban = round(random.uniform(55, 90), 2)

    try:
        data_sensor = simpan_data_sensor(suhu, kelembaban)
    except Exception as e:
        return json_error("Data simulasi gagal dibuat.", 500, e)

    return jsonify({
        "success": True,
        "message": "Data simulasi berhasil dibuat.",
        "data": data_sensor,
    })


@app.route("/api/sensor/latest")
@login_required
def sensor_latest():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    suhu,
                    kelembaban,
                    status_kondisi,
                    keterangan,
                    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at,
                    TIMESTAMPDIFF(SECOND, created_at, NOW()) AS detik_sejak_update
                FROM sensor_data
                ORDER BY id DESC
                LIMIT 1
            """)
            data = cursor.fetchone()

        if data:
            detik_sejak_update = to_int(data.get("detik_sejak_update"))

            if detik_sejak_update <= BATAS_OFFLINE_DETIK:
                data["status_perangkat"] = "Online"
                data["koneksi_perangkat"] = "online"
                data["pesan_perangkat"] = "ESP32 aktif dan baru saja mengirim data sensor."
            else:
                data["status_perangkat"] = "Offline"
                data["koneksi_perangkat"] = "offline"
                data["pesan_perangkat"] = (
                    f"Belum ada data baru dari ESP32 selama {detik_sejak_update} detik."
                )

        return jsonify({
            "success": True,
            "data": data,
        })

    except Exception as e:
        return json_error("Gagal mengambil data sensor terbaru.", 500, e)

    finally:
        if connection:
            connection.close()


@app.route("/api/sensor/history")
@login_required
def sensor_history():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    suhu,
                    kelembaban,
                    status_kondisi,
                    keterangan,
                    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i:%s') AS created_at
                FROM sensor_data
                ORDER BY id DESC
                LIMIT 20
            """)
            data = cursor.fetchall()

        data.reverse()

        return jsonify({
            "success": True,
            "data": data,
        })

    except Exception as e:
        return json_error("Gagal mengambil riwayat data sensor.", 500, e)

    finally:
        if connection:
            connection.close()


@app.route("/api/sensor/statistics")
@login_required
def sensor_statistics():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_data,
                    ROUND(AVG(suhu), 2) AS rata_suhu,
                    ROUND(AVG(kelembaban), 2) AS rata_kelembaban,
                    MAX(suhu) AS suhu_tertinggi,
                    MIN(suhu) AS suhu_terendah,
                    MAX(kelembaban) AS kelembaban_tertinggi,
                    MIN(kelembaban) AS kelembaban_terendah,
                    SUM(CASE WHEN status_kondisi = 'Normal' THEN 1 ELSE 0 END) AS total_normal,
                    SUM(CASE WHEN status_kondisi != 'Normal' THEN 1 ELSE 0 END) AS total_peringatan,
                    SUM(CASE WHEN status_kondisi = 'Terlalu Panas' THEN 1 ELSE 0 END) AS total_terlalu_panas,
                    SUM(CASE WHEN status_kondisi = 'Terlalu Dingin' THEN 1 ELSE 0 END) AS total_terlalu_dingin,
                    SUM(CASE WHEN status_kondisi = 'Terlalu Lembab' THEN 1 ELSE 0 END) AS total_terlalu_lembab,
                    SUM(CASE WHEN status_kondisi = 'Terlalu Kering' THEN 1 ELSE 0 END) AS total_terlalu_kering
                FROM sensor_data
            """)
            data = cursor.fetchone()

        data = data or {}

        data["total_data"] = to_int(data.get("total_data"))
        data["rata_suhu"] = to_float(data.get("rata_suhu"))
        data["rata_kelembaban"] = to_float(data.get("rata_kelembaban"))
        data["suhu_tertinggi"] = to_float(data.get("suhu_tertinggi"))
        data["suhu_terendah"] = to_float(data.get("suhu_terendah"))
        data["kelembaban_tertinggi"] = to_float(data.get("kelembaban_tertinggi"))
        data["kelembaban_terendah"] = to_float(data.get("kelembaban_terendah"))

        data["total_normal"] = to_int(data.get("total_normal"))
        data["total_peringatan"] = to_int(data.get("total_peringatan"))
        data["total_terlalu_panas"] = to_int(data.get("total_terlalu_panas"))
        data["total_terlalu_dingin"] = to_int(data.get("total_terlalu_dingin"))
        data["total_terlalu_lembab"] = to_int(data.get("total_terlalu_lembab"))
        data["total_terlalu_kering"] = to_int(data.get("total_terlalu_kering"))

        hasil_analisis = buat_kesimpulan_dan_rekomendasi(data)
        data.update(hasil_analisis)

        return jsonify({
            "success": True,
            "data": data,
        })

    except Exception as e:
        return json_error("Gagal mengambil statistik data sensor.", 500, e)

    finally:
        if connection:
            connection.close()


@app.route("/api/sensor/export-csv")
@login_required
def sensor_export_csv():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, suhu, kelembaban, status_kondisi, keterangan, created_at
                FROM sensor_data
                ORDER BY id DESC
            """)
            data = cursor.fetchall()

        csv_data = "id,suhu,kelembaban,status_kondisi,keterangan,created_at\n"

        for row in data:
            keterangan = str(row["keterangan"]).replace(",", " ").replace("\n", " ")

            csv_data += (
                f'{row["id"]},'
                f'{row["suhu"]},'
                f'{row["kelembaban"]},'
                f'{row["status_kondisi"]},'
                f'{keterangan},'
                f'{row["created_at"]}\n'
            )

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=data_sensor_maggot.csv",
            },
        )

    except Exception as e:
        return json_error("Gagal export data sensor.", 500, e)

    finally:
        if connection:
            connection.close()


@app.route("/api/sensor/reset", methods=["POST"])
@admin_required
def sensor_reset():
    connection = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sensor_data")
            connection.commit()

        return jsonify({
            "success": True,
            "message": "Semua data sensor berhasil dihapus.",
        })

    except Exception as e:
        return json_error("Gagal menghapus data sensor.", 500, e)

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG") == "1"
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=debug_mode,
    )