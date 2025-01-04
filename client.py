import socket
import logging
import greenhouse_pb2

def send_command(command, device, target_feature="", target_actuator="", value=0):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 50002))  # gateway ip and port

        cmd = greenhouse_pb2.Command()
        cmd.command = command
        cmd.device = device
        cmd.feature = target_feature
        cmd.actuator = target_actuator
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
            feature = input("Enter the sensor (humidity, temperature, light): ")
            send_command("GET", "sensor", target_feature=feature)

        elif option == "2":
            feature = input("Enter the actuator category (humidity, temperature, light): ")
            actuator = input("Enter the actuator (irrigator, heater, cooler, lights, curtains): ")
            send_command("GET", "actuator", target_feature=feature, target_actuator=actuator)

        elif option == "3":
            feature = input("Enter the actuator category (humidity, temperature, light): ")
            actuator = input("Enter the actuator (irrigator, heater, cooler, lights, curtains): ")
            value = float(input("Enter the desired value: "))
            send_command("SET", "actuator", target_feature=feature, target_actuator=actuator, value=value)

        elif option == "4":
            print("Exiting the program.")
            break

        else:
            print("Invalid option. Please try again.")