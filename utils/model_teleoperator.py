from websocket_server import WebsocketServer
import os
import socket
import sys
import time

class ModelTeleoperator:

    def __init__(self, host):
        self.server = None
        self.client = None
        self.host = host

        self.model_address = ("127.0.0.1", 36677)
        self.model_client = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Function to read the message from websocket
    def get_message(self, client, server, message):
        try:
            sys.stdout = open("/teleop_log.txt","w")
            if (message[:4] == "#key"):
                key = message[message.find('_')+1:]
                print("\nPRESSED KEY:" + str(key))
                if key == "w":
                    self.model_client.sendto(str.encode("UVF"), self.model_address) # User Velocity Forward
                elif key == "s":
                    self.model_client.sendto(str.encode("UVB"), self.model_address) # User Velocity Backward
                elif key == "a":
                    self.model_client.sendto(str.encode("UAL"), self.model_address) # User Angular Left
                elif key == "d":
                    self.model_client.sendto(str.encode("UAR"), self.model_address) # User Angular Right
                elif key == "x":
                    self.model_client.sendto(str.encode("US-"), self.model_address) # User Stop model

        except KeyboardInterrupt:
            sys.stdout.close()  # close file.txt
            sys.stdout = sys.__stdout__

    # Function that gets called when the connected closes
    def handle_close(self, client, server):
        self.client = None
        self.server.allow_new_connections()
        try:
            sys.stdout = open("/teleop_log.txt","w")
            print(client, 'closed')
        except KeyboardInterrupt:
            sys.stdout.close()  # close file.txt
            sys.stdout = sys.__stdout__

    # Called when a new client is received
    def get_client(self, client, server):
        self.client = client
        self.server.deny_new_connections()
        self.model_client.sendto(str.encode("US-"), self.model_address) # User Stop
        try:
            sys.stdout = open("/teleop_log.txt","w")
            print(client, 'connected')
        except KeyboardInterrupt:
            print(client, 'error connecting with teleoperator client')
            sys.stdout.close()  # close file.txt
            sys.stdout = sys.__stdout__


    # Activate the server
    def run_server(self):
        self.server = WebsocketServer(port=7164, host=self.host)
        self.server.set_fn_new_client(self.get_client)
        self.server.set_fn_message_received(self.get_message)
        self.server.set_fn_client_left(self.handle_close)

        home_dir = os.path.expanduser('~')

        logged = False
        while not logged:
            try:
                f = open(f"{home_dir}/ws_teleop.log", "w")
                f.write("websocket_teleop=ready")
                f.close()
                logged = True
            except:
                print("~/ws_teleop.log could not be opened for write", flush=True)
                time.sleep(0.1)

        self.server.run_forever()


# Execute!
if __name__ == "__main__":
    host = sys.argv[1]
    server = ModelTeleoperator(host)
    server.run_server()