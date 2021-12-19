from tkinter import Tk, Frame, Scrollbar, Label, END, Entry, Text, VERTICAL, Button, \
    messagebox  # Tkinter Python Module for GUI
import socket  # Sockets for network connection
import threading  # for multiple proccess
import mysql.connector
from datetime import datetime

class GUI:
    client_socket = None
    last_received_message = None

    def __init__(self, master, userID:int):
        self.root = master
        self.chat_transcript_area = None
        self.name_widget = None
        self.enter_text_widget = None
        self.join_button = None
        self.socket_connected = False
        self.userID = userID
        self.user = None
        self.connect_to_database()
        self.set_user()
        self.get_language_table()
        self.refresh() # TODO: insert this line to test query; comment out later
        self.initialize_socket()
        self.initialize_gui()
        self.listen_for_incoming_messages_in_a_thread()
        
    def connect_to_database(self):
        try:
            self.database = mysql.connector.connect(
                host="database-1.cml8g5orx21z.us-east-1.rds.amazonaws.com",
                user="admin",
                passwd="J3bpAdxfMbtN1vMlb48J", database="db1",
                autocommit=True # must commit to see updated rows
            )
            
            self.cursor = self.database.cursor()
            
            # test
            print('testing connection to database')
            query = "SELECT * FROM users"
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            for x in result:
                print(x)
            self.cursor.close()
        except:
            print('could not connect to database')
        return
        
    def set_user(self):
        query = "SELECT * from users WHERE id = " + str(self.userID)
        try:
            self.cursor = self.database.cursor()
            self.cursor.execute(query)
            result = self.cursor.fetchall() # returns a list
            # print(result)
            if result:
                self.user = result[0][1] # first result, name column
                print("chatting with user: " + self.user) # columns: id,name
        finally:
            self.cursor.close()
        return
    
    def get_language_table(self):
        query = "SELECT * from languages"
        try:
            self.cursor = self.database.cursor()
            self.cursor.execute(query)
            result = self.cursor.fetchall() # returns a list
            for x in result:
                print(x)
        finally:
            self.cursor.close()
        return
        
    def initialize_socket(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # initialazing socket with TCP and IPv4
        remote_ip = 'ec2-3-86-188-40.compute-1.amazonaws.com' # 127.0.0.1'  # IP address
        # remote_ip = '127.0.0.1'
        remote_port = 10319  # TCP port
        try:
            self.client_socket.connect((remote_ip, remote_port))  # connect to the remote server
            self.socket_connected = True
            print('socket connect success')
        except:
            self.socket_connected = False
            print('socket connect failed')
        else:
            print('done initializing socket')

    def initialize_gui(self):  # GUI initializer
        self.root.title("Socket Chat")
        self.root.resizable(0, 0)
        self.display_chat_box()
        self.display_name_section()
        self.display_chat_entry_box()

    def listen_for_incoming_messages_in_a_thread(self):
        thread = threading.Thread(target=self.receive_message_from_server,
                                  args=(self.client_socket,))  # Create a thread for the send and receive in same time
        thread.start()

    # function to recieve msg
    def receive_message_from_server(self, so):
        while self.socket_connected: # True:
            buffer = so.recv(256)
            if not buffer:
                break
            message = buffer.decode('utf-8')

            if "joined" in message:
                user = message.split(":")[1]
                message = user + " has joined"
                self.chat_transcript_area.insert('end', message + '\n')
                self.chat_transcript_area.yview(END)
            # TODO: TEST ME: add: if "!USER_LEFT <USERNAME>, display <USERNAME> 'has left' // server should send this
            elif "!USER_LEFT" in message:
                try:
                    user = message.split("!USER_LEFT ")[1] # reminder: include trailing space; "!USER_LEFT Alice Marigold" --> "Alice Marigold"
                except:
                    user = ""
                message = user + " has left"
                self.chat_transcript_area.insert('end', message + '\n')
                self.chat_transcript_area.yview(END)
            elif "!DB_UPDATED" in message:
                self.on_refresh()
            else:
                self.chat_transcript_area.insert('end', message + '\n')
                self.chat_transcript_area.yview(END)

        so.close()

    def display_name_section(self):
        frame = Frame()
        Label(frame, text='Enter your name:', font=("Helvetica", 16)).pack(side='left', padx=10)
        self.name_widget = Entry(frame, width=50, borderwidth=2)
        self.name_widget.pack(side='left', anchor='e')
        self.join_button = Button(frame, text="Join", width=10, command=self.on_join).pack(side='left')
        self.refresh_button = Button(frame, text="refresh", width=10, command=self.on_refresh).pack(side='left')
        frame.pack(side='top', anchor='nw')

    def display_chat_box(self):
        frame = Frame()
        Label(frame, text='Chat Box:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.chat_transcript_area = Text(frame, width=60, height=10, font=("Serif", 12))
        scrollbar = Scrollbar(frame, command=self.chat_transcript_area.yview, orient=VERTICAL)
        self.chat_transcript_area.config(yscrollcommand=scrollbar.set)
        self.chat_transcript_area.bind('<KeyPress>', lambda e: 'break')
        self.chat_transcript_area.pack(side='left', padx=10)
        scrollbar.pack(side='right', fill='y')
        frame.pack(side='top')

    def display_chat_entry_box(self):
        frame = Frame()
        Label(frame, text='Enter message:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.enter_text_widget = Text(frame, width=60, height=3, font=("Serif", 12))
        self.enter_text_widget.pack(side='left', pady=15)
        self.enter_text_widget.bind('<Return>', self.on_enter_key_pressed)
        frame.pack(side='top')

    def on_join(self):
        if len(self.name_widget.get()) == 0:
            messagebox.showerror(
                "Enter your name", "Enter your name to send a message")
            return
        self.name_widget.config(state='disabled')
        if self.socket_connected:
            self.client_socket.send(("joined:" + self.name_widget.get()).encode('utf-8'))
        else:
            print('socket not connected')

    def on_enter_key_pressed(self, event):
        if len(self.name_widget.get()) == 0:
            messagebox.showerror("Enter your name", "Enter your name to send a message")
            return
        self.send_chat() # TODO: change this to: send via S3
        self.clear_text()

    def clear_text(self):
        self.enter_text_widget.delete(1.0, 'end')
        
    def send_chat_via_S3(self): # TODO: install boto3
        data = self.enter_text_widget.get(1.0, 'end').strip()
        return
    
    # DONE: prevent client from sending "!DB_UPDTED" or "!USER_LEFT"; leave this in for now; can use this for testing now
    def send_chat(self):
        senders_name = self.name_widget.get().strip() + ": "
        data = self.enter_text_widget.get(1.0, 'end').strip()
        
        cond = "!DB_UPDATED" not in data and "!USER_LEFT" not in data
        # cond = True # use this to allow, for testing
        if cond:
            message = (senders_name + data).encode('utf-8')
            self.chat_transcript_area.insert('end', message.decode('utf-8') + '\n') # note: this update the message window even though message has not been sent
            self.chat_transcript_area.yview(END)
            if self.socket_connected:
                try:
                    self.client_socket.send(message)
                except:
                    print('could not connect to server; check if server is online') # TODO: test this; d/c server and send a msg
            else:
                print('socket not connected; message not sent')
        else:
            print('client should not send !DB_UPDATED or !USER_LEFT')
        self.enter_text_widget.delete(1.0, 'end')
        return 'break'

    def on_close_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
            self.client_socket.close()
            exit(0)
            
    def on_refresh(self):
        # clear message window, refresh() to get all messages, show all messages
        self.chat_transcript_area.delete(1.0, END)
        
        all_message_blocks = self.refresh()
        for message_block in all_message_blocks:
            self.chat_transcript_area.insert('end', message_block + '\n')

        self.chat_transcript_area.yview(END)
        return
    
    def refresh(self, DEBUG=True):
        
        def parse_string(x):
            if (x is not None):
                out = str(x)
            else:
                out = ""
            return out
        
        # get all messages from database in chronological order
        query = "SELECT * FROM messages ORDER BY created_at ASC"
        try:
            self.cursor = self.database.cursor()
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            all_message_blocks = []
            if DEBUG:
                for x in result:
                    print(x) # message: [id, userID, created_at, original_language, target_language, msg_original, msg_target]
            for x in result:
                q2 = "SELECT * FROM users WHERE id=" + str(x[1]) # get name via userID
                self.cursor.execute(q2)
                r2 = self.cursor.fetchall()
                name = r2[0][1] # users: [id, name]
                message_group = []
                message_group.append(x[2].strftime(name + ": " + "%m/%d/%Y %H:%M:%S"))
                message_group.append(parse_string(x[3]) + ": " + parse_string(x[5]))
                message_group.append(parse_string(x[4]) + ": " + parse_string(x[6]))
                all_message_blocks.append('\n'.join(message_group))
                if DEBUG:
                    print(*message_group, sep='\n')
        finally:
            self.cursor.close()
        return all_message_blocks
    


# the mail function
if __name__ == '__main__':
    userID = 1
    
    root = Tk()
    gui = GUI(root,userID=userID)
    root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
    root.mainloop()
    
# DONE: modify client to query database for a full update;  SELECT * from messages, order by timestamp and print each entry to textbox
# DONE: on receive "!DB_UPDATED", refresh text box

# current status:
# client can receiver !DB_UPDATED and !USER_LEFT and perform the respective actions
# TODO NEXT: <---------------------------
# TODO: server.py: send "!USER_LEFT <user>" on socket fail
# TODO: client -> S3 -> lambda pipleine, ending with lambda sending !DB_UPDATED
# TODO: add record button/functionality to start the client->s3->lambda pipeline
# TODO: change: auto fill in user name
# TODO: remove text chat functionality
# TODO: try Elastic IP address