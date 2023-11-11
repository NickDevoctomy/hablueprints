import appdaemon.plugins.hass.hassapi as hass

class MoldIndex(hass.Hass):
        
    def initialize(self):
        # Define your zones here
        self.zones = {
            'bedroom': {
                'name': 'Bedroom',
                'humidity_sensor': '',
                'temperature_sensor': '',
                'virtual_sensor': 'sensor.mold_index_bedroom',
                'defer_time': 5,
            },
        }

        for zone, config in self.zones.items():
            self.listen_state(self.state_changed, config['humidity_sensor'])
            self.listen_state(self.state_changed, config['temperature_sensor'])

            self.set_state(config['virtual_sensor'], state="unknown", attributes={
                "unit_of_measurement": "%",
                "friendly_name": f"{config['name']} Mold Index",
                #"icon": "mdi:water-percent",
            })

    def state_changed(self, entity, attribute, old, new, kwargs):
        for zone, config in self.zones.items():
