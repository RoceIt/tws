#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)


"""Provide costum classes and functions for networking.

Classes:

PickledBaseRequestHandler: pickled send/receive enabled BaseRequestHandler
PickledSocket: pickled send/receive enabled socket

Properties:

struct_to_pack_size: defines the number of bytes used to send data sizes

"""


import socket
import socketserver
import struct
import pickle

from collections import namedtuple


# Settings for sending the size of the data
struct_to_pack_data_size = '!Q' #unsigned long long with network byte order

ExceptionWithOrigin = namedtuple("ExceptionWithOrigin", "origin exception")

        
class PickledSocket(socket.socket):
    
    """Socket to send and receive pickelable python objects over a network.
    
    socket.socket class with 3 new methods:
    
    - send_data(data)
    - receive_data() -> data
    - send_using_function(function, data) -> functions returns value
    
    """
    
    def send_data(self, object_):
        """Send object_ pickled to socket.
        
        Arguments:
        object_ -- a pickelable python object
        
        """
        _send_pickle(self, object_)
        
    def receive_data(self):
        """Return unpickled object from the socket"""
        return _receive_pickle(self)
    
    def send_using_function(self, function, data, namespace):
        """Send data to socket with the help of function.
        
        Arguments:
        function -- a function
        data -- data that must be send to the function
        
        The function must accept exactly 3 parameters.  The first is the
        data, the second is the method to send data and the third the
        method to receive data from the socket.  The send and receive
        functions can be used several times.  It's the programmers
        responsibility to make sure sender and receiver handels the
        data and that the data send over the network is pickalable.
        
        example function:
        
        def a_sender(data, send, receive):
            send(data)
            return receive()
            
        """
        return function(data, self.send_data, self.receive_data, namespace)
    


class PickledBaseRequestHandler(socketserver.BaseRequestHandler):
    
    """BaseRequestHandler to communicate with a PickledSocket
    
    socketserver.BaseRequestHandler with 2 new methods:
    
    - send_data(data)
    - receive_data() -> data    
    
    """   
    
    def send_data(self, object_):
        """Send object_ pickled using request .
        
        Named arguments:
        object_ -- a pickelable python object
        
        """
        _send_pickle(self.request, object_)
        
    def receive_data(self):
        """Receive pickled data from socket"""
        return _receive_pickle(self.request)
    

# Helper functions for PickledSocket and  PickledBaseRequestHandler   

def _send_pickle(stream, data):
    """send object pickled to stream
    
    Procedure to send pickled object over a stream:
    - object is pickeled
    - length of pickle is stored in a fixed size struct
    - the length is send
    - the pickle is send
    
    """
    data_in_bytes_format = pickle.dumps(data)
    stream.sendall(_network_transmitable_len(data_in_bytes_format))
    stream.sendall(data_in_bytes_format)


def _receive_pickle(stream): 
    """receive pickle from stream and return object
    
    Procedure to receive pickle from stream and return the object:
    - read fixed size struct with length from the stream
    - read length bytes from stream
        
    """
    bytes_in_data_size_struct = struct.calcsize(struct_to_pack_data_size)
    data_size = _network_reveived_len(stream.recv(bytes_in_data_size_struct, 
                                                  socket.MSG_WAITALL))
    return pickle.loads(stream.recv(data_size, socket.MSG_WAITALL))   


def _network_transmitable_len(data):
    return struct.pack(struct_to_pack_data_size, len(data))
  
    
def _network_reveived_len(data, nr_of_bytes=struct_to_pack_data_size):
    try:
        the_length = struct.unpack(struct_to_pack_data_size, data)[0]
    except struct.error:
        raise socket.error('Pipe closed')
    return the_length