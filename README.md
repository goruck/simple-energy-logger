# simple-energy-logger

MQTT client that logs energy consumption of Shelly Plugs.

This is a MQTT client that logs energy consumption of devices plugged into
a Shelly Plug. Voltage, current, instantaneous active power, and total energy
consumed are logged to a csv file. The Plug must run a script that publishes 
Switch.GetStatus status to a MQTT Broker. Have only tested Shelly PlugPlus US but other Shelly IoT devices should work.

Typical usage example:

* Configure Shelly Plug to run ```mqtt-switch-status-announce.js``` that publishes ```Switch.GetStatus``` status
to a MQTT Broker.
* In ```elogger.py```:
    * Set ```BROKER``` to your MQTT Broker IP address.
    * Set ```CSV_FILE_NAME``` to the file where you want to log the plug's data.
    * Add a dict entry to ```APPLIANCE_TOPICS``` that maps your plug's MQTT topic
to the appliance name.
* Run MQTT logger client program: ```$ python3 elogger.py```