# hablueprints

My homeassistant blueprints and other various configurations.

## Blueprints

### heatercontrol.yaml

This blueprint will take a temp sensor, heater switch, min / max temp values and a boolean input value to thermostatically control the temperature of a room/area.

## AppDaemons

### humidity_control.py

This AppDaemon controls define rooms and zones in order to have them automatically humidity controlled via an associated dehumidifier.

* Rooms - A room consists of a humidity sensor and an optional door sensor for that room.
* Zone - A zone consists of a collection of rooms and a dehumidifier.
    * name - Name for this zone, differs from key in that it is used in the friendly name for the sensor.
    * rooms - Rooms to include in this zone
    * min_humidity - Minimum humidity to use for this zone, when the average falls below this level the dehumidifer will be turned off.
    * max_humidity - Maximum humidity to use for this zone, when the average exceeds this level the dehumidifer will be turned on.
    * dehumidifer_switch - The switch that controls the power to your dehumidifer. This requires either a smart dehumidifer or one that can be left in an 'on' state and just switched via a smart power switch.
    * virtual_sensor - The name for the virtual sensor to create for this zone.  You can use this in other automations if required, or just display it on your dashboard. It's also great for tracking how optimised your configuration is.
    * defer_time - The amount of minutes to defer humidity power switches by. This helps eliminate sudden switching from opening and closing a door.

When the average is calculated, all room sensors are evaluated, if the door sensor is null or open, then the humidity value is included in the average, otherwise it is excluded. Dehumidifiers cannot control the humidity of closed rooms, so this prevents the dehumidifer from over working.

#### Known Issues

* May cause load issues if many zones are configured, as a single sensor change currently causes all zones to be recalculated.  Using a single zone will not result in any additional load.
  - Extract zone reclaulation logic into function
  - Calculate zone of current sensor being evaluated
  - Update only that single zone
* Zones aren't initially calculated, a single sensor update is required. This should be changed so that each zone is forcefully updated after initialisation.
  - Will be much easier after zone recalculation logic is functionised as above


### mold_index.py

This AppDaemon defines a set of zones which consist of a single humidity and temperature sensor.  These do not have to be isolated rooms. Then using the previous 1 hours worth of data, a mold index is created that gives a theoretical change of mold growth.

* Zone - A zone consists of a collection of rooms and a dehumidifier.
    * name - Name for this zone, differs from key in that it is used in the friendly name for the sensor.
    * humidity_sensor - Humidity sensor entity name to use for this zone
    * temperature_sensor - Temperature sensor entity name to use for this zone
    * virtual_sensor - Name of the virtual sensor to create which will store the mold index for this zone
