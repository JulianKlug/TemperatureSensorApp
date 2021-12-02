from flask import Flask, Response

from inkbirdsensor import InkbirdSensor

app = Flask(__name__)

MAC_ADDRESS = '78:DB:2F:CE:29:4C'

inkbird_sensor = InkbirdSensor(MAC_ADDRESS)
inkbird_sensor.start_measure()

@app.route("/temp")
def read_temp():
    readings = InkbirdSensor.get_temperature()
    if not readings:
        return Response(status=500)
    temperature, humidity = readings

    d = f'<html><h1>Ob der Baechi</h1><br>' \
        f'<h5>Sensor 1 </h5><br>' \
        f'Temperature: {temperature} °C<br>' \
        f'Humidity: {humidity}%</html>'
    return d

app.run(host='0.0.0.0', port=5000)