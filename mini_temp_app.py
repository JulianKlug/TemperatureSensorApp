import os
import glob

from flask import Flask, Response, json

from read_sensor import get_readings

app = Flask(__name__)

MAC_ADDRESS = '00:00:00:00:00:00'

@app.route("/temp")
def read_temp():
    readings = get_readings(mac_address=MAC_ADDRESS)
    if not readings:
        return Response(status=500)
    temp_c, humidity =  readings

    d = {'temp_c': temp_c, 'humidity': humidity, 'hot': ('true' if temp_c > 30 else 'false')}
    return Response(json.dumps(d), mimetype='application/json')

app.run(host='0.0.0.0')