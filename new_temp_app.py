import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import plotly
import plotly.graph_objs as go
import pytz
from flask import Flask, request, render_template
# from pymongo import MongoClient

from utils.NotificationSystem import NotificationSystem
from sensor_card import Sensor_card

config_fn = Path("~/.config/buerchen_config.json").expanduser()

local_timezone = pytz.timezone('Europe/Zurich')

PORT = 3333


@dataclass
class Config:
    # db setttings
    mongodb_URI: str = None
    mongodb_database: str = None
    mongodb_collection: str = None

    # notification settings
    notification_sender_address: str = None
    notification_receiver_addresses: list[str] = None
    temp_warn_limit: int = 5

    # port
    flask_port: int = PORT

    def from_config(self):
        with open(config_fn) as f:
            config = json.load(f)
            self.mongodb_URI = config["mongodb_URI"]
            self.mongodb_database = config["mongodb_database"]
            self.mongodb_collection = config["mongodb_collection"]
            self.notification_sender_address = config["sender_address"]
            self.notification_receiver_addresses = config["receiver_addresses"]

        return self


CONFIG = Config().from_config()

# setup notification
notification_system = NotificationSystem('hendrik.klug@gmail.com', ['hendrik.klug@gmail.com', "tensu.wave@gmail.com"])

app = Flask(__name__)
client = MongoClient(CONFIG.mongodb_URI)
db = client[CONFIG.mongodb_database]
collection = db[CONFIG.mongodb_collection]


def delete_all_documents():
    # Delete all documents from the collection
    result = collection.delete_many({})
    print(result.deleted_count, "documents deleted.")


@app.route('/')
def index():
    # Get the past temperature and humidity values from the database
    now = datetime.now(local_timezone)
    past = now - timedelta(hours=24)
    past_data = list(collection.find({'date': {'$gte': past}}))
    past_temperatures = [data['temperature'] for data in past_data]
    past_humidities = [data['humidity'] for data in past_data]
    timestamps = [data['date'] for data in past_data]

    # Convert the last timestamp to a string:
    last_entry = timestamps[-1].strftime("%Y-%m-%d %H:%M")

    sensor_card = Sensor_card("Temperature Sensor", "Void", past_temperatures, past_humidities, timestamps)

    # read templates/index.html as string
    with open("templates/index.html", "r") as f:
        html = f.read()
    # replace placeholders with actual values
    html = html.replace("HTML_PLACEHOLDER", sensor_card.get_sensor_card())
    html = html.replace("JS_PLACEHOLDER", sensor_card.get_sensor_card_js())

    return html


@app.route('/data', methods=['POST'])
def handle_data():
    temperature = float(request.form['temperature'])
    humidity = float(request.form['humidity'])
    data = {
        'temperature': temperature,
        'humidity': humidity,
        'date': datetime.now(local_timezone),
    }
    result = collection.insert_one(data)
    print(f"received data: {data}")

    if temperature < CONFIG.temp_warn_limit:
        notification_system.notify(f"Temperature in Bürchen is below {CONFIG.temp_warn_limit}",
                                   f"Temperature is {temperature}°C")

    return f"Data inserted with ID: {result.inserted_id}"


if __name__ == '__main__':
    app.run('0.0.0.0', port=PORT)
