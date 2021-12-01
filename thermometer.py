import time

from read_sensor import get_readings


class Thermometer():
    def __init__(self, sensor_MAC, measure_interval=5):
        self.sensor_MAC = sensor_MAC
        self.temperature = None
        self.measure = True
        self.measure_interval = measure_interval

    # while measure true read sensor
    def measure_temperature(self):
        while self.measure:
            readings = get_readings(self.sensor_MAC)
            if readings:
                self.temperature, _ = readings
            time.sleep(self.measure_interval)

    def stop_measure(self):
        self.measure = False

    def start_measure(self):
        self.measure = True
        self.measure_temperature()

    def get_temperature(self):
        return self.temperature
