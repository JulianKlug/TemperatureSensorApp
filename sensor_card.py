import json
import uuid
import plotly
import plotly.graph_objs as go

class Sensor_card():
    def __init__(self, sensor_name, sensor_location, temperatures, humidities, timestamps):
        self.sensor_name = sensor_name
        self.sensor_location = sensor_location
        # generate unique id
        self.uid = str(uuid.uuid4().hex)

        self.temperatures = temperatures
        self.humidities = humidities
        self.timestamps = timestamps

        self.temperature = temperatures[-1]
        self.humidity = humidities[-1]
        self.last_entry = timestamps[-1]

        # Create an interactive plot of the past temperature and humidity values
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timestamps, y=self.humidities, name='Humidity', yaxis='y2'))
        fig.add_trace(go.Scatter(x=timestamps, y=self.temperatures, name='Temperature'))
        fig.update_layout(
            xaxis_title='Timestamp',
            yaxis=dict(title='Temperature (Celsius)'),
            yaxis2=dict(title='Humidity (%)', overlaying='y', side='right'),
            hovermode='closest'
        )
        self.plot_data = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def get_sensor_card(self):
        return f"""
                <div class="card">
                <div class="card-body">
                            <h2>{self.sensor_name} ({self.sensor_location})</h2>
                            <p>Temperature: {self.temperature}&deg;C 
                            (min: {min(self.temperatures)}&deg;C, 
                            max: {max(self.temperatures)}&deg;C)</p>
                            <p>Humidity: {self.humidity}% 
                            (min: {min(self.humidities)}%, 
                            max: {max(self.humidities)}%)</p>
                            <p>Last entry is from {self.last_entry}</p>
        
                            <div id={self.uid} class='chart'></div>
                </div> 
                </div>
                """

    def get_sensor_card_js(self):
        return f"""
                Plotly.plot("{self.uid}",{self.plot_data});
                """