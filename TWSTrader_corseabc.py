#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''This module provides a class that can follow up a trade according to the
set rules
'''

import mypy
import tws
from collections import namedtuple

import TWSClient


class TraderError(Exception): pass
class TraderWarning(TraderError): pass
class IllegalRequest(TraderWarning): pass

Action = namedtuple('Action', 'action data')

################################################################################
E_CANT_CLOSE_OPEN_POS = 'Can not close Trader, {} positions of {} open'

################################################################################
# trader status
################################################################################
EMPTY = '$EMPTY'
# empty trader
MONITORING = '$MONITORING'
# trader has order
IN_TRADE = '$IN_TRADE'
# trading
STOPPING = '$STOPPING'
#trader asked TWS to cancel trades
STOPPED = '$STOPPED'
# trader is stopped
################################################################################

################################################################################
# trader mode
################################################################################
#
REAL_ENTER_OK = '$REAL_ENTER_OK'
REAL_DONT_ENTER = '$REAL_DONT_ENTER'
SIMULATE_TWS = '$SIMULATE_TWS'
#
################################################################################

################################################################################
# usefull constants
################################################################################
#
BEAR = 'BEAR'
BULL = 'BULL'
POSTPONED = '$POSTPONED'

################################################################################
# reporters
################################################################################
TO_FILE = '$TO_FILE'
#
#
STD_REPORT_FILE = 'bar.txt'
#
################################################################################

class Trader:
    
    def __init__(self, name, b, c,
                 TWS_h=None,
                 max_stop=None,
                 lb_profit=100,
                 trading_permitted_until=None,
                 close_positions_after=None,
                 min_price_variation=None,
                 future_gap=None,
                 trading_permitted_from=mypy.datetime.min,
                 originator='UNKNOWN',
                 reporter=TO_FILE,
                 report_settings=STD_REPORT_FILE):

        self.name = name
        self.reporter = reporter
        self.report_settings = report_settings
        self.a = 0
        self.b = b
        self.c = c
        self.a_corr = self.b_corr = self.c_corr = 0
        self.trade_direction = BEAR if self.b < self.c else BULL
        self.enter_id = self.profit_id = self.stop_id = self.moc_id = None
        self.status = EMPTY
        self.positions = {}
        self.originator = originator
        self.value = 0
        self.TWS_h= TWS_h
        self.report('trader {} hired until b = {} or c = {}'
                    '          started by {}'
                    .format(self.name, self.b, self.c, self.originator))
        self.set_trading_hours(trading_permitted_until,
                               close_positions_after,
                               trading_permitted_from)
        self.future_gap = future_gap
        self.lb_profit = lb_profit
        self.max_stop = max_stop
        self.min_price_variation = min_price_variation
        self.previous_price = None # for running without TWS_h
        self.curr_time = None
        self.contract = None
        self.number_of_contracts = None

#    @property
#    def trade_direction(self):
#
#        if self.b is None:
#            direction = None
#        elif self.b < self.c:
#            direction = BEAR
#        else:
#            direction = BULL
#        return direction


    def crossed_a(self, bar):

        if not self.previous_price:
            crossed = False
        elif self.trade_direction == BEAR:
            if self.previous_price > self.a >= bar.low:
                crossed = True
            else:
                crossed = False
        elif self.trade_direction == BULL:
            if self.previous_price < self.a <= bar.high:
                crossed = True
            else:
                crossed = False
        else:
            crossed = False
        return crossed

    @property
    def enter_status(self):
        
        TWS_orders = self.TWS_h.order_status if self.TWS_h else None
        enter_id = self.enter_id
        status = None
        if self.TWS_h and enter_id:
            if enter_id in TWS_orders: 
                status = TWS_orders[enter_id].status
            else:
                status = 'order send to TWS, waiting'
                self.report('trader {} is waiting for TWS to confirm order'.
                            format(self.name),1)
        return status


    @property
    def exit_status(self):
        
        TWS_orders = self.TWS_h.order_status if self.TWS_h else None
        enter_id = self.enter_id
        status = None
        if self.TWS_h and self.enter_id:
            profit_status = TWS_orders[self.profit_id].status
            stop_status = TWS_orders[self.stop_id].status
            moc_status = TWS_orders[self.moc_id].status if self.moc_id else None
            if 'Filled' in (profit_status, stop_status, moc_status):
                status = 'Filled'
        return status


    @property
    def order_status(self):
        
      
        TWS_orders = self.TWS_h.order_status if self.TWS_h else None
        enter_id = self.enter_id
        status = self.enter_status
        if status == 'Filled':
            exit_status = self.exit_status
            if exit_status == 'Filled':
                status = 'order completed'
        return status

    @property
    def enter_trade_permitted(self):
        '''checks if you are allowed to enter a trade current time
        current time is the time set in the property curr_time when this is set
        curr_time has to be set in the update function and unset when leaving
        this function. If no current time is set it will be requested from TWS
        if available or set to system time'''
        def TWSorSystem_time():
            t = None
            if self.TWS_h:
                t = self.TWS_h.req_current_time()
            if not t:
                t = mypy.now()
            return t
        ### enter_trade_permitted ###
        first_in = self.trading_permitted_from
        last_in = self.trading_permitted_until
        time_ = self.curr_time if self.curr_time else self.TWS_h.req_current_time()
        permission = first_in <= time_
        if permission and last_in:
            permission = time_<= last_in
        return permission
        
        
    @property
    def mode(self):
        
        if self.TWS_h and self.enter_trade_permitted:
            mode = REAL_ENTER_OK
        elif self.TWS_h:
            mode = REAL_DONT_ENTER
        else:
            mode = SIMULATE_TWS
        return mode


#    @property
#    def enter_id(self):
#        
#        if (self.TWS_h and
#            self.__enter_id in self.TWS_h.order_status):
#            return self.__enter_id
#        elif not self.TWS_h:
#            return self.__enter_id
#        else:
#            return None
#
#
#    @enter_id.setter
#    def enter_id(self, id_):
#
#        self.__enter_id = id_



    @property
    def status(self):

        def standard():

            TWS_h = self.TWS_h
            #mypy.print_dict(TWS_h.order_status, 'ORDER STATUS')
            #print('enter_id ', self.enter_id, type(self.enter_id))
            order_status = self.order_status
            if self.__status == EMPTY and order_status:                
                if order_status == 'Filled':
                    self.__status = IN_TRADE
                    self.report('trader {}: could not remove order because '
                                'it has been filled\n'
                                'manual interaction?'.
                                format(self.name))
                if order_status == 'order completed':
                    self.__status = STOPPED
                    self.report('trader {}: could not remove order because '
                                'the order is completed!'.
                                format(self.name))
                if order_status == 'order send to TWS, waiting':
                    self.report('trader {} has enter_id but no enter status?'.
                                format(self.name))            
            if self.__status == MONITORING and order_status:
                if order_status == 'Filled':
                    self.__status = IN_TRADE
                    self.report('trader {}: order filled'.format(self.name))
                if order_status == 'order completed':
                    self.__status = STOPPED
                    self.report('trader {}: enter & exit order filled at once'.
                                format(self.name))
            elif self.__status == IN_TRADE:
                if self.order_status == 'order completed':
                    self.__status = STOPPED
                    self.report('trader {}: closed positions & stopped'.
                                format(self.name))
            elif self.__status == STOPPING:
                if order_status == 'Cancelled':
                    self.__status = STOPPED
                    self.report('trader {} removed orders & stopped'.
                                format(self.name))
                elif order_status == 'Filled':
                    self.__status = IN_TRADE
                    self.report('trader {} could not remove stop because '
                                'because it has filled orders\n'
                                'manual interaction?'.
                                format(self.name))                    
            return self.__status


        def simulator():

            return self.__status


        ### status ###

        status_fn = {REAL_ENTER_OK: standard,
                     REAL_DONT_ENTER: standard,
                     SIMULATE_TWS: simulator}
        return status_fn[self.mode]()


    @status.setter
    def status(self, status):
        self.__status = status


    def report(self, text, level=0):
        if self.reporter == TO_FILE:
            with open(self.report_settings[0], 'a') as of:
                of.write(text+'\n')          

    
    def set_trading_hours(self,
                          trading_permitted_until = mypy.datetime.max, #None,
                          close_positions_after = mypy.datetime.max, #None,
                          trading_permitted_from = mypy.datetime.min):

        if True: #not trading_permitted_until is None:
            self.trading_permitted_until = trading_permitted_until
        if True: #not close_positions_after is None:
            self.close_positions_after = close_positions_after
        self.trading_permitted_from = trading_permitted_from
        self.report('trader {} TRADING HOURS:\n'
                    '       from:   {}\n'
                    '       until:  {}\n'
                    '       cl.pos: {}'.
                    format(self.name,
                           self.trading_permitted_from,
                           self.trading_permitted_until,
                           self.close_positions_after))


    def set_reporter(self, reporter, *settings):

        reporters = [TO_FILE]
        if reporter == 'to file':
            reporter = TO_FILE
        if reporter in reporters:
            self.reporter = reporter
            self.report_settings = settings
            self.report('trader {} changed reporter\n'
                        '          {} {}'.
                        format(self.name, self.reporter,
                               self.report_settings))
        else:
            self.report('trader {} could not change reporter'.
                        format(self.name))
        


    def set_TWS_h(self, tws_handle, future_gap=None):

        if self.TWS_h:
            raise TraderError('Trader has TWS_h attached')
        if tws_handle:
            self.TWS_h = tws_handle
            self.future_gap = future_gap
            self.report('trader {} was assigned TWS handle: {}'.
                        format(self.name, tws_handle.name))
        else:
            self.TWS_h = self.future_gap = None


    def remove_TWS_h(self):

        if self.status == IN_TRADE:
            self.status == STOPPED
            self.report('trader {} !!!!! WARNING !!!!!\n'
                        '       TWS_h removed while in trade\n'
                        '       check TWS'.
                        format(self.name))
        if self.status == MONITORING:
            if self.enter_id:
                self.remove_order()
                self.enter_id = self.profit_id = None,
                self.stop_id = self.moc_id = None
                self.report('trader {} !!!!! WARNING !!!!!!\n'
                            '       TWS_h removed with open orders\n'
                            '       check TWS'.
                            format(self.name))
        self.TWS_h = self.future_gap = None
        self.report('trader {} TWS_h removed'.format(self.name))
            
            
            


    def set_future_gap(self, index_list, future_list):

        self.future_gap = (index_list, future_list)


    def send_order(self, contract, number_of_contracts, a, time_,
                   exchange='SMART', wait=False):

        def standard():
            
            TWS_h = self.TWS_h
            order_settings=dict(number_of_contracts=number_of_contracts,
                                direction=self.trade_direction,
                                enter_type='STP LMT',
                                enter_limit=self.a_corr,
                                enter_aux= self.a_corr,
                                profit_limit = self.b_corr,
                                stop_aux = self.c_corr)
            if self.trading_permitted_until:
                order_settings['enter_trade_before'] = self.trading_permitted_until
            if self.close_positions_after:
                order_settings['EOD_sell'] = self.close_positions_after
            bracket_order = tws.def_bracket_order(**order_settings)
#            print(bracket_order)
            e, p, s, m = TWS_h.place_bracket_order(contract, bracket_order)
            self.enter_id, self.profit_id, self.stop_id = e, p, s
            self.moc_id = m
            self.report('trader {} instructed to put order '
                        'a = {}, b = {}, c = {}'.
                        format(self.name, self.a_corr,
                               self.b_corr, self.c_corr))


        def eop():

            self.report('trader {} instructed to put order '
                        'a = {}, b = {}, c = {}\n'
                        '      !! ORDER POSTPONED EOP!!'.
                        format(self.name, self.a_corr,
                               self.b_corr, self.c_corr))


        def simulator():
            
             self.report('trader {} instructed to put order '
                        'a = {}, b = {}, c = {}\n'
                        '       !! VIRTUAL ORDER !!'.
                        format(self.name, self.a_corr,
                               self.b_corr, self.c_corr))            

        ### send_order ###

        send_order_fn = {REAL_ENTER_OK: standard,
                         REAL_DONT_ENTER: eop,
                         SIMULATE_TWS: simulator}
        status = self.status
        if status == STOPPED or status == STOPPING:
            raise IllegalRequest('Traider already stopped')
        if status == IN_TRADE:
            raise IllegalRequest('Traider already in trade')
        if status == MONITORING and self.enter_id:
            raise IllegalRequest('Traider already monitoring')
        self.a_corr, self.b_corr, self.c_corr = self.adjust(a, self.b, self.c)
        self.a = a
        self.contract = contract
        self.number_of_contracts = number_of_contracts
        send_order_fn[self.mode]()
        self.status = MONITORING


    def remove_order(self, wait=False):

        def standard():
            
            TWS_h = self.TWS_h
            if self.enter_id:
                TWS_h.cancel_order(self.enter_id)
            self.report('trader {} instructed TWS to remove order'.
                        format(self.name))

        
        def eop():
            
            TWS_h = self.TWS_h
            if self.enter_id:
                TWS_h.cancel_order(self.enter_id)
                self.report('trader {} instructed TWS to remove order'.
                            format(self.name))
            else:
                self.report('trader {} removed order'.format(self.name))


        def simulator():
            
            self.report('trader {} remover order\n'
                        '       !! VIRTUAL ORDER !!'
                        .format(self.name))

        ### remove_order ###

        remove_order_fn = {REAL_ENTER_OK: standard,
                           REAL_DONT_ENTER: eop,
                           SIMULATE_TWS: simulator}
        status = self.status
        if status == STOPPED or status == STOPPING:
            raise IllegalRequest('Traider already stopped')
        elif status == IN_TRADE:
            raise IllegalRequest('Traider already in trade')
        elif status == EMPTY:
            raise IllegalRequest('No orders to remove')
        self.a = 0
        self.a_corr = self.b_corr = self.c_corr = 0
        remove_order_fn[self.mode]()
        self.status = EMPTY


    def send_new_a_value(self, a, time_, wait=False):

        def standard():
          
            TWS_h = self.TWS_h
            try:
                TWS_h.change_order(self.enter_id, 
                                   limit=self.a_corr, aux=self.a_corr)
                TWS_h.change_order(self.profit_id, limit=self.b_corr)
                TWS_h.change_order(self.stop_id, aux=self.c_corr)
            except TWSClient.TWSClientWarning:
                self.report('trader {} could not change orders'.
                            format(self.name))
            self.report('trader {} instructed TWS to change '
                        'enter order a: '.
                        format(self.name, self.a))


        def eop():

            self.report('trader {} instructed to change a = {}'.
                        format(self.name, self.a))


        def simulator():

            self.report('trader {} instructed to change a = {}'
                        '       !! VIRTUAL ORDER !!'.
                        format(self.name, self.a))                            
            

        ### send_new_a_value ###

        send_new_a_value_fn = {REAL_ENTER_OK: standard,
                               REAL_DONT_ENTER: eop,
                               SIMULATE_TWS: simulator}
        status = self.status
        if status == STOPPED or status == STOPPING:
            raise IllegalRequest('Traider already stopped')
        elif status == IN_TRADE:
            raise IllegalRequest('Traider already in trade')
        elif status == EMPTY:
            raise IllegalRequest('No orders to change')
        self.a_corr, self.b_corr, self.c_corr = self.adjust(a, 
                                                            self.b,
                                                            self.c)
        self.a = a
        send_new_a_value_fn[self.mode]()
            

    def adjust(self, a, b, c):
        
        a_corr = a
        b_corr = a + ((b - a) * self.lb_profit / 100)
        if abs(a - c) > self.max_stop:
            c_corr = a + (1 if c > a else -1) * self.max_stop
        else:
            c_corr = c
        if self.future_gap:            
            gap = self.TWS_h.average_difference(*self.future_gap)[0]
            a_corr += gap
            b_corr += gap
            c_corr += gap
        if self.min_price_variation:
            a_corr = mypy.d_round(a_corr, self.min_price_variation)
            b_corr = mypy.d_round(b_corr, self.min_price_variation)
            c_corr = mypy.d_round(c_corr, self.min_price_variation)
        return a_corr, b_corr, c_corr


    def update(self, latest_bar):

        def standard():
            
            TWS_h = self.TWS_h
            if status == STOPPED or status == STOPPING or status == IN_TRADE:
                pass
            if self.status == EMPTY and self.enter_id:
                if self.order_status == 'Cancelled':
                    self.enter_id = self.profit_id = None
                    self.stop_id = self.moc_id = None
                    self.report('trader {}: TWS confirmed cancelled order'.
                                format(self.name))
                if latest_bar_outside_limits and self.enter_id:
                    self.status = STOPPING
                    self.report('trader {}: trader wants to stop but is '
                                'waiting for TWS to close open orders'.
                                format(self.name))
            if (self.status == EMPTY and
                latest_bar_outside_limits and
                not self.enter_id):
                self.status = STOPPED
                self.report('trader {} stopped latest bar outside limits'
                            .format(self.name))
            if status == MONITORING and latest_bar_outside_limits:
                self.remove_order()
                self.status = STOPPING if self.enter_id else STOPPED
            elif (status == MONITORING and not self.enter_id and
                  not(self.future_gap and 
                      self.TWS_h.average_difference(*self.future_gap)[1]<3)):
                self.send_order(self.contract,
                                self.number_of_contracts,
                                self.a,
                                mypy.now())
            elif (status == MONITORING and self.enter_id and
                  self.future_gap):
                if self.enter_id in TWS_h.order_status:
                    new_a, new_b, new_c = self.adjust(self.a, self.b, self.c)
                    if not (new_a == self.a_corr and 
                            new_b == self.b_corr and
                            new_c == self.c_corr):
                        self.send_new_a_value(self.a, mypy.now())


        def eop():

            TWS_h = self.TWS_h
            if status == STOPPED or status == STOPPING:
                pass
            if self.status == EMPTY and self.enter_id:
                if self.order_status == 'Cancelled':
                    self.enter_id = self.profit_id = None
                    self.stop_id = self.moc_id = None
                    self.report('trader {}: TWS confirmed cancelled order'.
                                format(self.name))
                if latest_bar_outside_limits and self.enter_id:
                    self.status = STOPPING
                    self.report('trader {}: trader wants to stop but is '
                                'waiting for open order'.
                                format(self.name))
            if (self.status == EMPTY and
                latest_bar_outside_limits and
                not self.enter_id):
                self.status = STOPPED
                self.report('trader {} stopped'.format(self.name))
            if status == MONITORING and latest_bar_outside_limits:
                self.remove_order()
                self.status = STOPPING if self.enter_id else STOPPED
            if status == MONITORING and self.enter_id:
                if self.order_status == 'Cancelled':
                    self.enter_id = self.profit_id = None
                    self.stop_id = self.moc_id = None
                    self.report('trader {}: TWS removed order'.
                                format(self.name))
            if status == MONITORING and self.crossed_a(latest_bar):
                # here we could do some smart things, get in and
                # watch what happens or even report back to the
                # the traders client so he can make a decission or
                # use a variable to tell what to do,
                # for now I just stop if he is getting out in the evening
                # becouse if gets in he also gets out and would have had
                # the stopped status                
                self.remove_order()
                self.status = STOPPING if self.enter_id else STOPPED
            if status == IN_TRADE:
                # here are some poss to, can't think of anything
                # with some potential right now. But I'm in eop so
                # there should be an active TWS that takes care of the
                # trade
                pass


        def simulator():

            if self.b > self.c:  #bull trade
                if status == EMPTY:
                    if lb.high > self.b or lb.low < self.c:
                        self.report('trade {} out of limits {},{}'.
                                    format(self.name, lb.high, lb.low))
                        self.status = STOPPED
                elif status == MONITORING:
                    if (self.previous_price 
                        and self.previous_price < self.a_corr
                        and (self.trading_permitted_until == None or
                             lb.time < self.trading_permitted_until)):
                        if lb.high >= self.a_corr:
                            self.status = IN_TRADE
                            self.report('trade {} entered {}'.
                                        format(self.name, lb.high))
                    self.previous_price = lb.high
                    if (lb.high == self.a_corr
                        and (self.trading_permitted_until == None or
                             lb.time < self.trading_permitted_until)):
                        self.status = IN_TRADE
                        self.report('trade {} entered {}'.
                                    format(self.name, lb.high))
                    if lb.high > self.b or lb.low < self.c:
                        self.status = STOPPED
                        self.report('trade {} out of limits {},{}'.
                                    format(self.name, lb.high, lb.low))
                    if False: #lb.time > self.trading_permitted_until:
                        self.status = EMPTY
                        self.report('trade {}: entering trades not allowed '
                                    'after {}\n' 
                                    '      removing orders'.
                                    format(self.name, 
                                           self.trading_permitted_until))
                elif status == IN_TRADE:
                    if lb.high >= self.b_corr:
                        self.status = STOPPED
                        self.report('trader {} gain {}'.
                                    format(self.name, lb.high))
                    elif lb.low <= self.c_corr:
                        self.status = STOPPED
                        self.report('trader {} loss {}'.
                                    format(self.name, lb.low))
                    elif (not self.close_positions_after == None and
                          lb.time > self.close_positions_after):
                        self.report('trader {} stopped EOD {}, {}'.
                                    format(self.name, lb.low, lb.high))
                        self.status = STOPPED
            elif self.c > self.b:  #bear trade
                if status == EMPTY:
                    if lb.high > self.c or lb.low < self.b:
                        self.report('trade {} out of limits {},{}'.
                                    format(self.name, lb.high, lb.low))
                        self.status = STOPPED
                elif status == MONITORING:
                    if (self.previous_price 
                        and self.previous_price > self.a_corr
                        and (self.trading_permitted_until == None or
                             lb.time < self.trading_permitted_until)):
                        if lb.low <= self.a_corr:
                            self.status = IN_TRADE
                            self.report('trade {} entered {}'.
                                        format(self.name, lb.low))
                    self.previous_price = lb.low
                    if (lb.low == self.a_corr
                        and (self.trading_permitted_until == None or
                             lb.time < self.trading_permitted_until)):
                        self.status = IN_TRADE
                        self.report('trade {} entered {}'.
                                    format(self.name, lb.low))
                    if lb.high > self.c or lb.low < self.b:
                        self.status = STOPPED
                        self.report('trade {} out of limits {},{}'.
                                    format(self.name, lb.high, lb.low))
                    if False: #lb.time > self.trading_permitted_until:
                        self.status = EMPTY
                        self.report('trade {}: entering trades not allowed \n'
                                    'after {}, removing orders'.
                                    format(self.name, 
                                           self.trading_permitted_until))
                elif status == IN_TRADE:
                    if lb.high >= self.c_corr:
                        self.status = STOPPED
                        self.report('trader {} loss {}'.
                                    format(self.name, lb.high))
                    elif lb.low <= self.b_corr:
                        self.status = STOPPED
                        self.report('trader {} gain {}'.
                                    format(self.name, lb.low))
                    elif (not self.close_positions_after == None and
                          lb.time > self.close_positions_after):
                        self.report('trader {} stopped EOD {}, {}'.
                                    format(self.name, lb.low, lb.high))
                        self.status = STOPPED
            
                
        ### update ###

        update_fn = {REAL_ENTER_OK: standard,
                     REAL_DONT_ENTER: eop,
                     SIMULATE_TWS: simulator}
        lb = latest_bar
        self.curr_time = lb.time
        status = self.status
        latest_bar_outside_limits = (lb.low < min(self.b, self.c) or
                                     lb.high > max(self.b, self.c))
        update_fn[self.mode]()
        self.previous_price = lb.low if self.trade_direction == BEAR else lb.high
        if self.future_gap:
            print('gap: {}'.
                  format(self.TWS_h.average_difference(*self.future_gap)[0]))
        if not status == self.status:
            answer = 'trader {}({}): {}'.format(self.name, lb.time, self.status)
            print(answer)
            self.report(answer)
        else:
            answer = ''
        self.curr_time = None
        return answer
