"""MQTT client that logs energy consumption of Shelly Plugs.

This is a MQTT client that logs energy consumption of devices plugged into
a Shelly Plug. Voltage, current, instantaneous active power, and total energy
consumed are logged to a csv file. The Plug must run a script that publishes 
Switch.GetStatus status to a MQTT Broker, see mqtt-switch-status-announce.js.
Have only tested Shelly PlugPlus US but other Shelly IoT devices should work.

Typical usage example:

* Configure Shelly Plug to run a script that publishes Switch.GetStatus status
to a MQTT Broker.
* Set BROKER to your MQTT Broker IP address.
* Set CSV_FILE_NAME to the file where you want to log the plug's data.
* Add a dict entry to APPLIANCE_TOPICS that maps your plug's MQTT topic
with the appliance name.
* Run this program: $ python3 elogger.py

Copyright (c) Lindo St. Angel 2023.
"""

import sys
import csv
import json
import pytz
from datetime import datetime
from time import time
from collections.abc import MutableMapping

import paho.mqtt.client as mqtt

# MQTT broker IP addr.
BROKER = 'localhost'
# Full path to output CSV file.
CSV_FILE_NAME = '/home/lindo/develop/simple-energy-logger/appliance_energy_data.csv'
# MQTT topics to subscribe to with appliance name mapping.
APPLIANCE_TOPICS = {
    'shellyplugus-c049ef8c27a0/status/switch:0': 'microwave',
    'shellyplugus-c049ef8be948/status/switch:0': 'kettle',
    'shellyplugus-c049ef8bf230/status/switch:0': 'dishwasher'
    # add more here
}

def _flatten_dict_gen(d, parent_key, sep):
    """Recursive generator for flatten_dict()"""
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v

def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.'):
    """Flattens a dict"""
    return dict(_flatten_dict_gen(d, parent_key, sep))

def on_connect(client, userdata, flags, rc):
    """Callback for when the client receives a CONNACK response from the server"""
    print(f'Connected with result code {rc}.')
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    topics = [(k, 0) for k, _ in APPLIANCE_TOPICS.items()]
    print(f'Subscribing to topics {topics}.')
    res, mid = client.subscribe(topics)
    if res != mqtt.MQTT_ERR_SUCCESS:
        print(f'Subscription error {res}, message ID {mid}.')
        sys.exit(1)

def on_message(client, userdata, msg):
    """Callback for when a PUBLISH message is received from the server"""
    #print(f'topic {msg.topic} payload {msg.payload}')
    csv_writer = userdata['csv_writer']
    fieldnames = userdata['fieldnames']
    if msg.topic in APPLIANCE_TOPICS:
        # Convert msg json to dict and flatten.
        sample = flatten_dict(json.loads(msg.payload))
        # Add appliance name.
        sample['appliance'] = APPLIANCE_TOPICS[msg.topic]
        # Add UTC datetime.
        sample['date'] = datetime.now(pytz.utc)
        # Add timestamp.
        sample['time'] = round(time(), 2)
        # Write sample dict to csv file.
        # Note: sample keys not in csv fieldnames are ignored.
        print(f'Writing {({k: v for k, v in sample.items() if k in fieldnames})}.')
        csv_writer.writerow(sample)

def on_log(client, userdata, level, buf):
    """Callback for logging"""
    print(f'log {buf}')

if __name__ == '__main__':
    client = mqtt.Client(protocol=mqtt.MQTTv311)
    client.on_connect = on_connect
    client.on_message = on_message
    #client.on_log = on_log

    # Establish unsecured connection with broker.
    # NB: use unsecured connection only if broker is on an internal server.
    client.connect(host=BROKER, port=1883, keepalive=60)

    with open(CSV_FILE_NAME, 'w') as csv_file:
        print(f'Opened CSV file {CSV_FILE_NAME}.')
        fieldnames = [
            'date',         # datetime
            'time',         # timestamp
            'appliance',    # appliance name
            'voltage',      # voltage in Volts
            'current',      # current in Amps
            'apower',       # instantaneous active power in Watts
            'aenergy.total' # total energy in Watt-hours
        ]
        csv_writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            extrasaction='ignore'
        )
        csv_writer.writeheader()
        client.user_data_set({'csv_writer': csv_writer, 'fieldnames': fieldnames})
        # Blocking call that processes network traffic, dispatches callbacks
        # and handles reconnecting.
        try:
            client.loop_forever()
        except KeyboardInterrupt:
            print('Got keyboard interrupt.')
            sys.exit(0)