# I2C Scanner

MicroPython script for **ESP32** and **Raspberry Pi Pico W**. Scans the I2C bus, lists every detected device, and attempts to identify the chip by address and optionally by reading its ID register.

## Features

- Scans all standard I2C addresses (0x08 – 0x77)
- Database of **100+ chip variants** across IMUs, sensors, displays, ADCs, EEPROMs, RTCs, and more
- **Deep scan** mode reads ID registers to disambiguate addresses shared by multiple chips (e.g. MPU6050 vs MPU9250 vs ICM20948 at 0x68)
- Prints a ready-to-use `I2C(...)` code snippet at the end

## Configuration

Edit the constants at the top of the file:

| Constant | Default | Description |
|---|---|---|
| `SDA_PIN` | `21` | GPIO for SDA (Pico W: 4 or 6) |
| `SCL_PIN` | `22` | GPIO for SCL (Pico W: 5 or 7) |
| `I2C_FREQ` | `400_000` | Bus frequency in Hz (`100_000` or `400_000`) |
| `I2C_BUS` | `0` | Hardware I2C bus index (`0` or `1`) |
| `DEEP_SCAN` | `True` | Read chip ID registers for high-confidence identification |

## Usage

Upload the single file to the device — no other files needed.

```python
# In Thonny shell or mpremote REPL:
import i2c_scanner

# Or run directly from your PC:
# mpremote run i2c_scanner.py
```

The script runs automatically on import and prints results to the serial terminal.

## Example Output

```
==============================================================
=                      I2C SCANNER                          =
==============================================================

  SDA pin:      GPIO 21
  SCL pin:      GPIO 22
  Frequency:    400 kHz
  Deep scan:    ON  (reading ID registers)

Scanning addresses 0x08 – 0x77 ...

  Found 2 device(s):  0x3C  0x68

  ------------------------------------------------------------
  Address: 0x3C  (decimal: 60)
  ------------------------------------------------------------
  Category    : Display
  Chip        : SSD1306
  Description : 0.96"/1.3" OLED controller, ADDR=GND

  ------------------------------------------------------------
  Address: 0x68  (decimal: 104)
  ------------------------------------------------------------
  IDENTIFIED  : MPU6050
  ID register : matched — high confidence
```

## Troubleshooting

If no devices are found:
- Check SDA/SCL wiring and add 4.7 kΩ pull-up resistors to 3.3 V
- Verify the device power supply
- Some chips need time after power-on — add a `time.sleep_ms(500)` before importing
