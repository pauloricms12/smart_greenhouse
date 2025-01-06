import socket
import threading
import queue
from concurrent import futures
import greenhouse_pb2
import pymongo

BUFFER_SIZE = 1024
PORT = 50000
GREENHOUSE_PORT = 50001
GREENHOUSE_IP = 'localhost'
CLIENT_PORT = 50002
MULTICAST_GROUP = ('224.1.1.1', 50010)
DEVICE_PORTS = {}

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["greenhouse"]
collection = db["devices"]

data_buffer = queue.Queue()

def listen_multicast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MULTICAST_GROUP))

    mreq = socket.inet_aton(MULTICAST_GROUP[0]) + socket.inet_aton('0.0.0.0')
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"[GATEWAY] Listening for multicast messages on {MULTICAST_GROUP}")
    while True:
        try:

            data, addr = sock.recvfrom(BUFFER_SIZE)
            device_info = greenhouse_pb2.DeviceRegistration()
            device_info.ParseFromString(data)

            DEVICE_PORTS[device_info.name] = device_info.port
            print(f"[GATEWAY] Received multicast from {addr}: {device_info}")
            
            collection.update_one(
                {"name": device_info.name},
                {"$set": {
                    "name": device_info.name,
                    "type": device_info.type,
                    "port": device_info.port
                }},
                upsert=True
            )

            confirmation = greenhouse_pb2.ResponseRegistration(
                    status="registered",
                    device=device_info.name
            )
            sock.sendto(confirmation.SerializeToString(), addr)

        except Exception as e:
            print(f"[GATEWAY] Error processing multicast: {e}")


def send_to_device(request):
    port = DEVICE_PORTS.get(request.name)
    if not port:
        print(f"[GATEWAY] Device {request.name} not found.")
        return None

    try:
        with socket.create_connection((GREENHOUSE_IP, port)) as s:
            s.send(request.SerializeToString())
            data = s.recv(BUFFER_SIZE)
            response = greenhouse_pb2.Response()
            response.ParseFromString(data)
            return response
    except Exception as e:
        print(f"[GATEWAY] Error connecting to {request.name} on port {port}: {e}")
        return None

def handle_client(conn, addr):
    print(f"[CLIENT] Connected from {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            request = greenhouse_pb2.Command()
            request.ParseFromString(data)
            print(f"[CLIENT] Command received: {request.command} for {request.name}")

            response = send_to_device(request)
            if response:
                conn.send(response.SerializeToString())
            else:
                conn.send(b"Device not available or error in communication.")
    except Exception as e:
        print(f"Error on Client: {e}")
    finally:
        conn.close()

def start_gateway(port, handler):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    print(f"[SERVER] Listening Clients on port {port}...")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handler, args=(conn, addr)).start()

if __name__ == "__main__":
    threading.Thread(target=listen_multicast, daemon=True).start()
    start_gateway(CLIENT_PORT, handle_client)

