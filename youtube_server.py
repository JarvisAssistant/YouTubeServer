from limitedmessagesocket.limited_message_socket import LimitedMessageSocket
import socket, json
from threading import Thread, Condition

class YouTubeServer:
    def __init__(self):
        self.server_address = (socket.gethostname(), 17777)
        self.socket = LimitedMessageSocket(self.server_address)
        self.command_queue = []
        self.command_queue_cv = Condition()
        self.server_thread = None

    def queue_command(self, command):
        value = Future()

        with self.command_queue_cv:
            self.command_queue.append((command, value))
            self.command_queue_cv.notify()

        return value.get()

    def start(self):
        self.server_thread = Thread(target=self.serve_forever)
        self.server_thread.start()
    
    def serve_forever(self):
        self.socket.listen()

        while True:
            print('Listening for a client at %s:%d...' % self.server_address)
            client_socket = self._wait_client()
            if not client_socket:
                print('Error with accepting client')
                continue

            client_socket = LimitedMessageSocket(None, client_socket)
            print('Found a client')

            self._send_commands(client_socket)

            print('Lost connection with the client')

    def _wait_client(self):
        try:
            return self.socket.accept()
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            return None

    def _send_commands(self, client_socket):
        while True:
            with self.command_queue_cv:
                self.command_queue_cv.wait_for(lambda : len(self.command_queue) > 0)
                message, future = self.command_queue.pop(0)

            try:
                client_socket.send(message)
                ret = client_socket.receive()
                print('print this %s' % ret)
                future.deliver(json.loads(ret))
            except Exception as e:
                print('Exception: %s' % str(e))
                client_socket.close()
                return

class Future:
    def __init__(self):
        self.cv = Condition()
        self.item = None

    def deliver(self, item):
        if item is None: raise Exception('item must not be None')

        with self.cv:
            self.item = item
            self.cv.notify()

    def get(self):
        with self.cv:
            self.cv.wait_for(lambda: not self.item is None)
            return self.item







