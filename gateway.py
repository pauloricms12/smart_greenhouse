import socket
import threading
from concurrent import futures
import greenhouse_pb2

BUFFER_SIZE = 1024
PORT = 50000
GREENHOUSE_PORT = 50001
GREENHOUSE_IP = 'localhost'
CLIENT_PORT = 50002
MULTICAST_GROUP = ('224.1.1.1', 50010)
DEVICE_PORTS = {}

device_status = []
device_status_lock = threading.Lock()

def receive_devices_statuses():
    global device_status

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((GREENHOUSE_IP, GREENHOUSE_PORT))
    sock.listen(5)
    print(f"[GATEWAY] Listening for Greenhouse on port {GREENHOUSE_PORT}...")

    while True:
        conn, addr = sock.accept()
        print(f"[GATEWAY] Connection established with Greenhouse at {addr}")
        try:
            while True:
                data = conn.recv(BUFFER_SIZE)
                if not data:
                    break

                response = greenhouse_pb2.Response()
                response.ParseFromString(data)

                with device_status_lock:
                    device_status = list(response.device_status)

                print("[GATEWAY] Updated device_status:")
                for status in device_status:
                    print(f"  - {status.name}: {status.value} {status.unit} ({status.feature})")
        except Exception as e:
            print(f"[GATEWAY] Error handling Greenhouse connection: {e}")
        finally:
            conn.close()

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
            if request.command == 'GET':
                global device_status

                with device_status_lock:
                    found_status = next(
                        (status for status in device_status if status.name == request.name), None
                    )

                if found_status:
                    response = greenhouse_pb2.Response()
                    device_status_proto = response.device_status.add()
                    device_status_proto.type = found_status.type
                    device_status_proto.name = found_status.name
                    device_status_proto.value = found_status.value
                    device_status_proto.status = "Ligado" if found_status.value else "Desligado"
                    device_status_proto.unit = found_status.unit
                    device_status_proto.feature = found_status.feature
                    conn.send(response.SerializeToString())
                else:
                    response = greenhouse_pb2.Response()
                    response.response = "Device not found."
            elif request.command == 'SET':
                response = send_to_device(request)
                if response:
                    conn.send(response.SerializeToString())
                else:
                    conn.send(b"Device not available or error in communication.")
    except Exception as e:
        print(f"Error on Client: {e}")
    finally:
        conn.close()

def start_client_listener():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", CLIENT_PORT))
    s.listen(5)
    print(f"[SERVER] Listening Clients on port {CLIENT_PORT}...")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    threading.Thread(target=listen_multicast, daemon=True).start()
    threading.Thread(target=receive_devices_statuses, daemon=True).start()
    start_client_listener()

