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
    collection = db.inkbird1

    values = get_values_from_db(collection)

    if not values:
        return Response(status=500)

    return f'<html><h1>Ob der Baechi</h1><br>' \
           f'<h5>Sensor 1 </h5><br>' \
           f'Temperature: {values["temp"]} °C<br>' \
           f'Humidity: {values["humidity"]}%<br>' \
           f'<i>Last measure: {values["date"]}</i></html>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
