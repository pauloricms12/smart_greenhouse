import socket
import threading
import time
import greenhouse_pb2
import logging

GREENHOUSE_PORT = 6000
GATEWAY_IP = 'localhost'
GATEWAY_PORT = 50001

class Greenhouse:
    def __init__(self, humiditycontrol, temperaturecontrol, lightcontrol):
        self.humiditycontrol = humiditycontrol
        self.temperaturecontrol = temperaturecontrol
        self.lightcontrol = lightcontrol

        self.sensors = {
            "humidity": lambda: self.humiditycontrol.humidity_value,
            "temperature": lambda: self.temperaturecontrol.temperature_value,
            "light": lambda: self.lightcontrol.light_value
        }

        self.actuators = {
            "humidity": {
                "irrigator": {
                    "status": lambda: self.humiditycontrol.irrigator_on,
                    "value": lambda: self.humiditycontrol.irrigator_intensity if self.humiditycontrol.irrigator_on else 0,
                    "set": lambda value: self._set_irrigator(value)
                }
            },
            "temperature": {
                "heater": {
                    "status": lambda: self.temperaturecontrol.heater_on,
                    "value": lambda: self.temperaturecontrol.heater_intensity if self.temperaturecontrol.heater_on else 0,
                    "set": lambda value: self._set_heater(value)
                },
                "cooler": {
                    "status": lambda: self.temperaturecontrol.cooler_on,
                    "value": lambda: self.temperaturecontrol.cooler_intensity if self.temperaturecontrol.cooler_on else 0,
                    "set": lambda value: self._set_cooler(value)
                }
            },
            "light": {
                "lights": {
                    "status": lambda: self.lightcontrol.lights_on,
                    "value": lambda: self.lightcontrol.lights_intensity if self.lightcontrol.lights_on else 0,
                    "set": lambda value: self._set_lights(value)
                },
                "curtains": {
                    "status": lambda: self.lightcontrol.curtains_open,
                    "value": lambda: self.lightcontrol.curtains_quantity if self.lightcontrol.curtains_open else 0,
                    "set": lambda value: self._set_courtains(value)
                }
            }
        }

    def _set_irrigator(self, value):
        if value < 0:
            raise ValueError("Irrigator intensity cannot be negative.")
        self.humiditycontrol.irrigator_intensity = value
        self.humiditycontrol.irrigator_on = value > 0

    def _set_heater(self, value):
        if value < 0:
            raise ValueError("Heater intensity cannot be negative.")
        self.temperaturecontrol.heater_intensity = value
        self.temperaturecontrol.heater_on = value > 0

    def _set_cooler(self, value):
        if value < 0:
            raise ValueError("Cooler intensity cannot be negative.")
        self.temperaturecontrol.cooler_intensity = value
        self.temperaturecontrol.cooler_on = value > 0

    def _set_lights(self, value):
        if value < 0:
            raise ValueError("Lights intensity cannot be negative.")
        self.lightcontrol.lights_intensity = value
        self.lightcontrol.lights_on = value > 0

    def _set_courtains(self, value):
        if value < 0:
            raise ValueError("Courtains quantity cannot be negative.")
        self.lightcontrol.curtains_quantity = value
        self.lightcontrol.curtains_open = value > 0

    def sensor_value(self, feature):
        return self.sensors.get(feature, lambda: "Feature Not Found. Try humidity, temperature or light")()

    def control_actuator(self, feature, actuator, value):
        return self.actuators.get(feature, {}).get(actuator, {}).get("set", lambda v: "Actuator Not Found.")(value)

    def actuator_status(self, feature, actuator):
        return {
            "status": "On" if(act := self.actuators.get(feature, {}).get(actuator, {})).get("status", lambda: False)() else "Off",
            "value": act.get("value", lambda: 0)()
        } if feature in self.actuators and actuator in self.actuators[feature] else "Actuator Not Found."
    

    def send_data(self, gateway_ip, gateway_port):
        while True:
            try:
                conn = socket.create_connection((gateway_ip, gateway_port))
                response = greenhouse_pb2.Response()

                humidity_sensor = response.device_statuses.add()
                humidity_sensor.feature = "humidity"
                humidity_sensor.device = "sensor"
                humidity_sensor.value = self.humiditycontrol.humidity_value
                humidity_sensor.unit = self.humiditycontrol.humidity_unit

                irrigator = response.device_statuses.add()
                irrigator.device = "actuator"
                irrigator.actuator = "irrigator"
                irrigator.value = self.humiditycontrol.irrigator_intensity
                irrigator.unit = self.humiditycontrol.irrigator_unit
                irrigator.on = self.humiditycontrol.irrigator_on
                irrigator.status = "Ligado" if self.humiditycontrol.irrigator_on else "Desligado"

                temperature_sensor = response.device_statuses.add()
                temperature_sensor.feature = "temperature"
                temperature_sensor.device = "sensor"
                temperature_sensor.value = self.temperaturecontrol.temperature_value
                temperature_sensor.unit = self.temperaturecontrol.temperature_unit

                heater = response.device_statuses.add()
                heater.device = "actuator"
                heater.actuator = "heater"
                heater.value = self.temperaturecontrol.heater_intensity
                heater.unit = self.temperaturecontrol.heater_unit
                heater.on = self.temperaturecontrol.heater_on
                heater.status = "Ligado" if self.temperaturecontrol.heater_on else "Desligado"

                cooler = response.device_statuses.add()
                cooler.device = "actuator"
                cooler.actuator = "cooler"
                cooler.value = self.temperaturecontrol.cooler_intensity
                cooler.unit = self.temperaturecontrol.cooler_unit
                cooler.on = self.temperaturecontrol.cooler_on
                cooler.status = "Ligado" if self.temperaturecontrol.cooler_on else "Desligado"

                light_sensor = response.device_statuses.add()
                light_sensor.feature = "light"
                light_sensor.device = "sensor"
                light_sensor.value = self.lightcontrol.light_value
                light_sensor.unit = self.lightcontrol.light_unit

                lights = response.device_statuses.add()
                lights.device = "actuator"
                lights.actuator = "lights"
                lights.on = self.lightcontrol.lights_on
                lights.status = "Ligado" if self.lightcontrol.lights_on else "Desligado"
                lights.value = self.lightcontrol.lights_intensity
                lights.unit = self.lightcontrol.lights_unit

                curtains = response.device_statuses.add()
                curtains.device = "actuator"
                curtains.actuator = "curtains"
                curtains.value = self.lightcontrol.curtains_intensity
                curtains.unit = self.lightcontrol.curtains_unit
                curtains.on = self.lightcontrol.curtains_open
                curtains.status = "Ligado" if self.lightcontrol.curtains_open else "Desligado"

                conn.sendall(response.SerializeToString())
                logging.debug(f"Serialized response: {response}")
                conn.close()
            except Exception as e:
                logging.error(f"Failed to send data to gateway: {e}")
            time.sleep(10)


    def handle_request(self, conn):
        data = conn.recv(1024)
        if data:
            command = greenhouse_pb2.Command()
            command.ParseFromString(data)
            if command.command == "GET":
                response = greenhouse_pb2.Response()
                response.response = "Data fetched"
                for feature, actuator in self.actuators.items():
                    for act_name, act in actuator.items():
                        response.device_statuses.add(
                            feature=feature,
                            value=act['value'](),
                            status=act['status']()
                        )
                conn.send(response.SerializeToString())

            elif command.command == "SET":
                self.control_actuator(command.feature, command.actuator, command.value)
                conn.send(b"Actuator set successfully.")
        conn.close()

    
    def start(self, port, gateway_ip, gateway_port):
        threading.Thread(target=self.send_data, args=(gateway_ip, gateway_port)).start()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('localhost', port))
        server.listen(5)
        print(f"Greenhouse listening on port {port}")

        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_request, args=(conn,)).start()


if __name__ == "__main__":
    humidity_control = greenhouse_pb2.HumidityControl(humidity_value=60.0, humidity_unit='%',irrigator_on=False, irrigator_intensity=0, irrigator_unit='L/h')
    temperature_control = greenhouse_pb2.TemperatureControl(temperature_value=22.0,temperature_unit='°C', heater_on=False, heater_intensity=0, heater_unit='°C', cooler_on=False, cooler_intensity=0, cooler_unit='°C')
    light_control = greenhouse_pb2.LightControl(light_value=75.0, light_unit='lux', lights_on=False, lights_intensity=0, lights_unit='lux', curtains_open=False, curtains_intensity=0, curtains_unit='%')

    greenhouse = Greenhouse(humidity_control, temperature_control, light_control)
    greenhouse.start(GREENHOUSE_PORT, GATEWAY_IP, GATEWAY_PORT)