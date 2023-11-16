import asyncio
import serial
import psycopg2

# Mapping dari nilai lama ke nilai baru untuk divisi
division_mapping = {"IT": 0, "Finance": 1, "HR": 2}
# Mapping dari nilai lama ke nilai baru untuk tipe (in, out)
type_mapping = {"in": 0, "out": 1}

async def read_serial(serial_port):
    conn = psycopg2.connect(
        host="localhost",
        database="presensi",
        user="postgres",
        password="postgres"
    )

    cursor = conn.cursor()

    while True:
        received_data = await asyncio.to_thread(serial_port.readline)
        decoded_data = received_data.decode('ascii').strip()
        decoded_data = "presensi"

        if decoded_data == "presensi":
            print("masuk")
            query = """
                SELECT id, name, division, type, synchronize, created_at, updated_at
                FROM presensis
                WHERE synchronize IS NULL
                LIMIT 2
            """
            cursor.execute(query)
            results = cursor.fetchall()

            # Update nilai divisi dan tipe dalam variabel results
            for i in range(len(results)):
                if results[i][2] in division_mapping and results[i][3] in type_mapping:
                    results[i] = results[i][:2] + (division_mapping[results[i][2]],) + (type_mapping[results[i][3]],) + results[i][4:]

            # Serialize data into the desired format
            serialized_data = "\n".join("|".join(
                str(value) if value is not None else '0' for value in row
            ) for row in results)
            print(serialized_data)

            # Send the serialized data through the serial port
            serial_port.write(serialized_data.encode('ascii'))

            # Wait for the "END" signal
            end_signal = await asyncio.to_thread(serial_port.readline)
            decoded_end_signal = end_signal.decode('ascii').strip()

            if decoded_end_signal == "END":
                # Set synchronize to true for the processed rows
                for row in results:
                    update_query = f"UPDATE presensis SET synchronize = true WHERE id = {row[0]};"
                    cursor.execute(update_query)

                # Commit changes to the database
                conn.commit()

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
