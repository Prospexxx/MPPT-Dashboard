import matplotlib
matplotlib.use('Agg')
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager

def plot_mppt_data_custom_time():
    # ==========================================
    # 1. PARAMETER PENGATURAN PLOT
    # ==========================================
    # Ganti dengan nama file txt hasil log kamu (misal: 'data_mppt_WODE.txt')
    nama_file = os.path.join(os.path.dirname(__file__), 'wode3.txt')
    
    max_duration = 10          # Durasi sumbu X yang ingin ditampilkan (detik)
    threshold_power = 1.0      # Batas daya untuk deteksi algoritma "Mulai jalan"
    target_gmpp_power = 44.32    # Daya puncak target dari kurva P-V
    avg_window = 2             # Window waktu untuk rata-rata steady state (2 detik terakhir)

    try:
        print(f"Membaca data dari '{nama_file}'...")
        # Membaca file txt (10 Kolom) dengan pemisah spasi/tab
        kolom = ['Waktu', 'Vin', 'Iin', 'Pin', 'Vout', 'Iout', 'Pout', 'Eff', 'Mode', 'Duty']
        df = pd.read_csv(nama_file, sep=r'\s+', header=None, names=kolom)
        
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
    df_start_mask = df['Pin'] > threshold_power
    
    if not df_start_mask.any():
        print(f"Peringatan: Tidak ada daya yang melebihi {threshold_power} W di file ini.")
        return
        
    first_high_idx = df_start_mask.idxmax()
    
    # Ambil 1 baris sebelum threshold terlampaui agar grafik mulai dari 0W
    start_idx = max(0, first_high_idx - 1)
    start_time = df.loc[start_idx, 'Waktu']
    
    # Filter data: Ambil data dari titik mulai, lalu jadikan waktunya mulai dari 0
    df_filtered = df.loc[start_idx:].copy()
    df_filtered['Waktu'] = df_filtered['Waktu'] - start_time

    # Potong data sesuai max_duration
    df_final = df_filtered[df_filtered['Waktu'] <= max_duration]

    if df_final.empty:
        print("Data kosong setelah dipotong durasi.")
        return

    # ==========================================
    # 3. PERHITUNGAN RATA-RATA STEADY STATE
    # ==========================================
    t_end = df_final['Waktu'].max()
    df_last_5s = df_final[df_final['Waktu'] >= (t_end - avg_window)]
    daya_mppt_avg = df_last_5s['Pin'].mean()
    efisiensi_tracking = (daya_mppt_avg / target_gmpp_power) * 100
    
    print(f"-> Sistem terdeteksi mulai pada waktu asli: {start_time:.2f} s")
    print(f"-> Rata-rata daya {avg_window} detik terakhir: {daya_mppt_avg:.2f} W")
    print(f"-> Tracking Efficiency: {efisiensi_tracking:.2f} %")

    # ==========================================
    # 4. PLOTTING — Publication Quality (Scopus/IEEE)
    # ==========================================

    # --- Reset and apply global rcParams ---
    plt.rcdefaults()
    plt.rcParams.update({
        # Typography
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'Times', 'DejaVu Serif'],
        'mathtext.fontset': 'stix',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'axes.labelweight': 'bold',
        # Axes frame
        'axes.linewidth': 0.8,
        'axes.edgecolor': '#333333',
        'axes.facecolor': 'white',
        # Ticks — inward, all four sides
        'xtick.labelsize': 9.5,
        'ytick.labelsize': 9.5,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True,
        'xtick.major.size': 4,
        'ytick.major.size': 4,
        'xtick.minor.size': 2,
        'ytick.minor.size': 2,
        'xtick.major.width': 0.8,
        'ytick.major.width': 0.8,
        'xtick.minor.width': 0.5,
        'ytick.minor.width': 0.5,
        'xtick.minor.visible': True,
        'ytick.minor.visible': True,
        # Legend
        'legend.fontsize': 8.5,
        'legend.framealpha': 1.0,
        'legend.edgecolor': '#555555',
        'legend.fancybox': False,
        'legend.handlelength': 2.0,
        'legend.handletextpad': 0.5,
        'legend.borderpad': 0.4,
        'legend.labelspacing': 0.35,
        # Figure
        'figure.facecolor': 'white',
        'figure.dpi': 150,
        'savefig.dpi': 600,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.02,
    })

    # --- Create figure ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(5.5, 6.0),
                                     gridspec_kw={'hspace': 0.32})
    fig.suptitle(f'MPPT Tracking Response',
                 fontsize=12, fontweight='bold', y=0.96)

    # --- Detect convergence point (True Settling Time) ---
    tolerance = 0.10  # 10% tolerance band around final steady state
    
    # Kita cari kapan daya mulai stabil di angka "daya_mppt_avg" (tidak keluar lagi dari batas toleransi).
    # Cari titik terakhir dari belakang di mana daya BERADA DI LUAR batas steady state:
    outside_mask = (df_final['Pin'] < daya_mppt_avg * (1 - tolerance)) | \
                   (df_final['Pin'] > daya_mppt_avg * (1 + tolerance))
                   
    if outside_mask.any():
        last_outside_time = df_final[outside_mask].iloc[-1]['Waktu']
        # tc adalah titik data PERTAMA setelah ia keluar dari jalur untuk terakhir kalinya
        settle_mask = df_final['Waktu'] > last_outside_time
        if settle_mask.any():
            t_converge = df_final[settle_mask].iloc[0]['Waktu']
        else:
            t_converge = t_end - avg_window
    else:
        # Jika dari awal tidak pernah keluar jalur (jarang terjadi)
        t_converge = df_final.iloc[0]['Waktu']

    # ========== PLOT (a): Duty Cycle ==========
    # Transient region shading
    ax1.axvspan(-0.5, t_converge, color='#fce4e4', alpha=0.6,
                label='Search Phase', zorder=0)
    ax1.axvspan(t_converge, max_duration, color='#e4f2e4', alpha=0.5,
                label='Steady State', zorder=0)

    # Step plot — shows each discrete MPPT adjustment clearly
    ax1.step(df_final['Waktu'], df_final['Duty'],
             where='post', color='#0060ad', linewidth=1.0, zorder=3)
    # Markers at each sample point
    ax1.plot(df_final['Waktu'], df_final['Duty'],
             linestyle='none', marker='o', markersize=3,
             markerfacecolor='#0060ad', markeredgecolor='white',
             markeredgewidth=0.3, zorder=4, label='Duty')

    # Convergence vertical line
    ax1.axvline(x=t_converge, color='#555555', linestyle=':',
                linewidth=0.8, zorder=2)

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Duty Cycle (%)')
    ax1.set_xlim(-0.5, max_duration)
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax1.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))

    # Grid
    ax1.grid(True, which='major', linestyle='-', linewidth=0.25, color='#cccccc', zorder=0)

    # Convergence time annotation — adaptive middle placement
    duty_ymax = df_final['Duty'].max()
    t_mid1 = max_duration * 0.35
    if t_converge > 0 and t_converge < max_duration * 0.8:
        t_mid1 = t_converge / 2
        
    df_before_mid1 = df_final[df_final['Waktu'] <= t_mid1]
    duty_at_mid = df_before_mid1['Duty'].iloc[-1] if not df_before_mid1.empty else 0
    
    y_text1 = duty_ymax * 0.75 if duty_at_mid < duty_ymax * 0.5 else duty_ymax * 0.25

    # Target point: the actual duty cycle value at the convergence time
    df_at_converge = df_final[df_final['Waktu'] >= t_converge]
    duty_at_converge = df_at_converge['Duty'].iloc[0] if not df_at_converge.empty else df_final['Duty'].iloc[-1]

    ax1.annotate(f'Convergence\n$t_c$ = {t_converge:.1f} s',
                 xy=(t_converge, duty_at_converge),
                 xytext=(t_mid1, y_text1),
                 fontsize=9.5, color='#333333', fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                           edgecolor='#888888', linewidth=0.6, alpha=0.95),
                 arrowprops=dict(arrowstyle='->', color='#666666', lw=1.0,
                                 relpos=(1.0, 0.5),
                                 connectionstyle='arc3,rad=-0.25'),
                 zorder=5)

    # Legend
    leg1 = ax1.legend(loc='upper right', frameon=True, facecolor='white',
                       edgecolor='#999999', borderaxespad=0.5, ncol=1, fontsize=8)
    leg1.get_frame().set_linewidth(0.6)

    # Subplot label
    ax1.text(-0.12, 1.02, '(a)', transform=ax1.transAxes, fontsize=12,
             fontweight='bold', va='bottom', ha='left')

    # ========== PLOT (b): Power Tracking ==========
    # Transient shading only
    ax2.axvspan(-0.5, t_converge, color='#fce4e4', alpha=0.6,
                label='Search Phase', zorder=0)

    # GMPP reference line
    ax2.axhline(y=target_gmpp_power, color='#228B22', linestyle='--',
                linewidth=1.0, dashes=(6, 3),
                label=f'Target = {target_gmpp_power} W', zorder=2)

    # Avg steady-state line (labeled with last N seconds info)
    ax2.axhline(y=daya_mppt_avg, color='#D2691E', linestyle='--',
                linewidth=1.0, dashes=(4, 2, 1, 2),
                label=f'Avg = {daya_mppt_avg:.2f} W', zorder=2)

    # Step plot for power — shows each discrete tracking step
    ax2.step(df_final['Waktu'], df_final['Pin'],
             where='post', color='#c03030', linewidth=1.0, zorder=3)
    # Markers
    ax2.plot(df_final['Waktu'], df_final['Pin'],
             linestyle='none', marker='o', markersize=3,
             markerfacecolor='#c03030', markeredgecolor='white',
             markeredgewidth=0.3, zorder=4,
             label=r'$P_{\mathrm{in}}$')

    # Convergence vertical line
    ax2.axvline(x=t_converge, color='#555555', linestyle=':',
                linewidth=0.8, zorder=2)

    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Input Power (W)')
    ax2.set_xlim(-0.5, max_duration)
    ax2.set_ylim(0, max(target_gmpp_power, df_final['Pin'].max()) * 1.12)
    ax2.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax2.xaxis.set_minor_locator(ticker.MultipleLocator(0.5))

    # Grid
    ax2.grid(True, which='major', linestyle='-', linewidth=0.25, color='#cccccc', zorder=0)

    # Legend
    leg2 = ax2.legend(loc='lower right', frameon=True, facecolor='white',
                       edgecolor='#999999', borderaxespad=0.5, fontsize=8)
    leg2.get_frame().set_linewidth(0.6)

    # Subplot label
    ax2.text(-0.12, 1.02, '(b)', transform=ax2.transAxes, fontsize=12,
             fontweight='bold', va='bottom', ha='left')

    # Tracking efficiency annotation — adaptive middle placement
    t_mid2 = max_duration * 0.4
    df_before_mid2 = df_final[df_final['Waktu'] <= t_mid2]
    pin_at_mid = df_before_mid2['Pin'].iloc[-1] if not df_before_mid2.empty else 0
    
    pin_max = max(target_gmpp_power, df_final['Pin'].max())
    y_text2 = pin_max * 0.75 if pin_at_mid < pin_max * 0.5 else pin_max * 0.25
    
    if abs(y_text2 - daya_mppt_avg) < pin_max * 0.15:
        y_text2 = pin_max * 0.2 if daya_mppt_avg > pin_max * 0.5 else pin_max * 0.8

    textstr = r'$\eta_{\mathrm{track}}$' + f' = {efisiensi_tracking:.2f}%'
    ax2.annotate(textstr, xy=(t_mid2, daya_mppt_avg),
                 xytext=(t_mid2, y_text2),
                 fontsize=9.5, fontweight='bold', ha='center', va='center',
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffde8',
                           edgecolor='#999999', linewidth=0.6),
                 arrowprops=dict(arrowstyle='->', color='#666666',
                                 lw=0.8, connectionstyle='arc3,rad=0'),
                 zorder=5)

    # Align the Y-axis labels symmetrically
    fig.align_ylabels([ax1, ax2])

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('c:/Users/PC/Documents/Tugas Akhir/program ta/Dashboard MPPT/Data_Logger/mppt_test_left.png', dpi=150)

if __name__ == '__main__':
    plot_mppt_data_custom_time()