import socket
import threading
import sys
import os

#Function to receive and print the messages from the server
def receive_messages(socket):
    while True:
        try:
            data = socket.recv(1024)
            if not data:
                break
            print(data.decode())
        except OSError as e:
            if e.errno == 10053:
                # Connection closed by the server, silently exit the loop
                break
            else:
                print(f"Error receiving message: {e}")
                break

#Function to send the message to the server
def send_message(socket, message):
    try:
        socket.send(message.encode())
    except socket.error as e:
        print(f"Error sending message: {e}")

#Function to send request for file list
def request_file_list(socket):
    request_message = "!filelist"
    send_message(socket, request_message)

    # Receive and print the file list from the server
    file_list = socket.recv(1024).decode()
    print(file_list)

#Function to send download request for specific file
def download_file(socket, filename):
    request_message = f"{filename} 0"
    send_message(socket, request_message)

    # Receive the file content from the server
    file_content = socket.recv(1024)
    
    # Check if the received content is an error message
    if file_content.startswith(b"Error"):
        print(file_content.decode())
    else:
        # Save the file content to a local file
        with open(filename, "wb") as file:
            file.write(file_content)
        print(f"Downloaded '{filename}' successfully.")

#main function
def main():
    if len(sys.argv) != 4:
        print("Usage: python client.py <username> <server_address> <port>")
        sys.exit(1)

    username = sys.argv[1]
    server_address = sys.argv[2]
    port = int(sys.argv[3])

    # Create a socket to connect to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        client_socket.connect((server_address, port))

        # Send the username to the server
        send_message(client_socket, username)

        # Start a separate thread to receive and print messages from the server
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receive_thread.start()

        #All the info to tell you how to use the instant messenger
        print("To send a private message, use the format: @username message")
        print("To broadcast a message, simply type the message.")
        print("To get the list of files, type: !filelist")
        print("To download a file, type: filename")
        print("To exit, type: $exit")

        while True:
            # Get the user input for sending messages
            try:
                user_input = input()
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt: Typing $exit to exit gracefully.")
                user_input = "$exit"

            # Check if the input is a special command
            if user_input.startswith("!filelist"):
                request_file_list(client_socket)
            elif " " in user_input and user_input.split()[0].startswith("@"):
                # Check if the input is a private message
                recipient, private_message = user_input.split(" ", 1)
                formatted_message = f"{recipient} {private_message}"
                send_message(client_socket, formatted_message)
            elif user_input == "$exit":
                print("Exiting the server. Goodbye!")
                break
            elif " " in user_input:
                # Check if the input is a download request
                filename, seq = user_input.split()
                seq = int(seq)
                download_file(client_socket, filename)
            else:
                # Otherwise, treat it as a broadcast message
                send_message(client_socket, user_input)

    finally:
        # Close the client socket
        client_socket.close()

if __name__ == "__main__":
    main()
