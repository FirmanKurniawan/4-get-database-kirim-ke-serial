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

async def read_serial(serial_port):
    conn = psycopg2.connect(
        host="localhost",
        database="presensi",
        user="postgres",
        password="postgres"
    )

    cursor = conn.cursor()

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

            # Wait for the "END" signal
            end_signal = await asyncio.to_thread(serial_port.readline)
            decoded_end_signal = end_signal.decode('ascii').strip()

            if decoded_end_signal == "END":
                print("Proses selesai.")
                # Wait for any remaining data to be read
                await asyncio.to_thread(serial_port.read_all())

        await asyncio.sleep(1)  # Menunggu sejenak sebelum mengulang loop

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
