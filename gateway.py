import socket
import threading
import queue
from concurrent import futures
import gateway_pb2
import greenhouse_pb2

BUFFER_SIZE = 1024
PORT = 50000
GREENHOUSE_PORT = 50001
CLIENT_PORT = 50002

data_buffer = queue.Queue()

def handle_greenhouse(conn, addr):
    print(f"[GREENHOUSE] Connected from {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break

            general_data = greenhouse_pb2.Response()
            general_data.ParseFromString(data)
            print(f"[GREENHOUSE] Received Data: {general_data}")

            with data_buffer.mutex:  
                data_buffer.queue.clear() #clean buffer
            data_buffer.put(general_data)

    except Exception as e:
        print(f"Error on greenhouse: {e}")
    finally:
        conn.close()

def handle_client(conn, addr):
    print(f"[CLIENT] Connected from {addr}")
    try:
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            request = greenhouse_pb2.Command()
            request.ParseFromString(data)
            print(f"[CLIENT] Command received: {request.command}")

            if request.command == "GET":
                response = greenhouse_pb2.Response(response="Data fetched")
                temp_buffer = []

                while not data_buffer.empty():
                    data = data_buffer.get()
                    temp_buffer.append(data)
                    if request.device == 'sensor':
                        if request.feature == 'all':
                            response.device_statuses.extend(
                                [d for d in data.device_statuses if d.device == "sensor"]
                            )
                        else:
                            response.device_statuses.extend(
                                [d for d in data.device_statuses 
                                if d.device == "sensor" and d.feature == request.feature]
                            )

                    elif request.device == 'actuator':
                        if request.actuator == 'all':
                            response.device_statuses.extend(
                                [d for d in data.device_statuses if d.device == "actuator"]
                            )
                        else:
                            response.device_statuses.extend(
                                [d for d in data.device_statuses 
                                if d.device == "actuator" and d.actuator == request.actuator]
                            )
                for item in temp_buffer:
                    data_buffer.put(item)
                conn.send(response.SerializeToString())

            elif request.command == "SET":
                print(f"[CLIENT] Sending command to greenhouse: {request}")
    except Exception as e:
        print(f"Error on Client: {e}")
    finally:
        conn.close()


def start_gateway(port, handler):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    print(f"[SERVER] Listening on port {port}...")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handler, args=(conn, addr)).start()

if __name__ == "__main__":
    with futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(start_gateway, GREENHOUSE_PORT, handle_greenhouse)
        executor.submit(start_gateway, CLIENT_PORT, handle_client)