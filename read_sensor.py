#!/usr/bin/env python3

# Get values from Inkbird IBS-TH1

from bluepy import btle
import logging

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

def float_value(nums):
    # check if temp is negative
    num = (nums[1]<<8)|nums[0]
    if nums[1] == 0xff:
        num = -( (num ^ 0xffff ) + 1)
    return float(num) / 100

def c_to_f(temperature_c):
    return 9.0/5.0 * temperature_c + 32

def get_readings(mac_address:str):
    try:
        dev = btle.Peripheral(mac_address, addrType=btle.ADDR_TYPE_PUBLIC)
        readings = dev.readCharacteristic(0x28)
        return readings
    except Exception as e:
        logging.error("Error reading BTLE: {}".format(e))
        return False

    # little endian, first two bytes are temp_c, second two bytes are humidity
    temperature_c = float_value(readings[0:2])
    humidity = float_value(readings[2:4])
    temperature_f = c_to_f(temperature_c)

    logging.info("converted data: temperature_f[{:0.2f}], temperature_c[{:0.2f}], humidity[{:0.2f}]".format(temperature_f, temperature_c, humidity))

    return temperature_c, humidity