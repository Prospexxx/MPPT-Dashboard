"""
Quick diagnostic: read raw bytes from COM4 at 115200 and show what arrives.
Close Arduino Serial Monitor first, then run this script.
Press Ctrl+C to stop.
"""
import serial
import time

PORT = "COM4"
BAUD = 115200

print(f"Opening {PORT} at {BAUD} baud...")
ser = serial.Serial(PORT, BAUD, timeout=1)
ser.reset_input_buffer()
print("Listening... (Ctrl+C to stop)\n")

try:
    for i in range(30):
        raw = ser.readline()
        if raw:
            # Show raw bytes AND decoded text
            text = raw.decode('utf-8', errors='replace').strip()
            has_null = b'\x00' in raw
            print(f"[{i:3d}] len={len(raw):4d}  null_bytes={'YES' if has_null else 'no '}  text='{text[:80]}'")
            print(f"      raw_hex={raw[:30].hex()}")
        else:
            print(f"[{i:3d}] (timeout - no data)")
except KeyboardInterrupt:
    pass
finally:
    ser.close()
    print("\nDone.")
