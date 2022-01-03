import requests


class HomeAssistantSensor():
    def __init__(self, api_adress, temperature_entity_id, humidity_entity_id, token):
        self.api_adress = api_adress
        self.temperature_entity_id = temperature_entity_id
        self.humidity_entity_id = humidity_entity_id
        self.token = token

    def read_status(self, entity_id):
        url = self.api_adress + '/api/states/' + entity_id
        headers = {
            "Authorization": "Bearer " + self.token,
            "content-type": "application/json",
        }
        response = requests.get(url, headers=headers)
        return response.json()['state']

    def read_sensor(self):
        temperature = self.read_status(self.temperature_entity_id)
        humidity = self.read_status(self.humidity_entity_id)
        return temperature, humidity