/*
 * mppt_algo.c
 * Integrated MPPT Library: P&O, WOA, DE, and CTM-WODE
 * Revisi: WODE diperhalus + evaluasi daya per duty agar tidak salah ranking.
 */

#include "mppt_algo.h"
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

// =========================================================================
// KONFIGURASI UMUM
// =========================================================================
#define POP_SIZE     4
#define D_MIN        0.10f
#define D_MAX        0.95f
#define SWEEP_STEP   0.005f
#define RAND_F()     ((float)rand() / (float)RAND_MAX)

// Konfigurasi WOA & DE lama
#define MAX_ITER_OLD    5
#define SETTLE_OLD      10

// =========================================================================
// KONFIGURASI DE REVISI
// =========================================================================
#define DE_DMIN         0.15f
#define DE_DMAX         0.65f
#define MAX_ITER_DE     8
#define SETTLE_DE       8
#define AVG_N_DE        4
#define DE_F_MIN        0.35f
#define DE_F_MAX        0.75f

// =========================================================================
// KONFIGURASI WODE REVISI
// =========================================================================
// Batas WODE sengaja tidak sampai 0.95 agar duty tidak liar saat awal tracking.
// Kalau converter kamu memang butuh duty > 0.65, naikkan WODE_DMAX pelan-pelan.

#define WODE_DMIN       0.10f
#define WODE_DMAX       0.55f

/*
 * FAST WODE:
 * Dibuat lebih sat-set: 1 kali scouting kasar + 1 kali refine lokal + lock.
 * Ini mengurangi osilasi lama yang muncul saat WODE terlalu banyak menguji duty jauh.
 */
#define MAX_ITER_WODE   2
#define SETTLE_WODE     4
#define AVG_N_WODE      3

// Duty dianggap sudah sampai target jika error di bawah 0.4%.
#define DUTY_EPS_WODE   0.004f

// Batas perubahan output duty per pemanggilan fungsi. 0.025 cukup cepat tapi masih lebih aman dari loncatan brutal.
#define WODE_SLEW_STEP  0.025f

// Ambang restart saat daya berubah. Dibuat agak besar agar ripple Cuk tidak dikira shading.
#define WODE_RESTART_DP 0.22f

// Fine tuning kecil setelah WODE lock. Kecil saja, biar tidak berubah jadi P&O liar.
#define WODE_FINE_STEP   0.0015f
#define WODE_FINE_DB_W   0.15f

// Batas probe atas sesuai permintaan: duty WODE hanya 0.10 sampai 0.55.
#define WODE_HIGH_PROBE_D 0.55f
#define WODE_LOCAL_WIDTH  0.040f

// State Machine untuk WOA & DE
typedef enum {
    STATE_INIT,
    STATE_SWEEP,
    STATE_EVALUATE,
    STATE_UPDATE,
    STATE_DONE
} AlgoState;

// =========================================================================
// VARIABEL STATIK / PERSISTENT
// =========================================================================
// Variabel untuk P&O
static float v_old_po = 0.0f;
static float p_old_po = 0.0f;
static float duty_po  = 0.1f;

// Variabel untuk WOA & DE
static AlgoState woa_state = STATE_INIT, de_state = STATE_INIT;
static int woa_iter = 0, woa_p_idx = 0, woa_wait = 0;
static int de_iter  = 0, de_p_idx  = 0, de_wait  = 0;

static float woa_D[POP_SIZE],  woa_P[POP_SIZE],  woa_Best_D  = 0.1f, woa_Best_P  = 0.0f, woa_sweep_d  = 0.1f;
static float de_D[POP_SIZE],   de_P[POP_SIZE],   de_Best_D   = 0.1f, de_Best_P   = 0.0f, de_sweep_d   = 0.1f;
static float de_Trial_D;
static uint8_t is_trial_eval = 0;

// Variabel tambahan untuk DE revisi
static uint8_t de_initial_eval_done = 0;
static float de_p_acc = 0.0f;
static int de_p_count = 0;

// Variabel untuk WODE revisi
static uint8_t  wode_is_init = 0;
static uint8_t  wode_u = 0;
static uint16_t wode_counter = 0;
static uint8_t  wode_iter_curr = 0;

static float wode_Pbest = 0.0f;
static float wode_Dbest = 0.35f;
static float wode_D_prev_out = WODE_DMIN;
static float wode_dcurrent = WODE_DMIN;

static float wode_dc[POP_SIZE] = {0};
static float wode_p[POP_SIZE]  = {0};

// Averaging daya per duty. Ini pengganti filter global yang sebelumnya bikin daya antar-duty tercampur.
static float wode_p_acc = 0.0f;
static int   wode_p_count = 0;

// Local refinement setelah WODE selesai mencari global area.
static uint8_t wode_fine_init = 0;
static int8_t  wode_fine_dir = 1;
static float   wode_lock_P_prev = 0.0f;

// =========================================================================
// FUNGSI PENDUKUNG
// =========================================================================
static float clampf_local(float x, float min_val, float max_val)
{
    if (x < min_val) return min_val;
    if (x > max_val) return max_val;
    return x;
}

static void WODE_Reset_Measurement(void)
{
    wode_counter = 0;
    wode_p_acc = 0.0f;
    wode_p_count = 0;
}

static void WODE_Init_Duty_Spread(void)
{
    /*
     * Scouting awal dibuat cepat dan dibatasi 0.10..0.55.
     * Urutan dimulai dari duty atas supaya kalau GMPP berada di area atas,
     * WODE tidak membuang waktu lama di duty rendah.
     */
    wode_dc[0] = 0.55f;
    wode_dc[1] = 0.40f;
    wode_dc[2] = 0.25f;
    wode_dc[3] = 0.10f;

    for (int i = 0; i < POP_SIZE; i++)
    {
        wode_dc[i] = clampf_local(wode_dc[i], WODE_DMIN, WODE_DMAX);
        wode_p[i] = 0.0f;
    }

    wode_fine_init = 0;
    wode_fine_dir = 1;
    wode_lock_P_prev = 0.0f;
}

static void WODE_Prepare_Local_Refine(float center_duty)
{
    /*
     * Setelah scouting kasar selesai, jangan eksplorasi jauh lagi.
     * Cukup uji area kecil di sekitar duty terbaik supaya tracking cepat lock.
     */
    float W = WODE_LOCAL_WIDTH;

    wode_dc[0] = center_duty;
    wode_dc[1] = center_duty - W;
    wode_dc[2] = center_duty + W;

    if (center_duty < ((WODE_DMIN + WODE_DMAX) * 0.5f))
    {
        wode_dc[3] = center_duty + (2.0f * W);
    }
    else
    {
        wode_dc[3] = center_duty - (2.0f * W);
    }

    for (int i = 0; i < POP_SIZE; i++)
    {
        wode_dc[i] = clampf_local(wode_dc[i], WODE_DMIN, WODE_DMAX);
        wode_p[i] = 0.0f;
    }
}

void Reset_All_Algorithms(void)
{
    v_old_po = 0.0f;
    p_old_po = 0.0f;
    duty_po  = 0.1f;

    woa_state = STATE_INIT;
    de_state  = STATE_INIT;

    woa_iter = 0; woa_p_idx = 0; woa_wait = 0;
    de_iter  = 0; de_p_idx  = 0; de_wait  = 0;
    is_trial_eval = 0;
    de_initial_eval_done = 0;
    de_p_acc = 0.0f;
    de_p_count = 0;

    // Trigger inisialisasi ulang WODE pada pemanggilan berikutnya.
    // D_prev_out sengaja tidak dipaksa 0 agar tidak membuat lonjakan duty mendadak.
    wode_is_init = 0;
    wode_u = 0;
    wode_counter = 0;
    wode_iter_curr = 0;
    wode_Pbest = 0.0f;
    wode_Dbest = 0.35f;
    wode_dcurrent = clampf_local(wode_D_prev_out, WODE_DMIN, WODE_DMAX);
    wode_p_acc = 0.0f;
    wode_p_count = 0;
    wode_fine_init = 0;
    wode_fine_dir = 1;
    wode_lock_P_prev = 0.0f;
}

void Check_Shading(float current_P, float best_P)
{
    // Jika daya drop di bawah 70% dari daya terbaik yang pernah didapat.
    if (best_P > 5.0f && current_P < (best_P * 0.7f))
    {
        Reset_All_Algorithms();
    }
}

static void Sort_Descending_WODE(float *p_array, float *dc_array, float *sorted_p, float *sorted_dc)
{
    for (int i = 0; i < POP_SIZE; i++)
    {
        sorted_p[i] = p_array[i];
        sorted_dc[i] = dc_array[i];
    }

    for (int i = 0; i < POP_SIZE - 1; i++)
    {
        for (int j = 0; j < POP_SIZE - 1 - i; j++)
        {
            if (sorted_p[j] < sorted_p[j + 1])
            {
                float temp_p = sorted_p[j];
                sorted_p[j] = sorted_p[j + 1];
                sorted_p[j + 1] = temp_p;

                float temp_d = sorted_dc[j];
                sorted_dc[j] = sorted_dc[j + 1];
                sorted_dc[j + 1] = temp_d;
            }
        }
    }
}

static float apply_slew_rate(float D_target, float D_prev)
{
    D_target = clampf_local(D_target, 0.0f, D_MAX);
    D_prev   = clampf_local(D_prev,   0.0f, D_MAX);

    float diff = D_target - D_prev;

    if (diff > WODE_SLEW_STEP)
    {
        return D_prev + WODE_SLEW_STEP;
    }
    else if (diff < -WODE_SLEW_STEP)
    {
        return D_prev - WODE_SLEW_STEP;
    }

    return D_target;
}


static void DE_Reset_Measurement(void)
{
    de_wait = 0;
    de_p_acc = 0.0f;
    de_p_count = 0;
}

static float DE_Read_Averaged_Power(float v_in, float i_in, float p_in)
{
    float raw_power;

    if (isfinite(p_in) && p_in > 0.0f)
    {
        raw_power = p_in;
    }
    else
    {
        raw_power = v_in * i_in;
    }

    if (!isfinite(raw_power) || raw_power < 0.0f)
    {
        raw_power = 0.0f;
    }

    de_p_acc += raw_power;
    de_p_count++;

    if (de_p_count < AVG_N_DE)
    {
        return -1.0f;
    }

    float p_avg = de_p_acc / (float)AVG_N_DE;
    de_p_acc = 0.0f;
    de_p_count = 0;

    return p_avg;
}

static void DE_Init_Population(void)
{
    for (int i = 0; i < POP_SIZE; i++)
    {
        de_D[i] = DE_DMIN + ((DE_DMAX - DE_DMIN) * ((float)i + 0.5f) / (float)POP_SIZE);
        de_P[i] = 0.0f;
    }

    de_Best_D = de_D[0];
    de_Best_P = 0.0f;
    de_Trial_D = de_D[0];

    de_iter = 0;
    de_p_idx = 0;
    is_trial_eval = 0;
    de_initial_eval_done = 0;
    DE_Reset_Measurement();
}

static float DE_Generate_Trial(uint8_t target_idx)
{
    int r1, r2, r3;

    do { r1 = rand() % POP_SIZE; } while (r1 == target_idx);
    do { r2 = rand() % POP_SIZE; } while (r2 == target_idx || r2 == r1);
    do { r3 = rand() % POP_SIZE; } while (r3 == target_idx || r3 == r1 || r3 == r2);

    float F = DE_F_MIN + ((DE_F_MAX - DE_F_MIN) * RAND_F());

    /*
     * DE/best/1 lebih cepat konvergen untuk MPPT duty 1 dimensi dibanding DE/rand/1.
     * Mutasi tetap memakai selisih dua kandidat agar tidak sekadar jadi P&O yang pakai kostum DE.
     */
    float trial = de_Best_D + F * (de_D[r2] - de_D[r3]);

    /* Crossover 1D: kadang pertahankan target agar tidak terlalu liar. */
    if (RAND_F() > 0.85f)
    {
        trial = de_D[target_idx];
    }

    return clampf_local(trial, DE_DMIN, DE_DMAX);
}

// =========================================================================
// 1. PERTURB AND OBSERVE (P&O)
// =========================================================================
float Run_PnO(float v_in, float i_in, float p_in) {
    (void)i_in;

    float dV   = v_in - v_old_po;
    float dP   = p_in - p_old_po;
    float step = 0.005f; // DIPERBESAR: Langkah duty cycle agar tracking tidak ngeden

    if (v_in < 1.0f) return 0.0f;

    // DIPERBAIKI: Threshold dikecilkan menjadi 0.05W agar P&O sensitif merespons perubahan
    if (fabsf(dP) > 0.05f) {
        if (dP > 0.0f) {
            if (dV > 0.0f) duty_po -= step; // Naikkan V_pv (Turunkan Duty Cycle)
            else           duty_po += step; // Turunkan V_pv (Naikkan Duty Cycle)
        } else {
            if (dV > 0.0f) duty_po += step;
            else           duty_po -= step;
        }
    }

    // Clamp batas Duty Cycle
    if (duty_po > 0.95f) duty_po = 0.95f;
    if (duty_po < 0.10f) duty_po = 0.10f;

    // Simpan nilai masa lalu untuk siklus berikutnya
    v_old_po = v_in;
    p_old_po = p_in;

    return duty_po;
}

// =========================================================================
// 2. WHALE OPTIMIZATION ALGORITHM (WOA)
// =========================================================================
float Run_WOA(float v_in, float i_in, float p_in) {
    switch (woa_state) {
        case STATE_INIT:
            woa_sweep_d = 0.10f; woa_Best_P = 0.0f;
            woa_state   = STATE_SWEEP;
            return woa_sweep_d;

        case STATE_SWEEP:
            if (p_in > woa_Best_P) { woa_Best_P = p_in; woa_Best_D = woa_sweep_d; }
            woa_sweep_d += SWEEP_STEP;
            if (woa_sweep_d >= 0.95f) {
                woa_D[0] = woa_Best_D;
                for (int i = 1; i < POP_SIZE; i++) {
                    woa_D[i] = woa_Best_D + ((RAND_F() * 0.05f) - 0.025f);
                    if (woa_D[i] > 0.95f) woa_D[i] = 0.95f;
                    if (woa_D[i] < 0.10f) woa_D[i] = 0.10f;
                }
                woa_iter = 0; woa_p_idx = 0; woa_wait = 0;
                woa_state = STATE_EVALUATE;
            }
            return woa_sweep_d;

        case STATE_EVALUATE:
            if (woa_wait < SETTLE_OLD) { woa_wait++; return woa_D[woa_p_idx]; }
            woa_P[woa_p_idx] = p_in;
            if (woa_P[woa_p_idx] > woa_Best_P) { woa_Best_P = woa_P[woa_p_idx]; woa_Best_D = woa_D[woa_p_idx]; }
            woa_wait = 0; woa_p_idx++;
            if (woa_p_idx >= POP_SIZE) { woa_p_idx = 0; woa_state = STATE_UPDATE; }
            return woa_D[woa_p_idx < POP_SIZE ? woa_p_idx : 0];

        case STATE_UPDATE: {
            float a = 2.0f - (float)woa_iter * (2.0f / MAX_ITER_OLD);
            for (int i = 0; i < POP_SIZE; i++) {
                float r = RAND_F(); float A = 2.0f * a * r - a;
                float C = 2.0f * r; float l = (RAND_F() * 2.0f) - 1.0f;
                if (RAND_F() < 0.5f) {
                    if (fabsf(A) < 1.0f) woa_D[i] = woa_Best_D - A * fabsf(C * woa_Best_D - woa_D[i]);
                    else { float D_rand = woa_D[rand() % POP_SIZE]; woa_D[i] = D_rand - A * fabsf(C * D_rand - woa_D[i]); }
                } else woa_D[i] = fabsf(woa_Best_D - woa_D[i]) * expf(l) * cosf(2.0f * M_PI * l) + woa_Best_D;
                if (woa_D[i] > 0.95f) woa_D[i] = 0.95f;
                if (woa_D[i] < 0.10f) woa_D[i] = 0.10f;
            }
            woa_iter++;
            if (woa_iter >= MAX_ITER_OLD) { duty_po = woa_Best_D; woa_state = STATE_DONE; }
            else woa_state = STATE_EVALUATE;
            return woa_D[0];
        }
        case STATE_DONE: Check_Shading(p_in, woa_Best_P); return Run_PnO(v_in, i_in, p_in);
    }
    return woa_Best_D;
}

// =========================================================================
// 3. DIFFERENTIAL EVOLUTION (DE) - REVISI
// =========================================================================
float Run_DE(float v_in, float i_in, float p_in)
{
    switch (de_state)
    {
        case STATE_INIT:
        {
            /*
             * Versi lama sweep 0.10 sampai 0.95 terlalu lebar dan bisa masuk area duty
             * yang membuat konverter/beban jatuh. Untuk pembanding yang lebih adil,
             * DE langsung mulai dari scouting terdistribusi di area kerja aman.
             */
            DE_Init_Population();
            de_state = STATE_EVALUATE;
            return de_D[de_p_idx];
        }

        case STATE_SWEEP:
        {
            /* Tidak dipakai lagi. Ditinggalkan agar enum lama tetap kompatibel. */
            DE_Init_Population();
            de_state = STATE_EVALUATE;
            return de_D[de_p_idx];
        }

        case STATE_EVALUATE:
        {
            float active_D = is_trial_eval ? de_Trial_D : de_D[de_p_idx];

            if (de_wait < SETTLE_DE)
            {
                de_wait++;
                return active_D;
            }

            float P_now = DE_Read_Averaged_Power(v_in, i_in, p_in);
            if (P_now < 0.0f)
            {
                return active_D;
            }

            DE_Reset_Measurement();

            if (!de_initial_eval_done)
            {
                /* Evaluasi populasi awal. */
                de_P[de_p_idx] = P_now;

                if (P_now > de_Best_P)
                {
                    de_Best_P = P_now;
                    de_Best_D = de_D[de_p_idx];
                }

                de_p_idx++;

                if (de_p_idx >= POP_SIZE)
                {
                    de_p_idx = 0;
                    de_initial_eval_done = 1;
                    de_state = STATE_UPDATE;
                    return de_Best_D;
                }

                return de_D[de_p_idx];
            }

            if (is_trial_eval)
            {
                /* Seleksi greedy: trial menggantikan target kalau dayanya lebih besar. */
                if (P_now > de_P[de_p_idx])
                {
                    de_P[de_p_idx] = P_now;
                    de_D[de_p_idx] = de_Trial_D;

                    if (P_now > de_Best_P)
                    {
                        de_Best_P = P_now;
                        de_Best_D = de_Trial_D;
                    }
                }

                is_trial_eval = 0;
                de_p_idx++;

                if (de_p_idx >= POP_SIZE)
                {
                    de_p_idx = 0;
                    de_iter++;

                    if (de_iter >= MAX_ITER_DE)
                    {
                        duty_po = de_Best_D;
                        de_state = STATE_DONE;
                        return de_Best_D;
                    }
                }

                de_state = STATE_UPDATE;
                return de_Best_D;
            }

            /* Safety fallback. Normalnya tidak masuk sini setelah initial eval selesai. */
            de_state = STATE_UPDATE;
            return de_Best_D;
        }

        case STATE_UPDATE:
        {
            de_Trial_D = DE_Generate_Trial(de_p_idx);
            is_trial_eval = 1;
            DE_Reset_Measurement();
            de_state = STATE_EVALUATE;
            return de_Trial_D;
        }

        case STATE_DONE:
        {
            /*
             * Jangan langsung lempar ke P&O seperti versi lama, karena itu membuat grafik DE
             * bisa jatuh mendadak setelah selesai iterasi. DE dikunci ke duty terbaik dulu.
             * Kalau daya berubah besar, baru reset algoritma.
             */
            if (de_Best_P > 5.0f)
            {
                float current_P = p_in;
                if (!isfinite(current_P) || current_P <= 0.0f)
                {
                    current_P = v_in * i_in;
                }
                if (!isfinite(current_P) || current_P < 0.0f)
                {
                    current_P = 0.0f;
                }

                if (current_P < (de_Best_P * 0.70f))
                {
                    de_state = STATE_INIT;
                    return de_Best_D;
                }
            }

            return de_Best_D;
        }
    }

    return de_Best_D;
}

// =========================================================================

// =========================================================================
// 4. CTM-WODE REVISI
// =========================================================================
float Run_WODE(float v_in, float i_in, float p_in_raw)
{
    // ============================================================
    // 1. INISIALISASI
    // ============================================================
    if (wode_is_init == 0)
    {
        wode_u = 0;
        wode_counter = 0;
        wode_iter_curr = 0;

        wode_Pbest = 0.0f;
        wode_Dbest = 0.35f;

        if (!isfinite(wode_D_prev_out))
        {
            wode_D_prev_out = WODE_DMIN;
        }

        wode_D_prev_out = clampf_local(wode_D_prev_out, WODE_DMIN, WODE_DMAX);

        WODE_Init_Duty_Spread();
        WODE_Reset_Measurement();

        wode_dcurrent = wode_dc[0];
        wode_is_init = 1;

        wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
        return wode_D_prev_out;
    }

    // ============================================================
    // 2. PASTIKAN DUTY AKTUAL SUDAH MENDEKATI TARGET
    // ============================================================
    if (fabsf(wode_D_prev_out - wode_dcurrent) > DUTY_EPS_WODE)
    {
        WODE_Reset_Measurement();
        wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
        return wode_D_prev_out;
    }

    // ============================================================
    // 3. SETTLING SETELAH DUTY SAMPAI TARGET
    // ============================================================
    if (wode_counter < SETTLE_WODE)
    {
        wode_counter++;
        wode_p_acc = 0.0f;
        wode_p_count = 0;

        wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
        return wode_D_prev_out;
    }

    // ============================================================
    // 4. AVERAGING DAYA PER DUTY
    // ============================================================
    float raw_power;

    if (isfinite(p_in_raw) && p_in_raw > 0.0f)
    {
        raw_power = p_in_raw;
    }
    else
    {
        raw_power = v_in * i_in;
    }

    if (!isfinite(raw_power) || raw_power < 0.0f)
    {
        raw_power = 0.0f;
    }

    wode_p_acc += raw_power;
    wode_p_count++;

    if (wode_p_count < AVG_N_WODE)
    {
        wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
        return wode_D_prev_out;
    }

    float P_now = wode_p_acc / (float)AVG_N_WODE;
    WODE_Reset_Measurement();

    // ============================================================
    // 5. MODE LOCK + FINE TUNING KECIL
    // ============================================================
    if (wode_iter_curr >= MAX_ITER_WODE && wode_Pbest > 5.0f)
    {
        float delta_P = fabsf(P_now - wode_Pbest) / wode_Pbest;

        if (delta_P > WODE_RESTART_DP)
        {
            wode_is_init = 0;
            wode_fine_init = 0;

            wode_D_prev_out = apply_slew_rate(wode_Dbest, wode_D_prev_out);
            return wode_D_prev_out;
        }

        if (wode_fine_init == 0)
        {
            wode_fine_init = 1;
            wode_fine_dir = 1;
            wode_lock_P_prev = P_now;

            if (P_now > wode_Pbest)
            {
                wode_Pbest = P_now;
            }

            wode_dcurrent = wode_Dbest;
            wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
            return wode_D_prev_out;
        }

        float dP_lock = P_now - wode_lock_P_prev;

        if (fabsf(dP_lock) > WODE_FINE_DB_W)
        {
            if (dP_lock < 0.0f)
            {
                wode_fine_dir = -wode_fine_dir;
            }
            else if (P_now > wode_Pbest)
            {
                wode_Pbest = P_now;
            }

            wode_Dbest += ((float)wode_fine_dir * WODE_FINE_STEP);
            wode_Dbest = clampf_local(wode_Dbest, WODE_DMIN, WODE_DMAX);
        }

        wode_lock_P_prev = P_now;
        wode_dcurrent = wode_Dbest;

        wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
        return wode_D_prev_out;
    }

    // ============================================================
    // 6. SIMPAN HASIL EVALUASI PARTIKEL SAAT INI
    // ============================================================
    wode_p[wode_u] = P_now;

    if (wode_u < (POP_SIZE - 1))
    {
        wode_u++;
        wode_dcurrent = wode_dc[wode_u];

        WODE_Reset_Measurement();

        wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
        return wode_D_prev_out;
    }

    // ============================================================
    // 7. SEMUA PARTIKEL SUDAH DIEVALUASI
    // ============================================================
    float s_p[POP_SIZE];
    float s_d[POP_SIZE];

    Sort_Descending_WODE(wode_p, wode_dc, s_p, s_d);

    if (s_p[0] > wode_Pbest)
    {
        wode_Pbest = s_p[0];
        wode_Dbest = s_d[0];
    }

    wode_iter_curr++;

    // ============================================================
    // 8. LOCK CEPAT SETELAH SCOUTING + REFINE
    // ============================================================
    if (wode_iter_curr >= MAX_ITER_WODE)
    {
        for (int i = 0; i < POP_SIZE; i++)
        {
            wode_dc[i] = wode_Dbest;
            wode_p[i] = 0.0f;
        }

        wode_u = 0;
        wode_dcurrent = wode_Dbest;
        wode_fine_init = 0;
        wode_fine_dir = 1;
        wode_lock_P_prev = 0.0f;

        WODE_Reset_Measurement();

        wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
        return wode_D_prev_out;
    }

    // ============================================================
    // 9. REFINE LOKAL CEPAT DI SEKITAR DBEST
    // ============================================================
    WODE_Prepare_Local_Refine(wode_Dbest);

    wode_u = 0;
    wode_dcurrent = wode_dc[0];

    WODE_Reset_Measurement();

    wode_D_prev_out = apply_slew_rate(wode_dcurrent, wode_D_prev_out);
    return wode_D_prev_out;
}

