#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from alarm_server_gscLib import server_client as alarm_client
from datetime import datetime, timedelta

from roc_input import SelectionMenu

def main():
    client = alarm_client()
    try:
        available_alarms = client.client_for_request('list_alarms')
    except ConnectionRefusedError:
        print("Can't connect with the alarm server?")
        exit()
    if available_alarms:
        menu = SelectionMenu(
            interface='TXT_LINE', 
            message='Select alarm to guard: ',
            auto_number=True,
        )
        menu.add_items(available_alarms)
        choice = menu.get_users_choice()
        try:
            sbb = client.client_for_request(
                'system_bell_buzzer', choice, choice)
        except ConnectionError:
            sbb = 'lost connection with server?'
    else:
        sbb = 'No alarms set!'
    print(sbb)
            
class Lifeguard():
    
    def __init__(self, name, max_time_without_ping, replace=True):
        assert isinstance(max_time_without_ping, timedelta)
        self.name = name
        self.max_gap = max_time_without_ping
        self.alarm = alarm_client()
        available_alarms = self.alarm.client_for_request('list_alarms')
        if not (replace and self.name in available_alarms): 
            self.alarm.client_for_request(
                'set_alarm', self.name, datetime.now() + self.max_gap)
        else:
            self.alife()
        
    def alife(self):
        self.alarm.client_for_request(
            'change_alarm_time', self.name, datetime.now() + self.max_gap)
        
    def stop(self):
        self.alarm.client_for_request(
            'remove_alarms', self.name)
        
if __name__ == '__main__':
    main()
    
        