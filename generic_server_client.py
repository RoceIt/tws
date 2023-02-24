#!/usr/bin/env python3
#
#  Copyright (c) 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)


"""System to construct a server/client model.

Creating client/server applications with a library system.
  
Exceptions
  ServerClientModelError  --> general exception
    RequestError --> error while making request
      RequestTimedOut --> request returned time out error
    LostServerConnectionError --> Socket error, connection lost
      
Classes
  GenericServerClientModel: the server/client base class
  ServerClientRequest: completly define a request to a server
  LibraryOfServerClientRequests(): handle collections of serverclientrequests

"""


import threading
import logging
import socket
import socketserver
import os.path

import mypy
from my_networking import PickledBaseRequestHandler, PickledSocket
from my_networking import ExceptionWithOrigin
from managed_namespace import ManagedNamespace
from mypy import LOG_LOCATION as log_dir

class ServerClientModelError(Exception): pass
class RequestError(ServerClientModelError): pass
class RequestArgumentError(RequestError): pass
class RequestTimedOut(RequestError): pass
class LostServerConnectionError(ServerClientModelError): pass


__ALL__ = ['GenericServerClientModel', 
           'ServerClientRequest', 'LibraryOfServerClientRequests',
           'ServerClientModelError', 'RequestError', 'RequestTimedOut']


class GenericServerClientModel():
    
    """Class to define/start a server and associated clients
    
    You can start a server or get clients from this class.  Without
    changes a started server will act as a filter and echo all data 
    that is send to it.  You can change this behavior.   If you subclass
    from this class and redefine the staticmethod standard_server_function
    you can change the standard behavior and make the server do and/or return
    whatever you want.  With the add_request and add_request_library methods you
    can add client/server requests to the model. 
    
    
    methods:   
      add_request(request)
      add_request_library(request)
      new_context_managed_client() -> context managed client socket
      new_client() -> client socket
      new_context_managed_client() -> client socket to use in 'with' statement
      raw_data_client(*data, wait_for_answer) -> server answer
      request_client(request_key, data, ...) -> server answer
      start_server()
      stop_server()
    
    """
    
    STREAMED_DATA = 'sd'
    
    def __init__(self, server_ip='localhost', server_port=0, name = 'gsc',
                 id_=None,
                 log_parent='', log_to='FILE', log_lvl=logging.DEBUG):
        """Sets the basic server properties.
        
        Without arguments the server ip will be 'localhost' and
        the portnumber will be assigned by the OS.  The server will
        start a new thread for every client.
        
        With the optional server_ip and server_port parameters you can
        assign ip and portnumber yourself.  log_parent, log_to and log_lvl
        can be set at intialisation.  The name parameter defaults is used
        to choose a name for the logger name and log file name.
        
        """
        self.name = name
        self.server_ip = server_ip
        self.server_port = server_port
        if id_ is None:
            id_ = (mypy.date_time2epoch(mypy.now()) *
                       threading.currentThread().__hash__())
        self.id_ = id_
        self._requests = dict()
        self.namespace_init_procedures = []
        self.server_namespace =  None
        self.client_namespace = None
        self.local_log_name = ('{}@{}:{}'.format(name , server_ip, server_port))
        self.log_parent, self.log_to, self.log_lvl = log_parent, log_to, log_lvl
        self.logger = _logger(log_parent, self.local_log_name, log_to, log_lvl)
        self.logger.info('Initialised Generic_Server_Client_Model')
        
        
    def add_request(self, new_request):
        """Add a request.
        
        The request must be of the ServerClientRequest class.  When the
        server receives this request it will run the associated function.
        
        """
        assert isinstance(new_request, ServerClientRequest)
        if new_request.request_key in self._requests:
            self.logger.warning('request {} already set'.
                              format(new_request.request_key))
            return
        self._requests[new_request.request_key] = dict(
                       server_function=new_request.server_function,
                       client_function=new_request.client_function,
                       mode=new_request.mode)
        self.logger.info('added request: {}({})'.
              format(new_request.request_key, new_request.mode))
        
    def add_request_library(self, library):
        """Add requests from the library"""
        assert isinstance(library, LibraryOfServerClientRequests)
        for request in library.requests():
            self.add_request(request)
        if library.has_init_procedure:
            self.namespace_init_procedures.append(library.init)
        
        
    def start_server(self):
        """Start a server proces."""
        handler = self._create_request_handler()
        self.server = socketserver.ThreadingTCPServer(
              (self.server_ip, self.server_port), handler)
        if self.server_port == 0:
            self.server_port = self.server.server_address[1]
        self.server_namespace = ManagedNamespace(
              '.'.join([self.log_parent, self.local_log_name, 'server']), 
              self.log_to, self.log_lvl)
        for init in self.namespace_init_procedures:
            init(self.server_namespace)
        self.server_namespace.self = self
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.logger.info('{} server started @ {}:{}'.
                         format(self.name, self.server_ip, self.server_port))
        return self.server_ip, self.server_port
    
    def stop_server(self):
        """Stop the server proces."""
        self.server.shutdown()
        self.server_namespace = None
        self.logger.info('{} server @ {}:{} stopped'.
                         format(self.name, self.server_ip, self.server_port))
        
    def new_client(self):
        """Return an open socket that can communicate with the server."""
        class client_with_exit_logger(PickledSocket):
            def __init__(self_, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self_.logger = self.logger
            def close(self_):
                client_ip, client_port = client.getsockname()
                super().close()
                self_.logger.info('client @ {}:{} closed'.
                      format(client_ip, client_port))
        client = client_with_exit_logger(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.server_ip, self.server_port))
        client_ip, client_port = client.getsockname()
        server_ip, server_port = client.getpeername()
        self.logger.info('client @ {}:{} connected with server @ {}:{}'
                .format(client_ip, client_port, server_ip, server_port))
        if self.client_namespace == None:
            self.client_namespace = ManagedNamespace(
                  '.'.join([self.log_parent, self.local_log_name, 'client']), 
                  self.log_to, self.log_lvl)
            self.client_namespace.self = self
        return client
    
    
    @property
    def new_context_managed_client(self):
        """Return a managed socket class to communicate with the server."""

        class context_managed_client():
            def __init__(self_):
                pass
            def __enter__(self_):
                self_.socket = self.new_client()
                return self_.socket
            def __exit__(self_, *ignore):
                self_.socket.close()
                
        return context_managed_client
    
        
    def raw_data_client(self, *data_to_send, wait_for_answer=True):
        """Opens a client, sends the data and returns the servers answer.
        
        The data is send as 1 pack
        If wait for answer is False, the client will not wait for an
        answer and return None.
        
        """
        data = data_to_send if len(data_to_send) > 1 else data_to_send[0]
        with self.new_context_managed_client() as client:
            client.send_data(data)
            self.logger.debug('raw data client: sending: {}'.format(data))
            if wait_for_answer:
                answer = client.receive_data()
                self.logger.debug('raw data client: received: {}'.format(data))
            else:
                answer = None
                self.logger.debug('raw data client: not waiting for an answer')
        return answer
    
    def client_for_request(self, request_key, *data_to_send):
        client_function = dict(
             single=self._client_for_request, 
             stream=self._streaming_client_for_request,
             keep_open=self._open_client_for_request)
        self.logger.debug('dispatching request {}'.format(request_key))
        if request_key.startswith('_'):
            data_to_send += (self.id_,)
        return client_function[self._requests[request_key]['mode']](
                  request_key, *data_to_send)
    
    def _client_for_request(self, request_key, *data_to_send):
        """send data using the requests client function"""
        request_and_data = (RequestKey(request_key),) + data_to_send
        with self.new_context_managed_client() as client:
            assert isinstance(client, PickledSocket)
            self.logger.info('single request: {}'.format(request_key))
            self.logger.debug('single request: sending {}'.
                              format(request_and_data))
            answer = self._run_client_function(client, request_key, 
                                               data_to_send)
            self.logger.debug('single request: received {}'.format(answer))
        return answer
          
    def _streaming_client_for_request(self, request_key, *data_to_send):
        """send data using the requests client function"""
        request_and_data = (RequestKey(request_key),) + data_to_send
        with self.new_context_managed_client() as client:
            assert isinstance(client, PickledSocket)
            self.logger.info('streaming request: {}'.format(request_key))
            self.logger.debug('streaming request: sending {}'.
                              format(request_and_data))
            answer = self._run_client_function(client, request_key, 
                                               data_to_send)
            self.logger.debug('streaming request: received {}'.format(answer))
            while 1:
                yield answer
                answer = self._run_client_function(client, 
                                                   self.STREAMED_DATA, '')
                self.logger.debug('streaming request: received {}'.
                                                           format(answer))
                
    def _open_client_for_request(self, request_key, *data_to_send):
        """send data using using a std client and keep the socket open"""
        request_and_data = (RequestKey(request_key),) + data_to_send
        client = self.new_client()
        assert isinstance(client, PickledSocket)
        self.logger.info('open request: {}'.format(request_key))
        self.logger.debug('open request: sending {}'.format(request_and_data))
        try:
            answer = self._run_client_function(client, request_key, 
                                               data_to_send)
        except:
            client.close()
            raise
        self.logger.debug('open request: received {}'.format(answer))
        return client, answer
        
    
    @staticmethod
    def standard_server_function(data, send, read, server):
        """Return all data back with the 'send' method.
        
        This function is the minimum for a server function. It takes
        three arguments: the data, a send method and a receive method.
        and returns someting with the send method. Even this last part
        is not required if the client is not expacting an answer.
       
        """        
        answer = data
        send(answer)
        
    def _create_request_handler(self):
        class the_request_handler(PickledBaseRequestHandler):
            def handle(self_):
                try:
                    data = self_.receive_data()
                    self._real_handler(data, self_.send_data, 
                                       self_.receive_data)
                except socket.error as err:                    
                    self.logger.info('client closed connection.')   
                    print('a server thread stopped, client closed connection')
                except Exception as err:
                    self.logger.error('server thread: {}'.format(err))
                    exception = ExceptionWithOrigin(
                          'uncought exception in server function', err)
                    try:
                        self_.send_data(exception)
                    except socket.error as err2:
                        pass
                    finally:    
                        print('a server thread stopped: {}'.format(err))
        return the_request_handler
    
    def _real_handler(self, data, send, receive):
        if isinstance(data[0], RequestKey):
            if data[0].startswith('_'):
                id_ = data[-1]
                data = data[:-1]
                if not id_ == self.id_:
                    raise ServerClientModelError(
                        'No permission to make this request')                
            self._requests[data[0]]['server_function'](data[1:], send, receive,
                                                       self.server_namespace)
        elif self.standard_server_function is not None:
            self.standard_server_function(data, send, receive, 
                                          self.server_namespace)
            
    def _run_client_function(self, client, request_key, data_to_send):
        try:
            if request_key is self.STREAMED_DATA:
                answer = client.receive_data()
            else:
                answer = client.send_using_function(
                    self._requests[request_key]['client_function'],
                    data_to_send, self.client_namespace)
        except socket.error as err:
            self.logger.error('client lost contact with server')
            raise LostServerConnectionError(err)
        except Exception as err:
            print('client function error')
            self.logger.exception(err)
            raise
        if isinstance(answer, ExceptionWithOrigin):
            print(answer.origin)
            print(answer.exception)
            raise answer.exception
        if isinstance(answer, Exception):
            raise answer
        return answer
            
class ServerClientRequest():
    
    """Define a request protocol.
    
    The request string is the string that will be send to the server to
    handle the request.  The server_function defines what the server
    must do with the request, the client_function defines the actions a
    client must take.  Both client_function and server_funtion receive a
    function to communicate over the network.
    
    properties:
    
    - request_string: string to start server handler
    - server_function: function to run in the server
    - client_function: function to run in the client
    
    """
    
    def __init__(self, request_string, mode='single'):
        assert mode in {'single', 'stream', 'keep_open','mute'},(
             'mode of ServerClientRequest must be single or stream')
        self.request_key = RequestKey(request_string)
        self.mode = mode
        if mode == 'mute':
            self.server_function = self._std_mute_server_function
            self.client_function = self._std_mute_client_function
        else:
            self.server_function = self._std_server_function
            self.client_function = self._std_client_function
        
        
    @property
    def request_key(self):
        return self.__request_key
    
    @request_key.setter
    def request_key(self, new_key):
        #self.__request_key = RequestKey(new_key)
        self.__request_key = new_key
        
    @property
    def server_function(self):
        return self.__server_function
    
    @server_function.setter
    def server_function(self, new_server_function):
        """The function used to send data to the server.
            
        The function must accept exactly 3 parameters.  The first is the
        data, the second is the method to send data and the third the
        method to receive data from the socket.  The send and receive
        functions can be used several times.  It's the programmers
        responsibility to make sure sender and receiver handels the
        data and that the data send over the network is pickalable.
        
        """ 
    
        self.__server_function = new_server_function
        
    @property
    def client_function(self):
        def wrapped_client_function(data, send, receive, client):
            data = (self.request_key,) + data
            answer = self.__client_function(data, send, receive, client)
            return answer
        return wrapped_client_function
    
    @client_function.setter
    def client_function(self, new_client_function):
        self.__client_function = new_client_function    
        
    @staticmethod
    def _std_server_function(data, send, receive, server):
        data = data
        send(data)
    
    @staticmethod
    def _std_client_function(data, send, receive, client):
        send(data)
        answer = receive()    
        return answer   
        
    @staticmethod
    def _std_mute_server_function(data, send, receive, server):
        pass
    
    @staticmethod
    def _std_mute_client_function(data, send, receive, client):
        send(data)
        return 'Request sended'
    

class LibraryOfServerClientRequests():
    
    """Collection of ServerClientRequests with load features.
    
    Use this as a baseclass to create libraries of ServerClientRequests.
    Method that ends with '__request' will be available with 'requests'.
    It's also possible to use other libraries as baseclass.
    
    recommanded documentation of libraries:
    Start the file with a docstring as in pep 8. Top row is a title or
    a one line discription. Leave one line open and write a clear
    discription of the purpose of the library. Under the header Requests
    summerise the request with a short discription (one line each),
    summerise the used/created namespace properties under Namespace 
    Properties and finaly list the library specific exceptions under
    Exceptions. Do not add headers if features not used.
    ----------------------------------------
    Title
    
    Discription
    
    Requests
      request 1: discription
      ...
    
    [  
    namespace properties
      property 1: discription
      ...
     ]
    
    [ 
    library errors
      local error 1: discription
     ]
    ----------------------------------------  
    Every  request should get it's own docstring. Start this one with
    a short one line discription.  If nescesarry you can go in to details
    in a following paragraph.  Discribe the arguments to send in the 
    expected order, precede the arguments you can scip with an asterix.
    type No arguments if no arguments expected. For every argument list 
    the type(s) expcected and a short discription.
    Next discribe the valid return values, cought exceptions included.
    Use the headers Server Side and Client Side to discribe specific info 
    about the 'new namespace properties', 'removed namespace properties' and
    'handeled exceptions'. Use a line for each item in every list. 
    ----------------------------------------  
    Title
    
    [Discription]
    
    Arguments
      argument 1: type(s), discription
      ...
      OR
      No arguments
      
    Return Value.
      value 1: discription
      ...
      exception 1: discription
      ...
      OR
      request is not returning an answer
    
    [     
    Server Side
      [
      -new namespace properties
        property 1: discription
        ...
        ]
      [
      -removed namespace properties
        property 1: discription
        ...
        ]
      [
      -handeled exceptions
        exception 1: discription
        ...
        ]
     ]
    
    [ 
    Client Side
      (idem Server Side)
      ]
    """
            
    def requests(self):
        for method in dir(self):
            if method.endswith('__request'):
                yield getattr(self, method)()    
    
    @property
    def has_init_procedure(self):
        return 'init' in dir(self)            
    
class RequestKey(str):
    """Makes sure the string is recognised as a request key."""
    pass
        
def send_message_to_server(server_client, message):    
    try:
        server_client.send_data(message)   
        response = server_client.receive_data()
        print("Received: {}".format(response))
    finally:
        print('    Closing client')
        server_client.close()
 
    
def _logger(parent_name, local_log_name, log_to, log_lvl):
    # Check 'ROCE_logging' docs for logging parameters.
    log_name = '.'.join([parent_name, local_log_name]).lstrip('.')
    logger = logging.getLogger(log_name)
    logger.setLevel(log_lvl)
    if parent_name:
        return logger
    formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')
    handler_list = []
    if log_to == 'STDERR':
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(formatter)
        handler_list.append(handler)
    elif log_to == 'FILE':
        log_file = os.path.join(log_dir, log_name)
        handler = logging.FileHandler(log_file, mode='a')
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        handler_list.append(handler)
        if log_lvl == logging.DEBUG:
            log_file = '.'.join([log_file, 'DEBUG'])
            handler = logging.FileHandler(log_file, mode='a')
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            handler_list.append(handler)       
    else:
        logger.propagate = False
        handler = logging.NullHandler()
        handler_list.append(handler)
    for handler in handler_list:
        logger.addHandler(handler)
    return logger

def server_request_answer(
            answer, error, send, 
            log=False, log_error=True, log_answer=True,
            succes_text='', error_text=''):
    """Send answer if no error, else send error.
    
    If succes text it will be printed to stdout, of error_text is 
    True, the err message will be printed if error_text is text,
    the text will be printed.
    """
    if error:
        send(error)
        err_mss = error.args[0]
        if log and log_error:
            log.error(
                'wrong request:: {}'.format(err_mss)
            )
        if error_text is True:
            print(err_mss)
        elif error_text:
            print(error_text)
    else:
        send(answer)
        if succes_text:
            print(succes_text)
        if log and log_answer:
            mss = ' '.join(['server): ', succes_text])
            log.info(mss)
    
        
if __name__ == "__main__":    
    print('in main')
    HOST, PORT = "localhost", 44216
    scm = GenericServerClientModel(HOST, PORT) 
    scm.start_server()
    ip, port = scm.server_ip, scm.server_port
    # test 1
    send_message_to_server(scm.new_client(), "test 1")
    # test 2
    with scm.new_context_managed_client() as cl:
        cl.send_data('test 2')
        response = cl.receive_data()
        print('Reveived: {}'.format(response))
    # test 3
    response = scm.raw_data_client('test 3', 'test 3b')
    print('Reveived: {}'.format(response))
    # test 4
    a_request = ServerClientRequest('test')
    scm.add_request(a_request)
    response = scm.client_for_request('test', 'test 4')
    print('Reveived: {}'.format(response))        
    # clean exit
    mypy.get_bool('print `enter` to stop server: ', default=True)
    scm.stop_server()
    