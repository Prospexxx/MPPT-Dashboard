# debug_serial.py — jalankan ini dulu, BUKAN dashboard
import serial
import serial.tools.list_ports

# Ganti COM4 sesuai port kamu
PORT     = "COM4"
BAUDRATE = 9600

print("=== DEBUG SERIAL ===")
print("Membuka port...")

try:
    ser = serial.Serial(PORT, BAUDRATE, timeout=2)
    print(f"Port {PORT} terbuka. Menunggu data dari STM32...\n")
    
    for i in range(30):  # Baca 30 baris
        line = ser.readline()
        if line:
            decoded = line.decode('utf-8', errors='ignore').strip()
            parts   = decoded.split()
            print(f"[{i+1:02d}] RAW  : '{decoded}'")
            print(f"      KOLOM: {len(parts)} kolom → {parts}")
            print()
        else:
            print(f"[{i+1:02d}] TIMEOUT — tidak ada data masuk!")
    
    # Test kirim perintah
    print("\n=== TEST KIRIM PERINTAH ===")
    for cmd in ["M1\n", "M2\n", "ST\n"]:
        ser.write(cmd.encode('utf-8'))
        ser.flush()
        print(f"Kirim: {repr(cmd)} → OK")
        import time; time.sleep(0.5)
    
    ser.close()
    print("\nSelesai.")

except serial.SerialException as e:
    print(f"ERROR: {e}")