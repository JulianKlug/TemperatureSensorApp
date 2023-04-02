import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from datetime import timezone
from pathlib import Path

import plotly
import plotly.graph_objs as go
from flask import Flask, request, render_template
from pymongo import MongoClient
import pytz

config_fn = Path("~/.config/buerchen_config.json").expanduser()

local_timezone = pytz.timezone('Europe/Zurich')


@dataclass
class Config:
    mongodb_URI: str = None
    mongodb_database: str = None
    mongodb_collection: str = None
    flask_port: int = 5000

    def from_config(self):
        with open(config_fn) as f:
            config = json.load(f)
            self.mongodb_URI = config["mongodb_URI"]
            self.mongodb_database = config["mongodb_database"]
            self.mongodb_collection = config["mongodb_collection"]

        return self


CONFIG = Config().from_config()

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

    print(f"past_temperatures: {past_temperatures}")

    # Create an interactive plot of the past temperature and humidity values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=timestamps, y=past_temperatures, name='Temperature'))
    fig.add_trace(go.Scatter(x=timestamps, y=past_humidities, name='Humidity'))
    fig.update_layout(
        xaxis_title='Timestamp',
        yaxis_title='Value')
    # plot_data = opy.plot(fig, auto_open=False, output_type='div')
    plot_data = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Convert the last timestamp to a string:
    last_entry = timestamps[-1].strftime("%Y-%m-%d %H:%M")

    # Render the HTML page with the current temperature and humidity values, and the plot
    return render_template('index.html', plot_data=plot_data, min_temperature=min(past_temperatures),
                           max_temperature=max(past_temperatures), min_humidity=min(past_humidities),
                           max_humidity=max(past_humidities), temperature=temperature, humidity=humidity,
                           last_entry=last_entry)


@app.route('/data', methods=['POST'])
def handle_data():
    temperature = request.form['temperature']
    humidity = request.form['humidity']
    data = {
        'temperature': float(temperature),
        'humidity': float(humidity),
        'date': datetime.now(local_timezone)
    }
    result = collection.insert_one(data)
    print(f"received data: {data}")
    return f"Data inserted with ID: {result.inserted_id}"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
