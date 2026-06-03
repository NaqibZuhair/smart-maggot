import os
import random
import pymysql

from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "smart_maggot"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )


def tentukan_status(suhu, kelembaban):
    if suhu > 32:
        return (
            "Terlalu Panas",
            "Suhu kandang terlalu tinggi. Perlu pengecekan ventilasi atau peneduh."
        )

    if suhu < 25:
        return (
            "Terlalu Dingin",
            "Suhu kandang terlalu rendah. Perlu penyesuaian lingkungan kandang."
        )

    if kelembaban > 80:
        return (
            "Terlalu Lembab",
            "Kelembaban terlalu tinggi. Media maggot perlu dikontrol agar tidak terlalu basah."
        )

    if kelembaban < 60:
        return (
            "Terlalu Kering",
            "Kelembaban terlalu rendah. Media maggot perlu dijaga agar tidak terlalu kering."
        )

    return (
        "Normal",
        "Kondisi suhu dan kelembaban kandang maggot berada dalam batas normal."
    )


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
                "keterangan": keterangan
            }

    finally:
        connection.close()


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/api/test")
def api_test():
    return jsonify({
        "success": True,
        "message": "API Flask berhasil aktif."
    })


@app.route("/api/db-test")
def db_test():
    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total_data FROM sensor_data")
            result = cursor.fetchone()

        connection.close()

        return jsonify({
            "success": True,
            "message": "Koneksi database berhasil.",
            "total_data_sensor": result["total_data"]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Koneksi database gagal.",
            "error": str(e)
        }), 500


@app.route("/api/sensor/store", methods=["POST"])
def sensor_store():
    data = request.get_json(silent=True)

    if data:
        suhu = data.get("suhu")
        kelembaban = data.get("kelembaban")
    else:
        suhu = request.form.get("suhu")
        kelembaban = request.form.get("kelembaban")

    if suhu is None or kelembaban is None:
        return jsonify({
            "success": False,
            "message": "Data suhu dan kelembaban wajib dikirim."
        }), 400

    try:
        suhu = round(float(suhu), 2)
        kelembaban = round(float(kelembaban), 2)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Suhu dan kelembaban harus berupa angka."
        }), 400

    data_sensor = simpan_data_sensor(suhu, kelembaban)

    return jsonify({
        "success": True,
        "message": "Data sensor berhasil disimpan.",
        "data": data_sensor
    })


@app.route("/api/sensor/simulate")
def sensor_simulate():
    suhu = round(random.uniform(24, 36), 2)
    kelembaban = round(random.uniform(55, 90), 2)

    data_sensor = simpan_data_sensor(suhu, kelembaban)

    return jsonify({
        "success": True,
        "message": "Data simulasi berhasil dibuat.",
        "data": data_sensor
    })


@app.route("/api/sensor/latest")
def sensor_latest():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM sensor_data
                ORDER BY id DESC
                LIMIT 1
            """)
            data = cursor.fetchone()

        return jsonify({
            "success": True,
            "data": data
        })

    finally:
        connection.close()


@app.route("/api/sensor/history")
def sensor_history():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM sensor_data
                ORDER BY id DESC
                LIMIT 20
            """)
            data = cursor.fetchall()

        data.reverse()

        return jsonify({
            "success": True,
            "data": data
        })

    finally:
        connection.close()

@app.route("/api/sensor/statistics")
def sensor_statistics():
    connection = get_db_connection()

    try:
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
                    SUM(CASE WHEN status_kondisi != 'Normal' THEN 1 ELSE 0 END) AS total_peringatan
                FROM sensor_data
            """)
            data = cursor.fetchone()

        return jsonify({
            "success": True,
            "data": data
        })

    finally:
        connection.close()

@app.route("/api/sensor/export-csv")
def sensor_export_csv():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, suhu, kelembaban, status_kondisi, keterangan, created_at
                FROM sensor_data
                ORDER BY id DESC
            """)
            data = cursor.fetchall()

        csv_data = "id,suhu,kelembaban,status_kondisi,keterangan,created_at\n"

        for row in data:
            keterangan = str(row["keterangan"]).replace(",", " ")
            csv_data += f'{row["id"]},{row["suhu"]},{row["kelembaban"]},{row["status_kondisi"]},{keterangan},{row["created_at"]}\n'

        return Response(
            csv_data,
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=data_sensor_maggot.csv"
            }
        )

    finally:
        connection.close()

@app.route("/api/sensor/reset", methods=["POST"])
def sensor_reset():
    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM sensor_data")
            connection.commit()

        return jsonify({
            "success": True,
            "message": "Semua data sensor berhasil dihapus."
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Gagal menghapus data sensor.",
            "error": str(e)
        }), 500

    finally:
        connection.close()

if __name__ == "__main__":
    app.run(debug=True)