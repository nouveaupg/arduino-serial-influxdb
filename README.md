# DHT22 Logging to InfluxDB via USB serial with Arduino

A lot of projects use the GPIO pins on Raspberry Pi to read the DHT22 sensor but that is really a waste in my opinion. Usually InfluxDB and Grafana are also installed on the RaspberryPi.

I think a better approach is to use cheaper Arduinos and then run this script on a Raspberry Pi that connects to a central InfluxDB server for aggregating many sensors together. This will run on just about anything that supports Python 3, it was developed for Ubuntu and can really be adapted to read any sensor via the USB bus.

### Installation
**You might need to adjust your permissions (like add the local user you're running this as to a certain group) to access the USB serial port without running as root.**
~~~
$ python3 -m venv venv
$ . venv/bin/activate
$ (venv) pip install -r requirements.txt
$ (venv) python dht_logger.py
~~~
config.yaml has all the configuration you need. Not sure if you need to install the Influx client program to use the Python libraries.

TODO: Setup a slick systemd service file to manage this.

Tried using the Async functionality at first but as normal this is a slow sense and "threading" in Python works fine a 9800 baud. DHT33 is a slow sensor.
