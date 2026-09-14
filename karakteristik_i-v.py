import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Nama file text kamu (menggunakan sumber data yang sama)
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

        # --- MULAI PLOTTING (KARAKTERISTIK I-V) ---
        plt.figure(figsize=(10, 6))

        # Plot Kurva I-V (Ubah Pin menjadi Iin pada sumbu Y)
        # Gunakan warna yang berbeda (misal: hijau) untuk membedakan dari kurva P-V
        plt.plot(df_gmpp['Vin'], df_gmpp['Iin'], color='green', linewidth=2.5, label='Karakteristik I-V (Eksperimen)')

        # 5. Mencari dan Menandai Titik Maximum Power Point (MPP)
        # Pencarian MPP TETAP berdasarkan Daya Maksimum (Pin)
        idx_mpp = df_gmpp['Pin'].idxmax()
        v_mpp = df_gmpp.loc[idx_mpp, 'Vin']
        p_mpp = df_gmpp.loc[idx_mpp, 'Pin'] # Daya MPP (untuk anotasi)
        i_mpp = df_gmpp.loc[idx_mpp, 'Iin'] # Arus pada MPP (untuk plot sumbu Y)

        # Beri bulatan merah di titik MPP pada kurva I-V
        plt.scatter(v_mpp, i_mpp, color='red', s=100, zorder=5, label='Titik Puncak (MPP)')

        # Beri teks koordinat MPP (Tampilkan Arus dan Tegangan)
        mpp_text = f'MPP Maksimal:\nImpp = {i_mpp:.2f} A pada Vmpp = {v_mpp:.2f} V\n(Daya: {p_mpp:.2f} W)'
        plt.annotate(mpp_text,
                     xy=(v_mpp, i_mpp),
                     # Atur posisi teks dinamis agar berada di atas kurva
                     xytext=(v_mpp - 5, i_mpp + (i_mpp * 0.15)), 
                     arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
                     fontsize=11, fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))

        # 6. Pengaturan Tampilan Grafik ala Jurnal
        plt.title('Kurva Karakteristik Arus-Tegangan (I-V)', fontsize=16, fontweight='bold', pad=15)
        plt.xlabel('Tegangan Input Panel - Vin (Volt)', fontsize=12, fontweight='bold')
        plt.ylabel('Arus Input Panel - Iin (Ampere)', fontsize=12, fontweight='bold')
        
        # Grid dan Limit (Sesuaikan margin sumbu Y untuk Arus)
        plt.grid(True, which='both', linestyle='--', alpha=0.6)
        plt.xlim(0, df_gmpp['Vin'].max() + 2)
        plt.ylim(0, df_gmpp['Iin'].max() + (df_gmpp['Iin'].max() * 0.25)) # Margin atas 25% untuk anotasi
        
        plt.legend(loc='lower left', fontsize=11)
        plt.tight_layout()

        # Tampilkan grafik ke layar
        print("Berhasil memplot grafik Karakteristik I-V!")
        plt.show()

except FileNotFoundError:
    print(f"[ERROR] File '{nama_file}' tidak ditemukan!")
    print("Pastikan file tersebut berada di folder yang sama dengan script ini.")
except Exception as e:
    print(f"[ERROR] Terjadi kesalahan: {e}")