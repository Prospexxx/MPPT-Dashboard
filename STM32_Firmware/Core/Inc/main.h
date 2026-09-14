/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2025 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f4xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */

/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

void HAL_TIM_MspPostInit(TIM_HandleTypeDef *htim);

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define RELAY1_Pin GPIO_PIN_8
#define RELAY1_GPIO_Port GPIOD
#define RELAY2_Pin GPIO_PIN_9
#define RELAY2_GPIO_Port GPIOD
#define RELAY3_Pin GPIO_PIN_10
#define RELAY3_GPIO_Port GPIOD
#define RELAY4_Pin GPIO_PIN_11
#define RELAY4_GPIO_Port GPIOD
#define BUZZER_Pin GPIO_PIN_15
#define BUZZER_GPIO_Port GPIOA
#define PB1_Pin GPIO_PIN_10
#define PB1_GPIO_Port GPIOC
#define PB2_Pin GPIO_PIN_11
#define PB2_GPIO_Port GPIOC
#define PB3_Pin GPIO_PIN_12
#define PB3_GPIO_Port GPIOC
#define PB4_Pin GPIO_PIN_0
#define PB4_GPIO_Port GPIOD
#define PB5_Pin GPIO_PIN_1
#define PB5_GPIO_Port GPIOD
#define PB6_Pin GPIO_PIN_2
#define PB6_GPIO_Port GPIOD
#define LED_1_Pin GPIO_PIN_3
#define LED_1_GPIO_Port GPIOD
#define LED_2_Pin GPIO_PIN_4
#define LED_2_GPIO_Port GPIOD
#define LED_3_Pin GPIO_PIN_5
#define LED_3_GPIO_Port GPIOD
#define LED_4_Pin GPIO_PIN_6
#define LED_4_GPIO_Port GPIOD
#define LED_5_Pin GPIO_PIN_7
#define LED_5_GPIO_Port GPIOD
#define LED_6_Pin GPIO_PIN_3
#define LED_6_GPIO_Port GPIOB

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
