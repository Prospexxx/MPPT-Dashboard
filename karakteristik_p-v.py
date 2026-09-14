import pandas as pd
import matplotlib.pyplot as plt

# Nama file text kamu
nama_file = 'karakteristik_shading4.txt'

try:
    print(f"Membaca data dari {nama_file}...")
    
    # 1. Membaca data dengan pandas
    # Menentukan nama kolom sesuai urutan data dari STM32 (10 kolom)
    kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
    
    # PERBAIKAN: Menambahkan r sebelum '\s+' untuk menghilangkan SyntaxWarning
    df = pd.read_csv(nama_file, sep=r'\s+', header=None, names=kolom)

    # 2. Pembersihan Data
    # Ubah semua data menjadi angka. Jika ada teks nyasar, akan diubah jadi NaN
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna() # Hapus baris yang mengandung NaN (kosong/error)

    if df.empty:
        print("Data kosong setelah dibersihkan. Cek isi file txt kamu!")
    else:
        # 3. Filter Khusus Mode GMPP (Mode 5)
        df_gmpp = df[df['Mode'] == 5]
        
        if df_gmpp.empty:
            print("Peringatan: Tidak ada data Mode 5 (GMPP). Memplot semua data...")
            df_gmpp = df # Fallback: Plot semua data yang ada

        # 4. Mengurutkan Data berdasarkan Vin agar kurva tidak berantakan
        df_gmpp = df_gmpp.sort_values(by='Vin')

        # --- MULAI PLOTTING ---
        plt.figure(figsize=(10, 6))

        # Plot Kurva P-V
        plt.plot(df_gmpp['Vin'], df_gmpp['Pin'], color='blue', linewidth=2.5, label='Karakteristik P-V (Eksperimen)')

        # 5. Mencari dan Menandai Titik Maximum Power Point (MPP)
        idx_mpp = df_gmpp['Pin'].idxmax()
        v_mpp = df_gmpp.loc[idx_mpp, 'Vin']
        p_mpp = df_gmpp.loc[idx_mpp, 'Pin']

        # Beri bulatan merah di titik tertinggi
        plt.scatter(v_mpp, p_mpp, color='red', s=100, zorder=5, label='Titik Puncak (MPP)')

        # Beri teks koordinat di dekat titik tertinggi
        plt.annotate(f'MPP Maksimal:\n{p_mpp:.2f} W pada {v_mpp:.2f} V',
                     xy=(v_mpp, p_mpp),
                     xytext=(v_mpp - 3, p_mpp + (p_mpp * 0.1)), # Posisi teks dinamis
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
                     fontsize=11, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

        # 6. Pengaturan Tampilan Grafik ala Jurnal
        plt.title('Kurva Karakteristik Daya-Tegangan (P-V)', fontsize=16, fontweight='bold', pad=15)
        plt.xlabel('Tegangan Input Panel - Vin (Volt)', fontsize=12, fontweight='bold')
        plt.ylabel('Daya Input Panel - Pin (Watt)', fontsize=12, fontweight='bold')
        
        # Grid dan Limit
        plt.grid(True, which='both', linestyle='--', alpha=0.6)
        plt.xlim(0, df_gmpp['Vin'].max() + 2)
        plt.ylim(0, df_gmpp['Pin'].max() + (df_gmpp['Pin'].max() * 0.2)) # Margin atas 20%
        
        plt.legend(loc='lower left', fontsize=11)
        plt.tight_layout()

        # Tampilkan grafik ke layar
        print("Berhasil memplot grafik!")
        plt.show()

except FileNotFoundError:
    print(f"[ERROR] File '{nama_file}' tidak ditemukan!")
    print("Pastikan file tersebut berada di folder yang sama dengan script ini.")
except Exception as e:
    print(f"[ERROR] Terjadi kesalahan: {e}")