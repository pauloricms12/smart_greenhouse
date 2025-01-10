import socket
import threading
import time
import greenhouse_pb2
import random

MULTICAST_GROUP = ('224.1.1.1', 50010)
BUFFER_SIZE = 1024
GATEWAY_IP = 'localhost'
GATEWAY_PORT = 50001

class Device:
    def __init__(self, type, feature, port, name):
        self.type = type
        self.port = port
        self.name = name
        self.feature = feature

    def start(self):
        self.multicast()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("localhost", self.port))
        sock.listen(5)
        print(f"{self.type} {self.name} listening on port {self.port}")
        
        while True:
            conn, addr = sock.accept()
            threading.Thread(target=self.handle_request, args=(conn,)).start()

    def handle_request(self, conn):
        data = conn.recv(1024)
        if data:
            command = greenhouse_pb2.Command()
            command.ParseFromString(data)
            
            if command.command == "SET":
                self.set_status(command.value)
                response = greenhouse_pb2.Response()
                response.response = "Status updated successfully."
                conn.send(response.SerializeToString())
            elif command.command == "GET":
                response = self.get_status()
                conn.send(response.SerializeToString())
        conn.close()

    def set_status(self, value):
        raise NotImplementedError

    def get_status(self):
        raise NotImplementedError

    def multicast(self):
        def device_registration():
            while True:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(5)

                device_info = greenhouse_pb2.DeviceRegistration(
                    name=self.name,
                    type=self.type,
                    port=self.port
                )

                print(f"{self.name} sending multicast")
                
                
                try:
                    sock.sendto(device_info.SerializeToString(), MULTICAST_GROUP)
                    print(f"{self.name} sent multicast registration to {MULTICAST_GROUP}")
            
                    data, addr = sock.recvfrom(BUFFER_SIZE)

                    response = greenhouse_pb2.ResponseRegistration()
                    response.ParseFromString(data)

                    if response.status == "registered" and response.device == self.name:
                        print(f"{self.name} registered on gateway: {response}")
                        while True:
                            sock.sendto(device_info.SerializeToString(), MULTICAST_GROUP)
                            print(f"{self.name} sent multicast registration to {MULTICAST_GROUP} again for confirmation")
                            time.sleep(60)
                        break
                except socket.timeout:
                    print(f"{self.name} not registered")
                    continue
                except Exception as e:
                    print(f"Error on device registration{self.name}: {e}")
                    break
                finally:
                    sock.close()
        threading.Thread(target=device_registration, daemon=True).start()
         

class Sensor(Device):
    def __init__(self, type, feature, port, name, value=0.0, unit=""):  
        super().__init__(type, feature, port, name)
        self.value = value
        self.unit = unit

    def get_status(self):
        response = greenhouse_pb2.Response()
        device_status = response.device_status.add()
        device_status.type = self.type
        device_status.value = self.value
        device_status.unit = self.unit
        return response
    
    def update_value(self, increment, max_value=None, base_value=None, curtains_intensity=None):
        if increment == 0 and base_value is not None: #curtains
            if curtains_intensity is not None and curtains_intensity > 0:
                self.value = base_value * (1 - (curtains_intensity / 100))
            else: #if turn off courtains
                self.value = base_value / (curtains_intensity / 100) if curtains_intensity and curtains_intensity > 0 else base_value
        elif increment == 0 and base_value is None: #lamps
            self.value = max_value
        elif increment < 0:#cooler
            self.value += increment
            if max_value is not None and self.value < max_value:
                self.value = max_value
        else: #others
            self.value += increment
            if max_value is not None and self.value > max_value:
                self.value = max_value

class Actuator(Device):
    def __init__(self, type, feature, port, name, unit=""):  
        super().__init__(type, feature, port, name)
        self.on = False
        self.value = 0
        self.unit = unit

    def set_status(self, value):
        self.value = value
        self.on = value > 0

    def get_status(self):
        response = greenhouse_pb2.Response()
        device_status = response.device_status.add()
        device_status.name = self.name
        device_status.type = self.type
        device_status.on = self.on
        device_status.status = "On" if self.on else "Off"
        device_status.value = self.value
        device_status.unit = self.unit
        return response

def updates(humidity_sensor, temperature_sensor, light_sensor, irrigator, heater, cooler, lamps, curtains):
    curtains_base_value = None
    while True:
        if irrigator.on:
            humidity_sensor.update_value(irrigator.value * 1, max_value=99.5)
        if heater.on:
            temperature_sensor.update_value(0.5, max_value=heater.value - 0.1)
        if cooler.on:
            temperature_sensor.update_value(-0.5, max_value=cooler.value + 0.1)
        if lamps.on:
            light_sensor.update_value(0, max_value=lamps.value)
        if curtains.on:
            if curtains_base_value is None:
                curtains_base_value = light_sensor.value
            light_sensor.update_value(0, base_value=curtains_base_value, curtains_intensity=curtains.value)
        else: #turn off curtains
            if curtains_base_value is not None:
                light_sensor.update_value(0, base_value=curtains_base_value, curtains_intensity=curtains.value)
            curtains_base_value = None
        humidity_sensor.value += random.choice([0.5, -0.5])
        humidity_sensor.value = min(max(humidity_sensor.value, 0), 100)
        temperature_sensor.value += random.choice([0.1, -0.1])
        light_sensor.value += random.choice([1, -1])

        time.sleep(2)

def send_status_to_gateway(devices):
    while True:
        try:
            with socket.create_connection((GATEWAY_IP, GATEWAY_PORT)) as s:

                response = greenhouse_pb2.Response()
                for device in devices:
                    device_status = response.device_status.add()
                    device_status.name = device.name
                    device_status.type = device.type
                    device_status.status = device.status
                    device_status.value = device.value
                    device_status.unit = device.unit
                    device_status.feature = device.feature

                s.sendall(response.SerializeToString())
                print("[Greenhouse] Sent status to Gateway.")

            time.sleep(2)  
        except Exception as e:
            print(f"[Greenhouse] Error sending status to Gateway: {e}")
            time.sleep(1)

if __name__ == "__main__":
    # Sensores
    temperature_sensor = Sensor(
        type="Sensor", 
        port=6001, 
        name="Temperature Sensor", 
        feature="Temperature", 
        value=22.0, 
        unit="°C"
    )
    threading.Thread(target=temperature_sensor.start).start()

    humidity_sensor = Sensor(
        type="Sensor", 
        port=6002, 
        name="Humidity Sensor", 
        feature="Humidity", 
        value=60.0, 
        unit="%"
    )
    threading.Thread(target=humidity_sensor.start).start()

    light_sensor = Sensor(
        type="Sensor", 
        port=6003, 
        name="Light Sensor", 
        feature="Light", 
        value=75.0, 
        unit="lux"
    )
    threading.Thread(target=light_sensor.start).start()

    # Atuadores
    irrigator = Actuator(
        type="Actuator", 
        feature="Humidity",  
        port=6004, 
        name="Irrigator", 
        unit="L/h"
    )
    threading.Thread(target=irrigator.start).start()

    heater = Actuator(
        type="Actuator", 
        feature="Temperature",  
        port=6005, 
        name="Heater", 
        unit="°C"
    )
    threading.Thread(target=heater.start).start()

    cooler = Actuator(
        type="Actuator", 
        feature="Temperature",  
        port=6006, 
        name="Cooler", 
        unit="°C"
    )
    threading.Thread(target=cooler.start).start()

    lamps = Actuator(
        type="Actuator",
        feature="Light",  
        port=6007, 
        name="Lamps", 
        unit="lux"
    )
    threading.Thread(target=lamps.start).start()

    curtains = Actuator(
        type="Actuator",
        feature="Light",  
        port=6008, 
        name="Curtains", 
        unit="%"
    )
    threading.Thread(target=curtains.start).start()


    devices = [humidity_sensor, temperature_sensor, light_sensor, irrigator, heater, cooler, lamps, curtains]

   

    threading.Thread(target=updates, args=(*devices,), daemon=True).start()
    threading.Thread(target=send_status_to_gateway, args=(devices, ), daemon=True).start()
