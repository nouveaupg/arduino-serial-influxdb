from serial.threaded import LineReader, ReaderThread
from influxdb import InfluxDBClient
import serial
import yaml
import traceback
import re
import logging
import time

serial_logger = logging.getLogger("serial")
serial_logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

influx_client = None


def celsius_to_fahrenheit(celsius: float) -> float:
    return (celsius * 1.8) + 32.0


HUMIDITY_REGEX = re.compile("^Humidity: [0-9]{2}\\.00%")
TEMPERATURE_REGEX = re.compile("Temperature: [0-9]{2}\\.[0-9]{2}°C")
HEAT_INDEX_REGEX = re.compile("Heat index: [0-9]{2}\\.[0-9]{2}°C")
TEMPERATURE_VALUE_REGEX = re.compile("[0-9]{2}\\.[0-9]{2}°C")
HUMIDITY_VALUE_REGEX = re.compile("[0-9]{2}\\.00%")


class TemperatureLogger(LineReader):
    def connection_made(self, transport) -> None:
        super(TemperatureLogger, self).connection_made(transport)
        print("Serial connection established.")

    def handle_line(self, line):
        humidity_match = HUMIDITY_REGEX.search(line)
        humidity_value = None
        celsius_temperature = None
        celsius_heat_index = None
        if humidity_match:
            humidity_part = line[humidity_match.start():humidity_match.end()]
            humidity_value_match = HUMIDITY_VALUE_REGEX.search(humidity_part)
            if humidity_value_match:
                humidity_value = int(humidity_part[humidity_value_match.start():humidity_value_match.start()+2])
        temperature_match = TEMPERATURE_REGEX.search(line)
        if temperature_match:
            temperature_part = line[temperature_match.start():temperature_match.end()]
            temp_value_match = TEMPERATURE_VALUE_REGEX.search(temperature_part)
            if temp_value_match:
                celsius_temperature = float(temperature_part[temp_value_match.start():temp_value_match.start()+5])
        heat_index_match = HEAT_INDEX_REGEX.search(line)
        if heat_index_match:
            heat_index_part = line[heat_index_match.start():heat_index_match.end()]
            temp_value_match = TEMPERATURE_VALUE_REGEX.search(heat_index_part)
            if temp_value_match:
                celsius_heat_index = float(heat_index_part[temp_value_match.start():temp_value_match.start() + 5])
        serial_logger.info(line)
        if influx_client and humidity_value and celsius_temperature and celsius_heat_index:
            data = [
                {
                    "measurement": "arduino-dht22",
                    "tags": {
                        "location": "bedroom"
                    },
                    "time": time.ctime(),
                    "fields": {
                        "humidity": humidity_value,
                        "temperature": celsius_temperature,
                        "heat_index": celsius_heat_index,
                        "temperature_fahrenheit": celsius_to_fahrenheit(celsius_temperature),
                        "heat_index_fahrenheit": celsius_to_fahrenheit(celsius_heat_index)
                    }
                }
            ]
            influx_client.write_points(data)

    def connection_lost(self, exc) -> None:
        serial_logger.error("Serial port connection lost.")


if __name__ == "__main__":
    print("DHT Logger v1 - reading config.yaml")
    try:
        config_stream = open("config.yaml", "r")
        config_data = yaml.load(config_stream, yaml.Loader)
        config_stream.close()
        serial_address = config_data.get("serial_address")
        baud_rate = config_data.get("baud_rate")
        serial_port_log_filename = config_data.get("serial_log_filename")
        if serial_port_log_filename:
            fh = logging.FileHandler(serial_port_log_filename)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            serial_logger.addHandler(fh)
        influxdb_host = config_data.get("influxdb_host")
        influxdb_port = config_data.get("influxdb_port")
        influxdb_user = config_data.get("influxdb_user")
        influxdb_passwd = config_data.get("influxdb_passwd")
        influxdb_dbname = config_data.get("influxdb_dbname")
        print(f"Connecting to InfluxDB {influxdb_host}:{influxdb_port}")
        influx_client = InfluxDBClient(influxdb_host, influxdb_port, influxdb_user, influxdb_passwd, influxdb_dbname)
        print(f"Attempting to connect to serial port {serial_address}")
        ser = serial.serial_for_url(serial_address, baudrate=baud_rate, timeout=1)
        thread = ReaderThread(ser, TemperatureLogger)
        thread.run()
    except IOError:
        print("Error reading config.yaml")
    except yaml.YAMLError as e:
        print(f"Error parsing config.yaml file: {e}")
