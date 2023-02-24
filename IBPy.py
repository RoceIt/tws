import socket
import logging
import os.path

import mypy

class IBPyException(Exception): pass
class ConnectingError(IBPyException): pass

E_CONNECTION_TIMED_OUT = 'connecting to TWS timed out'
E_CONNECTION_REFUSED = 'Connection refused\n{}'
E_UNEXPECTED_ANSWER = 'Server returned unexpected value\n{}'

LOG_FILENAME = os.path.join(mypy.LOG_LOCATION, 'IBPy.log')
LOG_LEVEL = logging.DEBUG

#HOST_IP = '127.1.1.1'
HOST_IP = '10.1.1.7'
HOST_PORT = 7496
SOCKET_EOL = '\0'.encode()
ADRESS = (HOST_IP, HOST_PORT)
CLIENT_VERSION = 47

class TWSconnection(socket.socket):

    eol = SOCKET_EOL
    
    def __init__(self, host=HOST_IP, port=HOST_PORT, client_id=0):
        adress = (host, port)
        self.logger = logging.getLogger('client {}'.format(client_id))
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self.settimeout(15)
        try:
            self.connect(adress)      
            self.send(CLIENT_VERSION)
            a = self.read_int()
            self.logger.debug('server version {}'.format(a))
            b = self.read_date()
            self.logger.debug('server time {}'.format(b))
            self.settimeout(None)
        except socket.timeout as err:
            self.close()
            self.logger.error(E_CONNECTION_TIMED_OUT)
            raise ConnectingError(E_CONNECTION_TIMED_OUT)
        except socket.error as err:
            self.close()
            mess = E_CONNECTION_REFUSED.format(err)
            self.logger.error(mess)
            raise ConnectingError(mess)
        except ValueError as err:
            self.close()
            mess = E_UNEXPECTED_ANSWER.format(err)
            self.logger.error(mess)
            raise ConnectingError(mess)
        
        
        

    def send(self, message):
        mess = str(message)
        if not len(mess) == 0:
            super().send(str(mess).encode())
        super().send(self.eol)

    def _read_line(self):
        answer = ''.encode()
        while True:
            b = self.recv(1)
            if b == self.eol:
                break
            answer += b
        return answer.decode()

    def read_int(self):
        answer = self._read_line()
        return int(answer)
        
    def read_date(self):
        date_ = self._read_line()
        date_ = mypy.py_date_time(date_, mypy.ISO8601TIMESTR)
        return date_


logging.basicConfig(filename=LOG_FILENAME,
                    level=LOG_LEVEL,
                    filemode='w')
