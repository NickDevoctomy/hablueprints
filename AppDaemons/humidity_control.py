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
                'name': 'Zone 1',
                'rooms': ['room1', 'room2'],
                'min_humidity': 50,
                'max_humidity': 60,
                'dehumidifier_switch': 'dehumidifer_power_switch',
                'virtual_sensor': 'sensor.average_humidity_zone1',
                'defer_time': 5,
                'max_runtime': 300
            },
        }

        self.timers = {}
        self.start_times = {}

        for room, sensors in self.rooms.items():
            self.listen_state(self.state_changed, sensors['humidity'])
            if sensors['door']:
                self.listen_state(self.state_changed, sensors['door'])

        for zone, config in self.zones.items():
            self.set_state(config['virtual_sensor'], state="unknown", attributes={
                "unit_of_measurement": "%",
                "friendly_name": f"{config['name']} Average Humidity",
                "icon": "mdi:water-percent",
            })

    def state_changed(self, entity, attribute, old, new, kwargs):
        for zone, config in self.zones.items():
            humidity_values = []

            # Check if a timer and action already exist for this zone
            if zone in self.timers:
                existing_timer_handle = self.timers[zone]['handle']
                existing_action = self.timers[zone]['action']
            else:
                existing_timer_handle = None
                existing_action = None

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

                # Force the dehumidifer off if it's been running for longer than max_runtime
                if zone in self.start_times:
                    elapsed_time = (self.datetime() - self.start_times[zone]).seconds / 60
                    if elapsed_time > config['max_runtime']:
                        self.force_off(zone, config)
                        del self.timers[zone]
                        return

                # Control the dehumidifier with deferred action
                if average_humidity < config['min_humidity']:
                    new_action = "off"
                elif average_humidity > config['max_humidity']:
                    new_action = "on"
                else:
                    new_action = None

                # Compare new action with existing action
                if new_action != existing_action:
                    # Cancel existing timer if it exists
                    if existing_timer_handle:
                        self.cancel_timer(existing_timer_handle)

                    # Schedule a new timer for the new action if required
                    if new_action:
                        new_timer_handle = self.run_in(self.deferred_action, config['defer_time'] * 60, zone=zone, action=new_action)
                        self.timers[zone] = {'handle': new_timer_handle, 'action': new_action}
                    else:
                        # Remove timer info for this zone if no action is required
                        if zone in self.timers:
                            del self.timers[zone]

    def deferred_action(self, kwargs):
        zone = kwargs['zone']
        action = kwargs['action']
        config = self.zones[zone]

        if action == "on":
            self.turn_on(config['dehumidifier_switch'])
            self.start_times[zone] = self.datetime()
        elif action == "off":
            self.force_off(zone, config)

        # Remove the timer handle as it has been executed
        del self.timers[zone]

    def force_off(self, zone, config):
        self.turn_off(config['dehumidifier_switch'])
        if zone in self.start_times:
            del self.start_times[zone]
