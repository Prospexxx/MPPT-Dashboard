import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QComboBox, QTextEdit, QLabel)

class DummySender(QWidget):
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Pemilihan Port
        layout.addWidget(QLabel("1. Pilih Port Bluetooth:"))
        self.combo_port = QComboBox()
        layout.addWidget(self.combo_port)

        self.btn_refresh = QPushButton("Refresh Port")
        self.btn_refresh.clicked.connect(self.scan_ports)
        layout.addWidget(self.btn_refresh)

        # Tombol Connect
        layout.addWidget(QLabel("2. Hubungkan:"))
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_connect.clicked.connect(self.toggle_connection)
        layout.addWidget(self.btn_connect)

        # Tombol Kirim Data
        layout.addWidget(QLabel("3. Test Kirim Perintah:"))
        self.btn_m1 = QPushButton("Kirim M1 (WODE)")
        self.btn_m1.clicked.connect(lambda: self.send_command("M1"))
        layout.addWidget(self.btn_m1)

        self.btn_m2 = QPushButton("Kirim M2 (WOA)")
        self.btn_m2.clicked.connect(lambda: self.send_command("M2"))
        layout.addWidget(self.btn_m2)

        self.btn_st = QPushButton("Kirim ST (Start/Stop)")
        self.btn_st.clicked.connect(lambda: self.send_command("ST"))
        layout.addWidget(self.btn_st)

        # Log Aktivitas (Dibuat SEBELUM dipanggil oleh scan_ports)
        layout.addWidget(QLabel("Log Aktivitas:"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        # SEKARANG AMAN dipanggil di sini karena log_box sudah tercipta
        self.scan_ports()

        self.setLayout(layout)
        self.setWindowTitle("Dummy TX Tester - MPPT")
        self.resize(350, 450)

    def log(self, text):
        self.log_box.append(text)
        # Scroll otomatis ke baris paling bawah
        self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def scan_ports(self):
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.combo_port.addItem(port.device)
        if self.combo_port.count() == 0:
            self.combo_port.addItem("No Port")
        self.log("Port di-refresh.")

    def toggle_connection(self):
        # Jika sedang terbuka, maka tutup
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                self.serial_port = None
                self.btn_connect.setText("Connect")
                self.btn_connect.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
                self.log("🔴 Serial ditutup.")
            except Exception as e:
                self.log(f"❌ Error saat menutup: {e}")
        # Jika sedang tertutup, maka buka
        else:
            port = self.combo_port.currentText()
            if port == "No Port":
                self.log("⚠️ Tidak ada port yang dipilih!")
                return
            try:
                self.log(f"⏳ Mencoba connect ke {port} (9600 baud)...")
                
                # Menggunakan timeout kecil agar aman (0.1 detik)
                self.serial_port = serial.Serial(port, 9600, timeout=0.1)
                
                self.btn_connect.setText("Disconnect")
                self.btn_connect.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
                self.log(f"🟢 TERHUBUNG ke {port}")
            except Exception as e:
                self.log(f"❌ GAGAL terhubung: {e}")

    def send_command(self, cmd):
        if self.serial_port and self.serial_port.is_open:
            try:
                # Format perintah ditambah newline (\n) agar dikenali oleh STM32
                pesan = (cmd + '\n').encode('utf-8')
                self.serial_port.write(pesan)
                
                # Flush buffer agar memastikan data dikirim secara paksa ke modul Bluetooth
                self.serial_port.flush()
                
                self.log(f"✅ Berhasil kirim: {cmd}")
            except Exception as e:
                # Jika crash saat pengiriman (misal karena koneksi Bluetooth putus tiba-tiba),
                # program tidak akan exit, tapi menampilkan errornya di kotak log.
                self.log(f"❌ ERROR/CRASH saat kirim: {e}")
        else:
            self.log("⚠️ Port belum terhubung! Klik Connect dulu.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Memaksa gaya "Fusion" agar UI terlihat rapi di Windows/Mac/Linux
    app.setStyle("Fusion")
    
    window = DummySender()
    window.show()
    sys.exit(app.exec_())