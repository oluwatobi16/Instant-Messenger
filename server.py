import socket
import threading
import sys
import os
from datetime import datetime
import zlib


clients = {}  # Dictionary to store connected clients

#Functions from common.py file shown in lectures.

#Function to read the filenames
def read_file(filename):
    with open(filename, "rb") as f:
        content = f.read()
    return content

def checksum(data):
    return (zlib.crc32(data) & 0xffffffff).to_bytes(4, byteorder="big")

# Function to check for file corruptions using checksum
def is_not_corrupt(packet, offset=1):
    segment = packet[offset:]
    packet_checksum = packet[:offset]
    calculated_checksum = checksum(segment)
    return packet_checksum == calculated_checksum

# Function to create a packet using the message segment, sequence number seq, and checksum
def make_pkt(segment, seq):
    
    seq_bytes = seq.to_bytes(4, byteorder="big")
    checksum_value = checksum(segment)
    return seq_bytes + segment + checksum_value

def handle_file_list(client_socket):
    # Get the list of files in the download folder
    files = os.listdir("downloads")

    # Send the list to the client
    file_list_message = "File List:\n" + "\n".join(files)
    client_socket.send(file_list_message.encode())

def handle_file_download(client_socket, filename):
    try:
        file_content = read_file(os.path.join("downloads", filename))
        seq = 0
        chunk_size = 1024

        while seq * chunk_size < len(file_content):
            start = seq * chunk_size
            end = (seq + 1) * chunk_size
            segment = file_content[start:end]
            packet = make_pkt(segment, seq)
            client_socket.send(packet)
            ack = client_socket.recv(1024)

            # Check for corruption and resend if needed
            if not is_not_corrupt(ack):
                continue

            seq += 1

        # Send an end-of-file marker
        client_socket.send(make_pkt(b"", seq))
    except FileNotFoundError:
        error_message = f"Error: File '{filename}' not found."
        client_socket.send(error_message.encode())

def broadcast_to_clients(message, exclude_client=None):
    # Broadcast the message to all connected clients excluding the specified client
    for client_name, client_socket in clients.items():
        if client_name != exclude_client:
            client_socket.send(message.encode())


#Function that handles the different client sockets
def handle_client(client_socket, client_name):
    # Add client connection to the Log client 
    log_connection = f"{datetime.now()} - {client_name} connected.\n"
    with open("server.log", "a") as log_file:
        log_file.write(log_connection)

    # Send welcome message to the client
    welcome_message = "Welcome to the server!"
    client_socket.send(welcome_message.encode())

    # Notify all clients about the new connection
    join_message = f"{client_name} has joined."
    broadcast_to_clients(join_message, exclude_client=client_name)

    file_list_requested = False

    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break

            decoded_data = data.decode()

            # Log the message to server.log
            log_message = f"{datetime.now()} - {client_name}: {decoded_data}\n"
            with open("server.log", "a") as log_file:
                log_file.write(log_message)

            # Check if the message is a file list request
            if decoded_data == "!filelist" and not file_list_requested:
                # Set a flag to indicate file list is requested
                file_list_requested = True
                # Handle file list request asynchronously using non-blocking socket
                threading.Thread(target=handle_file_list, args=(client_socket,), daemon=True).start()
            elif decoded_data.startswith("@"):
                recipient_name, message = decoded_data[1:].split(" ", 1)
                if recipient_name in clients:
                    recipient_socket = clients[recipient_name]
                    recipient_socket.send(f"(Private from {client_name}): {message}".encode())
                else:
                    client_socket.send(f"User '{recipient_name}' not found.".encode())
            elif " " in decoded_data:
                # Check if the message is a file download request
                filename, seq = decoded_data.split()
                seq = int(seq)
                handle_file_download(client_socket, filename)
            else:
                # Broadcast the message to all connected clients excluding the sender
                broadcast_message = f"{client_name}: {decoded_data}"
                broadcast_to_clients(broadcast_message, exclude_client=client_name)
        except (socket.error, ConnectionResetError):
            break  # Handle the exception gracefully for client disconnection

    # Print and Log the client disconnections
    log_disconnection = f"{datetime.now()} - {client_name} ({client_socket.getpeername()}) disconnected.\n"
    print(f"{client_socket.getpeername()} disconnected")
    with open("server.log", "a") as log_file:
        log_file.write(log_disconnection)

    # Notify all clients about the disconnection except the
    leave_message = f"{client_name} has left."
    broadcast_to_clients(leave_message, exclude_client=client_name)


    # Remove the client from the dictionary when done
    del clients[client_name]

    # Close the client socket
    client_socket.close()

def start_server(port):
    # Create a server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the server socket to a specific address and port
    server_socket.bind(('0.0.0.0', port))

    # Enable the server to accept connections
    server_socket.listen(5)
    print(f"Server listening on 127.0.0.1: {port}")

    while True:
        # Accept a client connection
        client_socket, addr = server_socket.accept()

        # Get the client name from the client
        client_name = client_socket.recv(1024).decode()

        # Store the client in the dictionary
        clients[client_name] = client_socket

        # Print and log the accepted connection address and port number
        print(f"Accepted connection from {addr[0]}:{addr[1]} for {client_name}")
        # Log client connection
        log_connection = f"{datetime.now()} - Accepted a connection from {addr[0]}:{addr[1]} for {client_name}.\n"
        with open("server.log", "a") as log_file:
            log_file.write(log_connection)

        # Create a new thread to handle the client
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_name))
        client_handler.start()

#main function
def main():
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    start_server(port)

if __name__ == "__main__":
    main()
