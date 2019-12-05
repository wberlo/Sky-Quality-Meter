# Sky-Quality-Meter
A sky quality meter using the ESP32 and TSL2591

Programmed in microPython using Thonny

The TSL library was stripped of most functionality, and only uses a read function with automatic gain and timing adjustment. This will provide the largest possible dynamic range.

I avoided the 100 ms integration time since this has a lower maximum reading (32k vs 65k)

The sky quality meter is not calibrated yet. Calibration should be done by adjusting the GA parameter in main.py.
The device uses I2C, connected to pins 4 (SDA) and 5 (SCL) on the ESP32.
