/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Hardware Controlled MPPT + Anti-EMI Debounce + Slow GMPP Sweep + UART RX
 ******************************************************************************
 */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <math.h>
#include "stdlib.h"
#include "string.h"
#include "stdio.h"
#include "i2c_lcd.h"
#include "mppt_algo.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
const uint32_t PWM_PERIOD_TICKS = 1291;
#define LCD_I2C_ADDRESS 0x27
#define UART_TX_INTERVAL_MS 100U
#define LCD_UPDATE_INTERVAL_MS 300U
#define MAIN_LOOP_DELAY_MS 10U
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
ADC_HandleTypeDef hadc1;
DMA_HandleTypeDef hdma_adc1;

I2C_HandleTypeDef hi2c1;
I2C_HandleTypeDef hi2c2;

SPI_HandleTypeDef hspi2;

TIM_HandleTypeDef htim4;
TIM_HandleTypeDef htim9;

UART_HandleTypeDef huart1;
DMA_HandleTypeDef hdma_usart1_rx;
DMA_HandleTypeDef hdma_usart1_tx;

/* USER CODE BEGIN PV */
static I2C_LCD_HandleTypeDef lcd_handle;
char uart_tx_buf[256];

// --- BUFFER ADC (DMA) ---
__IO uint16_t ADC_dma_buffer[8];

const uint8_t LCD_I2C_8BIT_ADDRESS = 0x4E;

// --- Konstanta Kalibrasi SENSOR ---
const float V_M_IN = 0.096227f;   // Slope (m)
const float V_C_IN = -152.9939f;  // Intercept (c)

const float FAKTOR_SKALA_I_IN = 0.006924f;
const float ADC_OFFSET_I_IN = 1915.0f;

const float V_M_OUT = 0.022194f;
const float V_C_OUT = -35.235832f;

const float FAKTOR_SKALA_I_OUT = 0.019387f;
const float ADC_OFFSET_I_OUT = 1915.0f;

// --- Variabel Filter (Smoothing) ---
const float ALPHA = 0.1f;
float adc_Vin_filt=0.0f, adc_Iin_filt=0.0f, adc_Vout_filt=0.0f, adc_Iout_filt=0.0f;

// --- Variabel Pengukuran ---
volatile float V_in=0, I_in=0, P_in=0;
volatile float V_out=0, I_out=0, P_out=0;
volatile float Eff_MPPT = 0.0f;

volatile float D_new      = 0.0f;
volatile float D_gate_est = 0.0f;

// --- STATE MACHINE ---
uint8_t is_running  = 1;
uint8_t mppt_mode   = 0;
float   manual_duty = 0.0f;

volatile float global_time_sec = 0.0f;
volatile float algo_time_sec   = 0.0f;

// --- BUFFER UART RECEIVE DARI PYTHON ---
uint8_t rx_data[1];
char rx_buffer[20];
uint8_t rx_index = 0;
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_DMA_Init(void);
static void MX_ADC1_Init(void);
static void MX_I2C1_Init(void);
static void MX_I2C2_Init(void);
static void MX_SPI2_Init(void);
static void MX_TIM4_Init(void);
static void MX_USART1_UART_Init(void);
static void MX_TIM9_Init(void);
/* USER CODE BEGIN PFP */
void MPPT_LCD_Init(I2C_HandleTypeDef *hi2c, uint8_t address);
void MPPT_LCD_ShowStartup(void);
void MPPT_SendData_UART(void);
void Cek_Push_Button(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
// --- FUNGSI HELPER LCD ADAPTIF ---
void Format_LCD_Adaptif(char *buffer, const char *label, float val, const char *unit) {
    // Angka 99.95, 9.995 dipakai untuk mencegah bug "pembulatan naik".
    // Misal: 99.99 jika pakai %.2f akan dibulatkan jadi 100.00 (6 karakter/melebihi batas).
    if (val >= 999.5f) {
        snprintf(buffer, 16, "%s%5.0f%s", label, val, unit); // Contoh: " 1000"
    }
    else if (val >= 99.95f) {
        snprintf(buffer, 16, "%s%5.1f%s", label, val, unit); // Contoh: "100.5"
    }
    else if (val >= 9.995f) {
        snprintf(buffer, 16, "%s%5.2f%s", label, val, unit); // Contoh: "12.34"
    }
    else {
        snprintf(buffer, 16, "%s%5.3f%s", label, val, unit); // Contoh: "1.444"
    }
}
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim) {
    if (htim->Instance == TIM9) {

        uint32_t raw_Iin  = ADC_dma_buffer[0];
        uint32_t raw_Vin  = ADC_dma_buffer[1];
        uint32_t raw_Iout = ADC_dma_buffer[2];
        uint32_t raw_Vout = ADC_dma_buffer[3];

        static uint8_t filter_init = 0;
        if (filter_init == 0) {
            adc_Vin_filt  = (float)raw_Vin;
            adc_Iin_filt  = (float)raw_Iin;
            adc_Vout_filt = (float)raw_Vout;
            adc_Iout_filt = (float)raw_Iout;
            filter_init   = 1;
        }

        adc_Vin_filt  = (ALPHA * (float)raw_Vin)  + ((1.0f - ALPHA) * adc_Vin_filt);
        adc_Iin_filt  = (ALPHA * (float)raw_Iin)  + ((1.0f - ALPHA) * adc_Iin_filt);
        adc_Vout_filt = (ALPHA * (float)raw_Vout) + ((1.0f - ALPHA) * adc_Vout_filt);
        adc_Iout_filt = (ALPHA * (float)raw_Iout) + ((1.0f - ALPHA) * adc_Iout_filt);

        float temp_Vin = (adc_Vin_filt * V_M_IN) + V_C_IN;
        if (temp_Vin < 0.0f) temp_Vin = 0.0f;
        V_in = temp_Vin;

        float temp_Iin = (adc_Iin_filt - ADC_OFFSET_I_IN) * FAKTOR_SKALA_I_IN;
        if (temp_Iin < 0.0f) temp_Iin = 0.0f;
        I_in = temp_Iin;

        P_in = V_in * I_in;

        float temp_Vout = (adc_Vout_filt * V_M_OUT) + V_C_OUT;
        if (temp_Vout < 0.0f) temp_Vout = 0.0f;
        V_out = temp_Vout;

        float temp_Iout = (adc_Iout_filt - ADC_OFFSET_I_OUT) * FAKTOR_SKALA_I_OUT;
        if (temp_Iout < 0.0f) temp_Iout = 0.0f;
        I_out = temp_Iout;

        P_out    = V_out * I_out;
        Eff_MPPT = (P_in > 0.5f) ? (P_out / P_in) : 0.0f;

        if (is_running) {
            global_time_sec += 0.01f;
            algo_time_sec   += 0.01f;

            float target_d_desimal = D_new / 100.0f;

            switch (mppt_mode) {
                            case 0: target_d_desimal = manual_duty / 100.0f;           break;
                            case 1: target_d_desimal = Run_WODE(V_in, I_in, P_in);     break;
                            case 2: target_d_desimal = Run_WOA(V_in, I_in, P_in);      break;
                            case 3: target_d_desimal = Run_DE(V_in, I_in, P_in);       break;
                            case 4: target_d_desimal = Run_PnO(V_in, I_in, P_in);      break;
                            case 5:
                                // Durasi total 60 detik, naik 0.5% per step
                                if (algo_time_sec >= 60.0f) {
                                    algo_time_sec = 0.0f;
                                }
                                int step = (int)(algo_time_sec / 0.315f);
                                target_d_desimal = (float)step * 0.005f;
                                break;
                        }

            if (target_d_desimal > 0.95f) target_d_desimal = 0.95f;
            if (target_d_desimal < 0.0f)  target_d_desimal = 0.0f;

            D_new = target_d_desimal * 100.0f;
        } else {
            if (D_new > 95.0f) D_new = 95.0f;
            if (D_new < 0.0f)  D_new = 0.0f;
            manual_duty = D_new;
        }

        float final_d_desimal = D_new / 100.0f;
        D_gate_est = final_d_desimal;
        uint32_t pwm_pulse = (uint32_t)(final_d_desimal * (float)(PWM_PERIOD_TICKS - 1));
        __HAL_TIM_SET_COMPARE(&htim4, TIM_CHANNEL_1, pwm_pulse);
    }
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_DMA_Init();
  MX_ADC1_Init();
  MX_I2C1_Init();
  MX_I2C2_Init();
  MX_SPI2_Init();
  MX_TIM4_Init();
  MX_USART1_UART_Init();
  MX_TIM9_Init();
  /* USER CODE BEGIN 2 */
    MPPT_LCD_Init(&hi2c1, LCD_I2C_8BIT_ADDRESS);
    MPPT_LCD_ShowStartup();
    HAL_Delay(500);

    HAL_ADC_Start_DMA(&hadc1, (uint32_t*)ADC_dma_buffer, 8);
    HAL_TIM_PWM_Start(&htim4, TIM_CHANNEL_1);
    HAL_TIM_Base_Start_IT(&htim9);

    // Mulai dengarkan 1 karakter pertama dari Python
    HAL_UART_Receive_IT(&huart1, rx_data, 1);

    HAL_GPIO_WritePin(GPIOD, RELAY1_Pin, GPIO_PIN_SET);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
        static uint32_t last_lcd_update_ms = 0U;
        static uint32_t last_uart_tx_ms = 0U;

        Cek_Push_Button(); // Tetap aktif sebagai fallback hardware

        uint32_t now_ms = HAL_GetTick();

        if ((now_ms - last_lcd_update_ms) >= LCD_UPDATE_INTERVAL_MS) {
            last_lcd_update_ms = now_ms;

            float v_in_l, i_in_l, p_in_l;
            float v_out_l, i_out_l, p_out_l;
            float eff_l, d_gate_l;

            __disable_irq();
            v_in_l   = V_in;   i_in_l   = I_in;   p_in_l   = P_in;
            v_out_l  = V_out;  i_out_l  = I_out;  p_out_l  = P_out;
            eff_l    = Eff_MPPT * 100.0f;
            d_gate_l = D_new;
            __enable_irq();

            char left[16], right[16];

            // Baris 0 (Tegangan)
            Format_LCD_Adaptif(left,  "Vin:", v_in_l, "V");
            Format_LCD_Adaptif(right, "Vo :", v_out_l, "V");
            lcd_gotoxy(&lcd_handle, 0,  0); lcd_puts(&lcd_handle, left);
            lcd_gotoxy(&lcd_handle, 10, 0); lcd_puts(&lcd_handle, right);

            // Baris 1 (Arus)
            Format_LCD_Adaptif(left,  "Iin:", i_in_l, "A");
            Format_LCD_Adaptif(right, "Io :", i_out_l, "A");
            lcd_gotoxy(&lcd_handle, 0,  1); lcd_puts(&lcd_handle, left);
            lcd_gotoxy(&lcd_handle, 10, 1); lcd_puts(&lcd_handle, right);

            // Baris 2 (Daya)
            Format_LCD_Adaptif(left,  "Pin:", p_in_l, "W");
            Format_LCD_Adaptif(right, "Po :", p_out_l, "W");
            lcd_gotoxy(&lcd_handle, 0,  2); lcd_puts(&lcd_handle, left);
            lcd_gotoxy(&lcd_handle, 10, 2); lcd_puts(&lcd_handle, right);

            // Baris 3 (Efisiensi & Duty Cycle)
            Format_LCD_Adaptif(left,  "Eff:", eff_l, "%");
            Format_LCD_Adaptif(right, "Dty:", d_gate_l, "%");
            lcd_gotoxy(&lcd_handle, 0,  3); lcd_puts(&lcd_handle, left);
            lcd_gotoxy(&lcd_handle, 10, 3); lcd_puts(&lcd_handle, right);
        }

        if ((now_ms - last_uart_tx_ms) >= UART_TX_INTERVAL_MS) {
            last_uart_tx_ms = now_ms;
            MPPT_SendData_UART();
        }

        HAL_Delay(MAIN_LOOP_DELAY_MS);
  /* USER CODE END 3 */
}
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Configure the main internal regulator output voltage
  */
  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 4;
  RCC_OscInitStruct.PLL.PLLN = 168;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV2;
  RCC_OscInitStruct.PLL.PLLQ = 4;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief ADC1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_ADC1_Init(void)
{

  /* USER CODE BEGIN ADC1_Init 0 */

  /* USER CODE END ADC1_Init 0 */

  ADC_ChannelConfTypeDef sConfig = {0};

  /* USER CODE BEGIN ADC1_Init 1 */

  /* USER CODE END ADC1_Init 1 */

  /** Configure the global features of the ADC (Clock, Resolution, Data Alignment and number of conversion)
  */
  hadc1.Instance = ADC1;
  hadc1.Init.ClockPrescaler = ADC_CLOCK_SYNC_PCLK_DIV4;
  hadc1.Init.Resolution = ADC_RESOLUTION_12B;
  hadc1.Init.ScanConvMode = ENABLE;
  hadc1.Init.ContinuousConvMode = ENABLE;
  hadc1.Init.DiscontinuousConvMode = DISABLE;
  hadc1.Init.ExternalTrigConvEdge = ADC_EXTERNALTRIGCONVEDGE_NONE;
  hadc1.Init.ExternalTrigConv = ADC_SOFTWARE_START;
  hadc1.Init.DataAlign = ADC_DATAALIGN_RIGHT;
  hadc1.Init.NbrOfConversion = 8;
  hadc1.Init.DMAContinuousRequests = ENABLE;
  hadc1.Init.EOCSelection = ADC_EOC_SINGLE_CONV;
  if (HAL_ADC_Init(&hadc1) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_0;
  sConfig.Rank = 1;
  sConfig.SamplingTime = ADC_SAMPLETIME_480CYCLES;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_1;
  sConfig.Rank = 2;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_2;
  sConfig.Rank = 3;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_3;
  sConfig.Rank = 4;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_10;
  sConfig.Rank = 5;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_11;
  sConfig.Rank = 6;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_12;
  sConfig.Rank = 7;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }

  /** Configure for the selected ADC regular channel its corresponding rank in the sequencer and its sample time.
  */
  sConfig.Channel = ADC_CHANNEL_13;
  sConfig.Rank = 8;
  if (HAL_ADC_ConfigChannel(&hadc1, &sConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN ADC1_Init 2 */

  /* USER CODE END ADC1_Init 2 */

}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C1_Init(void)
{

  /* USER CODE BEGIN I2C1_Init 0 */

  /* USER CODE END I2C1_Init 0 */

  /* USER CODE BEGIN I2C1_Init 1 */

  /* USER CODE END I2C1_Init 1 */
  hi2c1.Instance = I2C1;
  hi2c1.Init.ClockSpeed = 100000;
  hi2c1.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1 = 0;
  hi2c1.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2 = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C1_Init 2 */

  /* USER CODE END I2C1_Init 2 */

}

/**
  * @brief I2C2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_I2C2_Init(void)
{

  /* USER CODE BEGIN I2C2_Init 0 */

  /* USER CODE END I2C2_Init 0 */

  /* USER CODE BEGIN I2C2_Init 1 */

  /* USER CODE END I2C2_Init 1 */
  hi2c2.Instance = I2C2;
  hi2c2.Init.ClockSpeed = 100000;
  hi2c2.Init.DutyCycle = I2C_DUTYCYCLE_2;
  hi2c2.Init.OwnAddress1 = 0;
  hi2c2.Init.AddressingMode = I2C_ADDRESSINGMODE_7BIT;
  hi2c2.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c2.Init.OwnAddress2 = 0;
  hi2c2.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c2.Init.NoStretchMode = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN I2C2_Init 2 */

  /* USER CODE END I2C2_Init 2 */

}

/**
  * @brief SPI2 Initialization Function
  * @param None
  * @retval None
  */
static void MX_SPI2_Init(void)
{

  /* USER CODE BEGIN SPI2_Init 0 */

  /* USER CODE END SPI2_Init 0 */

  /* USER CODE BEGIN SPI2_Init 1 */

  /* USER CODE END SPI2_Init 1 */
  /* SPI2 parameter configuration*/
  hspi2.Instance = SPI2;
  hspi2.Init.Mode = SPI_MODE_MASTER;
  hspi2.Init.Direction = SPI_DIRECTION_2LINES;
  hspi2.Init.DataSize = SPI_DATASIZE_8BIT;
  hspi2.Init.CLKPolarity = SPI_POLARITY_LOW;
  hspi2.Init.CLKPhase = SPI_PHASE_1EDGE;
  hspi2.Init.NSS = SPI_NSS_SOFT;
  hspi2.Init.BaudRatePrescaler = SPI_BAUDRATEPRESCALER_2;
  hspi2.Init.FirstBit = SPI_FIRSTBIT_MSB;
  hspi2.Init.TIMode = SPI_TIMODE_DISABLE;
  hspi2.Init.CRCCalculation = SPI_CRCCALCULATION_DISABLE;
  hspi2.Init.CRCPolynomial = 10;
  if (HAL_SPI_Init(&hspi2) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN SPI2_Init 2 */

  /* USER CODE END SPI2_Init 2 */

}

/**
  * @brief TIM4 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM4_Init(void)
{

  /* USER CODE BEGIN TIM4_Init 0 */

  /* USER CODE END TIM4_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};
  TIM_MasterConfigTypeDef sMasterConfig = {0};
  TIM_OC_InitTypeDef sConfigOC = {0};

  /* USER CODE BEGIN TIM4_Init 1 */

  /* USER CODE END TIM4_Init 1 */
  htim4.Instance = TIM4;
  htim4.Init.Prescaler = 0;
  htim4.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim4.Init.Period = 1291;
  htim4.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim4.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim4, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_Init(&htim4) != HAL_OK)
  {
    Error_Handler();
  }
  sMasterConfig.MasterOutputTrigger = TIM_TRGO_RESET;
  sMasterConfig.MasterSlaveMode = TIM_MASTERSLAVEMODE_DISABLE;
  if (HAL_TIMEx_MasterConfigSynchronization(&htim4, &sMasterConfig) != HAL_OK)
  {
    Error_Handler();
  }
  sConfigOC.OCMode = TIM_OCMODE_PWM1;
  sConfigOC.Pulse = 0;
  sConfigOC.OCPolarity = TIM_OCPOLARITY_HIGH;
  sConfigOC.OCFastMode = TIM_OCFAST_DISABLE;
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_1) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_2) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_3) != HAL_OK)
  {
    Error_Handler();
  }
  if (HAL_TIM_PWM_ConfigChannel(&htim4, &sConfigOC, TIM_CHANNEL_4) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM4_Init 2 */

  /* USER CODE END TIM4_Init 2 */
  HAL_TIM_MspPostInit(&htim4);

}

/**
  * @brief TIM9 Initialization Function
  * @param None
  * @retval None
  */
static void MX_TIM9_Init(void)
{

  /* USER CODE BEGIN TIM9_Init 0 */

  /* USER CODE END TIM9_Init 0 */

  TIM_ClockConfigTypeDef sClockSourceConfig = {0};

  /* USER CODE BEGIN TIM9_Init 1 */

  /* USER CODE END TIM9_Init 1 */
  htim9.Instance = TIM9;
  htim9.Init.Prescaler = 16799;
  htim9.Init.CounterMode = TIM_COUNTERMODE_UP;
  htim9.Init.Period = 99;
  htim9.Init.ClockDivision = TIM_CLOCKDIVISION_DIV1;
  htim9.Init.AutoReloadPreload = TIM_AUTORELOAD_PRELOAD_ENABLE;
  if (HAL_TIM_Base_Init(&htim9) != HAL_OK)
  {
    Error_Handler();
  }
  sClockSourceConfig.ClockSource = TIM_CLOCKSOURCE_INTERNAL;
  if (HAL_TIM_ConfigClockSource(&htim9, &sClockSourceConfig) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN TIM9_Init 2 */

  /* USER CODE END TIM9_Init 2 */

}

/**
  * @brief USART1 Initialization Function
  * @param None
  * @retval None
  */
static void MX_USART1_UART_Init(void)
{

  /* USER CODE BEGIN USART1_Init 0 */

  /* USER CODE END USART1_Init 0 */

  /* USER CODE BEGIN USART1_Init 1 */

  /* USER CODE END USART1_Init 1 */
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
  /* USER CODE BEGIN USART1_Init 2 */

  /* USER CODE END USART1_Init 2 */

}

/**
  * Enable DMA controller clock
  */
static void MX_DMA_Init(void)
{

  /* DMA controller clock enable */
  __HAL_RCC_DMA2_CLK_ENABLE();

  /* DMA interrupt init */
  /* DMA2_Stream0_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA2_Stream0_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA2_Stream0_IRQn);
  /* DMA2_Stream2_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA2_Stream2_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA2_Stream2_IRQn);
  /* DMA2_Stream7_IRQn interrupt configuration */
  HAL_NVIC_SetPriority(DMA2_Stream7_IRQn, 0, 0);
  HAL_NVIC_EnableIRQ(DMA2_Stream7_IRQn);

}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};
  /* USER CODE BEGIN MX_GPIO_Init_1 */

  /* USER CODE END MX_GPIO_Init_1 */

  /* GPIO Ports Clock Enable */
  __HAL_RCC_GPIOH_CLK_ENABLE();
  __HAL_RCC_GPIOC_CLK_ENABLE();
  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOE_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();
  __HAL_RCC_GPIOD_CLK_ENABLE();

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(GPIOD, RELAY1_Pin|RELAY2_Pin|RELAY3_Pin|RELAY4_Pin
                          |LED_1_Pin|LED_2_Pin|LED_3_Pin|LED_4_Pin
                          |LED_5_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(BUZZER_GPIO_Port, BUZZER_Pin, GPIO_PIN_SET);

  /*Configure GPIO pin Output Level */
  HAL_GPIO_WritePin(LED_6_GPIO_Port, LED_6_Pin, GPIO_PIN_RESET);

  /*Configure GPIO pins : PE7 PE8 PE9 PE10
                           PE11 PE12 PE13 PE14 */
  GPIO_InitStruct.Pin = GPIO_PIN_7|GPIO_PIN_8|GPIO_PIN_9|GPIO_PIN_10
                          |GPIO_PIN_11|GPIO_PIN_12|GPIO_PIN_13|GPIO_PIN_14;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  HAL_GPIO_Init(GPIOE, &GPIO_InitStruct);

  /*Configure GPIO pins : RELAY1_Pin RELAY2_Pin RELAY3_Pin RELAY4_Pin
                           LED_1_Pin LED_2_Pin LED_3_Pin LED_4_Pin
                           LED_5_Pin */
  GPIO_InitStruct.Pin = RELAY1_Pin|RELAY2_Pin|RELAY3_Pin|RELAY4_Pin
                          |LED_1_Pin|LED_2_Pin|LED_3_Pin|LED_4_Pin
                          |LED_5_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /*Configure GPIO pin : BUZZER_Pin */
  GPIO_InitStruct.Pin = BUZZER_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(BUZZER_GPIO_Port, &GPIO_InitStruct);

  /*Configure GPIO pins : PB1_Pin PB2_Pin PB3_Pin */
  GPIO_InitStruct.Pin = PB1_Pin|PB2_Pin|PB3_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOC, &GPIO_InitStruct);

  /*Configure GPIO pins : PB4_Pin PB5_Pin PB6_Pin */
  GPIO_InitStruct.Pin = PB4_Pin|PB5_Pin|PB6_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  HAL_GPIO_Init(GPIOD, &GPIO_InitStruct);

  /*Configure GPIO pin : LED_6_Pin */
  GPIO_InitStruct.Pin = LED_6_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(LED_6_GPIO_Port, &GPIO_InitStruct);

  /* USER CODE BEGIN MX_GPIO_Init_2 */

  /* USER CODE END MX_GPIO_Init_2 */
}

/* USER CODE BEGIN 4 */

void Cek_Push_Button(void) {
    if (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_10) == GPIO_PIN_RESET) {
        HAL_Delay(150);
        if (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_10) == GPIO_PIN_RESET) {
            mppt_mode = 1; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            while(HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_10) == GPIO_PIN_RESET);
        }
    }
    else if (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_11) == GPIO_PIN_RESET) {
        HAL_Delay(150);
        if (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_11) == GPIO_PIN_RESET) {
            mppt_mode = 2; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            while(HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_11) == GPIO_PIN_RESET);
        }
    }
    else if (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_12) == GPIO_PIN_RESET) {
        HAL_Delay(150);
        if (HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_12) == GPIO_PIN_RESET) {
            mppt_mode = 3; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            while(HAL_GPIO_ReadPin(GPIOC, GPIO_PIN_12) == GPIO_PIN_RESET);
        }
    }
    else if (HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_0) == GPIO_PIN_RESET) {
        HAL_Delay(150);
        if (HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_0) == GPIO_PIN_RESET) {
            mppt_mode = 4; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            while(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_0) == GPIO_PIN_RESET);
        }
    }
    else if (HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_1) == GPIO_PIN_RESET) {
        HAL_Delay(150);
        if (HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_1) == GPIO_PIN_RESET) {
            mppt_mode = 5; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f;
            while(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_1) == GPIO_PIN_RESET);
        }
    }
    else if (HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_2) == GPIO_PIN_RESET) {
        HAL_Delay(150);
        if (HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_2) == GPIO_PIN_RESET) {
            mppt_mode = 0; is_running = 1; manual_duty = 0.0f; D_new = 0.0f;
            while(HAL_GPIO_ReadPin(GPIOD, GPIO_PIN_2) == GPIO_PIN_RESET);
        }
    }
}

void MPPT_LCD_Init(I2C_HandleTypeDef *hi2c, uint8_t address) {
    lcd_handle.hi2c    = hi2c;
    lcd_handle.address = address;
    lcd_init(&lcd_handle);
}

void MPPT_LCD_ShowStartup(void) {
    lcd_clear(&lcd_handle);
    lcd_puts(&lcd_handle, "Sistem Siap...");
}

void MPPT_SendData_UART(void) {
    float time_sec = HAL_GetTick() / 1000.0f;
    float v_in_local, i_in_local, p_in_local;
    float v_out_local, i_out_local, p_out_local;
    float eff_local, d_local;
    uint8_t mode_local;

    __disable_irq();
    v_in_local  = V_in;   i_in_local  = I_in;   p_in_local  = P_in;
    v_out_local = V_out;  i_out_local = I_out;  p_out_local = P_out;
    eff_local   = Eff_MPPT * 100.0f;
    d_local     = D_new;
    mode_local  = mppt_mode;
    __enable_irq();

    int len = snprintf(uart_tx_buf, sizeof(uart_tx_buf),
        "%.3f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.2f\t%.1f\t%d\t%.1f\r\n",
        time_sec, v_in_local, i_in_local, p_in_local,
        v_out_local, i_out_local, p_out_local,
        eff_local, (int)mode_local, d_local);

    if (len > 0) {
        HAL_UART_Transmit(&huart1, (uint8_t*)uart_tx_buf, len, 100);
    }
}

// --- FUNGSI PENERIMA PERINTAH DARI PYTHON ---
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART1) {
        if (rx_data[0] == '\n' || rx_data[0] == '\r') {
            rx_buffer[rx_index] = '\0';

            if (strcmp(rx_buffer, "MODE=0") == 0) {
                mppt_mode = 0; is_running = 1; manual_duty = 0.0f; D_new = 0.0f;
            }
            else if (strcmp(rx_buffer, "MODE=1") == 0) {
                mppt_mode = 1; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            }
            else if (strcmp(rx_buffer, "MODE=2") == 0) {
                mppt_mode = 2; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            }
            else if (strcmp(rx_buffer, "MODE=3") == 0) {
                mppt_mode = 3; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            }
            else if (strcmp(rx_buffer, "MODE=4") == 0) {
                mppt_mode = 4; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f; Reset_All_Algorithms();
            }
            else if (strcmp(rx_buffer, "MODE=5") == 0) {
                mppt_mode = 5; is_running = 1; algo_time_sec = 0.0f; global_time_sec = 0.0f;
            }

            rx_index = 0;
        } else {
            rx_buffer[rx_index++] = rx_data[0];
            if(rx_index >= 20) rx_index = 0;
        }
        HAL_UART_Receive_IT(&huart1, rx_data, 1);
    }
}
/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
