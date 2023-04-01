from dataclasses import dataclass

from flask import Flask, request, render_template
from pymongo import MongoClient
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from datetime import timezone
from io import BytesIO
import base64
import plotly.graph_objs as go


@dataclass
class Config:
    mongodb_URI: str = "mongodb://buerchen:K(;qifxzr.bh2d<xHA@localhost:27019/Buerchen?directConnection=true&serverSelectionTimeoutMS=2000&authSource=Buerchen"
    mongodb_database: str = "Buerchen"
    mongodb_collection: str = "Buerchen Temperatures"
    flask_port: int = 5000


CONFIG = Config()

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
    now = datetime.now(timezone.utc)
    past = now - timedelta(hours=24)
    past_data = list(collection.find({'date': {'$gte': past}}))
    past_temperatures = [data['temperature'] for data in past_data]
    past_humidities = [data['humidity'] for data in past_data]
    timestamps = [data['date'] for data in past_data]

    print(f"past_temperatures: {past_temperatures}")

    # Generate a plot of the past temperature and humidity values
    fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('Timestamp')
    ax1.set_ylabel('Temperature (C)', color=color)
    ax1.plot(timestamps, past_temperatures, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Humidity (%)', color=color)
    ax2.plot(timestamps, past_humidities, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()

    # Convert the plot to a base64-encoded string for display in the HTML page
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    plt.close()
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Render the HTML page with the current temperature and humidity values, and the plot
    return render_template('index.html', plot_data=plot_data, min_temperature=min(past_temperatures),
                           max_temperature=max(past_temperatures), min_humidity=min(past_humidities),
                           max_humidity=max(past_humidities), temperature=temperature, humidity=humidity, last_entry=timestamps[-1])


@app.route('/data', methods=['POST'])
def handle_data():
    temperature = request.form['temperature']
    humidity = request.form['humidity']
    data = {
        'temperature': float(temperature),
        'humidity': float(humidity),
        'date': datetime.now(timezone.utc),
    }
    result = collection.insert_one(data)
    print(f"received data: {data}")
    return f"Data inserted with ID: {result.inserted_id}"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
