from flask import Flask, Response

from thermometer import Thermometer

app = Flask(__name__)

MAC_ADDRESS = '78:DB:2F:CE:29:4C'

thermometer = Thermometer(MAC_ADDRESS)
thermometer.start_measure()

@app.route("/temp")
def read_temp():
    temperature = thermometer.get_temperature()
    if not temperature:
        return Response(status=500)

    d = f'<html><h1>Ob der Baechi</h1><br>' \
        f'<h5>Sensor 1 </h5><br>' \
        f'Temperature: {temperature} °C</html>'
    return d

app.run(host='0.0.0.0', port=5000)