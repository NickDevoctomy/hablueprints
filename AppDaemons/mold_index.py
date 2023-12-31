import appdaemon.plugins.hass.hassapi as hass
import datetime
import io
import csv
import math

class MoldIndex(hass.Hass):
        
    def initialize(self):
        # Define your zones here
        self.zones = {
            'bedroom': {
                'name': 'Bedroom',
                'humidity_sensor': '',
                'temperature_sensor': '',
                'virtual_sensor': 'sensor.mold_index_bedroom'
            },
        }

        for zone, config in self.zones.items():
            self.set_state(config['virtual_sensor'], state=0, attributes={
                "unit_of_measurement": "%",
                "friendly_name": f"{config['name']} Mold Index",
                "icon": "mdi:water-percent-alert"
            })

            self.calculate_mold_index({'zone_name':zone})
    
    def calculate_mold_index(self, kwargs):
        # get previous hour of data and calculate mold index
        zone_name = kwargs['zone_name']
        self.log(f"Calculating mold index for {zone_name}.")
        config = self.zones[zone_name]
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(hours=1)
        humidityHistory = self.get_history(entity_id=config['humidity_sensor'], start_time = start_time, end_time = end_time)
        tempHistory = self.get_history(entity_id=config['temperature_sensor'], start_time = start_time, end_time = end_time)

        humidityAverage = self.state_average('humidity', humidityHistory)
        tempAverage = self.state_average('temperature', tempHistory)

        mold_index = self.mold_growth_index(temperature=tempAverage, humidity=humidityAverage)
        self.log(f"Mold index for {zone_name} is currently at {mold_index}")

        self.set_state(config['virtual_sensor'], state=mold_index, attributes={
            "unit_of_measurement": "%",
            "friendly_name": f"{config['name']} Mold Index",
            "icon": "mdi:water-percent-alert"
        })
        # queue next update in 1 hour
        self.run_in(self.calculate_mold_index, 3600, zone_name=zone_name)

    def state_average(self, name, history):
        if history is None or not history[0]:
            self.log(f"No history data found for the {name} sensor.")
            return 0
        
        # Extract the state values and convert them to floats
        state_values = [float(state['state']) for state in history[0] if self.is_number(state['state'])]

        # Calculate the average if there are any state values
        if state_values:
            average = sum(state_values) / len(state_values)
            self.log(f"Average {name} state over the last hour: {average}")
            return average
        else:
            self.log(f"No {name} state values found so returning 0 as average.")
            return 0
        
    def is_number(self, string):
        try:
            float(string)
            return True
        except ValueError:
            return False
        
    def sigmoid(self, x: float) -> float:
        return 1 / (1 + math.exp(-x))
    
    def mold_growth_index(self, temperature: float, humidity: float) -> int:
        # Define temperature and humidity thresholds for mold growth
        temp_optimal = 25  # Optimal temperature for mold growth
        humidity_optimal = 70  # Optimal humidity for mold growth
    
        # Calculate the temperature factor with a sigmoid function
        temp_factor = self.sigmoid((temperature - temp_optimal) / 5)  # 5 is a chosen scaling factor to adjust the steepness
    
        # Calculate the humidity factor with a sigmoid function
        humidity_factor = self.sigmoid((humidity - humidity_optimal) / 10)  # 10 is a chosen scaling factor to adjust the steepness
    
        # Calculate the combined mold growth index
        mold_index = temp_factor * humidity_factor * 100
    
        # Ensure the mold index is within the bounds 0-100
        mold_index = max(0, min(100, int(mold_index)))
    
        return mold_index
