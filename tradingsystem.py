#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import itertools

from datetime import datetime, timedelta

import roc_output as r_out
import roc_string as r_str
import roc_datetime as r_dt

from daytrading import DaytradeMode
from theotrader import TheoreticalTrader

class Error(Exception): pass
class EventError(Error): pass
class SetupError(Error): pass
        
class TradingSystem(r_out.AddExportSystem):
    '''Turns interesting events into TraderRequest.
    
    '''
    
    def __init__(self, unique_request_id):
        self.unique_request_id = unique_request_id
        self.request_id_counter = itertools.count(1)
        self.default_market=None
        self.daytrader = DaytradeMode(False)
        self.theoretical_trader = None
        self.setup_ok = False
        super().__init__()
         
    def use_daytrader_mode(self, *arg_t, **kw_d):
        self.day_trade_mode = DaytradeMode(*arg_t, **kw_d)
         
    def use_theoretical_trader(self, a_theo_trader):
        assert isinstance(a_theo_trader, TheoreticalTrader)
        ###
        ###
        self.theoretical_trader = a_theo_trader
        
    def check_setup(self):
        self.setup_ok = True
        
    def event(self, event_name, event_time, **kw_d):
        '''Run the event, return the requests it might produce.
        
        The events are not stored by default, if you need them later
        store them in your derived class.
        
        '''
        assert self.setup_ok is True, 'check setup before running events'
        ###
        full_event_name = '_'.join([event_name, 'event'])
        event_method = getattr(self, full_event_name, None)
        ###
        if event_method is None:
            raise Error('Unknown event: {}'.format(event_name))
        requests = event_method(**kw_d)
        for request in requests:
            request.created = event_time
        if self.theoretical_trader:
            self.theoretical_trader.new_requests(requests)
        return requests
        
    def next_request_id(self):
        '''Return the next id_ to use for a request.'''
        ###
        prefix = self.unique_request_id
        ###
        count = next(self.request_id_counter)
        return '_'.join([prefix, str(count)])
    
    def new_market_data_for_theoretical_trader_event(self, bar_or_tick):
        '''Send the new bar or tick to the theoretical trader.'''
        if self.theoretical_trader is None:
            raise EventError('No theoretical trader added.')
        print('learn me how to do this please?')
            
    