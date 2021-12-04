"""
Read the temperature and humidity from sensors and upload them to the mongodb.
This script is executed every 5 minutes as a cronjob.
"""
import json
import time
from pathlib import Path

from pymongo import MongoClient

from inkbirdsensor import InkbirdSensor

config_path = Path('/home/hendrik/.config/burchen_db.json')

with open(config_path, 'rt') as json_file:
    config = json.load(json_file)

client = MongoClient(config['mongo_uri'])
db = client.ppb
collection = db.inkbird1

MAC_ADDRESS = '78:DB:2F:CE:29:4C'

inkbird_sensor = InkbirdSensor(MAC_ADDRESS)
temperature, humidity = inkbird_sensor.get_measurements()

if temperature:
    collection.insert_one(
        {
            'temp': temperature,
            'humidity': humidity,
            'date': time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime())
        }

    )
