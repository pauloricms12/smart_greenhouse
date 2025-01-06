import socket
import logging
import greenhouse_pb2

def send_command(command, name, value=0):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 50002))  # gateway ip and port

        cmd = greenhouse_pb2.Command()
        cmd.command = command
        cmd.name = name
        cmd.value = value

        client_socket.send(cmd.SerializeToString())

        data = client_socket.recv(1024)
        client_socket.close()

        if data:
            response = greenhouse_pb2.Response()
            try:
                response.ParseFromString(data)
                logging.info(f"Response from server (via Gateway): {response}")
                return response
            except Exception as e:
                logging.error(f"Failed to parse Protobuf message from Gatewat: {e}")
                return "Failed to parse response"
        else:
            logging.warning("No response received from the Gateway.")
            return "No response received from the Gateway."

    except ConnectionRefusedError:
        logging.error("Error: Unable to connect to the Gateway. Make sure it is running.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    while True:
        print("\nCommand Menu:")
        print("1. Check sensor status")
        print("2. Check actuator status")
        print("3. Control an actuator")
        print("4. Exit")

        option = input("Choose an option: ")

        if option == "1":
            sensor = input("Enter the sensor (Humidity, Temperature, Light): ")
            if sensor not in ["Humidity", "Temperature", "Light"]:
                print("Invalid option. Please try again.")
                continue
            send_command("GET", name = sensor)

        elif option == "2":
            actuator = input("Enter the actuator (Irrigator, Heater, Cooler, Lamps, Curtains): ")
            if actuator not in ['Irrigator', 'Irrigator', 'Heater', 'Cooler', 'Lamps', 'Curtains']:
                print("Invalid option. Please try again.")
                continue
            send_command("GET", actuator)

        elif option == "3":
            actuator = input("Enter the actuator (Irrigator, Heater, Cooler, Lamps, Curtains): ")
            if actuator not in ['Irrigator', 'Irrigator', 'Heater', 'Cooler', 'Lamps', 'Curtains']:
                print("Invalid option. Please try again.")
                continue
            value = float(input("Enter the desired value: "))
            send_command("SET", actuator, value=value)

        elif option == "4":
            print("Exiting the program.")
            break

        else:
            print("Invalid option. Please try again.")