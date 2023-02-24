#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

"""Requests to ring the system bel on events.

Ring the system bell every second when an event is triggered.

Request
  raise_alarm_from -- raise alarm when time is later then
  change_alarm_time -- change time of an alarm with time
  cancel_alarm -- remove alarm
  buzzer -- a client that rings the local bell
  
namespace properties
  alarm_times -- dict with key alarm name, value alarm time, for time alarms

exceptions
 SystemBellAlarmError: descendend of gsc.RequestError
"""

from generic_server_client import *

class AlarmServerError(RequestError): pass

class AlarmServer(LibraryOfServerClientRequests):
    
    @staticmethod
    def raise_alarm_from___request():
        """Set a timer alarm.
        
        Arguments:
          alarm_name -- the name af the alarm, a str
          alarm_time -- the time of the alarm
          
          
        Return Value:
          'set' -- alarm is set
          SystemBellAlarmError -- alarm already set
          
        Server Side
          -New key/value in alarm times dict
        """
        
        def digest_data(data):
            err_base = 'raise_alarm_from'
            err = None
            if not len(data) == 2 :
                err = 'alarm name, alarm time'
                raise RequestArgumentError(': '.join([err_base, err]))
            return data
        
        #SERVER FUNCTION
        def server_function(data, send, receive, server_ns):
            alarm_name, alarm_time = digest_data(data)
            with server_ns.atomic_action:
                if not hasattr(server_ns, 'alarm_times'):
                    server_ns.alarm_times = dict()
                elif alarm_name in server_ns.alarm_times:
                    mess = 'trying to set existing alarm: {}'.format(
                                                                alarm_name)
                    server.self.logger.warning(mess)
                    err = SystemBellAlarmError(mss)
                    send(err)
                    raise err
            server_ns.alarm_times[alarm_name] = alarm_time
            send(set)
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='raise_alarm_from',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request

def server_client(server_ip='localhost', server_port= 14703):
    cs = GenericServerClientModel(server_ip, server_port, 'alarm_server')
    cs.add_request_library(SystemBellAlarm())
    return cs