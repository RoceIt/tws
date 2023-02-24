#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

"""Requests to ring the system bel on events.

Ring the system bell every second when an event is triggered.

Request
  set_alarm -- raise alarm when time is later then
  change_alarm_time -- change time of an alarm with time
  remove_alarm -- remove alarm
  list_alarms -- list all available alarms
  alarm_acitve -- returns True if alarm is active else False
  system_bell_buzzer -- ring bell every second when alarm is active
  
namespace properties
  alarm_times -- dict with key alarm name, value alarm time, for time alarms

exceptions
 SystemBellAlarmError: descendend of gsc.RequestError
"""
from datetime import datetime
from collections import namedtuple
from time import sleep
from sys import stdout

from generic_server_client import *
from managed_namespace import ManagedNamespace
from roc_output import if_defined_print

succes_text = ''
        
class AlarmServerError(RequestError): pass

class AlarmServer(LibraryOfServerClientRequests):
    
    @staticmethod
    def init(namespace):
        assert isinstance(namespace, ManagedNamespace)
        ###
        ###
        namespace.alarm_times = dict()
        
    
    @staticmethod
    def set_alarm___request():
        """Set a timer alarm.
        
        Arguments:
          alarm_name -- the name af the alarm, a str
          alarm_time -- the time of the alarm
          
          
        Return Value:
          'set' -- alarm is set
          AlarmError -- alarm already set
          
        Server Side
          -New key/value in alarm times dict
        """
            
        ClearedData = namedtuple('ClearedData',
                'alarm_name '
                'alarm_time'
        )        
        
        def clear(data, namespace):
            if (len(data) == 2                and
                isinstance(data[0], str)      and
                isinstance(data[1], datetime)
            ):
                answer = ClearedData(*data), None
            else:
                mss = 'usage: set_alarm(str, datetime.datetime)'
                answer = None, RequestArgumentError(mss)
            return answer
        
        def server_function(data, send, receive, server_ns):
            cd, request_error = clear(data, server_ns)
            if isinstance(cd, ClearedData):
                with server_ns.atomic_action:
                    if cd.alarm_name not in server_ns.alarm_times:
                        server_ns.alarm_times[cd.alarm_name] = cd.alarm_time
                    else:
                        request_error = AlarmServerError(
                                          'set_alarm: '
                                          'trying to set existing alarm: {}'.
                                          format(cd.alarm_name)
                        )
                succes_text = ('set timed alarm: {} @ {}'.
                               format(cd.alarm_name, cd.alarm_time))
            server_request_answer(
                answer='set',
                error=request_error,
                send=send,
                log=server_ns.self.logger,
                succes_text=succes_text,
            )
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='set_alarm',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def alarm_active___request():        
        """Returns True if requested alarm is active.
        
        Arguments:
          alarm_name -- the name af the alarm, a str
          
          
        Return Value:
          True -- alarm is active
          False __ alarm is not active
          AlarmError -- alarm doesn't exist
          
        Server Side
          No changes
        """
            
        ClearedData = namedtuple('ClearedData',
                'alarm_name '
        )        
        
        def clear(data, namespace):
            if (len(data) == 1                and
                isinstance(data[0], str)
            ):
                alarm_name = data[0]
                if alarm_name in namespace.alarm_times:
                    answer = ClearedData(*data), None
                else:
                    mss = 'alarm not set: {}'.format(alarm_name)
                    answer = None, AlarmServerError(mss)
            else:
                mss = 'usage: alarm_active(str)'
                answer = None, RequestArgumentError(mss)
            return answer
        
        #SERVER FUNCTION
        def server_function(data, send, receive, server_ns):
            answer = True
            cd, request_error = clear(data, server_ns)
            if isinstance(cd, ClearedData):
                answer = server_ns.alarm_times[cd.alarm_name] < datetime.now()
            server_request_answer(
                answer=answer,
                error=request_error,
                send=send,
                log=server_ns.self.logger,
            )                    
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='alarm_active',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def change_alarm_time___request():        
        """Change the time of a set alarm.
        
        Arguments:
          alarm_name -- the name af the alarm, a str
          new_time -- the new alarm time
          
        Return Value:
          'set' -- new time is set
          AlarmError -- alarm doesn't exist
          
        Server Side
          new value for key alarm_name in alarm times
        """
            
        ClearedData = namedtuple('ClearedData',
                'alarm_name '
                'new_time'
        )
        
        def clear(data, namespace):
            if (len(data) == 2                and
                isinstance(data[0], str)      and
                isinstance(data[1], datetime)
            ):
                alarm_name = data[0]
                if alarm_name in namespace.alarm_times:
                    answer = ClearedData(*data), None
                else:
                    mss = 'alarm not set: {}'.format(alarm_name)
                    answer = None, AlarmServerError(mss)
            else:
                mss = 'usage: change_alarm_time(str, datetime.datetime)'
                answer = None, RequestArgumentError(mss)
            return answer
        
        #SERVER FUNCTION
        def server_function(data, send, receive, server_ns):
            cd, request_error = clear(data, server_ns)
            if isinstance(cd, ClearedData):
                server_ns.alarm_times[cd.alarm_name] = cd.new_time
                succes_text = ('alarm time changed: {} @ {}'.
                               format(cd.alarm_name, cd.new_time))
            server_request_answer(
                answer='set',
                error=request_error,
                send=send,
                log=server_ns.self.logger,
                succes_text=succes_text
            )                    
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='change_alarm_time',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def remove_alarm___request():        
        """Removes alarm from alarm list.
        
        Arguments:
          alarm_name -- the name of the alarm, a str
          
          
        Return Value:
          removed -- alarm is removed
          AlarmError -- alarm doesn't exist
          
        Server Side
          alarm key is removed from alarm names list
        """
            
        ClearedData = namedtuple('ClearedData',
                'alarm_name '
        )        
        
        def clear(data, namespace):
            if (len(data) == 1                and
                isinstance(data[0], str)
            ):
                alarm_name = data[0]
                if alarm_name in namespace.alarm_times:
                    answer = ClearedData(*data), None
                else:
                    mss = 'alarm not set: {}'.format(alarm_name)
                    answer = None, AlarmServerError(mss)
            else:
                mss = 'usage: remove_alarm(str)'
                answer = None, RequestArgumentError(mss)
            return answer
        
        #SERVER FUNCTION
        def server_function(data, send, receive, server_ns):
            cd, request_error = clear(data, server_ns)
            if isinstance(cd, ClearedData):
                del server_ns.alarm_times[cd.alarm_name]
                succes_text = 'alarm removed: {}'.format(cd.alarm_name,)
            server_request_answer(
                answer='removed',
                error=request_error,
                send=send,
                log=server_ns.self.logger,
                succes_text=succes_text,
            )                    
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='remove_alarm',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def system_bell_buzzer___request():        
        """Ring system bell when alarm is active.
        
        Arguments:
          alarm_name -- the name of the alarm, a str
          
          
        Return Value:
          removed -- alarm is removed
          stopped -- buzzer is stopped 
          AlarmError -- alarm doesn't exist
          
        Server Side
          nothing
        """
            
        ClearedData = namedtuple('ClearedData',
                'alarm_name '
        )        
        
        def clear(data, namespace):
            if (len(data) == 1                and
                isinstance(data[0], str)
            ):
                alarm_name = data[0]
                if alarm_name in namespace.alarm_times:
                    answer = ClearedData(*data), None
                else:
                    mss = 'alarm not set: {}'.format(alarm_name)
                    answer = None, AlarmServerError(mss)
            else:
                mss = 'usage: system_bell_buzzer(str)'
                answer = None, RequestArgumentError(mss)
            return answer
        
        #SERVER FUNCTION
        def server_function(data, send, receive, server_ns):
            answer = None
            cd, request_error = clear(data, server_ns)
            if isinstance(cd, ClearedData):
                while cd.alarm_name in server_ns.alarm_times:
                    send(server_ns.alarm_times[cd.alarm_name] < datetime.now())
                    next_request = receive()
                    if next_request == 'stop':
                        break
                    next_request = 'client is waiting'
                if next_request == 'stop':
                    answer = 'stopped'
                else:
                    answer = 'removed'
            server_request_answer(
                answer=answer,
                error=request_error,
                send=send,
                log=server_ns.self.logger,
            )     
                       
        # CLIENT FUNCTION           
        def client_function(data, send, receive, client):
            if len(data) > 2:
                data, mss = data[:-1], data[-1]
            else:
                mss = ''
            send(data)
            waiting = True
            try:
                while 1:
                    alarm_on = receive()
                    waiting = False
                    if alarm_on == 'removed':
                        break
                    if alarm_on is True:
                        print('\a', end='')
                        if mss:
                            print(' | '.join([str(datetime.now()), mss]))
                        stdout.flush()
                    sleep(1)
                    send('foo')
            except KeyboardInterrupt:
                print()
                if not waiting:
                    send('stop')
                    answer = receive()
                else:
                    answer = 'stopped'
                alarm_on = answer
            return alarm_on
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='system_bell_buzzer',
            mode='single',
        )
        request.server_function = server_function
        request.client_function = client_function 
        
        return request
    
    @staticmethod
    def list_alarms___request():        
        """List alarms from alarm list.
        
        Arguments:
          none          
          
        Return Value:
          a list with alarm names
          
        Server Side
          none
        """
            
        ClearedData = namedtuple('ClearedData',
                'foo'
        )        
        
        def clear(data, namespace):
            if len(data) == 0:
                    answer = ClearedData('foo'), None
            else:
                mss = 'usage: list_alarms()'
                answer = None, RequestArgumentError(mss)
            return answer
        
        #SERVER FUNCTION
        def server_function(data, send, receive, server_ns):
            cd, request_error = clear(data, server_ns)
            if isinstance(cd, ClearedData):
                alarm_names = list(server_ns.alarm_times.keys())
            server_request_answer(
                answer=alarm_names,
                error=request_error,
                send=send,
                log=server_ns.self.logger,
            )                    
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='list_alarms',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request

def server_client(server_ip='localhost', server_port= 14703):
    cs = GenericServerClientModel(server_ip, server_port, 'alarm_server')
    cs.add_request_library(AlarmServer())
    return cs