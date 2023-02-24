#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from datetime import datetime, timedelta, time

import roc_datetime as r_dt

class Error(Exception): pass
class SettingsError(Error): pass

class DaytradeMode():
    
    CLOSE_ALL_POS_NOW = 1
    START_MANAGED_EXIT = 2
    NO_NEW_TRADES = 3
    RESET = 4
    OUT_OF_DAY_BAR = 5
    
    def __init__(self, 
            std_end_time, 
            last_in=timedelta(0),
            managed_out=timedelta(0),
            last_out=timedelta(0)
        ):
        '''Initialise the DayTradeMode.
        
        Parameters:
          std_end_time -- the time the market closes, a datetime.datetime
          last_in -- trading is allowed until, timedelta
          managed_out -- ... that an exit manager is activated, timedelta
          last_out -- ... that the order is closed @ market, timedelta
          
        '''
        assert isinstance(std_end_time, (time, bool))
        assert isinstance(last_in, timedelta)
        assert isinstance(managed_out, timedelta)
        assert isinstance(last_out, timedelta)
        ###
        valid_settings = (
            (last_in > managed_out > last_out)
            or
            (not last_in                        and
             managed_out > last_out)
            or
            (not last_in                        and 
             not managed_out                    and
             last_out )
            or
            (not managed_out                    and
             last_in > last_out)
        )
        reset_gap = max(last_in, last_out, managed_out)
        if not last_in:
            last_in = reset_gap + timedelta(seconds=1)
            reset_gap = last_in
        ###
        if valid_settings:
            self.on = True
            self.std_end_time = std_end_time 
            self.last_in = last_in
            self.managed_out = managed_out
            self.last_out = last_out
            self.reset_gap = reset_gap
            self.sended_actions = set()
        elif std_end_time is False:
            self.on = False
        else:
            raise SettingsError("daytrademode, wrong parameters")
                    
                
    def actions_to_take(self, current_time):
        assert isinstance(current_time, datetime)
        ###
        std_end_time = r_dt.timetodatetime(
            a_time=self.std_end_time,
            fix_date=current_time.date()
        )
        gap = abs(std_end_time - current_time)
        if not self.on:
            action = None
        elif current_time > std_end_time:
            action = self.OUT_OF_DAY_BAR
        elif gap > self.reset_gap:
            action = self.RESET if self.sended_actions else None
        elif self.managed_out and gap > self.managed_out:
            action_sended = self.NO_NEW_TRADES in self.sended_actions
            action = self.NO_NEW_TRADES if not action_sended else None
        elif gap > self.last_out:            
            action_sended = self.NO_NEW_TRADES in self.sended_actions
            action = self.NO_NEW_TRADES if not action_sended else None
            if (not action                                               and
                self.managed_out                                         and
                not self.START_MANAGED_EXIT in self.actions_sended
            ):
                action = self.START_MANAGED_EXIT
        else:  
            action = self.CLOSE_ALL_POS_NOW
        ###
        if action == self.RESET:
            self.sended_actions.clear()
        elif action:
            self.sended_actions.add(action)            
        return action
    
    def trading_allowed(self):
        ###
        if not self.on:
            allowed = True
        else:
            allowed = not self.sended_actions
        ###
        return allowed