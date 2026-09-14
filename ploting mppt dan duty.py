import os
import pandas as pd
import matplotlib.pyplot as plt

def plot_mppt_data_custom_time():
    # ==========================================
    # 1. PARAMETER PENGATURAN PLOT
    # ==========================================
    # Ganti dengan nama file txt hasil log kamu (misal: 'data_mppt_WODE.txt')
    nama_file = os.path.join(os.path.dirname(__file__), 'pola_shading4.txt')
    
    max_duration = 30          # Durasi sumbu X yang ingin ditampilkan (detik)
    threshold_power = 1.0      # Batas daya untuk deteksi algoritma "Mulai jalan"
    target_gmpp_power = 144 # Daya puncak target dari kurva P-V
    avg_window = 5             # Window waktu untuk rata-rata steady state (5 detik terakhir)

    try:
        print(f"Membaca data dari '{nama_file}'...")
        # Membaca file txt (10 Kolom) dengan pemisah spasi/tab
        kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
        df = pd.read_csv(nama_file, sep='\s+', header=None, names=kolom)
        
        # Pembersihan otomatis: ubah ke angka, buang baris yang nyangkut huruf/error
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        
    except FileNotFoundError:
        print(f"[ERROR] File '{nama_file}' tidak ditemukan. Pastikan ada di folder yang sama.")
        return

    if df.empty:
        print("[ERROR] Data kosong setelah dibaca. Cek kembali isi file txt kamu!")
        return

    # ==========================================
    # 2. MENCARI TITIK MULAI (START TIME)
    # ==========================================
    # Cari baris pertama di mana daya (Pin) lebih besar dari threshold (1.0 W)
    df_start = df[df['Pin'] > threshold_power]
    
    if df_start.empty:
        print(f"Peringatan: Tidak ada daya yang melebihi {threshold_power} W di file ini.")
        return
        
    start_time = df_start.iloc[0]['Waktu']
    
    # Filter data: Ambil data dari titik mulai, lalu jadikan waktunya mulai dari 0
    df_filtered = df[df['Waktu'] >= start_time].copy()
    df_filtered['Waktu'] = df_filtered['Waktu'] - start_time

    # Potong data sesuai max_duration (contoh: 44 detik)
    df_final = df_filtered[df_filtered['Waktu'] <= max_duration]

    if df_final.empty:
        print("Data kosong setelah dipotong durasi.")
        return

    # ==========================================
    # 3. PERHITUNGAN RATA-RATA STEADY STATE
    # ==========================================
    # Cari waktu paling akhir dari data yang sudah dipotong
    t_end = df_final['Waktu'].max()
    
    # Ambil data dari (t_end - 5 detik) sampai t_end
    df_last_5s = df_final[df_final['Waktu'] >= (t_end - avg_window)]
    
    # Hitung rata-rata Daya (Pin) pada 5 detik terakhir
    daya_mppt_avg = df_last_5s['Pin'].mean()
    
    # Tambahan fitur untuk Skripsi: Hitung Efisiensi Tracking
    efisiensi_tracking = (daya_mppt_avg / target_gmpp_power) * 100
    
    print(f"-> Sistem terdeteksi mulai pada waktu asli: {start_time:.2f} s")
    print(f"-> Rata-rata daya {avg_window} detik terakhir: {daya_mppt_avg:.2f} W")
    print(f"-> Tracking Efficiency: {efisiensi_tracking:.2f} %")

    # ==========================================
    # 4. PROSES PLOTTING GRAFIK
    # ==========================================
    # Buat 2 baris grafik atas bawah
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9))

    # --- Plot 1: Duty Cycle vs Waktu ---
    ax1.plot(df_final['Waktu'], df_final['Duty'], color='blue', linewidth=2, label='Duty Cycle (%)')
    ax1.set_title('Grafik Pergerakan Duty Cycle Algoritma MPPT', fontweight='bold')
    ax1.set_xlabel('Waktu Sejak Mulai (s)')
    ax1.set_ylabel('Duty Cycle (%)')
    ax1.set_xlim(0, max_duration) 
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(loc='lower right')

    # --- Plot 2: Daya (Pin) vs Waktu ---
    ax2.plot(df_final['Waktu'], df_final['Pin'], color='red', alpha=0.8, linewidth=2, label='Daya Aktual Panel (Pin)')
    
    # Garis Lurus: Target GMPP (Hijau)
    ax2.axhline(y=target_gmpp_power, color='green', linestyle='-.', linewidth=2, 
                label=f'Target GMPP Teoritis ({target_gmpp_power} W)')
    
    # Garis Lurus: Rata-rata MPPT Steady State (Oranye)
    ax2.axhline(y=daya_mppt_avg, color='orange', linestyle='--', linewidth=2, 
                label=f'Daya Rata-Rata Steady ({daya_mppt_avg:.2f} W)')

    # Kotak Arsiran (Shading) untuk area 5 detik terakhir
    ax2.axvspan(t_end - avg_window, t_end, color='yellow', alpha=0.2, label=f'Area Steady State ({avg_window}s)')

    ax2.set_title(f'Grafik Tracking Daya (Efisiensi Tracking = {efisiensi_tracking:.2f} %)', fontweight='bold')
    ax2.set_xlabel('Waktu Sejak Mulai (s)')
    ax2.set_ylabel('Daya Input (Watt)')
    
    # Pengaturan Limit agar grafik proporsional
    ax2.set_xlim(0, max_duration)
    ax2.set_ylim(0, max(target_gmpp_power, df_final['Pin'].max()) + 15)
    
    ax2.grid(True, linestyle='--', alpha=0.7)
    ax2.legend(loc='lower right', fontsize='small')

    # Rapikan jarak antar grafik dan tampilkan
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    plot_mppt_data_custom_time()