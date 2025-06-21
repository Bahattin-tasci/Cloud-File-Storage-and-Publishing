# File Sharing Server
import socket
import threading
import os
from tkinter import Tk, Label, Button, Entry, filedialog, Listbox, END, messagebox

# Global variables
server_socket = None
clients = {}
files = {}
folder_path = None
# Adds a message to the server activity log
def log_activity(listbox, message):
    listbox.insert(END, message)
    listbox.see(END)
# Asks for a storage folder for uploaded files.
def create_folder(label_folder, listbox):
    global folder_path
    folder_path = filedialog.askdirectory()
    if folder_path:
        label_folder.config(text=folder_path)
        log_activity(listbox, f"Storage folder set to {folder_path}")
    else:
        messagebox.showerror( "No folder selected")
# Starts the server on the determined port and listens for incoming connections.
def starting_server(port_entry, listbox):
    global server_socket, folder_path
    port = port_entry.get()
    if not port.isdigit():
        messagebox.showerror( "Invalid port number")
        return

    if not folder_path:
        messagebox.showerror( "No storage folder selected")
        return

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", int(port)))
    server_socket.listen(5)

    threading.Thread(target=accept_clients, args=(listbox,), daemon=True).start()
    log_activity(listbox, f"Server started on port {port}")
# Continuously listens for new client connections and creates threads to handle them.
def accept_clients(listbox):
    global server_socket
    while True:
        client_socket, _ = server_socket.accept()
        threading.Thread(target=managing_client, args=(client_socket, listbox), daemon=True).start()
# Handles communication with a connected client, receiving and processing commands.
def managing_client(client_socket, listbox):
    global clients
    try:
        client_name = client_socket.recv(1024).decode()
        if client_name in clients:
            client_socket.send("ERROR: Name already in use.".encode())
            client_socket.close()
            log_activity(listbox, f"Connection rejected: {client_name} (duplicate name)")
            return

        clients[client_name] = client_socket
        client_socket.send("CONNECTED".encode())
        log_activity(listbox, f"Client is connected: {client_name}")

        while True:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            command, *args = data.split(" ")
            if command == "UPLOAD":
                managing_upload(client_socket, client_name, args[0], listbox)
            elif command == "LIST":
                managing_list(client_socket)
            elif command == "DELETE":
                managing_delete(client_socket, client_name, args[0], listbox)
            elif command == "DOWNLOAD":
               managing_download(client_socket, args[0], client_name, listbox)
            else:
                client_socket.send(" Unknown command.".encode())

    except ConnectionResetError:
        pass
    finally:
        log_activity(listbox, f"Client is disconnected: {client_name}")
        del clients[client_name]
        client_socket.close()
# Handles file uploads from clients.
def managing_upload(client_socket, client_name, filename, listbox):
    global files, folder_path

    file_path = os.path.join(folder_path, f"{client_name}_{filename}")
    with open(file_path, "wb") as file:
        while True:
            data = client_socket.recv(1024)
            if data == b"EOF":
                break
            file.write(data)

    files[filename] = (client_name, file_path)
    log_activity(listbox, f"File uploaded: {filename} by {client_name}")
    client_socket.send("UPLOAD SUCCESS".encode())

# Sends a list of available files to the client.
def managing_list(client_socket):
    global files
    try:
        file_list = "\n".join([f"{owner}: {filename}" for filename, (owner, _) in files.items()])
        client_socket.send(file_list.encode() if file_list else "No files available".encode())
    except Exception as e:
        client_socket.send(" Failed to retrieve file list.".encode())


# Handles file deletion requests from clients.
def managing_delete(client_socket, client_name, filename, listbox):
    global files
    if filename in files:
        if files[filename][0] == client_name:
            os.remove(files[filename][1])
            del files[filename]
            log_activity(listbox, f"File deleted: {filename} by {client_name}")
            client_socket.send("DELETE SUCCESS".encode())
        else:
            client_socket.send(" Unauthorized to delete this file.".encode())
    else:
        client_socket.send(" File not found.".encode())

# Handles file download requests from clients.
def managing_download(client_socket, filename, downloader, listbox):
    global files, clients
    try:
        if filename in files:
            file_owner, file_path = files[filename]

           
            client_socket.send("DOWNLOAD READY".encode())
            with open(file_path, "rb") as file:
                while chunk := file.read(1024):
                    client_socket.send(chunk)
            client_socket.send(b"EOF")
            log_activity(listbox, f"File '{filename}' downloaded by {downloader}")

           
        else:
            client_socket.send("ERROR: File not found or unauthorized.".encode())
    except Exception as e:
        log_activity(listbox, f"Error during file download: {e}")
        client_socket.send("File transfer failed.".encode())



# GUI Setup
root = Tk()
root.title("Server")

label_port = Label(root, text="Port:")
label_port.grid(row=0, column=0)

port_entry = Entry(root)
port_entry.grid(row=0, column=1)

creating_folder_button = Button(root, text="Set Folder", command=lambda: create_folder(label_folder, activity_listbox))
creating_folder_button.grid(row=1, column=0)

label_folder = Label(root, text="No folder selected")
label_folder.grid(row=1, column=1)

starting_button = Button(root, text="Start Server", command=lambda: starting_server(port_entry, activity_listbox))
starting_button.grid(row=2, column=0, columnspan=2)

activity_listbox = Listbox(root, width=50, height=20)
activity_listbox.grid(row=3, column=0, columnspan=2)

root.mainloop()