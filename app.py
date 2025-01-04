import greenhouse_pb2

# Criar uma mensagem de registro de dispositivo
device = greenhouse_pb2.DeviceRegistration()
device.device_name = "SensorTemperatura"
device.device_type = "sensor"
device.ip_address = "192.168.1.10"
device.port = 5001

# Serializar
serialized_data = device.SerializeToString()

# Deserializar
print('\n\n', serialized_data)
received_device = greenhouse_pb2.DeviceRegistration()
received_device.ParseFromString(serialized_data)
print(received_device)
