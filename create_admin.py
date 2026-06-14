import os
import getpass

import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "smart_maggot")
DB_PORT = int(os.getenv("DB_PORT", 3306))


def get_connection(use_database=True):
    config = {
        "host": DB_HOST,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "port": DB_PORT,
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False,
    }

    if use_database:
        config["database"] = DB_NAME

    return pymysql.connect(**config)


def setup_database():
    connection = get_connection(use_database=False)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            connection.commit()

        print(f"Database `{DB_NAME}` siap digunakan.")

    finally:
        connection.close()


def setup_tables():
    connection = get_connection(use_database=True)

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nama VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    role ENUM('admin', 'user') NOT NULL DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    suhu FLOAT NOT NULL,
                    kelembaban FLOAT NOT NULL,
                    status_kondisi VARCHAR(50) NOT NULL,
                    keterangan TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            connection.commit()

        print("Tabel `users` dan `sensor_data` siap digunakan.")

    finally:
        connection.close()


def create_or_update_admin():
    print("\n=== Buat atau Update Admin Dashboard ===")

    nama = input("Nama admin: ").strip()
    email = input("Email admin: ").strip().lower()
    password = getpass.getpass("Password admin: ").strip()
    konfirmasi_password = getpass.getpass("Ulangi password: ").strip()

    if not nama:
        print("Nama admin wajib diisi.")
        return

    if not email:
        print("Email admin wajib diisi.")
        return

    if not password:
        print("Password admin wajib diisi.")
        return

    if password != konfirmasi_password:
        print("Konfirmasi password tidak sama.")
        return

    password_hash = generate_password_hash(password)

    connection = get_connection(use_database=True)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s LIMIT 1", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                cursor.execute(
                    """
                    UPDATE users
                    SET nama = %s, password = %s, role = 'admin'
                    WHERE email = %s
                    """,
                    (nama, password_hash, email),
                )
                message = "Admin berhasil diperbarui."
            else:
                cursor.execute(
                    """
                    INSERT INTO users (nama, email, password, role)
                    VALUES (%s, %s, %s, 'admin')
                    """,
                    (nama, email, password_hash),
                )
                message = "Admin berhasil dibuat."

            connection.commit()

        print(message)
        print(f"Email login: {email}")

    finally:
        connection.close()


if __name__ == "__main__":
    setup_database()
    setup_tables()
    create_or_update_admin()