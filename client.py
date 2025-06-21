# Client-Server File Transfer Application
import socket
import threading
from tkinter import Tk, Label, Button, Entry, filedialog, simpledialog, Listbox, END, messagebox

# Global variables
client_socket = None
connected = False
# Add message to the log and scroll to the bottom
def updates_log(listbox, message):
    listbox.insert(END, message)
    listbox.see(END)
# Connect to the server and handle connection status
def connect_to_server(entry_name, server_entry, port_entry, listbox, buttons):
    global client_socket, connected
    name = entry_name.get()
    server_ip = server_entry.get()
    port = port_entry.get()
    # Validation of inputs
    if not name or not server_ip or not port.isdigit():
        messagebox.showerror("Error", "All fields must be filled correctly")
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, int(port)))
        client_socket.send(name.encode())
        response = client_socket.recv(1024).decode()

        if response == "CONNECTED":
            connected = True
            updates_log(listbox, f"Connected to server as {name}")
            button_enablers(buttons)
        else:
            messagebox.showerror("Error", response)
            client_socket.close()

    except Exception as e:
        messagebox.showerror("Error", f"Connection failed: {e}")
# Enables action buttons
def button_enablers(buttons):
    for button in buttons:
        button.config(state="normal")
# Uploads a file to the server
def uploading_files(listbox):
    global client_socket
    if not connected:
        messagebox.showerror("Error", "Not connected to server")
        return

    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    filename = file_path.split("/")[-1]
    try:
        client_socket.send(f"UPLOAD {filename}".encode())
        with open(file_path, "rb") as file:
            while chunk := file.read(1024):
                client_socket.send(chunk)
        client_socket.send(b"EOF")

        response = client_socket.recv(1024).decode()
        updates_log(listbox, response)
    except Exception as e:
        messagebox.showerror( f"Upload failed: {e}")
# Lists files on the server
def listing_files(listbox):
    global client_socket
    if not connected:
        messagebox.showerror( "Not connected to server")
        return

    try:
        client_socket.send("LIST".encode())
        file_list = client_socket.recv(4096).decode()
        if file_list.startswith("ERROR"):
            messagebox.showerror("Error", file_list)
        else:
            updates_log(listbox, "Files on server:")
            updates_log(listbox, file_list if file_list else "No files found")
    except Exception as e:
        messagebox.showerror( f"Failed to list files: {e}")


# Downloads a file from the server
def downloading_files(listbox):
    global client_socket
    if not connected:
        messagebox.showerror( "Not connected to server")
        return

    filename = simpledialog.askstring("Download File", "Enter the filename to download:")
    owner = simpledialog.askstring("Owner", "Enter the owner's name:")
    if not filename or not owner:
        return

    try:
        client_socket.send(f"DOWNLOAD {filename} {owner}".encode())
        response = client_socket.recv(1024).decode()

        if response == "DOWNLOAD READY":
            save_path = filedialog.askdirectory()
            if not save_path:
                return

            with open(f"{save_path}/{filename}", "wb") as file:
                while True:
                    data = client_socket.recv(1024)
                    if data == b"EOF":
                        break
                    file.write(data)

            updates_log(listbox, f"Downloaded: {filename}")
        else:
            updates_log(listbox, response)

    except Exception as e:
        messagebox.showerror( f"Download failed: {e}")
# Delete a file from the server
def deleting_files(listbox):
    global client_socket
    if not connected:
        messagebox.showerror("Not connected to server")
        return

    filename = simpledialog.askstring("Delete File", "Enter the filename to delete:")
    if not filename:
        return

    try:
        client_socket.send(f"DELETE {filename}".encode())
        response = client_socket.recv(1024).decode()
        updates_log(listbox, response)
    except Exception as e:
        messagebox.showerror( f"Delete failed: {e}")
# Close the connection and exit the application
def closing_connection(root):
    global client_socket
    if client_socket:
        client_socket.close()
    root.destroy()

# GUI Setup
root = Tk()
root.title("Client")

label_name = Label(root, text="Client Name:")
label_name.grid(row=0, column=0)

entry_name = Entry(root)
entry_name.grid(row=0, column=1)

label_server = Label(root, text="Server IP:")
label_server.grid(row=1, column=0)

server_entry = Entry(root)
server_entry.grid(row=1, column=1)

port_label = Label(root, text="Port:")
port_label.grid(row=2, column=0)

port_entry = Entry(root)
port_entry.grid(row=2, column=1)

listbox_activities = Listbox(root, width=50, height=20)
listbox_activities.grid(row=4, column=0, columnspan=2)

connecting_button = Button(root, text="Connect", command=lambda: connect_to_server(entry_name, server_entry, port_entry, listbox_activities, buttons))
connecting_button.grid(row=3, column=0, columnspan=2)

uploading_button = Button(root, text="Upload File", command=lambda: uploading_files(listbox_activities), state="disabled")
uploading_button.grid(row=5, column=0)

listing_button = Button(root, text="List Files", command=lambda: listing_files(listbox_activities), state="disabled")
listing_button.grid(row=5, column=1)

downloading_button = Button(root, text="Download File", command=lambda: downloading_files(listbox_activities), state="disabled")
downloading_button.grid(row=6, column=0)

deleting_button = Button(root, text="Delete File", command=lambda: deleting_files(listbox_activities), state="disabled")
deleting_button.grid(row=6, column=1)

buttons = [uploading_button, listing_button, downloading_button, deleting_button]

root.protocol("WM_DELETE_WINDOW", lambda: closing_connection(root))
root.mainloop()