import socket
import threading

def handle_client(client_socket):
    while True:
        # Receive data from the client
        data = client_socket.recv(1024)
        if not data:
            break

        # Print the received data
        print(f"Received from {client_socket.getpeername()}: {data.decode('utf-8')}")

        # Echo the data back to the client
        client_socket.send(data)

    # Close the client socket when the loop ends
    client_socket.close()

def main():
    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a specific address and port
    server_socket.bind(("127.0.0.1", 12345))

    # Enable the server to accept connections
    server_socket.listen(5)
    print("Server listening on 127.0.0.1:12345")

    try:
        while True:
            # Wait for a connection from a client
            client_socket, client_address = server_socket.accept()
            print(f"Accepted connection from {client_address}")

            # Start a new thread to handle the client
            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()

    except KeyboardInterrupt:
        print("Server shutting down.")
        server_socket.close()

if __name__ == "__main__":
    main()
