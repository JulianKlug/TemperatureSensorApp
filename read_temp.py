"""
Read the temperature and humidity from sensors and upload them to the mongodb.
This script is executed every 5 minutes as a cronjob.
"""
from datetime import datetime
from pathlib import Path

from modun.file_io import json2dict
from pymongo import MongoClient

from inkbirdsensor import InkbirdSensor

config_path = Path('~/.config/burchen_db.json').expanduser()

config = json2dict(config_path)

client = MongoClient(config['mongo_uri'])
db = client.ppb
collection = db.inkbird1

MAC_ADDRESS = '78:DB:2F:CE:29:4C'

inkbird_sensor = InkbirdSensor(MAC_ADDRESS)

temperature, humidity = inkbird_sensor.get_measurements()

print('temp: ', temperature, 'hum', humidity)

collection.insert_one(
    {
        'temp': temperature,
        'humidity': humidity,
        'date': datetime.utcnow()
    }

)
