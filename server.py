import psycopg2
import serial

# Konfigurasi koneksi ke database PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="presensi",
    user="postgres",
    password="postgres"
)

# Membuka kursor untuk berinteraksi dengan database
cursor = conn.cursor()

# Port serial
serial_port = serial.Serial('COM4', 19200, timeout=1)  # Sesuaikan dengan port dan baud rate yang sesuai

try:
    # Mengirim data "presensi" ke port serial
    data_to_send = "presensi\n"
    serial_port.write(data_to_send.encode('utf-8'))

    # Menerima dan memproses data dari port serial dengan perulangan
    while True:
        received_data = serial_port.readline().decode('utf-8').strip()

        # Jika data yang diterima adalah pernyataan SQL INSERT, lakukan aksi berikut
        if received_data.startswith("INSERT INTO presensis"):
            # Eksekusi pernyataan SQL INSERT ke database
            cursor.execute(received_data)
            conn.commit()

            print("Data presensi telah dieksekusi ke database.")

except KeyboardInterrupt:
    # Tangani penutupan program ketika pengguna menekan Ctrl+C
    print("Program dihentikan oleh pengguna.")

except Exception as e:
    # Tangani kesalahan
    print(f"Terjadi kesalahan: {str(e)}")

finally:
    # Tutup kursor dan koneksi database
    cursor.close()
    conn.close()

    # Tutup port serial
    serial_port.close()
