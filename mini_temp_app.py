import os
import glob

from flask import Flask, Response, json

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
    # d = {'temp_c': temp_c, 'humidity': humidity, 'hot': ('true' if temp_c > 30 else 'false')}
    d = {'temp_c': temperature}
    return Response(json.dumps(d), mimetype='application/json')

app.run(host='0.0.0.0')