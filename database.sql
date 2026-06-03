CREATE DATABASE IF NOT EXISTS smart_maggot;
USE smart_maggot;

CREATE TABLE IF NOT EXISTS sensor_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    suhu FLOAT NOT NULL,
    kelembaban FLOAT NOT NULL,
    status_kondisi VARCHAR(50) NOT NULL,
    keterangan TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);