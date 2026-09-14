#ifndef MPPT_ALGO_H_
#define MPPT_ALGO_H_

#include <stdint.h>
#include <math.h>

void Reset_All_Algorithms(void);
float Run_PnO(float v_in, float i_in, float p_in);
float Run_WODE(float v_in, float i_in, float p_in);
float Run_WOA(float v_in, float i_in, float p_in);
float Run_DE(float v_in, float i_in, float p_in);

// Definisi nilai PI jika belum ada di library math.h bawaan STM32
#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

#endif /* MPPT_ALGO_H_ */
