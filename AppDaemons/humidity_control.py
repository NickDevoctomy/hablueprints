import appdaemon.plugins.hass.hassapi as hass

class HumidityAverage(hass.Hass):

    def initialize(self):
        # Define your room pairs here
        self.rooms = {
            'room1': {'humidity': 'sensor.humidity1', 'door': 'binary_sensor.door1'},
            'room2': {'humidity': 'sensor.humidity2', 'door': None},
        }

        # Define your zones here
        self.zones = {
            'zone1': {
                'name' : 'Zone 1',
                'rooms': ['room1', 'room2'],
                'min_humidity': 50,
                'max_humidity': 60,
                'dehumidifier_switch': 'dehumidifer_power_switch',
                'virtual_sensor': 'sensor.average_humidity_zone1'
            },
        }

        # Listen for changes to any of the defined sensors
        for room, sensors in self.rooms.items():
            self.listen_state(self.state_changed, sensors['humidity'])
            if sensors['door']:
                self.listen_state(self.state_changed, sensors['door'])

        # Initialize virtual sensors
        for zone, config in self.zones.items():
            self.set_state(config['virtual_sensor'], state="unknown", attributes={
                "unit_of_measurement": "%",
                "friendly_name": f"{config['name']} Average Humidity",
                "icon": "mdi:water-percent",
            })

    def state_changed(self, entity, attribute, old, new, kwargs):
        for zone, config in self.zones.items():
            humidity_values = []

            for room in config['rooms']:
                sensors = self.rooms[room]
                humidity_sensor = sensors['humidity']
                door_sensor = sensors['door']

                if self.get_state(humidity_sensor) is not None:
                    if door_sensor and self.get_state(door_sensor) == "on":
                        humidity_values.append(float(self.get_state(humidity_sensor)))
                    elif not door_sensor:
                        humidity_values.append(float(self.get_state(humidity_sensor)))

            if humidity_values:
                average_humidity = round(sum(humidity_values) / len(humidity_values), 2)

                # Update the virtual sensor
                self.set_state(config['virtual_sensor'], state=average_humidity, attributes={
                    "unit_of_measurement": "%",
                    "friendly_name": f"{config['name']} Average Humidity",
                    "icon": "mdi:water-percent",
                })

                # Control the dehumidifier
                if average_humidity < config['min_humidity']:
                    self.turn_off(config['dehumidifier_switch'])
                elif average_humidity > config['max_humidity']:
                    self.turn_on(config['dehumidifier_switch'])
