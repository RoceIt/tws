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
# bar positions
################################################################################
OUTSIDE_LIMITS = '$OUTSIDE_LIMITS'
# bar has values outside the limits of the corse abc
IN_LIMITS = '$IN_LIMITS'
# bar is inside limits but no a value is set for other tests
BETWEEN_AB = '$BETWEEN_AB'
# bar is between a and b
BETWEEN_AC = '$BETWEEN_AC'
# bar is between a and c
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
                 report_settings=STD_REPORT_FILE,
                 time_ = None):

        self.name = name
        self.reporter = reporter
        self.report_settings = [report_settings]
        self.a = 0
        self.b = b
        self.c = c
        self.a_corr = self.b_corr = self.c_corr = 0
        self.trade_direction = BEAR if self.b < self.c else BULL
        self.enter_id = self.profit_id = self.stop_id = self.moc_id = None
        self.curr_time = None
        self.status = EMPTY
        self.positions = 0
        self.originator = originator
        self.value = 0
        self.TWS_h= TWS_h
        self.report('trader {} hired until b = {} or c = {}\n'
                    '          started by {} @ {}'
                    .format(self.name, self.b, self.c, self.originator,
                            time_))
        self.set_trading_hours(trading_permitted_until,
                               close_positions_after,
                               trading_permitted_from)
        self.future_gap = future_gap
        self.lb_profit = lb_profit
        self.max_stop = max_stop
        self.min_price_variation = min_price_variation 
        self.previous_bar = None
        #self.previous_bar_position = None
        self.contract = None
        self.number_of_contracts = None
        self.enter_time = self.enter_value = None
        self.exit_time = self.exit_value = None
        self.min_in_trade = self.max_in_trade = None
        self.result = None
        self.reported = False

    @property
    def TWSorSystem_time(self):
        '''returns TWS time if available else system time'''
        t = None
        if self.TWS_h:
            t = self.TWS_h.req_current_time()
        if not t:
            t = mypy.now()
        return t

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
    def order_entry_price(self):
        '''Returns the entry price of the last filled order'''
        TWS_orders = self.TWS_h.order_status
        enter_id = self.enter_id
        price = TWS_orders[enter_id].avg_fill_price
        return price
    
    @property
    def order_exit_price(self):
        '''Returns the exit price of the last filled order'''
        TWS_orders = self.TWS_h.order_status
        price = max(TWS_orders[self.profit_id].avg_fill_price,
                    TWS_orders[self.stop_id].avg_fill_price,
                    TWS_orders[self.moc_id].avg_file_price if self.moc_id else 0
                    )
        return price
    
    @property
    def enter_trade_permitted(self):
        '''checks if you are allowed to enter a trade current time
        current time is the time set in the property curr_time when this is set
        curr_time has to be set in the update function and unset when leaving
        this function. If no current time is set it will be requested from TWS
        if available or set to system time'''
        ### enter_trade_permitted ###
        trading_permitted = True
        t = self.curr_time if self.curr_time else self.TWSorSystem_time
        if self.trading_permitted_until:
            trading_permitted = t <= self.trading_permitted_until
        if trading_permitted and self.trading_permitted_from:
            trading_permitted = t >= self.trading_permitted_from
        return trading_permitted
    
    @property
    def open_positions_permitted(self):
        '''checks if open positions are allowed'''        
        t = self.curr_time if self.curr_time else self.TWSorSystem_time
        test = True
        if self.close_positions_after:
            test = t <= self.close_positions_after
        return test
        
    @property
    def mode(self):
        
        if self.TWS_h and self.enter_trade_permitted:
            mode = REAL_ENTER_OK
        elif self.TWS_h:
            mode = REAL_DONT_ENTER
        else:
            mode = SIMULATE_TWS
        return mode
    

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
        self.report('trader {} status changed to {} @ {}'.
                    format(self.name, status, self.curr_time))

    def register_entry(self):
        '''register information when entering a trade'''
        def standard():
            self.enter_time = self.TWSorSystem_time
            self.enter_value = self.order_entry_price
            if self.trade_direction is BULL:
                self.positions = self.number_of_contracts
            else:
                self.positions = -self.number_of_contracts
        def no_entry():
            print('entering a trade???????????? in eop')
        def simulator():
            self.enter_time = self.curr_time
            self.enter_value = self.a
        if self.trade_direction is BULL:
            self.positions = self.number_of_contracts
        else:
            self.positions = -self.number_of_contracts

        ### register entry ###
        register_entry_fn = {REAL_ENTER_OK: standard,
                             REAL_DONT_ENTER: no_entry,
                             SIMULATE_TWS: simulator}
        register_entry_fn[self.mode]()
        bs = {BEAR: 'sold', BULL: 'bought'}
        self.report('trader {} executed order \n'
                    '       {} {} {} for {} @ {}'.
                    format(self.name, bs[self.trade_direction],
                           self.number_of_contracts, self.contract, 
                           self.enter_value, self.enter_time))
        
    def register_exit(self, price=None):
        '''register information when entering a trade'''
        def standard(foo):
            self.exit_time = self.TWSorSystem_time
            self.exit_value = self.order_exit_price
            result_per_contract = self.exit_value - self.enter_value 
            self.result = self.positions * result_per_contract
            self.positions = 0
        def simulator(price):
            if not price:
                print('register exit needs a price in simulator mode')
                raise
            self.exit_time = self.curr_time
            self.exit_value = price
            result_per_contract = price - self.enter_value 
            self.result = self.positions * result_per_contract
            self.positions = 0
        ### register exit ###
        register_exit_fn = {REAL_ENTER_OK: standard,
                             REAL_DONT_ENTER: standard,
                             SIMULATE_TWS: simulator}
        register_exit_fn[self.mode](price)
        result = 'GAIN' if self.result > 0 else 'LOSS'
        self.report('trader {} closed positions for {} @ {}\n'
                    '       {}: {}'.
                    format(self.name, self.exit_value, self.enter_time,
                           result, self.result))

    def report(self, text, level=0):
        if self.reporter == TO_FILE:
            with open(self.report_settings[0], 'a') as of:
                of.write(text+'\n')          

    
    def set_trading_hours(self,
                          trading_permitted_until = mypy.datetime.max, #None,
                          close_positions_after = mypy.datetime.max, #None,
                          trading_permitted_from = mypy.datetime.min):
        '''sets trading hours and sends new values to the reporter'''
        self.trading_permitted_until = trading_permitted_until
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
            
    def reset_previous_bar_info(self):
        #self.previous_bar = self.previous_bar_position = None
        self.previous_bar = None


    def remove_TWS_h(self):

        if self.status == IN_TRADE:
            self.status == STOPPED
            self.report('trader {} !!!!! WARNING !!!!!\n'
                        '       TWS_h removed while in trade\n'
                        '       check TWS'.
                        format(self.name))
        if self.status == MONITORING:
            if self.enter_id:
                self.remove_order(client='remove_TWS_h')
                self.enter_id = self.profit_id = None,
                self.stop_id = self.moc_id = None
                self.report('trader {} !!!!! WARNING !!!!!!\n'
                            '       TWS_h removed with open orders\n'
                            '       check TWS'.
                            format(self.name))
                self.status = EMPTY
        self.TWS_h = self.future_gap = None
        self.report('trader {} TWS_h removed'.format(self.name))
            
            
            


    def set_future_gap(self, index_list, future_list):

        self.future_gap = (index_list, future_list)


    def send_order(self, contract, number_of_contracts, a, time_,
                   exchange='SMART', 
                   client='unknown', wait=False):

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
            raise IllegalRequest('Trader already stopped')
        if status == IN_TRADE:
            raise IllegalRequest('Trader already in trade')
        if status == MONITORING and self.enter_id:
            raise IllegalRequest('Trader already monitoring')
        self.a_corr, self.b_corr, self.c_corr = self.adjust(a, self.b, self.c)
        self.a = a
        self.contract = contract
        self.number_of_contracts = number_of_contracts
        if (not self.a_corr == self.c_corr and
            not self.a_corr == self.b_corr):
            send_order_fn[self.mode]()
            self.status = MONITORING
            self.report('       instructed by {} @ {}'.
                        format(client, time_))
        else:
            #catch the  trades where c=a and a=b there's nothing to
            #gain there
            self.status = STOPPED
            self.report('trader {} stopped\n'
                        '         a_corr {} is the same as '
                        'b_corr {} or c_corr {}\n'
                        '         @ {}'.
                        format(self.name, 
                               self.a_corr, self.b_corr, self.c_corr,
                               time_))


    def remove_order(self, client='unknown', time_=None, wait=False):

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
            
            self.report('trader {} removed order\n'
                        '       !! VIRTUAL ORDER !!'
                        .format(self.name))

        ### remove_order ###

        remove_order_fn = {REAL_ENTER_OK: standard,
                           REAL_DONT_ENTER: eop,
                           SIMULATE_TWS: simulator}
        status = self.status
        if not time_:
            time_ = self.curr_time            
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
        self.report('       instructed by {} @ {}'.
                    format(client, time_))


    def send_new_a_value(self, a, client='unknown', time_=None, wait=False):

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
        if not time_:
            time_ = self.curr_time
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
        self.report('       instructed by {} @ {}'.
                    format(client, time_))
            

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
        if self.TWS_h and self.min_price_variation:
            a_corr = mypy.d_round(a_corr, self.min_price_variation)
            b_corr = mypy.d_round(b_corr, self.min_price_variation)
            c_corr = mypy.d_round(c_corr, self.min_price_variation)
        return a_corr, b_corr, c_corr


    def update(self, latest_bar):
        '''check situation according to the latest market prices'''
        #def position(bar):
        #    if not bar.inside_interval(self.b, self.c):
        #        answer = OUTSIDE_LIMITS
        #    elif self.a == 0:
        #        answer = IN_LIMITS
        #    elif not bar.outside_interval(self.a, self.b):
        #        answer = BETWEEN_AB
        #    elif not bar.outside_interval(self.a, self.c):
        #        answer = BETWEEN_AC
        #    try:
        #        return answer
        #    except Exception:
        #        print(bar, self.a, self.b, self.c)
        #        raise
            
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
                self.remove_order(client='trader.update.standard')
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
                        self.send_new_a_value(self.a, 
                                              client='trader.update.standard',
                                              time_=mypy.now())


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
                self.remove_order(client='trader.update.eop.outside_limits')
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
                self.remove_order('trader.update.eop.crossed a')
                self.status = STOPPING if self.enter_id else STOPPED
            if status == IN_TRADE:
                # here are some poss to, can't think of anything
                # with some potential right now. But I'm in eop so
                # there should be an active TWS that takes care of the
                # trade
                pass


        def simulator():
            
            if latest_bar_outside_limits:
                #Stop a trader when de limits are broken
                if (self.positions and
                    (self.b_corr > lb.high > self.b
                     or
                     self.b_corr < lb.low < self.b)):
                    return
                self.status = STOPPED
                self.report('trader {} out of limits {},{}'.
                            format(self.name, lb.high, lb.low))
                if self.positions:
                    if (lb.high > self.b > self.a
                        or
                        lb.low < self.b < self.a):
                        #out on the good side, b_corr is a save guess
                        price = self.b_corr
                    elif lb.high > self.c > self.a:
                        #bear out on the wrong side,
                        price = max(self.c_corr, lb.low)
                    elif lb.low < self.c < self.a:
                        #bull out on th wrong side
                        price = min(self.c_corr, lb.high)
                    else:                        
                        self.report('      !!! unhandeled open positions !!!'
                                    '      how did i get here?'.
                                    format(self.name))
                        print('self.a {} \nself.b {} \nself.c {}'.
                              format(self.a, self.b, self.c))
                        raise
                    self.register_exit(price)
            elif status is EMPTY and self.positions:
                #Stop empty traders with positions, they should NOT exist
                self.status = STOPPED
                self.report('trader {} status is empty but'
                            '      !!! unhandeled open positions !!!'
                            '       set status to STOPPED'.
                            format(self.name))
            elif not self.previous_bar:
                #happens with frechly started and restarted traders
                #make sure you don't think you had a chance to buy at
                #the current price
                pass
            elif status is MONITORING and self.enter_trade_permitted:
                #a trade with an order attached and entering a trade is 
                #allowed
                #if ((self.latest_bar_position is BETWEEN_AB and
                #    self.previous_bar_position is BETWEEN_AC)
                #    or
                #    (self.latest_bar_position is BETWEEN_AC and
                #    self.previous_bar_position is BETWEEN_AB)):
                if self.a in self.previous_bar + lb:
                    #prices have crossed a
                    if lb.inside_interval(self.c_corr, self.b_corr):
                        #if the prices stayed in  the corrected values
                        #it's a normal trade
                        self.status = IN_TRADE
                        self.register_entry()
                    elif not lb.outside_interval(self.c_corr, self.c):
                        #if there were values between c_corr and cit's
                        #hard to tell what happened. implemented bad
                        #case scenario in @ a, out @ c-corr
                        self.register_entry()
                        self.status = IN_TRADE
                        #check if the close of the bar is outside c_corr, c
                        #if not, stop the trade, could be a loss
                        helper_min = min(self.c_corr, self.c)
                        helper_max = max(self.c_corr, self.c)
                        if helper_min < lb.close < helper_max:
                            self.register_exit(self.c_corr)
                            self.status = STOPPED
                    elif not lb.outside_interval(self.b_corr, self.b):
                        #bar also crossed the profit taker
                        #scenario in @ a, out @ b_corr
                        self.register_entry()
                        self.register_exit(self.b_corr)
                        self.status = STOPPED
            elif status is MONITORING and not self.enter_trade_permitted:
                #Needs some more thinking !!
                #if ((self.latest_bar_position is BETWEEN_AB and
                #    self.previous_bar_position is BETWEEN_AC)
                #    or
                #    (self.latest_bar_position is BETWEEN_AC and
                #    self.previous_bar_position is BETWEEN_AB)):
                if self.a in self.previous_bar + lb:
                    #order is triggert so for now i set it to stopped
                    #it's also possible not to register this and see what happens
                    #next day
                    self.STATUS = STOPPED
                    self.report('trader {} stopped, because triggered after '
                                'hours'.
                                format(self.name))        
            elif status is IN_TRADE and not self.open_positions_permitted:
                #close open positions when you're not allowed to have any
                #simulator sells at the worst price in this bar
                self.status = STOPPED
                low = (lb.low - self.enter_value) * self.positions
                high = (lb.high - self.enter_value) * self.positions
                price = lb.low if low < high else lb.high
                self.register_exit(price)
            elif (status is IN_TRADE and 
                  not lb.inside_interval(self.c_corr, self.b_corr)):
                #if last bar broke c_corr or b_corr the trade is over
                self.status = STOPPED
                if not lb.outside_interval(self.c_corr, self.c):
                    price = self.c_corr
                elif not lb.outside_interval(self.b_corr, self.b):
                    price = self.b_corr
                else:
                    print('trader {}, a: {}, b: {}, c: {}, b_c: {}, c_c: {}'.
                          format(self.name, self.a, self.b, self.c,
                                 self.b_corr, self.c_corr))
                    print('lb: ', lb)
                    print('there must be something wrong, you\'re outside '
                          'c_corr b_corr but I can\'t find where?')
                    raise
                self.register_exit(price)
                            
                
        ### update ###

        update_fn = {REAL_ENTER_OK: standard,
                     REAL_DONT_ENTER: eop,
                     SIMULATE_TWS: simulator}
        lb = latest_bar
        self.curr_time = lb.time
        status = self.status
        if status is STOPPED:
            return ''
        latest_bar_outside_limits = (lb.low < min(self.b, self.c) or
                                     lb.high > max(self.b, self.c))
        #self.latest_bar_position = position(lb)
        #print(self.curr_time, self.c_corr, self.a_corr, self.b_corr, '|', lb.low, lb.high)
        #print(self.curr_time, self.c, self.a, self.b, '|', lb.low, lb.high)
        #print('   ', self.latest_bar_position)
        #input('...')
        update_fn[self.mode]()
        self.previous_price = lb.low if self.trade_direction == BEAR else lb.high #R
        self.previous_bar = lb
        #self.previous_bar_position = self.latest_bar_position
        if self.future_gap:
            print('gap: {}'.
                  format(self.TWS_h.average_difference(*self.future_gap)[0]))
        new_status = self.status
        if new_status is IN_TRADE:
            if self.min_in_trade:
                self.min_in_trade = min(self.min_in_trade, lb.low)
                self.max_in_trade = max(self.max_in_trade, lb.high)
            else:
                self.min_in_trade = lb.low
                self.max_in_trade = lb.high
        if not status == new_status:
            answer = 'trader {}({}): {}'.format(self.name, lb.time, self.status)
            self.report(answer)
        else:
            answer = ''
        self.curr_time = None
        return answer
