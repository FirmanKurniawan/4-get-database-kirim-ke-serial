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
    while True:
        # Menerima data dari port serial
        received_data = serial_port.readline().decode('utf-8').strip()

        # Jika data yang diterima adalah "presensi", lakukan aksi berikut
        if received_data == "presensi":
            # Query database untuk mengambil data yang ingin Anda dump
            query = """
                SELECT id, name, email, type, synchronize, created_at, updated_at
                FROM presensis
                WHERE synchronize IS NULL
            """
            # Eksekusi query
            cursor.execute(query)

            # Ambil hasil query
            results = cursor.fetchall()

            # Nama file untuk menyimpan pernyataan SQL INSERT
            sql_file = "data_dump.txt"  # Ganti dengan nama file yang Anda inginkan

            # Tulis pernyataan SQL INSERT ke file dan kirim ke port serial
            with open(sql_file, "w") as file:
                for row in results:
                    # Membuat pernyataan SQL INSERT dengan format waktu yang sesuai
                    timestamp_created = row[5].strftime('%Y-%m-%d %H:%M:%S+00')  # Mengonversi waktu created_at menjadi string
                    timestamp_updated = row[6].strftime('%Y-%m-%d %H:%M:%S+00')  # Mengonversi waktu updated_at menjadi string
                    insert_statement = f"INSERT INTO presensis (id, name, email, type, synchronize, created_at, updated_at) VALUES ({row[0]}, '{row[1]}', '{row[2]}', '{row[3]}', {row[4]}, '{timestamp_created}', '{timestamp_updated}');\n"
                    file.write(insert_statement)

                    # Kirim data ke port serial
                    serial_port.write(insert_statement.encode('utf-8'))

                    # Setel kolom "synchronize" menjadi "true"
                    update_query = f"UPDATE presensis SET synchronize = true WHERE id = {row[0]};"
                    cursor.execute(update_query)

            # Commit perubahan ke database
            conn.commit()

            print("Data presensi baru telah disimpan dan dikirim kembali ke port serial.")

except KeyboardInterrupt:
    # Tangani penutupan program ketika pengguna menekan Ctrl+C
    print("Program dihentikan oleh pengguna.")

except Exception as e:
    # Tangani kesalahan lainnya
    print(f"Terjadi kesalahan: {str(e)}")

finally:
    # Tutup kursor dan koneksi database
    cursor.close()
    conn.close()

    # Tutup port serial
    serial_port.close()
