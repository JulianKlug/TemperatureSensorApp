from pathlib import Path

import numpy as np
from flask import Flask, Response
from modun.file_io import json2dict
from requests import get

app = Flask(__name__)


def get_values_from_db(collection):
    for elem in collection.find({}).sort("_id", -1):
        if not np.isnan(elem['temp']):
            return elem


def get_sensor1_values(api_token: str) -> dict:
    return_dict = {}
    for val in ['temp', 'humidity']:
        url = f"http://localhost:8123/api/states/sensor.{val}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "content-type": "application/json",
        }

        response = get(url, headers=headers).json()
        return_dict[f"{val}"] = response['state'] + response['attributes']["unit_of_measurement"]
        return_dict[f"{val}_last_update"] = response['last_updated']

    return return_dict


@app.route("/")
def read_temp():
    config = json2dict(Path('~/.config/burchen_db.json').expanduser())

    sensor1_values = get_sensor1_values(config["hass_api_token"])

    if not sensor1_values:
        return Response(status=500)
    return f'<html>' \
           f'<h1>Ob der Baechi</h1>' \
           f'<br>' \
           f'<b>Sensor 1 </b><br>' \
           f'Temperature: {sensor1_values["temp"]}<br>' \
           f'Humidity: {sensor1_values["humidity"]}%<br>' \
           f'<i>Last measure: {sensor1_values["temp_last_update"]}</i><br>' \
           f'<div width:100vh height:100vh>' \
           f'<img src="https://github.com/JulianKlug/TemperatureSensorApp/raw/main/ceyna.png" alt="Ceyna"' \
           f'style="padding: 0 5px 10px 10px; position: absolute; bottom: 0; right: 0;">' \
           f'</div>' \
           f'</html>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
