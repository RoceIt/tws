import socket

HOST_IP = '10.1.1.7'
HOST_PORT = 7496

ADRESS = (host_ip, host_port)
CLIENT_VERSION = 47

class TWSconnection(socket.socket):

    eol = '\0'.encode()
    
    def __init__(self, host=HOST_IP, port=HOST_PORT, client_id=0):
        if host == None or port == None:
            adress = ADRESS
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.connect(ADRESS)
        

    def send(self, message):
        if not len(message) == 0:
            super().send(str(message).encode())
        super().send(self.eol)

    def _read_line(self):
        answer = ''.encode()
        while True:
            b = self.recv(1)
            if b == self.eol:
                break
            answer += b
        return answer

    def read_int(self):
        try:
            answer = self._read_line()
            return int(answer.decode())
        except:
            raise

