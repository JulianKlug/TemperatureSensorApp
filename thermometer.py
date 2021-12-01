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
            measured_temperature, _ = get_readings(self.sensor_MAC)
            if measured_temperature:
                self.temperature = measured_temperature

    def stop_measure(self):
        self.measure = False

    def start_measure(self):
        self.measure = True
        self.measure_temperature()

    def get_temperature(self):
        return self.temperature
