# imports
import socket
import threading
import argparse



class ChatServer:
    clients_list = []
    
    last_received_message = ""
    
    def __init__(self, room:int, port:int):
        self.room = room
        self.port = port
        self.server_socket = None
        self.create_listening_server()
    
    # listen for incoming connection
    def create_listening_server(self):
        
        self.server_socket = socket.socket(socket.AF_INET,
                                           socket.SOCK_STREAM)  # create a socket using TCP port and ipv4
        local_ip = '0.0.0.0'  # '127.0.0.1'
        # local_ip = '127.0.0.1'
        local_port = self.port # 10319
        # this will allow you to immediately restart a TCP server
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # this makes the server listen to requests coming from other computers on the network
        self.server_socket.bind((local_ip, local_port))
        print("Listening for incoming messages..")
        self.server_socket.listen(5)  # listen for incomming connections / max 5 clients
        self.receive_messages_in_a_new_thread()
    
    # fun to receive new msgs
    def receive_messages(self, client):
        so, (ip, port) = client
        while True:
            incoming_buffer = None
            try:
                # print('==========TRY==========')
                incoming_buffer = so.recv(256)  # initialize the buffer
            except:
                # print('========EXCEPT=========')
                print('could not receive from', client, '; removing...')
                self.clients_list.remove(client)
                print('client list:')
                self.print_clients()
                self.broadcast_to_all_clients(so,msg="!USER_LEFT " + str(ip) + ":" + str(port))# TODO: create a dictionary to keep track of socket -> users(name)
                
            if not incoming_buffer:
                break
            self.last_received_message = incoming_buffer.decode('utf-8')
            self.broadcast_to_all_clients(so)  # send to all clients
        # print('============A========')
        so.close()
        # print('=============B=========')
    
    # broadcast the message to all clients
    def broadcast_to_all_clients(self, senders_socket, msg=None):
        # print('----------------')
        print(self.last_received_message)
        print(msg)
        
        for client in self.clients_list:
            socket, (ip, port) = client
            if socket is not senders_socket:
                if msg is not None:
                    try:
                        socket.sendall(msg.encode('utf-8'))
                    except:
                        # print('couln\'t send')
                        print('could not broadcast to', client, '; removing...')
                        self.clients_list.remove(client) # need this because AWS lambda functions are ephermeral
                        print('client list:')
                        self.print_clients()
                else:
                    try:
                        socket.sendall(self.last_received_message.encode('utf-8'))
                    except:
                        # print('couldn\'t send')
                        print('could not broadcast to', client, '; removing...')
                        self.clients_list.remove(client)
                        print('client list:')
                        self.print_clients()
    
    def receive_messages_in_a_new_thread(self):
        while True:
            client = so, (ip, port) = self.server_socket.accept()
            self.add_to_clients_list(client)
            print('Connected to ', ip, ':', str(port))
            print('current client list:')
            self.print_clients()
            t = threading.Thread(target=self.receive_messages, args=(client,))
            t.start()
    
    # add a new client
    def add_to_clients_list(self, client):
        if client not in self.clients_list:
            self.clients_list.append(client)
    
    def print_clients(self):
        for client in self.clients_list:
            print(client)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('room', type=int)
    parser.add_argument('port', type=int)
    
    args = parser.parse_args()
    x = ChatServer(room=args.room, port=args.port)

# DONE: use argparse for port; remember to open a port range in AWS
    
