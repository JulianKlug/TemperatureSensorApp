"""
Read the temperature and humidity from sensors and upload them to the mongodb.
This script is executed every 5 minutes as a cronjob.
"""
import json
import time
from pathlib import Path
from pymongo import MongoClient

from home_assistant_sensor import HomeAssistantSensor
from inkbirdsensor import InkbirdSensor

config_path = Path('/home/hendrik/.config/burchen_db.json')

with open(config_path, 'rt') as json_file:
    config = json.load(json_file)

# setup database connection
client = MongoClient(config['mongo_uri'])
db = client.ppb
inkbird1_collection = db.inkbird1
HA_sensor1_collection = db.HA_sensor1

# setup inkbird sensor
INKBIRD_MAC_ADDRESS = '78:DB:2F:CE:29:4C'
inkbird_sensor = InkbirdSensor(INKBIRD_MAC_ADDRESS)
inkbird_temperature, inkbird_humidity = inkbird_sensor.get_measurements()

# setup home assistant sensor
home_assistant_sensor = HomeAssistantSensor(config['home_assistant_api_url'],
                                            config['home_assistant_temperature_entity_id'],
                                            config['home_assistant_humidity_entity_id'],
                                            config['home_assistant_api_token'])
home_assistant_temperature, home_assistant_humidity = home_assistant_sensor.get_measurements()

HA_sensor1_collection.insert_one(
    {
        'temp': home_assistant_temperature,
        'humidity': home_assistant_humidity,
        'date': time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime())
    }

)

if inkbird_temperature:
    inkbird1_collection.insert_one(
        {
            'temp': inkbird_temperature,
            'humidity': inkbird_humidity,
            'date': time.strftime("%d-%m-%Y %H:%M:%S", time.gmtime())
        }

    )
