# ═══════════════════════════════════════════════════════════════
#   I2C SCANNER — ESP32 / Raspberry Pi Pico W
#   MicroPython  |  Standalone script — no other files needed
#
#   Scans the I2C bus and tries to identify every device found.
#   When multiple chips share an address, all are listed.
#   Optional deep scan reads ID registers to narrow down ambiguous hits.
#
#   Usage:
#     1. Upload this single file to the device
#     2. Open serial terminal (Thonny shell, mpremote, etc.)
#     3. >>> import i2c_scanner
#        or run directly: mpremote run i2c_scanner.py
# ═══════════════════════════════════════════════════════════════

from machine import I2C, Pin
import time

# ── Configuration ──────────────────────────────────────────────
SDA_PIN   = 21       # change for your board (Pico W: 4 or 6)
SCL_PIN   = 22       # change for your board (Pico W: 5 or 7)
I2C_FREQ  = 400_000  # 100_000 or 400_000 Hz
I2C_BUS   = 0        # 0 or 1  (Pico W: 0 or 1)
DEEP_SCAN = True     # read chip ID registers to disambiguate

# ── Chip Database ──────────────────────────────────────────────
# { address_int: [ (chip_name, category, description), ... ] }
# When multiple chips share an address ALL are listed.
# Addresses shown are the most common / default variant.

CHIP_DB = {

    # ── 0x00 – 0x0F  ───────────────────────────────────────────
    0x0B: [
        ("LC709203F",  "Battery",       "LiPo fuel gauge / state-of-charge monitor"),
    ],
    0x0C: [
        ("AK8963",     "Magnetometer",  "3-axis magnetometer (internal in MPU9250)"),
        ("MLX90393",   "Magnetometer",  "3-axis magnetometer, ADDR=00"),
        ("IST8310",    "Magnetometer",  "3-axis magnetometer"),
    ],
    0x0D: [
        ("QMC5883L",   "Magnetometer",  "3-axis magnetometer — HMC5883L clone"),
        ("MLX90393",   "Magnetometer",  "3-axis magnetometer, ADDR=01"),
    ],
    0x0E: [
        ("MLX90393",   "Magnetometer",  "3-axis magnetometer, ADDR=10"),
        ("IST8310",    "Magnetometer",  "3-axis magnetometer, alternate addr"),
    ],
    0x0F: [
        ("MLX90393",   "Magnetometer",  "3-axis magnetometer, ADDR=11"),
    ],

    # ── 0x10 – 0x1F  ───────────────────────────────────────────
    0x10: [
        ("VEML7700",   "Light",         "Ambient light sensor (lux)"),
        ("VEML3235",   "Light",         "Ultra-high sensitivity ambient light sensor"),
        ("VEML6075",   "UV",            "UVA and UVB light sensor"),
    ],
    0x11: [
        ("Si4713",     "Audio",         "FM radio transmitter with I2C control"),
        ("PMSA003I",   "Air Quality",   "Particulate matter air quality sensor"),
        ("VEML6030",   "Light",         "Ambient light sensor, ADDR=VCC"),
    ],
    0x12: [
        ("PMSA003I",   "Air Quality",   "Particulate matter sensor (alternate)"),
    ],
    0x14: [
        ("GT911",      "Touch",         "Capacitive touchscreen controller"),
    ],
    0x18: [
        ("MCP9808",    "Temperature",   "High-accuracy digital temperature sensor"),
        ("LIS3DH",     "Accelerometer", "3-axis MEMS accelerometer, ADDR=GND"),
        ("LIS3DE",     "Accelerometer", "3-axis accelerometer (industrial)"),
    ],
    0x19: [
        ("MCP9808",    "Temperature",   "High-accuracy temperature sensor, A2-A0=001"),
        ("LIS3DH",     "Accelerometer", "3-axis accelerometer, ADDR=VCC"),
        ("LSM303AGR",  "IMU",           "Accelerometer part of LSM303AGR combo"),
    ],
    0x1A: [
        ("AGS02MA",    "Gas",           "TVOC gas sensor"),
        ("MCP9808",    "Temperature",   "Temperature sensor, A2-A0=010"),
    ],
    0x1B: [
        ("AT42QT1070", "Touch",         "7-key capacitive touch sensor"),
        ("MCP9808",    "Temperature",   "Temperature sensor, A2-A0=011"),
    ],
    0x1C: [
        ("MAG3110",    "Magnetometer",  "3-axis digital magnetometer"),
        ("LSM303",     "Magnetometer",  "Magnetometer part of LSM303 combo"),
        ("MCP9808",    "Temperature",   "Temperature sensor, A2-A0=100"),
        ("FXOS8700",   "IMU",           "Accel + magnetometer combo"),
    ],
    0x1D: [
        ("ADXL345",    "Accelerometer", "3-axis digital accelerometer, ADDR=VCC"),
        ("MMA8451",    "Accelerometer", "3-axis 14-bit accelerometer"),
        ("MCP9808",    "Temperature",   "Temperature sensor, A2-A0=101"),
        ("FXOS8700",   "IMU",           "Accel + magnetometer combo, alt addr"),
    ],
    0x1E: [
        ("HMC5883L",   "Magnetometer",  "3-axis digital compass / magnetometer"),
        ("LIS2MDL",    "Magnetometer",  "3-axis magnetometer"),
        ("LSM303",     "Magnetometer",  "Magnetometer part of LSM303 combo (alt)"),
        ("MCP9808",    "Temperature",   "Temperature sensor, A2-A0=110"),
    ],
    0x1F: [
        ("MCP9808",    "Temperature",   "Temperature sensor, A2-A0=111 (max addr)"),
    ],

    # ── 0x20 – 0x2F  ───────────────────────────────────────────
    0x20: [
        ("PCF8574",    "IO Expander",   "8-bit I2C I/O expander, A2-A0=000"),
        ("MCP23008",   "IO Expander",   "8-bit I/O expander with interrupt, A2-A0=000"),
        ("MCP23017",   "IO Expander",   "16-bit I/O expander with interrupt, A2-A0=000"),
        ("PCA9555",    "IO Expander",   "16-bit I/O expander, A2-A0=000"),
        ("XL9535",     "IO Expander",   "16-bit I/O expander, A2-A0=000"),
    ],
    0x21: [
        ("PCF8574",    "IO Expander",   "8-bit I/O expander, A2-A0=001"),
        ("MCP23008",   "IO Expander",   "8-bit I/O expander, A2-A0=001"),
        ("MCP23017",   "IO Expander",   "16-bit I/O expander, A2-A0=001"),
        ("PCA9555",    "IO Expander",   "16-bit I/O expander, A2-A0=001"),
    ],
    0x22: [
        ("PCF8574",    "IO Expander",   "8-bit I/O expander, A2-A0=010"),
        ("MCP23008",   "IO Expander",   "8-bit I/O expander, A2-A0=010"),
        ("MCP23017",   "IO Expander",   "16-bit I/O expander, A2-A0=010"),
    ],
    0x23: [
        ("PCF8574",    "IO Expander",   "8-bit I/O expander, A2-A0=011"),
        ("MCP23008",   "IO Expander",   "8-bit I/O expander, A2-A0=011"),
        ("BH1750",     "Light",         "Digital ambient light sensor, ADDR=GND"),
    ],
    0x24: [
        ("PCF8574",    "IO Expander",   "8-bit I/O expander, A2-A0=100"),
        ("MCP23017",   "IO Expander",   "16-bit I/O expander, A2-A0=100"),
    ],
    0x25: [
        ("PCF8574",    "IO Expander",   "8-bit I/O expander, A2-A0=101"),
        ("MCP23017",   "IO Expander",   "16-bit I/O expander, A2-A0=101"),
    ],
    0x26: [
        ("PCF8574",    "IO Expander",   "8-bit I/O expander, A2-A0=110"),
        ("MCP23017",   "IO Expander",   "16-bit I/O expander, A2-A0=110"),
    ],
    0x27: [
        ("PCF8574",    "IO Expander",   "8-bit I/O expander, A2-A0=111"),
        ("MCP23017",   "IO Expander",   "16-bit I/O expander, A2-A0=111 (most common LCD backpack addr)"),
    ],
    0x28: [
        ("BNO055",     "IMU",           "9-axis absolute orientation sensor, ADDR=GND"),
        ("STUSB4500",  "USB-PD",        "USB Power Delivery controller"),
        ("CAP1188",    "Touch",         "8-channel capacitive touch, ADDR=GND"),
    ],
    0x29: [
        ("BNO055",     "IMU",           "9-axis absolute orientation, ADDR=VCC"),
        ("VL53L0X",    "Distance",      "Time-of-flight distance sensor 0-2m"),
        ("VL53L1X",    "Distance",      "Time-of-flight distance sensor 0-4m"),
        ("VL6180X",    "Distance",      "Time-of-flight proximity + ALS sensor"),
        ("TSL2561",    "Light",         "IR + full-spectrum light sensor, ADDR=GND"),
        ("TCS34725",   "Color",         "RGB + clear color sensor"),
        ("AS7341",     "Spectral",      "11-channel spectral color sensor"),
    ],
    0x2A: [
        ("NAU7802",    "ADC",           "24-bit ADC for load cells (Sparkfun Qwiic scale)"),
    ],
    0x2B: [
        ("CAP1188",    "Touch",         "8-channel capacitive touch, ADDR=010"),
    ],
    0x2C: [
        ("CAP1188",    "Touch",         "8-channel capacitive touch, ADDR=100"),
    ],
    0x2D: [
        ("CAP1188",    "Touch",         "8-channel capacitive touch, ADDR=VCC"),
    ],

    # ── 0x36 – 0x3F  ───────────────────────────────────────────
    0x36: [
        ("MAX17043",   "Battery",       "1-cell LiPo fuel gauge"),
        ("MAX17048",   "Battery",       "1-2 cell LiPo fuel gauge"),
    ],
    0x38: [
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=000"),
        ("AHT10",      "Temp/Humidity", "Temperature & humidity sensor (older)"),
        ("AHT20",      "Temp/Humidity", "Temperature & humidity sensor"),
        ("AHT21",      "Temp/Humidity", "Temperature & humidity sensor"),
        ("FT6236",     "Touch",         "Capacitive touchscreen controller"),
        ("FT6206",     "Touch",         "Capacitive touchscreen controller"),
    ],
    0x39: [
        ("TSL2561",    "Light",         "IR + full-spectrum light sensor, ADDR=float"),
        ("APDS9960",   "Gesture",       "RGB, gesture, proximity, and ALS sensor"),
        ("AS7341",     "Spectral",      "11-channel spectral color sensor, alternate"),
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=001"),
    ],
    0x3A: [
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=010"),
    ],
    0x3B: [
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=011"),
    ],
    0x3C: [
        ("SSD1306",    "Display",       "0.96\"/1.3\" OLED controller, ADDR=GND (most common)"),
        ("SH1106",     "Display",       "1.3\" OLED controller, ADDR=GND"),
        ("SSD1327",    "Display",       "128x128 greyscale OLED controller"),
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=100"),
    ],
    0x3D: [
        ("SSD1306",    "Display",       "OLED controller, ADDR=VCC"),
        ("SH1106",     "Display",       "1.3\" OLED controller, ADDR=VCC"),
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=101"),
    ],
    0x3E: [
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=110"),
        ("SX1509",     "IO Expander",   "16-bit I/O expander with LED driver, ADDR=00"),
    ],
    0x3F: [
        ("PCF8574A",   "IO Expander",   "8-bit I/O expander variant, A2-A0=111"),
        ("SX1509",     "IO Expander",   "16-bit I/O expander with LED driver, ADDR=01"),
    ],

    # ── 0x40 – 0x4F  ───────────────────────────────────────────
    0x40: [
        ("INA219",     "Power",         "Current/power monitor, A1=A0=GND"),
        ("INA260",     "Power",         "Precision current/power monitor"),
        ("INA3221",    "Power",         "3-channel current/power monitor"),
        ("PCA9685",    "PWM",           "16-channel 12-bit PWM / servo driver, A5-A0=000000"),
        ("HDC1080",    "Temp/Humidity", "Temperature & humidity sensor"),
        ("HTU21D",     "Temp/Humidity", "Humidity & temperature sensor"),
        ("SHT21",      "Temp/Humidity", "Humidity & temperature sensor"),
        ("SI7021",     "Temp/Humidity", "Temperature & humidity sensor"),
        ("TMP007",     "Temperature",   "IR thermopile temperature sensor"),
    ],
    0x41: [
        ("INA219",     "Power",         "Current/power monitor, A1=GND A0=VCC"),
        ("INA260",     "Power",         "Precision current/power monitor, alt addr"),
        ("INA3221",    "Power",         "3-channel power monitor, A1=GND A0=VS"),
        ("TMP007",     "Temperature",   "IR thermopile sensor, A2-A0=001"),
    ],
    0x42: [
        ("INA219",     "Power",         "Current/power monitor, A1=VCC A0=GND"),
        ("INA260",     "Power",         "Precision current/power monitor, alt addr"),
    ],
    0x43: [
        ("INA219",     "Power",         "Current/power monitor, A1=A0=VCC"),
        ("INA260",     "Power",         "Precision current/power monitor, alt addr"),
        ("INA3221",    "Power",         "3-channel power monitor, A1=VS A0=GND"),
    ],
    0x44: [
        ("SHT31",      "Temp/Humidity", "High-accuracy temp & humidity, ADDR=GND (default)"),
        ("SHT30",      "Temp/Humidity", "Temperature & humidity sensor"),
        ("SHT35",      "Temp/Humidity", "High-precision temp & humidity"),
        ("OPT3001",    "Light",         "Precision ambient light sensor, A1=A0=GND"),
        ("TMP006",     "Temperature",   "IR thermopile contactless temp sensor"),
    ],
    0x45: [
        ("SHT31",      "Temp/Humidity", "High-accuracy temp & humidity, ADDR=VCC"),
        ("SHT30",      "Temp/Humidity", "Temperature & humidity, alt addr"),
        ("OPT3001",    "Light",         "Precision ambient light, A1=GND A0=VCC"),
    ],
    0x46: [
        ("OPT3001",    "Light",         "Precision ambient light, A1=VCC A0=GND"),
    ],
    0x47: [
        ("OPT3001",    "Light",         "Precision ambient light, A1=A0=VCC"),
    ],
    0x48: [
        ("ADS1115",    "ADC",           "16-bit 4-ch ADC with PGA, ADDR=GND"),
        ("ADS1015",    "ADC",           "12-bit 4-ch ADC with PGA, ADDR=GND"),
        ("ADS1100",    "ADC",           "16-bit single-ch self-calibrating ADC"),
        ("PCF8591",    "ADC/DAC",       "8-bit 4-ch ADC + 1-ch DAC, A2-A0=000"),
        ("LM75",       "Temperature",   "Digital temperature sensor, A2-A0=000"),
        ("TMP102",     "Temperature",   "Tiny digital temperature sensor, ADD0=GND"),
        ("TMP117",     "Temperature",   "High-precision digital temp sensor, ADD0=GND"),
        ("MAX31725",   "Temperature",   "Low-power digital temp sensor"),
        ("MAX31726",   "Temperature",   "Digital temp sensor with alert"),
    ],
    0x49: [
        ("ADS1115",    "ADC",           "16-bit 4-ch ADC, ADDR=VCC"),
        ("ADS1015",    "ADC",           "12-bit 4-ch ADC, ADDR=VCC"),
        ("ADS1100",    "ADC",           "Single-ch ADC, factory addr variant"),
        ("PCF8591",    "ADC/DAC",       "8-bit ADC/DAC, A2-A0=001"),
        ("LM75",       "Temperature",   "Digital temperature sensor, A2-A0=001"),
        ("TMP102",     "Temperature",   "Digital temperature sensor, ADD0=VCC"),
        ("TMP117",     "Temperature",   "High-precision temp sensor, ADD0=VCC"),
        ("TSL2561",    "Light",         "IR + full-spectrum light, ADDR=VCC"),
    ],
    0x4A: [
        ("ADS1115",    "ADC",           "16-bit 4-ch ADC, ADDR=SDA"),
        ("ADS1015",    "ADC",           "12-bit 4-ch ADC, ADDR=SDA"),
        ("BNO080",     "IMU",           "9-axis IMU with sensor fusion, ADDR=GND"),
        ("MAX44009",   "Light",         "Ultra-low power ambient light, ADDR=GND"),
        ("PCF8591",    "ADC/DAC",       "8-bit ADC/DAC, A2-A0=010"),
        ("TMP117",     "Temperature",   "High-precision temp sensor, ADD0=SDA"),
    ],
    0x4B: [
        ("ADS1115",    "ADC",           "16-bit 4-ch ADC, ADDR=SCL"),
        ("ADS1015",    "ADC",           "12-bit 4-ch ADC, ADDR=SCL"),
        ("BNO080",     "IMU",           "9-axis IMU with sensor fusion, ADDR=VCC"),
        ("MAX44009",   "Light",         "Ultra-low power ambient light, ADDR=VCC"),
        ("PCF8591",    "ADC/DAC",       "8-bit ADC/DAC, A2-A0=011"),
        ("TMP117",     "Temperature",   "High-precision temp sensor, ADD0=SCL"),
    ],
    0x4C: [
        ("PCF8591",    "ADC/DAC",       "8-bit ADC/DAC, A2-A0=100"),
        ("ADS1100",    "ADC",           "Single-ch 16-bit ADC, factory addr"),
        ("EMC1001",    "Temperature",   "CPU temperature monitor"),
    ],
    0x4D: [
        ("ADS1100",    "ADC",           "Single-ch 16-bit ADC, factory addr"),
        ("MCP3221",    "ADC",           "12-bit single-ch I2C ADC"),
        ("PCF8591",    "ADC/DAC",       "8-bit ADC/DAC, A2-A0=101"),
    ],
    0x4E: [
        ("ADS1100",    "ADC",           "Single-ch ADC, factory addr"),
        ("PCF8591",    "ADC/DAC",       "8-bit ADC/DAC, A2-A0=110"),
    ],
    0x4F: [
        ("ADS1100",    "ADC",           "Single-ch ADC, factory addr"),
        ("PCF8591",    "ADC/DAC",       "8-bit ADC/DAC, A2-A0=111"),
        ("LM75",       "Temperature",   "Digital temperature sensor, A2-A0=111"),
    ],

    # ── 0x50 – 0x5F  ───────────────────────────────────────────
    0x50: [
        ("AT24C02",    "EEPROM",        "2Kbit I2C EEPROM, A2-A0=000"),
        ("AT24C32",    "EEPROM",        "32Kbit I2C EEPROM (on DS3231 RTC modules)"),
        ("M24C32",     "EEPROM",        "32Kbit I2C EEPROM, E2-E0=000"),
    ],
    0x51: [
        ("AT24Cxx",    "EEPROM",        "I2C EEPROM, A2-A0=001"),
        ("PCF8563",    "RTC",           "Real-time clock / calendar"),
        ("M24C32",     "EEPROM",        "32Kbit EEPROM, E2-E0=001"),
    ],
    0x52: [
        ("AT24Cxx",    "EEPROM",        "I2C EEPROM, A2-A0=010"),
        ("ENS160",     "Air Quality",   "Digital TVOC / eCO2 / AQI sensor"),
        ("RV3028",     "RTC",           "Extreme low power RTC module"),
    ],
    0x53: [
        ("AT24Cxx",    "EEPROM",        "I2C EEPROM, A2-A0=011"),
        ("ADXL345",    "Accelerometer", "3-axis digital accelerometer, ADDR=GND (default)"),
        ("ENS160",     "Air Quality",   "TVOC/eCO2 sensor, ADDR=VCC"),
    ],
    0x54: [
        ("AT24Cxx",    "EEPROM",        "I2C EEPROM, A2-A0=100"),
    ],
    0x55: [
        ("AT24Cxx",    "EEPROM",        "I2C EEPROM, A2-A0=101"),
        ("BQ27441",    "Battery",       "Single-cell LiPo fuel gauge"),
        ("BQ27421",    "Battery",       "Single-cell LiPo fuel gauge (smaller)"),
    ],
    0x56: [
        ("AT24Cxx",    "EEPROM",        "I2C EEPROM, A2-A0=110"),
    ],
    0x57: [
        ("AT24Cxx",    "EEPROM",        "I2C EEPROM, A2-A0=111"),
        ("MAX30102",   "Biosensor",     "Pulse oximeter and heart rate sensor"),
        ("MAX30105",   "Biosensor",     "Particle and biometric sensor"),
    ],
    0x58: [
        ("SGP30",      "Air Quality",   "TVOC and eCO2 air quality sensor"),
    ],
    0x59: [
        ("SGP40",      "Air Quality",   "TVOC index sensor for indoor air quality"),
    ],
    0x5A: [
        ("CCS811",     "Air Quality",   "TVOC / eCO2 sensor, ADDR=GND"),
        ("MPR121",     "Touch",         "12-channel capacitive touch sensor, ADD=GND"),
        ("MLX90614",   "Temperature",   "IR contactless temperature sensor, default"),
    ],
    0x5B: [
        ("CCS811",     "Air Quality",   "TVOC / eCO2 sensor, ADDR=VCC"),
        ("MPR121",     "Touch",         "12-channel capacitive touch sensor, ADD=VCC"),
        ("MLX90614",   "Temperature",   "IR contactless temp sensor, alt addr"),
    ],
    0x5C: [
        ("MPR121",     "Touch",         "12-channel capacitive touch, ADD=SDA"),
        ("BH1750",     "Light",         "Digital ambient light sensor, ADDR=VCC"),
        ("LPS22HB",    "Pressure",      "Barometric pressure & temp sensor, SA0=GND"),
        ("LPS25HB",    "Pressure",      "MEMS pressure sensor, SA0=GND"),
        ("LPS33HW",    "Pressure",      "Water resistant pressure sensor"),
    ],
    0x5D: [
        ("MPR121",     "Touch",         "12-channel capacitive touch, ADD=SCL"),
        ("GT911",      "Touch",         "Capacitive touchscreen controller, alt addr"),
        ("LPS22HB",    "Pressure",      "Barometric pressure sensor, SA0=VCC"),
        ("LPS25HB",    "Pressure",      "MEMS pressure sensor, SA0=VCC"),
    ],

    # ── 0x60 – 0x6F  ───────────────────────────────────────────
    0x60: [
        ("MCP4725",    "DAC",           "12-bit single-ch DAC, A2-A0=000 (default)"),
        ("MPL3115A2",  "Pressure",      "Precision barometric pressure / altitude"),
        ("Si5351",     "Clock",         "Programmable clock generator, ADDR=GND"),
        ("SI1145",     "Light/UV",      "Digital UV index / IR / visible light sensor"),
        ("DRV8830",    "Motor",         "I2C motor driver, ADDR=GND"),
    ],
    0x61: [
        ("MCP4725",    "DAC",           "12-bit DAC, A2-A0=001"),
        ("SCD30",      "Gas",           "NDIR CO2 / temperature / humidity sensor"),
        ("Si5351",     "Clock",         "Programmable clock generator, ADDR=VCC"),
    ],
    0x62: [
        ("MCP4725",    "DAC",           "12-bit DAC, A2-A0=010"),
        ("SCD40",      "Gas",           "Miniature CO2 / temp / humidity sensor"),
        ("SCD41",      "Gas",           "CO2 / temp / humidity sensor, extended range"),
    ],
    0x63: [
        ("MCP4725",    "DAC",           "12-bit DAC, A2-A0=011"),
        ("Si4713",     "Audio",         "FM radio transmitter, alternate addr"),
    ],
    0x68: [
        ("MPU6050",    "IMU",           "6-axis accel + gyro, AD0=GND (most common)"),
        ("MPU6500",    "IMU",           "6-axis accel + gyro (newer die), AD0=GND"),
        ("MPU9250",    "IMU",           "9-axis accel + gyro + mag, AD0=GND"),
        ("ICM20948",   "IMU",           "9-axis IMU, AD0=GND"),
        ("DS3231",     "RTC",           "Extremely accurate I2C RTC with temp sensor"),
        ("DS1307",     "RTC",           "Real-time clock (5V, no temp sensor)"),
        ("PCF8523",    "RTC",           "Real-time clock with power management"),
        ("DS1337",     "RTC",           "Real-time clock compatible with DS1307"),
        ("MCP342x",    "ADC",           "18-bit delta-sigma ADC, default addr"),
        ("L3G4200D",   "Gyroscope",     "3-axis MEMS gyroscope"),
        ("ITG3205",    "Gyroscope",     "3-axis MEMS gyroscope (SparkFun breakout)"),
    ],
    0x69: [
        ("MPU6050",    "IMU",           "6-axis accel + gyro, AD0=VCC"),
        ("MPU9250",    "IMU",           "9-axis IMU, AD0=VCC"),
        ("ICM20948",   "IMU",           "9-axis IMU, AD0=VCC"),
        ("SEN55",      "Air Quality",   "Particulate + NOx + VOC + RH/T sensor"),
        ("L3G4200D",   "Gyroscope",     "3-axis gyroscope, SDO=VCC"),
    ],
    0x6A: [
        ("LSM6DS3",    "IMU",           "6-axis accel + gyro, SA0=GND"),
        ("LSM6DSOX",   "IMU",           "6-axis IMU with ML core, SA0=GND"),
        ("LSM6DSL",    "IMU",           "6-axis IMU with step counter, SA0=GND"),
        ("ICM42688",   "IMU",           "6-axis high-performance IMU"),
    ],
    0x6B: [
        ("LSM6DS3",    "IMU",           "6-axis accel + gyro, SA0=VCC"),
        ("LSM6DSOX",   "IMU",           "6-axis IMU with ML core, SA0=VCC"),
        ("LSM6DSL",    "IMU",           "6-axis IMU, SA0=VCC"),
    ],
    0x6F: [
        ("MCP7940N",   "RTC",           "Real-time clock with SRAM and battery switchover"),
        ("MCP7941x",   "RTC",           "RTC with pre-programmed EUI-48/64 MAC"),
        ("MCP342x",    "ADC",           "18-bit ADC, A2-A1-A0=111"),
    ],

    # ── 0x70 – 0x77  ───────────────────────────────────────────
    0x70: [
        ("HT16K33",    "Display",       "LED matrix driver / 16-key scanner, A2-A0=000"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C multiplexer, A2-A0=000"),
        ("PCA9547",    "I2C Mux",       "8-channel I2C mux with reset, A2-A0=000"),
        ("SX1509",     "IO Expander",   "16-bit I/O expander, ADDR=10"),
    ],
    0x71: [
        ("HT16K33",    "Display",       "LED matrix driver, A2-A0=001"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C mux, A2-A0=001"),
        ("SX1509",     "IO Expander",   "16-bit I/O expander, ADDR=11"),
    ],
    0x72: [
        ("HT16K33",    "Display",       "LED matrix driver, A2-A0=010"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C mux, A2-A0=010"),
    ],
    0x73: [
        ("HT16K33",    "Display",       "LED matrix driver, A2-A0=011"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C mux, A2-A0=011"),
    ],
    0x74: [
        ("HT16K33",    "Display",       "LED matrix driver, A2-A0=100"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C mux, A2-A0=100"),
    ],
    0x75: [
        ("HT16K33",    "Display",       "LED matrix driver, A2-A0=101"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C mux, A2-A0=101"),
    ],
    0x76: [
        ("BME280",     "Env",           "Barometric pressure + humidity + temp, SDO=GND"),
        ("BMP280",     "Env",           "Barometric pressure + temp, SDO=GND"),
        ("BME680",     "Env/Gas",       "Pressure + humidity + temp + VOC gas, SDO=GND"),
        ("BME688",     "Env/Gas",       "BME680 with AI + gas sensor, SDO=GND"),
        ("BMP388",     "Pressure",      "High-precision pressure + temp, SDO=GND"),
        ("DPS310",     "Pressure",      "Barometric pressure sensor, SDO=GND"),
        ("MS5611",     "Pressure",      "High-res barometric pressure sensor, CSB=GND"),
        ("HT16K33",    "Display",       "LED matrix driver, A2-A0=110"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C mux, A2-A0=110"),
    ],
    0x77: [
        ("BME280",     "Env",           "Pressure + humidity + temp, SDO=VCC (default on many modules)"),
        ("BMP280",     "Env",           "Pressure + temp, SDO=VCC (default on many modules)"),
        ("BMP180",     "Pressure",      "Barometric pressure + temp (older, 5V-tolerant)"),
        ("BMP085",     "Pressure",      "Barometric pressure + temp (older, original)"),
        ("BME680",     "Env/Gas",       "Pressure + humidity + temp + VOC, SDO=VCC"),
        ("BME688",     "Env/Gas",       "BME680 with AI, SDO=VCC"),
        ("BMP388",     "Pressure",      "High-precision pressure + temp, SDO=VCC"),
        ("DPS310",     "Pressure",      "Barometric pressure sensor, SDO=VCC"),
        ("MS5611",     "Pressure",      "High-res barometric pressure, CSB=VCC"),
        ("HT16K33",    "Display",       "LED matrix driver, A2-A0=111"),
        ("TCA9548A",   "I2C Mux",       "8-channel I2C mux, A2-A0=111"),
    ],
}

# ── Deep Scan Probes ───────────────────────────────────────────
# { address: [ (register, expected_byte, chip_name_confirmed), ... ] }
# Probes are tried in order; first match wins.
# Reading a wrong register is generally safe — data is just unexpected.

CHIP_PROBES = {
    0x0C: [(0x00, 0x48, "AK8963 (magnetometer)")],
    0x19: [(0x0F, 0x33, "LIS3DH")],
    0x1D: [(0x00, 0xE5, "ADXL345")],
    0x18: [(0x0F, 0x33, "LIS3DH (ADDR=GND)")],
    0x28: [(0x00, 0xA0, "BNO055")],
    0x29: [
        (0x00, 0xA0, "BNO055"),
        (0x0F, 0x2A, "VL53L0X/VL53L1X (read model register instead)"),
    ],
    0x53: [(0x00, 0xE5, "ADXL345")],
    0x68: [
        (0x75, 0x68, "MPU6050"),
        (0x75, 0x70, "MPU6500"),
        (0x75, 0x71, "MPU9250"),
        (0x75, 0x72, "MPU6050 (variant)"),
        (0x75, 0x19, "ICM20948"),
    ],
    0x69: [
        (0x75, 0x68, "MPU6050 (AD0=HIGH)"),
        (0x75, 0x71, "MPU9250 (AD0=HIGH)"),
        (0x75, 0x19, "ICM20948 (AD0=HIGH)"),
    ],
    0x6A: [
        (0x0F, 0x69, "LSM6DS3"),
        (0x0F, 0x6C, "LSM6DSOX"),
        (0x0F, 0x6B, "LSM6DSL"),
        (0x0F, 0x6A, "LSM6DS33"),
    ],
    0x6B: [
        (0x0F, 0x69, "LSM6DS3 (SA0=VCC)"),
        (0x0F, 0x6C, "LSM6DSOX (SA0=VCC)"),
    ],
    0x76: [
        (0xD0, 0x60, "BME280"),
        (0xD0, 0x58, "BMP280"),
        (0xD0, 0x56, "BME280 (engineering sample)"),
        (0xD0, 0x61, "BME680 / BME688"),
        (0xD0, 0x50, "BMP388"),
    ],
    0x77: [
        (0xD0, 0x60, "BME280"),
        (0xD0, 0x58, "BMP280"),
        (0xD0, 0x55, "BMP180"),
        (0xD0, 0x54, "BMP085"),
        (0xD0, 0x61, "BME680 / BME688"),
        (0xD0, 0x50, "BMP388"),
    ],
}


# ═══════════════════════════════════════════════════════════════
#   OUTPUT HELPERS
# ═══════════════════════════════════════════════════════════════
W = 62   # total line width

def _line(char="-"):
    print(char * W)

def _title(text):
    pad = (W - len(text) - 2) // 2
    print("=" * W)
    print("=" + " " * pad + text + " " * (W - len(text) - pad - 2) + "=")
    print("=" * W)

def _header(text):
    print()
    print("-" * W)
    print("  " + text)
    print("-" * W)

def _kv(key, value, indent=2):
    print(f"{' ' * indent}{key:<14}{value}")


# ═══════════════════════════════════════════════════════════════
#   PROBE — Read one register byte from a device
# ═══════════════════════════════════════════════════════════════
def _read_reg(i2c, addr, reg):
    """
    Safely read one byte from `reg` on device `addr`.
    Returns the byte value or None on error.
    """
    try:
        i2c.writeto(addr, bytes([reg]))
        result = i2c.readfrom(addr, 1)
        return result[0]
    except Exception:
        return None


def _probe_chip(i2c, addr):
    """
    Try each probe for `addr`. Returns confirmed name string or None.
    """
    probes = CHIP_PROBES.get(addr)
    if not probes:
        return None
    for (reg, expected, name) in probes:
        val = _read_reg(i2c, addr, reg)
        if val is not None and val == expected:
            return name
    return None


# ═══════════════════════════════════════════════════════════════
#   MAIN SCANNER
# ═══════════════════════════════════════════════════════════════
def scan():
    """Run the full I2C scan and print results."""

    # ── Init I2C ───────────────────────────────────────────────
    try:
        i2c = I2C(I2C_BUS, sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=I2C_FREQ)
    except Exception as e:
        print(f"I2C init failed: {e}")
        print(f"Check SDA_PIN={SDA_PIN}, SCL_PIN={SCL_PIN}, I2C_BUS={I2C_BUS}")
        return

    # ── Header ────────────────────────────────────────────────
    print()
    _title("I2C SCANNER")
    print()
    _kv("SDA pin:", f"GPIO {SDA_PIN}")
    _kv("SCL pin:", f"GPIO {SCL_PIN}")
    _kv("Frequency:", f"{I2C_FREQ // 1000} kHz")
    _kv("Deep scan:", "ON  (reading ID registers)" if DEEP_SCAN else "OFF")
    print()

    # ── Scan ──────────────────────────────────────────────────
    print("Scanning addresses 0x08 – 0x77 ...")
    time.sleep_ms(100)

    try:
        found = i2c.scan()
    except Exception as e:
        print(f"Scan failed: {e}")
        return

    print()

    if not found:
        print("  No devices found.")
        print()
        print("  Troubleshooting tips:")
        print("  - Check SDA/SCL wiring and pull-up resistors (4.7 kΩ to 3.3V)")
        print("  - Verify device power supply")
        print("  - Some chips need time after power-on — try a 500 ms delay")
        print()
        return

    # ── Address summary ────────────────────────────────────────
    addr_strs = "  ".join(f"0x{a:02X}" for a in found)
    print(f"  Found {len(found)} device(s):  {addr_strs}")

    # ── Per-device details ────────────────────────────────────
    for addr in found:
        _header(f"Address: 0x{addr:02X}  (decimal: {addr})")

        # Deep scan (optional)
        confirmed = None
        if DEEP_SCAN:
            confirmed = _probe_chip(i2c, addr)

        if confirmed:
            print(f"  IDENTIFIED  : {confirmed}")
            print(f"  ID register : matched — high confidence")
        else:
            # Look up all possible chips
            chips = CHIP_DB.get(addr, [])

            if not chips:
                print("  Status      : UNKNOWN address")
                print("  Note        : Not in the chip database.")
                print("                Could be a custom device, unusual config,")
                print("                or a chip variant not yet listed.")
            else:
                categories = sorted(set(c[1] for c in chips))
                print(f"  Category    : {' / '.join(categories)}")

                if len(chips) == 1:
                    name, _, desc = chips[0]
                    print(f"  Chip        : {name}")
                    print(f"  Description : {desc}")
                else:
                    print(f"  Possibilities ({len(chips)}):")
                    for (name, cat, desc) in chips:
                        # Truncate description if too long
                        if len(desc) > 40:
                            desc = desc[:38] + ".."
                        print(f"    {name:<16} [{cat}]  {desc}")

                # Suggest probe if available
                if CHIP_PROBES.get(addr) and not confirmed:
                    print(f"  Deep scan   : ran — could not confirm (ID mismatch or not applicable)")
                elif not DEEP_SCAN and CHIP_PROBES.get(addr):
                    print(f"  Tip         : Set DEEP_SCAN = True to narrow down this address")

    # ── Summary ───────────────────────────────────────────────
    print()
    _line("=")
    known   = sum(1 for a in found if a in CHIP_DB)
    unknown = len(found) - known
    print(f"  Total found : {len(found)}")
    print(f"  Identified  : {known}  |  Unknown: {unknown}")
    print(f"  DB entries  : {len(CHIP_DB)} addresses  /  "
          f"{sum(len(v) for v in CHIP_DB.values())} chip variants")
    _line("=")
    print()

    # ── Copy-paste code snippet ────────────────────────────────
    if found:
        print("  Quick import snippet for your sensors.py:")
        print()
        print(f"  from machine import I2C, Pin")
        print(f"  i2c = I2C({I2C_BUS}, sda=Pin({SDA_PIN}), scl=Pin({SCL_PIN}), freq=400_000)")
        print(f"  # Detected: " + ", ".join(f"0x{a:02X}" for a in found))
        print()


# ── Run immediately when imported or executed ──────────────────
scan()
