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

# Centralize active devices
def updates(*devices):
    curtains_base_value = None
    while True:
        for device in devices:
            if isinstance(device, Sensor) and device.feature == "Humidity" and any(act.name == "Irrigator" and act.on for act in devices if isinstance(act, Actuator)):
                device.update_value(3, max_value=99.5)
            elif isinstance(device, Sensor) and device.feature == "Temperature":
                heater = next((act for act in devices if act.name == "Heater" and act.on), None)
                cooler = next((act for act in devices if act.name == "Cooler" and act.on), None)
                if heater:
                    device.update_value(2, max_value=heater.value - 0.1)
                if cooler:
                    device.update_value(-2, max_value=cooler.value + 0.1)
            elif isinstance(device, Sensor) and device.feature == "Light":
                lamps = next((act for act in devices if act.name == "Lamps" and act.on), None)
                curtains = next((act for act in devices if act.name == "Curtains"), None)
                if lamps:
                    device.update_value(0, max_value=lamps.value)
                if curtains:
                    if curtains.on:
                        if curtains_base_value is None:
                            curtains_base_value = device.value
                        device.update_value(0, base_value=curtains_base_value, curtains_intensity=curtains.value)
                    else:
                        curtains_base_value = None

        time.sleep(1)

def send_status_to_gateway(devices):
    while True:
        try:
            with socket.create_connection((GATEWAY_IP, GATEWAY_PORT)) as s:

                response = greenhouse_pb2.Response()
                for device in devices:
                    device_status = response.device_status.add()
                    device_status.name = device.name
                    device_status.type = device.type
                    device_status.value = device.value
                    device_status.status = "On" if device.value else "Off"
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
    temperature_sensor = Sensor("Sensor", "Temperature", 6001, "Temperature Sensor", 22.0, "°C")
    humidity_sensor = Sensor("Sensor", "Humidity", 6002, "Humidity Sensor", 60.0, "%")
    light_sensor = Sensor("Sensor", "Light", 6003, "Light Sensor", 75.0, "lux")

    # Atuadores
    irrigator = Actuator("Actuator", "Humidity", 6004, "Irrigator", "L/h")
    heater = Actuator("Actuator", "Temperature", 6005, "Heater", "°C")
    cooler = Actuator("Actuator", "Temperature", 6006, "Cooler", "°C")
    lamps = Actuator("Actuator", "Light", 6007, "Lamps", "lux")
    curtains = Actuator("Actuator", "Light", 6008, "Curtains", "%")

    active_devices = [
        cooler,
        temperature_sensor
    ]

    for device in active_devices:
        threading.Thread(target=device.start).start()

    threading.Thread(target=updates, args=(temperature_sensor, humidity_sensor, light_sensor, irrigator, heater, cooler, lamps, curtains), daemon=True).start()
    threading.Thread(target=send_status_to_gateway, args=(active_devices,), daemon=True).start()
