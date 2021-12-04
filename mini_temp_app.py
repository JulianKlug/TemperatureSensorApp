from flask import Flask, Response

from inkbirdsensor import InkbirdSensor

app = Flask(__name__)

MAC_ADDRESS = '78:DB:2F:CE:29:4C'

inkbird_sensor = InkbirdSensor(MAC_ADDRESS)
inkbird_sensor.start_measure()


@app.route("/temp")
def read_temp():
    temperature = inkbird_sensor.get_temperature()
    humidity = inkbird_sensor.get_humidity()
    last_measure_time_string = inkbird_sensor.get_last_measure_time_string()
    if not temperature or not humidity:
        return Response(status=500)

    d = f'<html><h1>Ob der Baechi</h1><br>' \
        f'<h5>Sensor 1 </h5><br>' \
        f'Temperature: {temperature} °C<br>' \
        f'Humidity: {humidity}%<br>' \
        f'<i>Last measure: {last_measure_time_string}</i></html>'
    return d


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
