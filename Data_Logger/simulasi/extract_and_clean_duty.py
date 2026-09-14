import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def process_duty():
    sim_dir = r"c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\simulasi"
    img_path = os.path.join(sim_dir, "duty.png")

    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Image not found at {img_path}")

    print(f"Loading image from: {img_path}")
    img = Image.open(img_path)
    arr = np.array(img.convert("RGB"))

    # Plot pixel bounds and calibration
    # X: Col 44 -> 0.0 s, Col 950 -> 10.0 s (90.6 px / s)
    # Y: Row 519 -> 0.0, Row 18 -> 0.5 (501 px / 0.5 D -> 1002.0 px / 1.0 D)
    c_left, c_right = 44.0, 950.0

    def col_to_t(c):
        return (c - 44.0) / 90.6

    def row_to_d(r):
        return (519.0 - r) / 1002.0

    # Blue curve mask
    is_blue = (arr[:, :, 2] > 140) & (arr[:, :, 0] < 70) & (arr[:, :, 1] < 70)
    # Exclude legend box in top right
    is_blue[18:60, 800:945] = False

    time_pts = []
    duty_raw_pts = []
    prev_val = 0.35
    dt_px = 1.0 / 90.6

    for c in range(int(c_left), int(c_right) + 1):
        t = col_to_t(c)
        rows = np.where(is_blue[18:520, c])[0] + 18
        if len(rows) == 0:
            continue

        d_min = row_to_d(np.max(rows))
        d_max = row_to_d(np.min(rows))
        d_mid = (d_min + d_max) / 2.0
        d_min = max(0.0, min(0.5, d_min))
        d_max = max(0.0, min(0.5, d_max))
        d_mid = max(0.0, min(0.5, d_mid))

        span = np.max(rows) - np.min(rows)

        if span <= 6:
            time_pts.append(t)
            duty_raw_pts.append(d_mid)
            prev_val = d_mid
        else:
            if abs(prev_val - d_min) < abs(prev_val - d_max):
                time_pts.append(t)
                duty_raw_pts.append(d_min)
                time_pts.append(t + dt_px * 0.49)
                duty_raw_pts.append(d_max)
                prev_val = d_max
            else:
                time_pts.append(t)
                duty_raw_pts.append(d_max)
                time_pts.append(t + dt_px * 0.49)
                duty_raw_pts.append(d_min)
                prev_val = d_min

    t_arr = np.array(time_pts)
    d_raw_arr = np.array(duty_raw_pts)

    # ========================================================
    # CLEANING: Remove 2nd peak on 3rd pattern (t ≈ 4.35 - 4.75 s)
    # Steady state value for pattern 3 is ~0.1492
    # ========================================================
    d_clean_arr = d_raw_arr.copy()

    for i, t in enumerate(t_arr):
        if 4.34 <= t <= 4.75:
            d_clean_arr[i] = 0.1492

    print(f"Total duty data points extracted: {len(t_arr)}")

    # ========================================================
    # 1. WRITE TXT DATA FILES
    # ========================================================
    clean_txt_path = os.path.join(sim_dir, "data_duty.txt")
    with open(clean_txt_path, "w") as f:
        f.write("# Time(s)\tDuty_Cycle(D)\n")
        for t, d in zip(t_arr, d_clean_arr):
            f.write(f"{t:.4f}\t{d:.4f}\n")
    print(f"Saved: {clean_txt_path}")

    raw_txt_path = os.path.join(sim_dir, "data_duty_raw.txt")
    with open(raw_txt_path, "w") as f:
        f.write("# Time(s)\tDuty_Cycle_Raw(D)\n")
        for t, d in zip(t_arr, d_raw_arr):
            f.write(f"{t:.4f}\t{d:.4f}\n")
    print(f"Saved: {raw_txt_path}")

    # ========================================================
    # 2. GENERATE SCIENTIFIC COLOR PLOT (duty_clean.png)
    # ========================================================
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['mathtext.fontset'] = 'cm'

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)

    ax.plot(t_arr, d_clean_arr, color='blue', linestyle='-', linewidth=1.8, label='WODE Duty Cycle')

    ax.set_xlabel(r'Time, $t$ (s)', fontsize=12, fontweight='bold')
    ax.set_ylabel(r'Duty Cycle, $D$', fontsize=12, fontweight='bold')

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 0.52)
    ax.set_xticks(np.arange(0, 11, 1))
    ax.set_yticks(np.arange(0, 0.55, 0.05))

    ax.grid(True, linestyle='-', alpha=0.5, color='gray')
    ax.tick_params(direction='in', length=6, width=1.2, labelsize=11, top=True, right=True)

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')

    ax.legend(loc='upper right', framealpha=1.0, edgecolor='black', prop={'family': 'serif', 'size': 11})

    plt.tight_layout()
    clean_img_path = os.path.join(sim_dir, "duty_clean.png")
    plt.savefig(clean_img_path, dpi=200)
    plt.close()
    print(f"Saved cleaned duty plot: {clean_img_path}")

    # ========================================================
    # 3. GENERATE SCIENTIFIC BLACK PLOT (duty_black.png)
    # ========================================================
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)

    ax.plot(t_arr, d_clean_arr, color='black', linestyle='-', linewidth=1.8, label='WODE Duty Cycle')

    ax.set_xlabel(r'Time, $t$ (s)', fontsize=12, fontweight='bold')
    ax.set_ylabel(r'Duty Cycle, $D$', fontsize=12, fontweight='bold')

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 0.52)
    ax.set_xticks(np.arange(0, 11, 1))
    ax.set_yticks(np.arange(0, 0.55, 0.05))

    ax.grid(True, linestyle='-', alpha=0.5, color='gray')
    ax.tick_params(direction='in', length=6, width=1.2, labelsize=11, top=True, right=True)

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')

    ax.legend(loc='upper right', framealpha=1.0, edgecolor='black', prop={'family': 'serif', 'size': 11})

    plt.tight_layout()
    black_img_path = os.path.join(sim_dir, "duty_black.png")
    plt.savefig(black_img_path, dpi=200)
    plt.close()
    print(f"Saved black duty plot: {black_img_path}")

    # ========================================================
    # 4. GENERATE COMPARISON PLOT (duty_comparison.png)
    # ========================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=200, sharex=True)

    ax1.plot(t_arr, d_raw_arr, color='blue', linestyle='-', linewidth=1.5, label='Original (With 2nd Peak)')
    ax1.set_title('Original Duty Cycle (Extracted from duty.png)', fontsize=11, fontweight='bold')
    ax1.set_ylabel(r'$D$', fontsize=11, fontweight='bold')
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 0.52)
    ax1.set_yticks(np.arange(0, 0.55, 0.1))
    ax1.grid(True, linestyle='-', alpha=0.5)
    ax1.legend(loc='upper right', framealpha=1.0, edgecolor='black')

    ax1.axvspan(4.34, 4.75, color='orange', alpha=0.25, label='Peak Kedua')
    ax1.text(4.55, 0.40, 'Peak ke-2\n(Dihapus)', color='darkred', ha='center', fontsize=9, fontweight='bold')

    ax2.plot(t_arr, d_clean_arr, color='black', linestyle='-', linewidth=1.5, label='Cleaned (2nd Peak Removed)')
    ax2.set_title('Cleaned Duty Cycle (2nd Peak Removed on Pattern 3)', fontsize=11, fontweight='bold')
    ax2.set_xlabel(r'Time, $t$ (s)', fontsize=11, fontweight='bold')
    ax2.set_ylabel(r'$D$', fontsize=11, fontweight='bold')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 0.52)
    ax2.set_yticks(np.arange(0, 0.55, 0.1))
    ax2.grid(True, linestyle='-', alpha=0.5)
    ax2.legend(loc='upper right', framealpha=1.0, edgecolor='black')

    plt.tight_layout()
    comp_img_path = os.path.join(sim_dir, "duty_comparison.png")
    plt.savefig(comp_img_path, dpi=200)
    plt.close()
    print(f"Saved comparison plot: {comp_img_path}")

if __name__ == "__main__":
    process_duty()
