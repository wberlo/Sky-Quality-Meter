# tsl2591 lux sensor interface

import time

VISIBLE = 2
INFRARED = 1
FULLSPECTRUM = 0

# ADDR = 0x29
SENSOR_ADDRESS=0x29
READBIT = 0x01
COMMAND_BIT = 0xA0
CLEAR_BIT = 0x40
WORD_BIT = 0x20
BLOCK_BIT = 0x10
ENABLE_POWERON = 0x01
ENABLE_POWEROFF = 0x00
ENABLE_AEN = 0x02
ENABLE_AIEN = 0x10
CONTROL_RESET = 0x80
SDA_PIN= 4
SCL_PIN = 5
# 
LUX_DF = 408.0
# 
# My value of LUX_DF
#LUX_DF = 4080.0
LUX_COEFB = 1.64
LUX_COEFC = 0.59
LUX_COEFD = 0.86

UP = 1
DOWN = 0

REGISTER_ENABLE = 0x00
REGISTER_CONTROL = 0x01
REGISTER_THRESHHOLDL_LOW = 0x02
REGISTER_THRESHHOLDL_HIGH = 0x03
REGISTER_THRESHHOLDH_LOW = 0x04
REGISTER_THRESHHOLDH_HIGH = 0x05
REGISTER_INTERRUPT = 0x06
REGISTER_CRC = 0x08
REGISTER_ID = 0x0A
REGISTER_CHAN0_LOW = 0x14
REGISTER_CHAN0_HIGH = 0x15
REGISTER_CHAN1_LOW = 0x16
REGISTER_CHAN1_HIGH = 0x17
INTEGRATIONTIME_100MS = 0x00
INTEGRATIONTIME_200MS = 0x01
INTEGRATIONTIME_300MS = 0x02
INTEGRATIONTIME_400MS = 0x03
INTEGRATIONTIME_500MS = 0x04
INTEGRATIONTIME_600MS = 0x05

GAIN_LOW = 0x00
GAIN_MED = 0x10
GAIN_HIGH = 0x20
GAIN_MAX = 0x30

def _bytes_to_int(data):
    return data[0] + (data[1]<<8)

from machine import I2C, Pin
class SMBusEmulator:
    __slots__ = ('i2c',)
    def __init__(self, scl_pinno=SCL_PIN, sda_pinno=SDA_PIN):
        self.i2c = I2C(scl=Pin(scl_pinno, Pin.IN),
                       sda=Pin(sda_pinno, Pin.IN))

    def write_byte_data(self, addr, cmd, val):
        buf = bytes([cmd, val])
        self.i2c.writeto(addr, buf)

    def read_word_data(self, addr, cmd):
        assert cmd < 256
        buf = bytes([cmd])
        self.i2c.writeto(addr, buf)
        data = self.i2c.readfrom(addr, 4)
        return _bytes_to_int(data)


class Tsl2591:
    def __init__(
                 self,
                 sensor_id,
                 integration=INTEGRATIONTIME_200MS,
                 gain=GAIN_HIGH
                 ):
        self.sensor_id = sensor_id
        self.bus = SMBusEmulator()
        self.integration_time = integration
        self.gain = gain
        self.set_timing(self.integration_time)
        self.set_gain(self.gain)
        self.disable()

    def set_timing(self, integration):
        self.enable()
        self.integration_time = integration
        self.bus.write_byte_data(
                    SENSOR_ADDRESS,
                    COMMAND_BIT | REGISTER_CONTROL,
                    self.integration_time | self.gain
                    )
        self.disable()

    def set_gain(self, gain):
        self.enable()
        self.gain = gain
        self.bus.write_byte_data(
                    SENSOR_ADDRESS,
                    COMMAND_BIT | REGISTER_CONTROL,
                    self.integration_time | self.gain
                    )
        self.disable()

    def enable(self):
        self.bus.write_byte_data(
                    SENSOR_ADDRESS,
                    COMMAND_BIT | REGISTER_ENABLE,
                    ENABLE_POWERON | ENABLE_AEN | ENABLE_AIEN
                    )

    def disable(self):
        self.bus.write_byte_data(
                    SENSOR_ADDRESS,
                    COMMAND_BIT | REGISTER_ENABLE,
                    ENABLE_POWEROFF
                    )

    def calculate_light(self, full, ir):
# This is a highly experimental function to calculate radiometric intensity.
# Calculations are based on the TSL2591 spec sheet at ams.com
# An attempt is made to calculate irradiance in uW/cm2 for white light (4000 K)
        if (full == 0xFFFF) | (ir == 0xFFFF):
            return -1
            
        case_integ = {
            INTEGRATIONTIME_100MS: 100.,
            INTEGRATIONTIME_200MS: 200.,
            INTEGRATIONTIME_300MS: 300.,
            INTEGRATIONTIME_400MS: 400.,
            INTEGRATIONTIME_500MS: 500.,
            INTEGRATIONTIME_600MS: 600.
            }
        if self.integration_time in case_integ.keys():
            atime = case_integ[self.integration_time]
        else:
            atime = 600.

        case_gain = {
            GAIN_LOW: 1.,
            GAIN_MED: 24.5,
            GAIN_HIGH: 400.,
            GAIN_MAX: 9876.
            }

        if self.gain in case_gain.keys():
            again = case_gain[self.gain]
        else:
            again = 9876.
# spec sheet of TSL2591 has 264.1 counts per uW/cm2 at GAIN_HIGH (400) and 100 MS for CH0
# and 34.9 counts per uW/cm2 for CH1
        cpuW0 = (atime/100.) * (again/400.) * 264.1
#        cpuW1 = (atime/100.) * (again/400.) * 34.9
        fullc = full / cpuW0
        irc = ir / cpuW0
        return fullc, irc

#
# bump functions
#
# source: https://github.com/gshau/SQM_TSL2591/blob/master/SQM_TSL2591/SQM_TSL2591.cpp
#

    def adjTime(self, adjDirection):
        if (self.integration_time == INTEGRATIONTIME_100MS):
            if (adjDirection > DOWN):
                self.set_timing(INTEGRATIONTIME_200MS)
            else:
                self.set_timing(INTEGRATIONTIME_100MS)
        elif (self.integration_time == INTEGRATIONTIME_200MS):
            if (adjDirection > DOWN):
                self.set_timing(INTEGRATIONTIME_300MS)
            else:
                self.set_timing(INTEGRATIONTIME_100MS)
        elif (self.integration_time == INTEGRATIONTIME_300MS):
            if (adjDirection > DOWN):
                self.set_timing(INTEGRATIONTIME_400MS)
            else:
                self.set_timing(INTEGRATIONTIME_200MS)
        elif (self.integration_time == INTEGRATIONTIME_400MS):
            if (adjDirection > DOWN):
                self.set_timing(INTEGRATIONTIME_500MS)
            else:
                self.set_timing(INTEGRATIONTIME_300MS)
        elif (self.integration_time == INTEGRATIONTIME_500MS):
            if (adjDirection > DOWN):
                self.set_timing(INTEGRATIONTIME_600MS)
            else:
                self.set_timing(INTEGRATIONTIME_400MS)
        else:
            if (adjDirection > DOWN):
                self.set_timing(INTEGRATIONTIME_600MS)
            else:
                self.set_timing(INTEGRATIONTIME_500MS)

    def adjGain(self, adjDirection):
        if (self.gain == GAIN_LOW):
            if (adjDirection > DOWN):
                self.set_gain(GAIN_MED)
            else:
                self.set_gain(GAIN_LOW)
        elif (self.gain == GAIN_MED):
            if (adjDirection > DOWN):
                self.set_gain(GAIN_HIGH)
            else:
                self.set_gain(GAIN_LOW)
        elif (self.gain == GAIN_HIGH):
            if (adjDirection > DOWN):
                self.set_gain(GAIN_MAX)
            else:
                self.set_gain(GAIN_MED)
        else:
            if (adjDirection > DOWN):
                self.set_gain(self, GAIN_MAX)
            else:
                self.set_gain(self, GAIN_HIGH)


# advanced read function
#
# auto gain and auto timing
# if the returned values are near 0xFFFF, gain and timing will be decreased
# if the returned values are near 0, gain and timing will be increased
    def advanced_read(self):
        self.enable()
        time.sleep(0.120*self.integration_time+1)
        full = self.bus.read_word_data(
                    SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN0_LOW
                    )
        ir = self.bus.read_word_data(
                  SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN1_LOW
                  )
        while ((full > 0xFFE0) & (self.gain > GAIN_LOW)):
              self.adjGain(DOWN)
              full = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN0_LOW
                      )
              ir = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN1_LOW
                      )
        while ((full > 0xFFE0) & (self.integration_time > INTEGRATIONTIME_100MS)):
              self.adjTime(DOWN)
              full = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN0_LOW
                      )
              ir = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN1_LOW
                      )
        while ((full < 0x0010) & (self.gain < GAIN_MAX)):
              self.adjGain(UP)
              full = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN0_LOW
                      )
              ir = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN1_LOW
                      )
        while ((full < 0x0010) & (self.integration_time < INTEGRATIONTIME_600MS)):
              self.adjTime(UP)
              full = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN0_LOW
                      )
              ir = self.bus.read_word_data(
                      SENSOR_ADDRESS, COMMAND_BIT | REGISTER_CHAN1_LOW
                      )
        self.disable()
        return full, ir



    def sample(self):
        full, ir = self.get_full_luminosity()
        return self.calculate_lux(full, ir)

#
# Experimental
# Do repeated reads for very low light levels
# This will reduce noise
#
# source: https://github.com/gshau/SQM_TSL2591/blob/master/SQM_TSL2591/SQM_TSL2591.cpp
#
    def read_low_lux(self):
        nread = 1
        full, ir = self.advanced_read()
        fullSum = full
        irSum = ir
        visSum = fullSum - irSum
        while ((visSum < 128) & (nread < 40)):
            nread = nread +1
            full, ir = self.advanced_read()
            fullSum = fullSum + full
            irSum = irSum + ir
            visSum = fullSum - irSum
        full = fullSum/nread
        ir = irSum/nread
        return self.calculate_light(full, ir)