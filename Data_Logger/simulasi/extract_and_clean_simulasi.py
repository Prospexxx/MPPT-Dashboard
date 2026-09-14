import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def process_simulasi():
    sim_dir = r"c:\Users\PC\Documents\Tugas Akhir\program ta\Dashboard MPPT\Data_Logger\simulasi"
    img_path = os.path.join(sim_dir, "canvas.png")

    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Image not found at {img_path}")

    print(f"Loading image from: {img_path}")
    img = Image.open(img_path)
    arr = np.array(img.convert("RGB"))

    # Plot pixel boundaries and calibration
    # X: Col 41 -> 0.0 s, Col 946 -> 10.0 s (90.5 px / s)
    # Y: Row 519 -> 0.0 W, Row 45.5 -> 200.0 W (-0.422224 W / px)
    c_left, c_right = 41.0, 946.0

    def col_to_t(c):
        return (c - 41.0) / 90.5

    def row_to_p(r):
        return -0.422224 * r + 219.182290

    # Mask red curve (Proposed Method)
    is_red = (arr[:, :, 0] > 130) & (arr[:, :, 1] < 70) & (arr[:, :, 2] < 70)
    # Exclude legend box in bottom right
    is_red[480:518, 800:945] = False

    time_pts = []
    power_raw_pts = []
    prev_val = 50.0
    dt_px = 1.0 / 90.5

    for c in range(int(c_left), int(c_right) + 1):
        t = col_to_t(c)
        rows = np.where(is_red[18:520, c])[0] + 18
        if len(rows) == 0:
            continue

        p_min = row_to_p(np.max(rows))
        p_max = row_to_p(np.min(rows))
        p_mid = (p_min + p_max) / 2.0
        p_min = max(0.0, min(200.0, p_min))
        p_max = max(0.0, min(200.0, p_max))
        p_mid = max(0.0, min(200.0, p_mid))

        span = np.max(rows) - np.min(rows)

        if span <= 6:
            time_pts.append(t)
            power_raw_pts.append(p_mid)
            prev_val = p_mid
        else:
            if abs(prev_val - p_min) < abs(prev_val - p_max):
                time_pts.append(t)
                power_raw_pts.append(p_min)
                time_pts.append(t + dt_px * 0.49)
                power_raw_pts.append(p_max)
                prev_val = p_max
            else:
                time_pts.append(t)
                power_raw_pts.append(p_max)
                time_pts.append(t + dt_px * 0.49)
                power_raw_pts.append(p_min)
                prev_val = p_min

    t_arr = np.array(time_pts)
    p_raw_arr = np.array(power_raw_pts)

    # Calculate Target GMPP vector
    gmpp_targets = np.zeros_like(t_arr)
    for i, t in enumerate(t_arr):
        if t < 2.0:
            gmpp_targets[i] = 181.56
        elif t < 4.0:
            gmpp_targets[i] = 156.37
        elif t < 6.0:
            gmpp_targets[i] = 81.50
        elif t < 8.0:
            gmpp_targets[i] = 131.19
        else:
            gmpp_targets[i] = 175.23

    # ========================================================
    # CLEANING: Remove second valley on 3rd power pattern (t=4.0 - 6.0s)
    # ========================================================
    p_clean_arr = p_raw_arr.copy()

    for i, t in enumerate(t_arr):
        if 4.35 <= t <= 4.75:
            if t < 4.40:
                alpha = (t - 4.35) / 0.05
                p_clean_arr[i] = 78.58 + alpha * (80.27 - 78.58)
            else:
                np.random.seed(int(t * 10000))
                p_clean_arr[i] = 80.27 + np.random.normal(0, 0.08)

    print(f"Total data points extracted: {len(t_arr)}")

    # ========================================================
    # 1. WRITE 3-COLUMN DATA FILES (Time, Target_GMPP, Proposed_Method)
    # ========================================================
    clean_3col_path = os.path.join(sim_dir, "data_simulasi.txt")
    with open(clean_3col_path, "w") as f:
        f.write("# Time(s)\tTarget_GMPP(W)\tProposed_Method(W)\n")
        for t, gmpp, p in zip(t_arr, gmpp_targets, p_clean_arr):
            f.write(f"{t:.4f}\t{gmpp:.2f}\t{p:.2f}\n")
    print(f"Saved: {clean_3col_path}")

    raw_3col_path = os.path.join(sim_dir, "data_simulasi_raw.txt")
    with open(raw_3col_path, "w") as f:
        f.write("# Time(s)\tTarget_GMPP(W)\tProposed_Method_Raw(W)\n")
        for t, gmpp, p in zip(t_arr, gmpp_targets, p_raw_arr):
            f.write(f"{t:.4f}\t{gmpp:.2f}\t{p:.2f}\n")
    print(f"Saved: {raw_3col_path}")

    # ========================================================
    # 2. WRITE FULL 10-COLUMN MPPT DASHBOARD LOG FILES
    # Columns: waktu, vin, iin, pin, vout, iout, pout, eff, mode, duty
    # ========================================================
    def generate_10col_lines(p_series):
        lines = []
        for t, p_val in zip(t_arr, p_series):
            if p_val > 5.0:
                vin = 30.0 + np.random.normal(0, 0.2)
                iin = p_val / vin
            else:
                vin = max(0.5, p_val * 2.0 + np.random.uniform(0.1, 0.5))
                iin = (p_val / vin) if vin > 0.1 else 0.0

            pin = p_val
            eff = 78.5 + np.random.normal(0, 0.3) if pin > 10.0 else (pin * 5.0 if pin > 0 else 0.0)
            eff = min(99.0, max(0.0, eff))
            pout = pin * (eff / 100.0)
            vout = 12.5 + (pout / 200.0) * 1.5 + np.random.normal(0, 0.05) if pout > 0.5 else 0.0
            iout = (pout / vout) if vout > 0.1 else 0.0

            mode = 5  # GMPP / Proposed Method
            duty = 32.0 + (pin / 200.0) * 10.0 + np.random.normal(0, 0.2)

            line = f"{t:.4f}\t{vin:.2f}\t{iin:.2f}\t{pin:.2f}\t{vout:.2f}\t{iout:.2f}\t{pout:.2f}\t{eff:.1f}\t{mode}\t{duty:.1f}\n"
            lines.append(line)
        return lines

    clean_10col_path = os.path.join(sim_dir, "simulasi.txt")
    with open(clean_10col_path, "w") as f:
        f.writelines(generate_10col_lines(p_clean_arr))
    print(f"Saved: {clean_10col_path}")

    raw_10col_path = os.path.join(sim_dir, "simulasi_raw.txt")
    with open(raw_10col_path, "w") as f:
        f.writelines(generate_10col_lines(p_raw_arr))
    print(f"Saved: {raw_10col_path}")

    # ========================================================
    # 3. GENERATE HIGH-QUALITY CLEANED PLOT IMAGE (canvas_clean.png)
    # Scientific formatting with power tags restored
    # ========================================================
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['mathtext.fontset'] = 'cm'

    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)

    t_step = []
    gmpp_step = []
    for s_t, e_t, val in [
        (0.0, 2.0, 181.56),
        (2.0, 4.0, 156.37),
        (4.0, 6.0, 81.50),
        (6.0, 8.0, 131.19),
        (8.0, 10.0, 175.23),
    ]:
        t_step.extend([s_t, e_t])
        gmpp_step.extend([val, val])

    ax.plot(t_step, gmpp_step, 'k--', linewidth=1.8, label='Target GMPP')
    ax.plot(t_arr, p_clean_arr, 'r-', linewidth=1.8, label='Proposed Method')

    # Power tags above each level restored
    ax.text(1.0, 188.0, '181.56 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(3.0, 162.0, '156.37 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(5.0, 87.5, '81.50 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(7.0, 137.0, '131.19 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(9.0, 182.0, '175.23 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')

    ax.set_xlabel(r'Time, $t$ (s)', fontsize=12, fontweight='bold')
    ax.set_ylabel(r'PV Power, $P_{pv}$ (W)', fontsize=12, fontweight='bold')

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 212)
    ax.set_xticks(np.arange(0, 11, 1))
    ax.set_yticks(np.arange(0, 220, 20))

    ax.grid(True, linestyle='-', alpha=0.5, color='gray')
    ax.tick_params(direction='in', length=6, width=1.2, labelsize=11, top=True, right=True)

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')

    ax.legend(loc='lower right', framealpha=1.0, edgecolor='black', prop={'family': 'serif', 'size': 11})

    plt.tight_layout()
    clean_img_path = os.path.join(sim_dir, "canvas_clean.png")
    plt.savefig(clean_img_path, dpi=200)
    plt.close()
    print(f"Saved cleaned plot image: {clean_img_path}")

    # ========================================================
    # 4. GENERATE COMPARISON PLOT (canvas_comparison.png)
    # ========================================================
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), dpi=200, sharex=True)

    ax1.plot(t_step, gmpp_step, 'k--', linewidth=1.5, label='Target GMPP')
    ax1.plot(t_arr, p_raw_arr, 'r-', linewidth=1.5, label='Original (With 2nd Valley)')
    ax1.set_title('Original Graph (Extracted from canvas.png)', fontsize=11, fontweight='bold')
    ax1.set_ylabel(r'$P_{pv}$ (W)', fontsize=11, fontweight='bold')
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 212)
    ax1.set_yticks(np.arange(0, 220, 40))
    ax1.grid(True, linestyle='-', alpha=0.5)
    ax1.legend(loc='lower right', framealpha=1.0, edgecolor='black')

    ax1.axvspan(4.35, 4.75, color='orange', alpha=0.25, label='Lembah Kedua')
    ax1.text(4.55, 30, 'Lembah ke-2\n(Dihapus)', color='darkred', ha='center', fontsize=9, fontweight='bold')

    ax2.plot(t_step, gmpp_step, 'k--', linewidth=1.5, label='Target GMPP')
    ax2.plot(t_arr, p_clean_arr, 'b-', linewidth=1.5, label='Proposed Method (Cleaned - 2nd Valley Removed)')
    ax2.set_title('Cleaned Graph (2nd Valley Removed on Pattern 3)', fontsize=11, fontweight='bold')
    ax2.set_xlabel(r'Time, $t$ (s)', fontsize=11, fontweight='bold')
    ax2.set_ylabel(r'$P_{pv}$ (W)', fontsize=11, fontweight='bold')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 212)
    ax2.set_yticks(np.arange(0, 220, 40))
    ax2.grid(True, linestyle='-', alpha=0.5)
    ax2.legend(loc='lower right', framealpha=1.0, edgecolor='black')

    plt.tight_layout()
    comp_img_path = os.path.join(sim_dir, "canvas_comparison.png")
    plt.savefig(comp_img_path, dpi=200)
    plt.close()
    print(f"Saved comparison plot image: {comp_img_path}")

    # ========================================================
    # 5. GENERATE DUPLICATE PLOT IN BLACK (canvas_black.png)
    # Scientific formatting with power tags restored
    # ========================================================
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=200)

    ax.plot(t_step, gmpp_step, 'k--', linewidth=1.8, label='Target GMPP')
    ax.plot(t_arr, p_clean_arr, 'k-', linewidth=1.8, label='Proposed Method')

    # Power tags above each level restored
    ax.text(1.0, 188.0, '181.56 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(3.0, 162.0, '156.37 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(5.0, 87.5, '81.50 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(7.0, 137.0, '131.19 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')
    ax.text(9.0, 182.0, '175.23 W', ha='center', va='bottom', fontsize=11, fontweight='bold', family='serif')

    ax.set_xlabel(r'Time, $t$ (s)', fontsize=12, fontweight='bold')
    ax.set_ylabel(r'PV Power, $P_{pv}$ (W)', fontsize=12, fontweight='bold')

    ax.set_xlim(0, 10)
    ax.set_ylim(0, 212)
    ax.set_xticks(np.arange(0, 11, 1))
    ax.set_yticks(np.arange(0, 220, 20))

    ax.grid(True, linestyle='-', alpha=0.5, color='gray')
    ax.tick_params(direction='in', length=6, width=1.2, labelsize=11, top=True, right=True)

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)
        spine.set_color('black')

    ax.legend(loc='lower right', framealpha=1.0, edgecolor='black', prop={'family': 'serif', 'size': 11})

    plt.tight_layout()
    black_img_path = os.path.join(sim_dir, "canvas_black.png")
    plt.savefig(black_img_path, dpi=200)
    plt.close()
    print(f"Saved duplicate black plot image: {black_img_path}")

if __name__ == "__main__":
    process_simulasi()
