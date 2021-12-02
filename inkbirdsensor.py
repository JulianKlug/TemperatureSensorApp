import time
from threading import Thread
from read_sensor import get_readings
import numpy as np
from bluepy import btle
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


class InkbirdSensor():
    # Get values from Inkbird IBS-TH1

    def __init__(self, sensor_MAC, measure_interval=5):
        self.sensor_MAC = sensor_MAC
        self.temperature = np.NaN
        self.humidity = np.NaN
        self.measure = True
        self.measure_interval = measure_interval

    # while measure true read sensor
    def measurement_loop(self):
        while self.measure:
            readings = self.read_sensor(self.sensor_MAC)
            if readings:
                self.temperature, self.humidity = readings
            time.sleep(self.measure_interval)

    def stop_measure(self):
        self.measure = False

    def start_measure(self):
        self.measure = True
        t = Thread(target=self.measurement_loop)
        t.start()

    def get_temperature(self):
        return self.temperature

    def convert_to_float_value(self, nums):
        # check if temp is negative
        num = (nums[1] << 8) | nums[0]
        if nums[1] == 0xff:
            num = -((num ^ 0xffff) + 1)
        return float(num) / 100


    def read_sensor(self, mac_address: str):
        try:
            dev = btle.Peripheral(mac_address, addrType=btle.ADDR_TYPE_PUBLIC)
            readings = dev.readCharacteristic(0x002d)
        except Exception as e:
            logging.error("Error reading BTLE: {}".format(e))
            return False

        # little endian, first two bytes are temp_c, second two bytes are humidity
        temperature_c = self.convert_to_float_value(readings[0:2])
        humidity = self.convert_to_float_value(readings[2:4])

        logging.info(
            "converted data: temperature_c[{:0.2f}], humidity[{:0.2f}]".format(temperature_c, humidity))


        return temperature_c, humidity