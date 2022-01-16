from pathlib import Path

import numpy as np
from flask import Flask, Response
from modun.file_io import json2dict
from pymongo import MongoClient

app = Flask(__name__)


def get_values_from_db(collection):
    for elem in collection.find({}).sort("_id", -1):
        if not np.isnan(elem['temp']):
            return elem


@app.route("/")
def read_temp():
    config = json2dict(Path('~/.config/burchen_db.json').expanduser())
    client = MongoClient(config['mongo_uri'])
    db = client.ppb
    inkbird1_collection = db.inkbird1
    HA_sensor1_collection = db.HA_sensor1

    inkbird1_values = get_values_from_db(inkbird1_collection)
    HA_sensor1_values = get_values_from_db(HA_sensor1_collection)

    if not inkbird1_values:
        return Response(status=500)
    return f'<html>' \
           f'<h1>Ob der Baechi</h1>' \
           f'<br>' \
           f'<b>Sensor 1 </b><br>' \
           f'Temperature: {inkbird1_values["temp"]} °C<br>' \
           f'Humidity: {inkbird1_values["humidity"]}%<br>' \
           f'<i>Last measure: {inkbird1_values["date"]}</i><br>' \
           f'<b>Sensor 2 </b><br>' \
           f'Temperature: {HA_sensor1_values["temp"]} °C<br>' \
           f'Humidity: {HA_sensor1_values["humidity"]}%<br>' \
           f'<div width:100vh height:100vh>' \
           f'<img src="https://github.com/JulianKlug/TemperatureSensorApp/raw/main/ceyna.png" alt="Ceyna"' \
           f'style="padding: 0 5px 10px 10px; position: absolute; bottom: 0; right: 0;">' \
           f'</div>' \
           f'</html>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
