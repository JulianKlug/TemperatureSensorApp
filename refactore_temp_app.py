import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import plotly
import plotly.graph_objs as go
import pytz
from flask import Flask, request, render_template
from pymongo import MongoClient

from utils.NotificationSystem import NotificationSystem
from tuya_connector import TuyaOpenAPI, TUYA_LOGGER

config_fn = Path("~/.config/buerchen_config.json").expanduser()

local_timezone = pytz.timezone('Europe/Zurich')


@dataclass
class Config:
    # db setttings
    mongodb_URI: str = None
    mongodb_database: str = None

    # notification settings
    notification_sender_address: str = None
    notification_receiver_addresses: list[str] = None
    temp_warn_limit: int = 5

    # port
    flask_port: int = 5000

    # tuya settings
    tuya_access_id: str = None
    tuya_access_key: str = None

    def from_config(self):
        with open(config_fn) as f:
            config = json.load(f)
            self.mongodb_URI = config["mongodb_URI"]
            self.mongodb_database = config["mongodb_database"]
            self.notification_sender_address = config["sender_address"]
            self.notification_receiver_addresses = config["receiver_addresses"]
            self.tuya_access_id = config["tuya_access_id"]
            self.tuya_access_key = config["tuya_access_key"]

        return self


CONFIG = Config().from_config()

# setup notification
notification_system = NotificationSystem('hendrik.klug@gmail.com', ['hendrik.klug@gmail.com', "tensu.wave@gmail.com"])

app = Flask(__name__)
mongo_client = MongoClient(CONFIG.mongodb_URI)
db = mongo_client[CONFIG.mongodb_database]


def convert_tuya_temp(temp: int) -> float:
    return temp * 1e-1 if len(str(temp)) else temp


@dataclass
class Sensor:
    device_id: str = None
    collection_name: str = None
    mongo_collection: any = None

    def __post_init__(self):
        self.mongo_collection = db[self.collection_name]


@dataclass
class TempHumidSensor(Sensor):

    def get_card(self):
        # Get the past temperature and humidity values from the database
        now = datetime.now(local_timezone)
        past = now - timedelta(hours=24)
        past_data = list(self.mongo_collection.find({'date': {'$gte': past}}))
        past_temperatures = [data['temperature'] for data in past_data]
        past_humidities = [data['humidity'] for data in past_data]
        timestamps = [data['date'] for data in past_data]

        last_entry_date = timestamps[-1].strftime("%Y-%m-%d %H:%M")

        return get_card(sensor_name=self.collection_name, past_temperatures=past_temperatures,
                        past_humidities=past_humidities, timestamps=timestamps,
                        last_battery_state=past_data[-1]['battery_state'], last_entry_date=last_entry_date)


@dataclass
class BottomBathroomTempSensor(TempHumidSensor):
    device_id: str = "bfa66db5543bd8c8c4xb4r"
    collection_name: str = "BuerchenBadUntenTempSensor"
    mongo_collection: any = None

    def log_status(self, openapi: TuyaOpenAPI) -> None:
        response = openapi.get(f"/v1.0/iot-03/devices/{self.device_id}/status")
        temperature = convert_tuya_temp(response['result'][0]['value'])
        humidity = response['result'][1]['value']
        battery_state = response['result'][2]['value']

        result = self.mongo_collection.insert_one(
            {"temperature": temperature, "humidity": humidity, "battery_state": battery_state,
             'date': datetime.now(local_timezone),
             })


@dataclass
class KellerPlug(Sensor):
    device_id: str = "bfd9acf903d28936b8bngr"
    collection_name: str = "KellerPlug"
    mongo_collection: any = None

    def log_status(self, openapi: TuyaOpenAPI) -> None:
        response = openapi.get(f"/v1.0/iot-03/devices/{self.device_id}/status")
        result = self.mongo_collection.insert_one({
            'set_temperature': response['result'][3]['value'],
            'current_temperature': response['result'][6]['value'],
            'correction_value': response['result'][7]['value'],
            'date': datetime.now(local_timezone),
        })


@dataclass
class EspTempSensor(TempHumidSensor):
    collection_name: str = "Buerchen Temperatures"
    mongo_collection: any = None

    def __post_init__(self):
        self.mongo_collection = db[self.collection_name]

    def log_status(self, post_request) -> None:
        temperature = float(post_request.form['temperature'])
        humidity = float(post_request.form['humidity'])
        self.mongo_collection.insert_one({
            'temperature': temperature,
            'humidity': humidity,
            'date': datetime.now(local_timezone),
        })


TUYA_DEVICES = {BottomBathroomTempSensor}
ESP_SENSOR = EspTempSensor()


def delete_all_documents():
    # Delete all documents from the collection
    result = collection.delete_many({})
    print(result.deleted_count, "documents deleted.")


@app.route('/')
def index():
    # Get the latest temperature and humidity values from the database
    latest_data = collection.find_one(sort=[('_id', -1)])
    temperature = latest_data['temperature']
    humidity = latest_data['humidity']

    # Get the past temperature and humidity values from the database
    now = datetime.now(local_timezone)
    past = now - timedelta(hours=24)
    past_data = list(collection.find({'date': {'$gte': past}}))
    past_temperatures = [data['temperature'] for data in past_data]
    past_humidities = [data['humidity'] for data in past_data]
    timestamps = [data['date'] for data in past_data]

    # Create an interactive plot of the past temperature and humidity values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=past_humidities, name='Humidity', yaxis='y2'))
    fig.add_trace(go.Scatter(x=timestamps, y=past_temperatures, name='Temperature'))
    fig.update_layout(
        xaxis_title='Timestamp',
        yaxis=dict(title='Temperature (Celsius)'),
        yaxis2=dict(title='Humidity (%)', overlaying='y', side='right'),
        hovermode='closest'
    )
    plot_data = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Convert the last timestamp to a string:
    last_entry = timestamps[-1].strftime("%Y-%m-%d %H:%M")

    # Render the HTML page with the current temperature and humidity values, and the plot
    return render_template('index.html', plot_data=plot_data, min_temperature=min(past_temperatures),
                           max_temperature=max(past_temperatures), min_humidity=min(past_humidities),
                           max_humidity=max(past_humidities), temperature=temperature, humidity=humidity,
                           last_entry=last_entry)


def log_tuya_values():
    API_ENDPOINT = "https://openapi.tuyaeu.com"
    # Init OpenAPI and connect
    openapi = TuyaOpenAPI(API_ENDPOINT, CONFIG.tuya_access_id, CONFIG.tuya_access_key)
    openapi.connect()

    for device in TUYA_DEVICES:
        device = device()
        device.log_status(openapi)


@app.route('/data', methods=['POST'])
def handle_data():
    ESP_SENSOR.log_status(request)

    log_tuya_values()

    # if temperature < CONFIG.temp_warn_limit:
    #     notification_system.notify(f"Temperature in Bürchen is below {CONFIG.temp_warn_limit}",
    #                                f"Temperature is {temperature}°C")
    #
    # return f"Data inserted with ID: {result.inserted_id}"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
