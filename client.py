from tkinter import Tk, Frame, Scrollbar, Label, END, Entry, Text, VERTICAL, Button, \
    messagebox  # Tkinter Python Module for GUI
import socket  # Sockets for network connection
import threading  # for multiple proccess
import mysql.connector
from datetime import datetime
import argparse
import boto3
from playsound import playsound
import requests
from tqdm import tqdm
import pyaudio
import wave
import time
import wget

class GUI:
    client_socket = None
    last_received_message = None

    def __init__(self, master, userID:int, room:int, port:int,
                 original_language_ID:int, target_language_ID:int,
                 microphone_index:int,
                 aws_access_key_id, aws_secret_access_key, aws_session_token):
        self.microphone_index = microphone_index
        
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_session_token = aws_session_token
        self.session = boto3.Session(aws_access_key_id=self.aws_access_key_id,
                                     aws_secret_access_key=self.aws_secret_access_key,
                                     aws_session_token=self.aws_session_token)
        self.ptt_state = "Push to Talk" # or "Recording"
        self.recording = False
        self.room = room
        self.port = port
        self.userID = userID
        self.user = None
        self.original_language_ID = original_language_ID
        self.target_language_ID = target_language_ID
        
        self.root = master
        self.chat_transcript_area = None
        self.name_widget = None
        self.enter_text_widget = None
        self.join_button = None
        self.socket_connected = False
        
        self.connect_to_database()
        self.set_user()
        self.get_language_table()
        self.refresh() # TODO: insert this line to test query; comment out later
        self.initialize_socket()
        self.initialize_gui()
        self.listen_for_incoming_messages_in_a_thread()
        return
    
    
    
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
        remote_ip = 'ec2-34-195-127-232.compute-1.amazonaws.com' # 127.0.0.1'  # IP address
        # remote_ip = '127.0.0.1'
        remote_port = self.port # 10319  # TCP port
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
        self.display_push_to_talk()

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
        self.name_widget.delete(0, END)
        self.name_widget.insert(0, str(self.user))
        self.name_widget.config(state='disabled')
        self.name_widget.pack(side='left', anchor='e')
        # self.join_button = Button(frame, text="-Join-", width=10, command=self.on_join).pack(side='left')
        
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
    
    def display_push_to_talk(self):
        frame = Frame()
        # Label(frame, text='Push To Talk', font=("Serif", 12)).pack(side='top', anchor='w')
        self.connect_button = Button(frame, text="Re-connect", width=10, command=self.initialize_socket).pack(side='left')
        self.refresh_button = Button(frame, text="Refresh", width=10, command=self.on_refresh).pack(side='left')
        self.ptt_button = Button(frame, text="Push to Talk", width=15, command=self.on_push_to_talk)
        self.ptt_button.pack(side='left')
        self.play_last_button = Button(frame, text="Play Last", width=10, command=self.on_play_last)
        self.play_last_button.pack(side='left')
        frame.pack(side='top')
        return

    def on_join(self): # TODO: deprecate
        # if len(self.name_widget.get()) == 0:
        #     messagebox.showerror(
        #         "Enter your name", "Enter your name to send a message")
        #     return
        # self.name_widget.config(state='disabled')
        # if self.socket_connected:
        #     self.client_socket.send(("joined:" + self.name_widget.get()).encode('utf-8'))
        # else:
        #     print('socket not connected')
        return

    def on_enter_key_pressed(self, event):
        if len(self.name_widget.get()) == 0:
            messagebox.showerror("Enter your name", "Enter your name to send a message")
            return
        self.send_chat() # TODO: change this to: send via S3
        self.clear_text()

    def clear_text(self):
        self.enter_text_widget.delete(1.0, 'end')
        
    def send_chat_via_S3(self): # DONE: install boto3 # TODO: delete this function
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
                    # DONE: add a connect button; call initialize_socket()
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
        
        # play most recent audio
        self.on_play_last()
        return
    
    def refresh(self, DEBUG=True):
        '''
        on clicking refresh, gets all messages from the client's room
        '''
        
        def parse_string(x):
            if (x is not None):
                out = str(x)
            else:
                out = ""
            return out
        
        # get all messages from database in chronological order
        # query = "SELECT * FROM messages ORDER BY created_at ASC"
        # try:
        #     self.cursor = self.database.cursor()
        #     self.cursor.execute(query)
        #     result = self.cursor.fetchall()
        #     all_message_blocks = []
        #     if DEBUG:
        #         for x in result:
        #             print(x) # message: [id, userID, created_at, original_language, target_language, msg_original, msg_target, msg_speech, room]
        #     for x in result:
        #         q2 = "SELECT * FROM users WHERE id=" + str(x[1]) # get name via userID
        #         self.cursor.execute(q2)
        #         r2 = self.cursor.fetchall()
        #         name = r2[0][1] # users: [id, name]
        #         message_group = []
        #         message_group.append(x[2].strftime(name + ": " + "%m/%d/%Y %H:%M:%S"))
        #         message_group.append(parse_string(x[3]) + ": " + parse_string(x[5])) # original_language: msg_original
        #         message_group.append(parse_string(x[4]) + ": " + parse_string(x[6]))  # target_language: msg_target
        #         all_message_blocks.append('\n'.join(message_group))
        #         if DEBUG:
        #             print(*message_group, sep='\n')
        # finally:
        #     self.cursor.close()
        
        
        query = "SELECT m.created_at, u.name, m.room, \
                l.transcribe_lang_code AS original_lang, \
                l2.transcribe_lang_code AS target_lang, \
                m.msg_original, m.msg_target, m.msg_speech \
                FROM messages m \
                INNER JOIN users u ON m.userID = u.id \
                INNER JOIN languages l ON m.original_language=l.id \
                INNER JOIN languages l2 ON m.target_language=l2.id \
                WHERE m.room = " + str(self.room) # choose user id; then select messages from that user's room" # TODO: change 4 to self.room
        # created_at, name, room, original_lang, target_lang, msg_original, msg_target, msg_speech

        try:
            self.cursor = self.database.cursor()
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            all_message_blocks = []
            if DEBUG:
                for x in result:
                    print(x)
            for x in result:
                message_group = []
                message_group.append(x[0].strftime(x[1] + ": " + "%m/%d/%Y %H:%M:%S")) # name: date-time
                message_group.append(parse_string(x[3]) + ": " + parse_string(x[5]))  # original_language: msg_original
                message_group.append(parse_string(x[4]) + ": " + parse_string(x[6]))  # target_language: msg_target
                all_message_blocks.append('\n'.join(message_group))
                if DEBUG:
                    print(*message_group, sep='\n')
        finally:
            self.cursor.close()
        
        return all_message_blocks
    
    def on_push_to_talk(self):
        # flip/flop between the "Push to Talk" and "Recording" state; see self.ptt_state
        
        # change text/state
        if self.ptt_state == "Push to Talk":
            # set next state
            self.ptt_state = "Recording"
            # self.ptt_button['text'] = "Recording..."
            self.ptt_button.config(text="Recording...")
            
            # start recording in another thread
            # in thread: while self.recording==True, record chunks
            self.recording = True
            thread = threading.Thread(target=self.record_thread, args=())
            thread.start()
        elif self.ptt_state == "Recording":
            # set next state
            self.ptt_state = "Push to Talk"
            # self.ptt_button['text'] = "Push to Talk"
            self.ptt_button.config(text="Push to Talk")
            
            # stop recording and upload
            self.recording = False
            # TODO: need to wait for thread to finish, then open()
            time.sleep(1) # for now, just wait
            
            # save .wav and upload to S3 // note: this could take a few seconds
            def upload_audio_to_S3():
                audio = open('./recording.wav',
                             'rb')  # note: this must match in the recording function...hard coded for now
                bucket_name = "bucket-132423434"  # this is the bucket associated with the AWS credentials entered via argparse
                now = datetime.now()
                s3_filename = now.strftime('recording_' + '%Y%m%d_%H%M%S' + '.wav')  # "recording.wav"
                s3 = self.session.resource('s3')
                object = s3.Object(bucket_name, s3_filename)
                result = object.put(Body=audio.read(),
                                    Metadata={  # TODO: check w/ Duygu on metadata; first check db schema
                                        'user_id': str(self.userID),
                                        'source_lang': str(self.original_language_ID),
                                        'target_lang': str(self.target_language_ID),
                                        'room': str(self.room)
                                    })
                res = result.get('ResponseMetadata')
                if res.get('HTTPStatusCode') == 200:
                    print('File Uploaded Successfully')
                else:
                    print('File Not Uploaded')
                return
            thread_upload = threading.Thread(target=upload_audio_to_S3)
            thread_upload.start()
        else:
            # catch
            self.ptt_state = "Push to Talk"
        
        
        return
    
    def record_thread(self):
        
        form_1 = pyaudio.paInt16  # 16-bit resolution
        chans = 1  # 1 channel
        samp_rate = 44100  # 16000 # 44.1kHz sampling rate
        chunk = 4096  # 2^12 samples for buffer
        #record_secs = 10  # seconds to record
        dev_index = self.microphone_index  # device index found by p.get_device_info_by_index(ii)
        wav_output_filename = 'recording.wav'  # name of .wav file

        audio = pyaudio.PyAudio()  # create pyaudio instantiation

        # create pyaudio stream
        stream = audio.open(format=form_1, rate=samp_rate, channels=chans,
                            input_device_index=dev_index, input=True,
                            frames_per_buffer=chunk)
        print("recording")
        frames = []
        while self.recording:
            data = stream.read(chunk)
            frames.append(data)

        print("finished recording")
        
        # stop the stream, close it, and terminate the pyaudio instantiation
        stream.stop_stream()
        stream.close()
        audio.terminate()

        # save the audio frames as .wav file
        wavefile = wave.open(wav_output_filename, 'wb')
        wavefile.setnchannels(chans)
        wavefile.setsampwidth(audio.get_sample_size(form_1))
        wavefile.setframerate(samp_rate)
        wavefile.writeframes(b''.join(frames))
        wavefile.close()
        return
    
    def on_play_last(self, DEBUG=True):
        query = "SELECT id, msg_speech FROM messages WHERE room = 456 ORDER BY created_at DESC LIMIT 1" # get most recent audio
        try:
            self.cursor = self.database.cursor()
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            #print(result) # [(5, 'https://s3.amazonaws.com/synthesized.walkietalkie/hello_de.m.mp3')]
            file = result[0][1]
            if DEBUG:
                print(file)
            
            # first, download file
            # file_local = wget.download(file)
            # if DEBUG:
            #     print(file_local)
            playsound(file) # TODO: playsound is not reliable; no spaces in filename?
            
        except:
            print('could not connect to database or play audio')
        
        
        return


# the mail function
if __name__ == '__main__':
    def initialize_audio_devices():
        print('initializing audio devices')
        p = pyaudio.PyAudio()
        for ii in range(p.get_device_count()):
            print(ii, p.get_device_info_by_index(ii).get('name'))
        
        mic_index = input('select microphone index:')
        microphone_index = int(mic_index)
        return microphone_index
    
    # userID = 1 # # TODO: deprecate; replace with argparse
    parser = argparse.ArgumentParser() # https://towardsdatascience.com/a-simple-guide-to-command-line-arguments-with-argparse-6824c30ab1c3
    # add positional args first
    parser.add_argument('userID', type=int, default=1) # 1=guest
    parser.add_argument('room', type=int)
    parser.add_argument('port', type=int)
    parser.add_argument('aws_access_key_id', type=str)
    parser.add_argument('aws_secret_access_key', type=str)
    parser.add_argument('aws_session_token', type=str)
    # then optional args
    parser.add_argument('--microphone_index', type=int)
    parser.add_argument('--original_language_ID', type=int, default=1)
    parser.add_argument('--target_language_ID', type=int, default=2)
    
    
    args = parser.parse_args()
    
    root = Tk()
    gui = GUI(root,userID=args.userID,
              room=args.room,
              port=args.port,
              original_language_ID=args.original_language_ID,
              target_language_ID=args.target_language_ID,
              aws_access_key_id=args.aws_access_key_id,
              aws_secret_access_key=args.aws_secret_access_key,
              aws_session_token=args.aws_session_token,
              microphone_index=initialize_audio_devices()
              )
    root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
    root.mainloop()
    
# DONE: modify client to query database for a full update;  SELECT * from messages, order by timestamp and print each entry to textbox
# DONE: on receive "!DB_UPDATED", refresh text box

# current status:
# client can receiver !DB_UPDATED and !USER_LEFT and perform the respective actions
# TODO NEXT: <---------------------------
# DONE: server.py: send "!USER_LEFT <user>" on socket fail
# DOING: client -> S3 -> lambda pipleine, ending with lambda sending !DB_UPDATED
# DONE: add record button/functionality to start the client->s3->lambda pipeline
# DONE: change: auto fill in user name
# TODO: remove text chat functionality
# DONE: try Elastic IP address
# DONE: push to talk functionality
# DONE: add AWS authentication
# DONE: test add to S3
# TODO: change to Duygu's  credentials and test the AWS pipeline

# Vincent's S3 bucket: bucket-132423434

# run commands:
# use python for pycharm terminal
# python3 client.py userID room aws_access_key_id aws_secret_access_key aws_session_token --original_language_ID 1 --target_language_ID 2
# python client.py  userID room  aws_access_key_id aws_secret_access_key aws_session_token --original_language_ID 1 --target_language_ID 2

# TODO test basic scenario:
# user 1 @ room 1: en -> de
# user 2 @ room 1: de -> en

# TODO: on !DB_UPDATED, only play back audio if from another client (not from self)
