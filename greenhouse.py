import socket
import threading
import time
import greenhouse_pb2

MULTICAST_GROUP = ('224.1.1.1', 50010)
BUFFER_SIZE = 1024

class Device:
    def __init__(self, type, port, name):
        self.type = type
        self.port = port
        self.name = name

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

                print(f"{self.name} trying to register with gateway")
                
                
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
    def __init__(self, type, port, name, value=0.0, unit=""):  
        super().__init__(type, port, name)
        self.value = value
        self.unit = unit

    def get_status(self):
        response = greenhouse_pb2.Response()
        device_status = response.device_status.add()
        device_status.device = self.type
        device_status.value = self.value
        device_status.unit = self.unit
        return response
    
    def update_value(self, increment, max_value=None, base_value=None):
        if increment == 0 and base_value is not None: #curtains
            self.value = base_value * (1 - (curtains.intensity / 100))
        elif increment == 0 and base_value is None: #lamps
            self.value = max_value
        else: #others
            self.value += increment
            if max_value is not None and self.value > max_value:
                self.value = max_value

class Actuator(Device):
    def __init__(self, type, port, name, unit=""):  
        super().__init__(type, port, name)
        self.on = False
        self.intensity = 0
        self.unit = unit

    def set_status(self, value):
        self.intensity = value
        self.on = value > 0

    def get_status(self):
        response = greenhouse_pb2.Response()
        device_status = response.device_status.add()
        device_status.device = self.type
        device_status.on = self.on
        device_status.value = self.intensity
        device_status.unit = self.unit
        return response

def actuator_on(humidity_sensor, temperature_sensor, light_sensor, irrigator, heater, cooler, lamps, curtains):
    base_light_value = light_sensor.value
    while True:
        if irrigator.on:
            humidity_sensor.update_value(irrigator.intensity * 0.1, max_value=100)
        if heater.on:
            temperature_sensor.update_value(0.01, max_value=heater.intensity)
        if cooler.on:
            temperature_sensor.update_value(-0.01, max_value=cooler.intensity)
        if lamps.on:
            light_sensor.update_value(0, max_value = lamps.intensity)
        if curtains.on:
            light_sensor.update_value(0, base_value=base_light_value)

        time.sleep(1)

if __name__ == "__main__":
    temperature_sensor = Sensor("Sensor", 6001, "Temperature", 22.0, "°C")
    humidity_sensor = Sensor("Sensor", 6003, "Humidity", 60.0, "%")
    light_sensor = Sensor("Sensor", 6004, "Light", 75.0, "lux")

    irrigator = Actuator("Actuator", 6005, "Irrigator", "L/h")
    heater = Actuator("Actuator", 6006, "Heater", "°C")
    cooler = Actuator("Actuator", 6007, "Cooler", "°C")
    lamps = Actuator("Actuator", 6008, "Lamps", "lux")
    curtains = Actuator("Actuator", 6009, "Curtains", "%")

    threading.Thread(target=temperature_sensor.start).start()
    threading.Thread(target=humidity_sensor.start).start()
    threading.Thread(target=light_sensor.start).start()
    threading.Thread(target=irrigator.start).start()
    threading.Thread(target=heater.start).start()
    threading.Thread(target=cooler.start).start()
    threading.Thread(target=lamps.start).start()
    threading.Thread(target=curtains.start).start()

    threading.Thread(target=actuator_on, args=(
        humidity_sensor, temperature_sensor, light_sensor, irrigator, heater, cooler, lamps, curtains)).start()
