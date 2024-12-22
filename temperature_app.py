import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import dash
import numpy as np
import plotly.graph_objs as go
import pytz
from dash import Input, Output, dcc, html
from flask import request
from pymongo import MongoClient
from tuya_connector import TuyaOpenAPI

# config_fn = Path("~/.config/buerchen_config.json").expanduser()
config_fn = Path("buerchen_config.json").expanduser()

local_timezone = pytz.timezone("Europe/Zurich")


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

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Ob der Baechi"

mongo_client = MongoClient(CONFIG.mongodb_URI)
db = mongo_client[CONFIG.mongodb_database]


def convert_tuya_temp(temp: int) -> float:
    return np.round(temp * 1e-1 if len(str(temp)) else temp, 2)


@dataclass
class Sensor:
    name: str = None
    device_id: str = None
    collection_name: str = None
    mongo_collection: any = None
    uid: str = None

    def __post_init__(self):
        self.mongo_collection = db[self.collection_name]
        self.uid = str(uuid.uuid4().hex)

    def verify_temperature_value(self, temperature_value: float):
        if temperature_value < CONFIG.temp_warn_limit:
            # notification_system.notify(
            print(
                f"Temperature of {self.name} is below {CONFIG.temp_warn_limit}",
                f"Temperature is {temperature_value}°C",
            )


@dataclass
class TempHumidSensor(Sensor):
    def _create_figure(self, timestamps, humidities, temperatures):
        # Create an interactive plot of the past temperature and humidity values
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(x=timestamps, y=humidities, name="Humidity", yaxis="y2")
        )
        fig.add_trace(go.Scatter(x=timestamps, y=temperatures, name="Temperature"))
        fig.update_layout(
            xaxis_title="Timestamp",
            yaxis=dict(title="Temperature (Celsius)"),
            yaxis2=dict(title="Humidity (%)", overlaying="y", side="right"),
            hovermode="closest",
        )
        return fig

    def get_html_sensor_card(
        self, temperatures, humidities, last_entry_date, battery_status=None
    ):
        battery_status_text = (
            f"Battery Status: {battery_status}" if battery_status else ""
        )
        current_temperature = temperatures[-1] if temperatures else "No data available"
        current_humidity = humidities[-1] if humidities else "No data available"
        min_temperature = min(temperatures) if temperatures else "No data available"
        max_temperature = max(temperatures) if temperatures else "No data available"
        min_humidity = min(humidities) if humidities else "No data available"
        max_humidity = max(humidities) if humidities else "No data available"

        return [
            html.H2(self.name),
            html.P(
                f"Temperature: {current_temperature}°C "
                f"(min: {min_temperature}°C, max: {max_temperature}°C)"
            ),
            html.P(
                f"Humidity: {current_humidity}% "
                f"(min: {min_humidity}%, max: {max_humidity}%)"
            ),
            html.P(battery_status_text),
            html.P(f"Last entry is from {last_entry_date}"),
        ]

    def get_card(self):
        # Get the past temperature and humidity values from the database
        now = datetime.now(local_timezone)
        past = now - timedelta(hours=24)
        past_data = list(self.mongo_collection.find({"date": {"$gte": past}}))

        if not past_data:
            past_temperatures = []
            past_humidities = []
            timestamps = []
            last_entry_date = "No data available from the last 24 hours."
            battery_status = None
        else:
            past_temperatures = [data["temperature"] for data in past_data]
            past_humidities = [data["humidity"] for data in past_data]
            timestamps = [data["date"] for data in past_data]
            last_entry_date = timestamps[-1].strftime("%Y-%m-%d %H:%M")
            battery_status = past_data[-1].get("battery_state")

        # Create the figure
        fig = self._create_figure(timestamps, past_humidities, past_temperatures)

        # Create the card layout using Dash HTML components
        return html.Div(
            className="card",
            children=[
                html.Div(
                    className="card-body",
                    children=[
                        *self.get_html_sensor_card(
                            past_temperatures,
                            past_humidities,
                            last_entry_date,
                            battery_status=battery_status,
                        ),
                        dcc.Graph(figure=fig),
                    ],
                )
            ],
        )


@dataclass
class BottomBathroomTempSensor(TempHumidSensor):
    device_id: str = "bfa66db5543bd8c8c4xb4r"
    collection_name: str = "BuerchenBadUntenTempSensor"
    mongo_collection: any = None
    name: str = "Bad Unten Temperatur"

    def log_status(self, openapi: TuyaOpenAPI) -> None:
        response = openapi.get(f"/v1.0/iot-03/devices/{self.device_id}/status")
        temperature = convert_tuya_temp(response["result"][0]["value"])
        humidity = response["result"][1]["value"]
        battery_state = response["result"][2]["value"]

        self.verify_temperature_value(temperature)

        result = self.mongo_collection.insert_one(
            {
                "temperature": temperature,
                "humidity": humidity,
                "battery_state": battery_state,
                "date": datetime.now(local_timezone),
            }
        )


@dataclass
class KellerPlug(Sensor):
    device_id: str = "bfd9acf903d28936b8bngr"
    collection_name: str = "KellerPlug"
    mongo_collection: any = None
    name: str = "Keller Steckdose"

    def log_status(self, openapi: TuyaOpenAPI) -> None:
        response = openapi.get(f"/v1.0/iot-03/devices/{self.device_id}/status")

        log_dict = {
            "set_temperature": response["result"][3]["value"],
            "current_temperature": response["result"][6]["value"],
            "correction_value": response["result"][7]["value"],
            "date": datetime.now(local_timezone),
        }

        self.verify_temperature_value(response["result"][6]["value"])

        self.mongo_collection.insert_one(log_dict)

    def _create_figure(self, timestamps, temperatures):
        # Create an interactive plot of the past temperature values
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timestamps, y=temperatures, name="Temperature"))
        fig.update_layout(
            xaxis_title="Timestamp",
            yaxis=dict(title="Temperature (Celsius)"),
            hovermode="closest",
        )
        return fig

    def get_card(self):
        now = datetime.now(local_timezone)
        past = now - timedelta(hours=24)
        past_data = list(self.mongo_collection.find({"date": {"$gte": past}}))

        if not past_data:
            return html.Div(
                className="card",
                children=[
                    html.H2(self.name),
                    html.P("No data available in the last 24 hours"),
                ],
            )

        # Extract temperature data
        past_temperatures = [data["current_temperature"] for data in past_data]
        timestamps = [data["date"] for data in past_data]
        threshold_temperature = past_data[-1]["set_temperature"]
        correction_value = past_data[-1]["correction_value"]

        # Calculate min and max temperatures
        min_temperature = (
            min(past_temperatures) if past_temperatures else "No data available"
        )
        max_temperature = (
            max(past_temperatures) if past_temperatures else "No data available"
        )

        # Create the figure
        fig = self._create_figure(timestamps, past_temperatures)

        # Return the card layout
        return html.Div(
            className="card",
            children=[
                html.Div(
                    className="card-body",
                    children=[
                        html.H2(self.name),
                        html.P(
                            f"Temperature: {past_temperatures[-1]}°C "
                            f"(min: {min_temperature}°C, max: {max_temperature}°C)"
                            if past_temperatures
                            else "No temperature data available"
                        ),
                        html.P(f"Threshold Temperature: {threshold_temperature}°C"),
                        html.P(f"Correction Value: {correction_value}°C"),
                        html.P(
                            f"Last entry: {timestamps[-1].strftime('%Y-%m-%d %H:%M')}"
                        ),
                        dcc.Graph(figure=fig),
                    ],
                )
            ],
        )


@dataclass
class EspTempSensor(TempHumidSensor):
    collection_name: str = "Buerchen Temperatures"
    mongo_collection: any = None
    name: str = "ESP Temperature Sensor"

    def __post_init__(self):
        self.mongo_collection = db[self.collection_name]

    def log_status(self, post_request) -> None:
        temperature = float(post_request.form["temperature"])
        humidity = float(post_request.form["humidity"])

        self.verify_temperature_value(temperature)

        self.mongo_collection.insert_one(
            {
                "temperature": temperature,
                "humidity": humidity,
                "date": datetime.now(local_timezone),
            }
        )


TUYA_DEVICES = [BottomBathroomTempSensor(), KellerPlug()]
ESP_SENSOR = EspTempSensor()
DEVICES = [ESP_SENSOR, *TUYA_DEVICES]


# App layout
app.layout = html.Div(
    children=[
        html.Div(
            id="sensor-cards",
            children=[
                html.Div(f"{device.name} data will appear here.", id=f"{device.uid}")
                for device in DEVICES
            ],
        ),
        dcc.Interval(
            id="interval-component", interval=10 * 1000, n_intervals=0
        ),  # Updates every 10 seconds
        # Add Ceyna at the bottom left
        html.Div(
            children=[
                html.Img(
                    src="https://github.com/JulianKlug/TemperatureSensorApp/raw/main/ceyna.png",
                    alt="Ceyna",
                    style={
                        "position": "fixed",
                        "bottom": "10px",
                        "right": "10px",
                        "width": "450px",  # Adjust width as needed
                    },
                )
            ],
        ),
    ]
)


# Callback to update sensor cards
@app.callback(
    Output("sensor-cards", "children"),
    [Input("interval-component", "n_intervals")],
)
def update_cards(n_intervals):
    # Header Card
    header_card = html.Div(
        className="card",
        children=[
            html.H1("Ob der Baechi", className="card-title"),
            html.Hr(),
            html.P(
                children=[
                    "Sauce: ",
                    html.A(
                        "GitHub",
                        href="https://github.com/JulianKlug/TemperatureSensorApp",
                        target="_blank",  # Open in new tab
                    ),
                ],
                className="card-text",
            ),
        ],
    )

    card_htmls = [header_card]
    for sensor in DEVICES:
        # Get the HTML and Plotly JSON from the sensor
        # card_html, plot_data = sensor.get_card()

        card_content = sensor.get_card()
        # Append the card and graph to the layout
        card_htmls.append(card_content)
    return card_htmls


def log_tuya_values():
    API_ENDPOINT = "https://openapi.tuyaeu.com"
    # Init OpenAPI and connect
    openapi = TuyaOpenAPI(API_ENDPOINT, CONFIG.tuya_access_id, CONFIG.tuya_access_key)
    openapi.connect()

    for device in TUYA_DEVICES:
        device.log_status(openapi)


@app.server.route("/data", methods=["POST"])
def handle_data():
    ESP_SENSOR.log_status(request)

    log_tuya_values()

    return "Data inserted into database.", 200


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=CONFIG.flask_port)
