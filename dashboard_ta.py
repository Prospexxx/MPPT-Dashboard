import os
import sys
import serial
import serial.tools.list_ports
import pyqtgraph as pg
import numpy as np
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QLabel,
                             QComboBox, QSizePolicy)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QTimer

class DashboardTA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MPPT Dashboard - 2 Way Control & Auto-Split Log")
        self.setWindowIcon(QIcon('logo_aplikasi.ico'))
        self.setGeometry(100, 100, 1200, 750)

        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; color: #ffffff; }
            QLabel { font-size: 15px; font-weight: bold; color: #ffffff; }
            QPushButton { background-color: #000000; color: #ffffff; border-radius: 5px;
                          padding: 5px; font-weight: bold; border: 1px solid #555555; font-size: 14px; }
            QPushButton:hover { background-color: #333333; }
            QComboBox { background-color: #000000; color: #ffffff; border-radius: 5px;
                        padding: 5px; border: 1px solid #555555; font-size: 14px; }
            QComboBox QAbstractItemView { background-color: #1e1e1e; color: #ffffff;
                                          selection-background-color: #333333; }
        """)

        self.serial_port = None
        self._serial_buffer = ""
        self.BAUD_RATE   = 115200

        # --- FITUR AUTO SAVE & SPLIT LOG ---
        self.file_master = None
        self.file_modes = {}
        try:
            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_folder = f"run_{now_str}"
            os.makedirs(run_folder, exist_ok=True)
            
            self.file_master = open(os.path.join(run_folder, f"data_mppt_MASTER_{now_str}.txt"), "a")
            self.file_modes[0] = open(os.path.join(run_folder, f"data_mppt_STOP_{now_str}.txt"), "a")
            self.file_modes[1] = open(os.path.join(run_folder, f"data_mppt_WODE_{now_str}.txt"), "a")
            self.file_modes[2] = open(os.path.join(run_folder, f"data_mppt_WOA_{now_str}.txt"), "a")
            self.file_modes[3] = open(os.path.join(run_folder, f"data_mppt_DE_{now_str}.txt"), "a")
            self.file_modes[4] = open(os.path.join(run_folder, f"data_mppt_PnO_{now_str}.txt"), "a") 
            self.file_modes[5] = open(os.path.join(run_folder, f"data_mppt_GMPP_{now_str}.txt"), "a")
            print(f"Semua file log (Master dan per-Mode) siap digunakan di folder '{run_folder}'.")
        except Exception as e:
            print(f"Gagal membuat file log: {e}")

        self.init_ui()
        self.scan_ports()

        self.max_data = 50000
        self.waktu_general = []; self.data_general = []
        self.waktu_duty    = []; self.data_duty    = []
        self.waktu_wode    = []; self.data_wode    = []
        self.waktu_woa     = []; self.data_woa     = []
        self.waktu_de      = []; self.data_de      = []
        self.waktu_pno     = []; self.data_pno     = [] 

        self.current_mode = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.baca_serial_dan_update)
        self.timer.start(20)

    def scan_ports(self):
        self.combo_port.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.combo_port.addItem(port.device)
        if self.combo_port.count() == 0:
            self.combo_port.addItem("No Port")

    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
                self.serial_port = None
                self.btn_connect.setText("Connect")
                self.btn_connect.setStyleSheet("background-color: #005500; color: white;")
                self.lbl_status.setText("🔴 OFFLINE (Terputus)")
                self.lbl_status.setStyleSheet(
                    "background-color: #8b0000; color: white; padding: 8px;"
                    "border-radius: 5px; font-size: 15px;")
                self.combo_port.setEnabled(True)
                self.btn_refresh.setEnabled(True)
            except Exception:
                pass
        else:
            selected_port = self.combo_port.currentText()
            if selected_port == "No Port":
                return
            try:
                self.serial_port = serial.Serial(
                    selected_port, self.BAUD_RATE, timeout=0.1)
                self.serial_port.set_buffer_size(rx_size=65536)
                self.serial_port.reset_input_buffer()
                self._serial_buffer = ""
                self.btn_connect.setText("Disconnect")
                self.btn_connect.setStyleSheet("background-color: #8b0000; color: white;")
                self.lbl_status.setText(f"🟢 ONLINE ({selected_port})")
                self.lbl_status.setStyleSheet(
                    "background-color: #006400; color: white; padding: 8px;"
                    "border-radius: 5px; font-size: 15px;")
                self.combo_port.setEnabled(False)
                self.btn_refresh.setEnabled(False)
            except Exception:
                self.lbl_status.setText("🔴 GAGAL KONEK")
                self.lbl_status.setStyleSheet(
                    "background-color: #8b0000; color: white; padding: 8px;"
                    "border-radius: 5px; font-size: 15px;")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        plot_layout = QGridLayout()
        pg.setConfigOption('background', '#000000')
        pg.setConfigOption('foreground', 'w')

        self.plot_all   = self.create_plot("Perbandingan Algoritma MPPT", "Waktu (s)", "Daya (W)")
        self.plot_all.addLegend(offset=(-10, 10))
        self.plot_wode  = self.create_plot("Algoritma WOADE", "Waktu (s)", "Daya (W)")
        self.plot_woa   = self.create_plot("Algoritma WOA",   "Waktu (s)", "Daya (W)")
        self.plot_de    = self.create_plot("Algoritma DE",    "Waktu (s)", "Daya (W)")
        self.plot_pno   = self.create_plot("Algoritma Perturb & Observe", "Waktu (s)", "Daya (W)") 
        self.plot_duty  = self.create_plot("Duty Cycle",      "Waktu (s)", "Duty (%)")

        plot_layout.addWidget(self.plot_all,  0, 0); plot_layout.addWidget(self.plot_wode,  0, 1)
        plot_layout.addWidget(self.plot_woa,  1, 0); plot_layout.addWidget(self.plot_de,    1, 1)
        plot_layout.addWidget(self.plot_pno,  2, 0); plot_layout.addWidget(self.plot_duty,  2, 1)

        self.line_wode  = self.plot_wode.plot([],  [], pen=pg.mkPen(color='r', width=1.5))
        self.line_woa   = self.plot_woa.plot([],   [], pen=pg.mkPen(color='g', width=1.5))
        self.line_de    = self.plot_de.plot([],    [], pen=pg.mkPen(color='b', width=1.5))
        self.line_pno   = self.plot_pno.plot([], [], pen=pg.mkPen(color='c', width=1.5)) 
        self.line_duty  = self.plot_duty.plot([],  [], pen=pg.mkPen(color='m', width=1.5))

        self.line_all_general = self.plot_all.plot([], [], pen=pg.mkPen(color='y', width=1.5), name="GMPP/Manual")
        self.line_all_wode    = self.plot_all.plot([], [], pen=pg.mkPen(color='r', width=1.5), name="WODE")
        self.line_all_woa     = self.plot_all.plot([], [], pen=pg.mkPen(color='g', width=1.5), name="WOA")
        self.line_all_de      = self.plot_all.plot([], [], pen=pg.mkPen(color='b', width=1.5), name="DE")
        self.line_all_pno     = self.plot_all.plot([], [], pen=pg.mkPen(color='c', width=1.5), name="P&O") 

        main_layout.addLayout(plot_layout, stretch=4)

        control_widget = QWidget()
        control_widget.setMinimumWidth(250)
        control_widget.setMaximumWidth(320)
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        self.lbl_status = QLabel("🔴 OFFLINE (Silakan Connect)")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.lbl_status.setStyleSheet(
            "background-color: #8b0000; color: white; padding: 8px;"
            "border-radius: 5px; font-size: 15px;")
        self.lbl_status.setFixedHeight(40)
        control_layout.addWidget(self.lbl_status)

        conn_layout = QHBoxLayout()
        self.combo_port  = QComboBox(); self.combo_port.setMinimumHeight(35)
        self.btn_refresh = QPushButton("🔄"); self.btn_refresh.setFixedSize(35, 35)
        self.btn_refresh.clicked.connect(self.scan_ports)
        self.btn_connect = QPushButton("Connect"); self.btn_connect.setMinimumHeight(35)
        self.btn_connect.setStyleSheet("background-color: #005500; color: white;")
        self.btn_connect.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.combo_port, stretch=2)
        conn_layout.addWidget(self.btn_refresh)
        conn_layout.addWidget(self.btn_connect, stretch=2)
        control_layout.addLayout(conn_layout)

        btn_layout = QGridLayout(); btn_layout.setSpacing(10)
        btn_layout.setColumnStretch(0, 1)
        btn_layout.setColumnStretch(1, 1)

        self.ind_wode  = QPushButton("Mode: WODE")
        self.ind_woa   = QPushButton("Mode: WOA")
        self.ind_de    = QPushButton("Mode: DE")
        self.ind_pno   = QPushButton("Mode: P&O") 
        self.ind_gmpp  = QPushButton("Mode: GMPP")
        self.ind_stop  = QPushButton("Mode: STOP (0%)") 
        
        self.btn_clear = QPushButton("Clear Plot")
        self.btn_clear.setStyleSheet("background-color: #8b0000; color: #ffffff;")

        for ind in [self.ind_wode, self.ind_woa, self.ind_de, self.ind_pno, self.ind_gmpp, self.ind_stop]:
            ind.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            ind.setFixedHeight(35)

        self.btn_clear.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_clear.setFixedHeight(35)
        self.btn_clear.clicked.connect(self.bersihkan_grafik)

        # MENGHUBUNGKAN TOMBOL DENGAN FUNGSI PENGIRIM SERIAL
        self.ind_stop.clicked.connect(lambda: self.kirim_perintah_mode(0))
        self.ind_wode.clicked.connect(lambda: self.kirim_perintah_mode(1))
        self.ind_woa.clicked.connect(lambda:  self.kirim_perintah_mode(2))
        self.ind_de.clicked.connect(lambda:   self.kirim_perintah_mode(3))
        self.ind_pno.clicked.connect(lambda:  self.kirim_perintah_mode(4))
        self.ind_gmpp.clicked.connect(lambda: self.kirim_perintah_mode(5))

        btn_layout.addWidget(self.ind_wode,  0, 0)
        btn_layout.addWidget(self.ind_woa,   0, 1)
        btn_layout.addWidget(self.ind_de,    1, 0)
        btn_layout.addWidget(self.ind_pno,   1, 1) 
        btn_layout.addWidget(self.ind_gmpp,  2, 0)
        btn_layout.addWidget(self.ind_stop,  2, 1)
        btn_layout.addWidget(self.btn_clear, 3, 0, 1, 2) 

        control_layout.addLayout(btn_layout)

        param_layout = QVBoxLayout(); param_layout.setSpacing(5)
        box_style = ("background-color: #000000; color: #ffffff; border-radius: 10px;"
                     "border: 1px solid #555555; font-size: 14px; padding: 5px;")

        lbl_in_title = QLabel("INPUT")
        lbl_in_title.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        lbl_in_title.setStyleSheet("color: #a0a0a0; font-size: 14px; font-weight: bold;")
        param_layout.addWidget(lbl_in_title)

        grid_in = QGridLayout(); grid_in.setSpacing(5)
        grid_in.setColumnStretch(0, 1)
        grid_in.setColumnStretch(1, 1)
        self.lbl_vin       = QLabel("Vin = 0.00 V")
        self.lbl_iin       = QLabel("Iin = 0.00 A")
        self.lbl_pin       = QLabel("Pin = 0.00 W")
        self.lbl_duty_val  = QLabel("Duty = 0.00 %")
        for lbl in [self.lbl_vin, self.lbl_iin, self.lbl_pin, self.lbl_duty_val]:
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
            lbl.setStyleSheet(box_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter) 
            lbl.setFixedHeight(40)
        grid_in.addWidget(self.lbl_vin,      0, 0); grid_in.addWidget(self.lbl_iin,      0, 1)
        grid_in.addWidget(self.lbl_pin,      1, 0); grid_in.addWidget(self.lbl_duty_val, 1, 1)
        param_layout.addLayout(grid_in)

        param_layout.addSpacing(5)
        lbl_out_title = QLabel("OUTPUT")
        lbl_out_title.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        lbl_out_title.setStyleSheet("color: #a0a0a0; font-size: 14px; font-weight: bold;")
        param_layout.addWidget(lbl_out_title)

        grid_out = QGridLayout(); grid_out.setSpacing(5)
        grid_out.setColumnStretch(0, 1)
        grid_out.setColumnStretch(1, 1)
        self.lbl_vout = QLabel("Vout = 0.00 V")
        self.lbl_iout = QLabel("Iout = 0.00 A")
        self.lbl_pout = QLabel("Pout = 0.00 W")
        self.lbl_eff  = QLabel("Eff  = 0.00 %")
        for lbl in [self.lbl_vout, self.lbl_iout, self.lbl_pout, self.lbl_eff]:
            lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
            lbl.setStyleSheet(box_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter) 
            lbl.setFixedHeight(40)
        grid_out.addWidget(self.lbl_vout, 0, 0); grid_out.addWidget(self.lbl_iout, 0, 1)
        grid_out.addWidget(self.lbl_pout, 1, 0); grid_out.addWidget(self.lbl_eff,  1, 1)
        param_layout.addLayout(grid_out)
        control_layout.addLayout(param_layout)

        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        self.lbl_logo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) 
        try:
            pixmap = QPixmap('logo_pens.png')
            if not pixmap.isNull():
                scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_logo.setPixmap(scaled)
                self.lbl_logo.setFixedHeight(scaled.height())
        except Exception:
            pass
        control_layout.addStretch(1)
        control_layout.addWidget(self.lbl_logo)
        main_layout.addWidget(control_widget)

    # --- FUNGSI BARU UNTUK MENGIRIM PERINTAH MODE ---
    def kirim_perintah_mode(self, mode_id):
        if self.serial_port and self.serial_port.is_open:
            perintah = f"MODE={mode_id}\n"
            try:
                self.serial_port.write(perintah.encode('utf-8'))
                print(f"Mengirim perintah ke alat: {perintah.strip()}")
            except Exception as e:
                print(f"Gagal mengirim perintah: {e}")
        else:
            print("Gagal kirim: Port Serial belum terkoneksi!")

    def create_plot(self, title, xlabel, ylabel):
        p = pg.PlotWidget(title=title)
        p.setLabel('bottom', xlabel)
        p.setLabel('left', ylabel)
        p.showGrid(x=True, y=True, alpha=0.3)
        return p

    def bersihkan_grafik(self):
        self.waktu_general.clear(); self.data_general.clear()
        self.waktu_wode.clear();    self.data_wode.clear()
        self.waktu_woa.clear();     self.data_woa.clear()
        self.waktu_de.clear();      self.data_de.clear()
        self.waktu_pno.clear();     self.data_pno.clear() 
        self.waktu_duty.clear();    self.data_duty.clear()

        self.line_all_general.setData([], []); self.line_all_wode.setData([], [])
        self.line_all_woa.setData([], []);     self.line_all_de.setData([], [])
        self.line_all_pno.setData([], []) 
        self.line_wode.setData([], []);  self.line_woa.setData([], [])
        self.line_de.setData([], []);    self.line_pno.setData([], []) 
        self.line_duty.setData([], [])

    def update_btn_color(self, active_btn):
        for btn in [self.ind_wode, self.ind_woa, self.ind_de, self.ind_pno, self.ind_gmpp, self.ind_stop]:
            if btn == active_btn:
                if btn == self.ind_stop:
                    btn.setStyleSheet("background-color: #8b0000; color: white; border-radius: 5px;")
                else:
                    btn.setStyleSheet("background-color: #005500; color: white; border-radius: 5px;")
            else:
                btn.setStyleSheet("background-color: #000000; color: #555555; border-radius: 5px; border: 1px solid #333333;")

    def _update_btn_dari_mode(self, mode):
        map_btn = {
            0: self.ind_stop,  
            1: self.ind_wode,
            2: self.ind_woa,
            3: self.ind_de,
            4: self.ind_pno, 
            5: self.ind_gmpp,
        }
        self.update_btn_color(map_btn.get(mode, None))

    def tambah_data_tanpa_nyambung(self, arr_x, arr_y, t, val):
        if np.isnan(val) or np.isinf(val):
            val = 0.0

        if len(arr_x) > 0:
            if t < arr_x[-1]:       
                arr_x.clear()
                arr_y.clear()
            elif t == arr_x[-1]:
                arr_y[-1] = val
                return
            elif (t - arr_x[-1]) > 2.0: 
                arr_x.append(t - 0.1)
                arr_y.append(np.nan)
                
        arr_x.append(t)
        arr_y.append(val)
        
        if len(arr_x) > self.max_data + 500:
            del arr_x[:-self.max_data]
            del arr_y[:-self.max_data]

    def baca_serial_dan_update(self):
        if not self.serial_port or not self.serial_port.is_open:
            return
        try:
            updated_plots = set()
            last_vin = last_iin = last_pin = 0.0
            last_vout = last_iout = last_pout = 0.0
            last_duty = last_eff = 0.0
            last_mode = self.current_mode

            if self.serial_port.in_waiting > 0:
                self._serial_buffer += self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')

            if '\n' not in self._serial_buffer:
                return

            lines = self._serial_buffer.split('\n')
            self._serial_buffer = lines[-1]

            for raw_line in lines[:-1]:
                line = raw_line.replace('\x00', '').strip()
                if not line:
                    continue

                print(line)

                if self.file_master is not None:
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.file_master.write(f"[{current_time}] {line}\n")
                    self.file_master.flush()

                data = line.split()
                if len(data) < 10:
                    continue

                try:
                    t    = float(data[0])
                    vin  = float(data[1]); iin  = float(data[2]); pin  = float(data[3])
                    vout = float(data[4]); iout = float(data[5]); pout = float(data[6])
                    mode = int(data[8])
                    duty = float(data[9])
                except (ValueError, IndexError):
                    continue

                self.current_mode = mode
                last_mode = mode
                eff = (pout / pin * 100.0) if abs(pin) > 0.1 else 0.0

                last_vin = vin; last_iin = iin; last_pin = pin
                last_vout = vout; last_iout = iout; last_pout = pout
                last_duty = duty; last_eff = eff

                if mode in self.file_modes and self.file_modes[mode] is not None:
                    self.file_modes[mode].write(f"[{current_time}] {line}\n")
                    self.file_modes[mode].flush()

                self.tambah_data_tanpa_nyambung(self.waktu_duty, self.data_duty, t, duty)
                updated_plots.add('duty')

                if mode == 0 or mode == 5:
                    self.tambah_data_tanpa_nyambung(self.waktu_general, self.data_general, t, pin)
                    updated_plots.add('general')
                elif mode == 1:
                    self.tambah_data_tanpa_nyambung(self.waktu_wode, self.data_wode, t, pin)
                    updated_plots.add('wode')
                elif mode == 2:
                    self.tambah_data_tanpa_nyambung(self.waktu_woa, self.data_woa, t, pin)
                    updated_plots.add('woa')
                elif mode == 3:
                    self.tambah_data_tanpa_nyambung(self.waktu_de, self.data_de, t, pin)
                    updated_plots.add('de')
                elif mode == 4:
                    self.tambah_data_tanpa_nyambung(self.waktu_pno, self.data_pno, t, pin)
                    updated_plots.add('pno')

            # Update UI sekali saja setelah semua baris diproses
            if not updated_plots:
                return

            self._update_btn_dari_mode(last_mode)
            self.lbl_vin.setText(f"Vin = {last_vin:.2f} V")
            self.lbl_iin.setText(f"Iin = {last_iin:.2f} A")
            self.lbl_pin.setText(f"Pin = {last_pin:.2f} W")
            self.lbl_duty_val.setText(f"Duty = {last_duty:.1f} %")
            self.lbl_vout.setText(f"Vout = {last_vout:.2f} V")
            self.lbl_iout.setText(f"Iout = {last_iout:.2f} A")
            self.lbl_pout.setText(f"Pout = {last_pout:.2f} W")
            self.lbl_eff.setText(f"Eff = {last_eff:.1f} %")

            if 'duty' in updated_plots:
                self.line_duty.setData(self.waktu_duty, self.data_duty)
            if 'general' in updated_plots:
                self.line_all_general.setData(self.waktu_general, self.data_general)
            if 'wode' in updated_plots:
                self.line_wode.setData(self.waktu_wode, self.data_wode)
                self.line_all_wode.setData(self.waktu_wode, self.data_wode)
            if 'woa' in updated_plots:
                self.line_woa.setData(self.waktu_woa, self.data_woa)
                self.line_all_woa.setData(self.waktu_woa, self.data_woa)
            if 'de' in updated_plots:
                self.line_de.setData(self.waktu_de, self.data_de)
                self.line_all_de.setData(self.waktu_de, self.data_de)
            if 'pno' in updated_plots:
                self.line_pno.setData(self.waktu_pno, self.data_pno)
                self.line_all_pno.setData(self.waktu_pno, self.data_pno)

        except Exception as e:
            print(f"Serial error: {e}")

    def closeEvent(self, event):
        if self.file_master:
            self.file_master.close()
            
        for mode, f in self.file_modes.items():
            if f is not None:
                f.close()
                
        print("Aplikasi ditutup. Semua file log berhasil diamankan ke dalam hardisk.")
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DashboardTA()
    window.show()
    sys.exit(app.exec())