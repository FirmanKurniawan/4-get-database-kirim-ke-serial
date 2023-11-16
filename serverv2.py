import asyncio
import serial
import psycopg2

# Mapping dari nilai lama ke nilai baru untuk divisi
division_mapping = {0: "IT", 1: "Finance", 2: "HR"}
# Mapping dari nilai lama ke nilai baru untuk tipe (in, out)
type_mapping = {0: "in", 1: "out"}

async def process_serial_data(serial_data, cursor):
    # Pisahkan data menjadi elemen-elemen menggunakan pemisah "|"
    data_elements = serial_data.strip().split("|")

    # Ubah nilai kolom 3, 4, 5 sesuai dengan mapping
    division_code = int(data_elements[2])
    type_code = int(data_elements[3])
    synchronize_code = int(data_elements[4])

    data_elements[2] = division_mapping.get(division_code, "Unknown Division")
    data_elements[3] = type_mapping.get(type_code, "Unknown Type")
    data_elements[4] = "null" if synchronize_code == 0 else "Not Null"

    # Buat pernyataan SQL INSERT
    insert_statement = f"INSERT INTO presensis (id, name, division, type, synchronize, created_at, updated_at) VALUES ({data_elements[0]}, '{data_elements[1]}', '{data_elements[2]}', '{data_elements[3]}', {data_elements[4]}, '{data_elements[5]}', '{data_elements[6]}');"
    
    # Eksekusi pernyataan INSERT ke database
    cursor.execute(insert_statement)

async def send_presensi_data(serial_port):
    # Kirim data "presensi" ke port serial
    serial_port.write("presensi\n".encode('ascii'))
    print("Data presensi dikirim")

    # Tunggu sebentar untuk memberikan waktu pada komputer lain untuk memproses dan mengirim balik data
    await asyncio.sleep(2)

async def send_end(serial_port):
    serial_port.write("END\n".encode('ascii'))

    # Tunggu sebentar untuk memberikan waktu pada komputer lain untuk memproses dan mengirim balik data
    await asyncio.sleep(2)

async def read_serial(serial_port):
    conn = psycopg2.connect(
        host="localhost",
        database="presensi",
        user="postgres",
        password="postgres"
    )

    cursor = conn.cursor()

    try:
        # Kirim data presensi ke port serial
        await send_presensi_data(serial_port)

        while True:
            # Menerima data dari port serial
            received_data = await asyncio.to_thread(serial_port.readline)
            decoded_data = received_data.decode('ascii').strip()

            # Memeriksa apakah data diterima
            if decoded_data:
                print("Data diterima")

                # Process and print each line of the received data
                for line in decoded_data.split("\n"):
                    await process_serial_data(line, cursor)
                    conn.commit()  # Commit perubahan ke database

                    await send_end(serial_port)

            await asyncio.sleep(1)  # Menunggu sejenak sebelum mengulang loop
    finally:
        conn.close()

async def main():
    serial_port = serial.Serial('COM5', 19200, timeout=1)

    try:
        task = asyncio.create_task(read_serial(serial_port))
        await asyncio.gather(task)
    except KeyboardInterrupt:
        pass
    finally:
        serial_port.close()

if __name__ == "__main__":
    asyncio.run(main())
