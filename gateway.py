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
            general_data = greenhouse_pb2.GeneralResponse()
            general_data.ParseFromString(data)
            print(f"[GREENHOUSE] Received Data: {general_data}")
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
                response = greenhouse_pb2.GeneralResponse(response="Data fetched")
                while not data_buffer.empty():
                    data = data_buffer.get()
                    for device_status in data.device_statuses:
                        response.device_statuses.append(device_status)
                conn.send(response.SerializeToString())
            elif request.command == "SET":
                #send command to greenhouse and get the response
                print(f"[CLIENT] Sending command to greenhouse: {request}")
    except Exception as e:
        print(f"Error on Client: {e}")
    finally:
        conn.close()

def start_server(port, handler):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)
    print(f"[SERVER] Listening on port {port}...")

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handler, args=(conn, addr)).start()

if __name__ == "__main__":
    with futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(start_server, GREENHOUSE_PORT, handle_greenhouse)
        executor.submit(start_server, CLIENT_PORT, handle_client)