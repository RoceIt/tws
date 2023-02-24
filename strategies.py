#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)

#import datetime

import validate
#from trader import TraderRequest
from market import Market, Order
import roc_datetime as r_dt

class Error(Exception): pass

class Strategy():
    '''
    !!!!
    Tell the user if and how this strategy is compatible with others. 
    Make sure to discribe which local market and contract names are
    required.
    Don't forget to discribe how the requests size paremeter is used.
    '''
    
    name = 'make sure it makes sense and is not dubious'
    required_market_names = []
    required_contract_names = []
    
    @staticmethod
    def strategy_finished(*arg_t, **kw_d):
        '''The perfect gov manager, used to do nothing!'''
        return None

class EnterStrategy(Strategy):
    '''
    An enter strategy.
    '''    
    provides_locals = [
        #'single_entry_order_tracker',
    ] 

class ExitStrategy(Strategy):
    '''
    An exit strategy.
    '''
    provides_locals = []
    required_locals = [
        #'single_entry_order_tracker',
    ]
    
    @classmethod
    def validate(cls, request, the_trader):
        for required_local in cls.required_locals:
            if required_local not in request.provided_strategy_locals:
                return ('{} not provided by available strategies'.
                        format(required_local))

class SingleDefault(EnterStrategy):
    '''Makes it possible to enter with one contract in the market.
    
    provides the single_entry_order_tracker when sended.
    '''

    name = 'single default'
    provides_locals = [
        'single_entry_order_tracker',
    ]
    
    def __init__(self,
            start=None,
            valid_until=None,
            limit_price=0,
            message = 'enter',
    ):
        ###
        ###
        self.start = start or ('now',)
        self.valid_until = valid_until or ('gtc',)
        self.limit_price = limit_price
        self.single_entry_order_tracker = None
        self.single_entry_size_filled = 0
        self.single_entry_value = 0
        self.message = message
    
    def arm(self, request, the_trader):
        order_id = '#'.join([request.id_, 'single_enter'])
        market_name = request.default_market()
        contract = request.default_contract()
        print("using contract: {}".format(contract))
        order_type = 'limit' if self.limit_price > 0 else 'market'
        order_kw_d = dict()            
        order_kw_d['id'] = order_id
        order_kw_d['action'] = 'buy' if request.direction == 'long' else 'sell'
        order_kw_d['size'] = ('number', request.size)
        order_kw_d['contract'] = contract
        order_kw_d['start'] = self.start
        order_kw_d['until'] = self.valid_until
        order_kw_d['type'] = order_type
        if self.limit_price > 0:
            order_kw_d['limit'] = ('number', self.limit_price)
        order_kw_d['message'] = self.message
        enter_order = Order(**order_kw_d)
        ###
        request.single_entry_order_tracker = (market_name, order_id)
        request.order_trackers['single_enter'] = (market_name, order_id)
        orders = {request.single_entry_order_tracker: enter_order}
        managers = [self.report_entry_progression(request, the_trader)]    
        return orders, managers
    
    def report_entry_progression(self, request, the_trader):
        market_name, order_id = request.single_entry_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()
        def order_manager(at_time):
            print('@@@@@@@@@@ running order manager')
            print(request)
            order_info = market.status_report(order_id, at_time)
            if (order_info.filled is True
                or 
                order_info.stopped
            ):
                next_manager = done
            else:
                next_manager = order_manager
            return next_manager
        return order_manager
    
class CloseOnSignal(ExitStrategy):
    
    name = 'close_on_signal'
    provides_locals = [
        'cos_order_tracker',
    ]
    required_locals = [
        'single_entry_order_tracker',
    ]
    
    def __init__(self,
            signal='close_on_signal',
            signal_message='closed position on signal {}'
            ):
        self.signal, self.message = (
                signal,
                signal_message.format(signal)
        )
    
    def arm(self, request, the_trader):
        tracked_order_market, order_id = request.single_entry_order_tracker
        cos_id = '#'.join([request.id_, 'close_on_signal'])
        action = 'close'
        parent = order_id
        size = ('parent', 100) # 100% of parent order size
        contract = until = ''
        cos_order = Order(
            id=cos_id,
            action=action,
            size=size,
            contract=contract,
            parent_order_id=parent,
            start=('on signal', self.signal),
            until=until,
            type='market',
            message=self.message,
        )
        ###
        request.cos_order_tracker = (tracked_order_market, cos_id)
        request.order_trackers['cos'] = (tracked_order_market, cos_id)
        orders = {
            request.cos_order_tracker: cos_order,
        }
        managers = [self.watch_cos_order(request, the_trader)]
        return orders, managers
    
    def watch_cos_order(self, request, the_trader):       
        market_name, order_id = request.cos_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()
        def exit_manager_1(at_time):
            #print('cos watching:', market_name, '/', order_id)
            cos_info = market.status_report(order_id, at_time)
            if cos_info.stopped is True:
                print('coss closed')
                next_manager = done
            else:
                next_manager = exit_manager_1
            return next_manager
        return exit_manager_1
            
class SingleStopProfitTaker(ExitStrategy):
    
    name = 'single stop profit taker'
    provides_locals = [
        'single_stop_order_tracker',
        'single_profit_order_tracker',
    ]
    required_locals = [
        'single_entry_order_tracker',
    ]
    
    def __init__(self,
            fix_stop=False,
            stop_base=False,
            stop_ofset=None,
            stop_percentage=None,
            initial_safety_stop_value=False,
            initial_stop_message='stopped out, initial stop',
            stop_message='stopped out',
            
            fix_profit=False,
            profit_base=False,
            profit_ofset=None,
            profit_percentage=None,
            profit_message='profit taker reached',
            
            min_tick = None,
        ):
        if (fix_stop and stop_base
            or
            fix_profit and profit_base
            or
            not stop_base and (stop_ofset or stop_percentage)
            or
            not profit_base and (profit_ofset or profit_percentage)
            or
            stop_ofset and stop_percentage
            or
            profit_ofset and profit_percentage
        ):
            raise Error('Dubious strategie settings.')
        
        ###
        ###
        (self.fix_stop, self.stop_base, self.stop_ofset, self.stop_percentage, 
         self.initial_safety_stop_value, self.fix_profit, self.profit_base,
         self.profit_ofset, self.profit_percentage, self.min_tick
         ) = (
         fix_stop, stop_base, stop_ofset, stop_percentage, 
         initial_safety_stop_value, fix_profit, profit_base, profit_ofset, 
         profit_percentage, min_tick)
    
    def arm(self, request, the_trader):
        parent_order_market, parent_order_id = request.single_entry_order_tracker
        stop_id = '#'.join([request.id_, 'single_stop'])
        profit_id = '#'.join([request.id_, 'single_profit'])
        action = 'close'
        parent = parent_order_id
        size = ('parent', 100) # 100% of parent order size
        contract = start = until = ''
        if self.fix_stop:
            stop_stop = ('number', self.fix_stop)
            stop_message = 'stopped out fix @ {}'.format(self.fix_stop)
        if self.fix_profit:
            profit_limit = ('number', self.fix_profit)
            profit_message = 'fix profit @ {}'.format(self.fix_profit)
        if self.stop_ofset:
            stop_stop = ('ofset', 
                         self.stop_base, self.stop_ofset, self.min_tick)
            stop_message = 'stopped out ofset @ {}'.format(self.stop_ofset)
        if self.profit_ofset:
            profit_limit = ('ofset', 
                            self.profit_base, self.profit_ofset, self.min_tick)
            profit_message = 'ofset profit @ {}'.format(self.profit_ofset)
        if self.stop_percentage:
            stop_stop = ('percentage', 
                         self.stop_base, self.stop_percentage, self.min_tick)
            stop_message = ('stopped out ofset @ {}%'.
                              format(self.stop_percentage))
        if self.profit_percentage:
            profit_limit = ('percentage', 
                            self.stop_base, self.profit_percentage, self.min_tick)
            profit_message = 'profit @ {}%'.format(self.profit_percentage)
        stop_order = Order(
            id=stop_id,
            action=action,
            size=size,
            contract=contract,
            parent_order_id=parent,
            start=start,
            until=until,
            type='stop',
            stop=stop_stop,
            message=stop_message,
        )
        profit_order = Order(
            id=profit_id,
            action=action,
            size=size,
            contract=contract,
            parent_order_id=parent,
            start=start,
            until=until,
            type='limit',
            limit=profit_limit,
            message=profit_message,
        )
        ###
        request.single_stop_order_tracker = (
            parent_order_market, 
            stop_id,
        )
        request.order_trackers['single_stop'] = (parent_order_market, stop_id)
        request.single_profit_order_tracker = (
            parent_order_market, 
            profit_id,
        )
        request.order_trackers['single_profit'] = (parent_order_market, profit_id)
        orders = {
            request.single_stop_order_tracker: stop_order,
            request.single_profit_order_tracker: profit_order,
        }
        managers = [self.report_exit_progression_1(request, the_trader)]
        return orders, managers
    
    def report_exit_progression_1(self, request, the_trader):        
        market_name, order_id = request.single_entry_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()
        def exit_manager_1(at_time):
            enter_info = market.status_report(order_id, at_time)
            if enter_info.filled is True:
                next_manager = self.report_exit_progression_2(
                    request, 
                    the_trader,
                )
            elif enter_info.stopped:
                next_manager = done
            else:
                next_manager = exit_manager_1
            return next_manager
        return exit_manager_1
    
    def report_exit_progression_2(self, request, the_trader):
        market_name, stop_id = request.single_stop_order_tracker
        foo, profit_id = request.single_profit_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()
        def exit_manager_2(at_time):
            stop_stopped = market.status_report(stop_id, at_time).stopped
            profit_stopped = market.status_report(profit_id, at_time).stopped
            if stop_stopped or profit_stopped:
                next_manager = done
            else:
                next_manager = exit_manager_2
            return next_manager
        return exit_manager_2
    
class SingleTrailingStop(ExitStrategy):
    
    name = "single_trailing_stop"
    provides_locals = [
        'single_trailing_order_tracker',
    ]
    required_locals = [
        'single_entry_order_tracker',
    ]
    
    def __init__(self,            
            fix_stop=False,
            stop_base=False,
            stop_ofset=None,
            stop_percentage=None,
            initial_safety_stop_value=False,
            initial_stop_message='stopped out, initial stop',
            stop_message='stopped out',
            
            start_trailing_at_fix=False,
            start_trailing_base=False,
            start_trailing_ofset=None,
            start_trailing_percentage=None,
            
            move_trail_timedelta=None,
            trailing_message='stopped out while trailing',
            
            min_tick = None,            
            ):
        ###
        ###
        (self.fix_stop, self.stop_base, self.stop_ofset, self.stop_percentage, 
         self.initial_safety_stop_value, self.start_trailing_at_fix, 
         self.start_trailing_base, self.start_trailing_ofset, 
         self.start_trailing_percentage, self.move_trail_timedelta,
         self.min_tick
         ) = (
         fix_stop, stop_base, stop_ofset, stop_percentage, 
         initial_safety_stop_value, start_trailing_at_fix, start_trailing_base,
         start_trailing_ofset, start_trailing_percentage, move_trail_timedelta,
         min_tick)
        self.trail_trigger = 0
        
    def arm(self, request, the_trader):
        parent_order_market, parent_order_id = request.single_entry_order_tracker
        trail_id = '#'.join([request.id_, 'trailing_stop'])
        action = 'close'
        parent = parent_order_id
        size = ('parent', 100) # 100% of parent order size
        contract = start = until = ''
        if self.fix_stop:
            stop_stop = ('number', self.fix_stop)
            stop_message = 'stopped out fix @ {}'.format(self.fix_stop)
        if self.stop_ofset:
            stop_stop = ('ofset', 
                         self.stop_base, self.stop_ofset, self.min_tick)
            stop_message = 'stopped out ofset @ {}'.format(self.stop_ofset)
        if self.stop_percentage:
            stop_stop = ('percentage', 
                         self.stop_base, self.stop_percentage, self.min_tick)
            stop_message = ('stopped out ofset @ {}%'.
                              format(self.stop_percentage))
        trail_order = Order(
            id=trail_id,
            action=action,
            size=size,
            contract=contract,
            parent_order_id=parent,
            start=start,
            until=until,
            type='stop',
            stop=stop_stop,
            message=stop_message,
        )
        ###
        request.single_trailing_order_tracker = (
            parent_order_market, trail_id,
        )
        request.order_trackers['single_trailing'] = (parent_order_market, trail_id)
        orders = {
            request.single_trailing_order_tracker: trail_order,
        }
        managers = [self.check_if_parent_is_filled(request, the_trader)]
        return orders, managers
    
    def check_if_parent_is_filled(self, request, the_trader):
        market_name, order_id = request.single_entry_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()
        def trail_manager_1(at_time):
            enter_info = market.status_report(order_id, at_time)
            if enter_info.filled is True:
                self.entered_trail = at_time
                next_manager = self.check_if_trail_is_triggered(
                    request, 
                    the_trader,
                )
            elif enter_info.stopped:
                next_manager = done
            else:
                next_manager = trail_manager_1
            return next_manager
        return trail_manager_1
    
    def check_if_trail_is_triggered(self, request, the_trader):      
        parent_name, parent_order_id = request.single_entry_order_tracker      
        market_name, trail_id = request.single_trailing_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()  
        def trail_manager_2(at_time):
            trail_order_status = market.status_report(trail_id, at_time)
            if trail_order_status.stopped:
                next_manager = done
            else:
                parent_order_status = market.status_report(
                                                parent_order_id, at_time)
                new_trail_trigger = find_trail_trigger(
                    parent_order_status,
                    self.start_trailing_at_fix,
                    self.start_trailing_base,
                    self.start_trailing_ofset,
                    self.start_trailing_percentage,
                )
                if not new_trail_trigger == self.trail_trigger:
                    print('Trail triggerd @ {}'.format(new_trail_trigger))
                    self.trail_trigger = new_trail_trigger
                action = trail_order_status.order.action
                contract = trail_order_status.order.contract
                if action == "sell":
                    triggered = market.data_of_contracts.max_since(
                        contract, self.entered_trail) > (
                            self.trail_trigger) #- trail_trigger.__class__(0.5))
                                           # for better results when simulating
                                           # trying to simulate index results
                else:
                    triggered = market.data_of_contracts.min_since(
                        contract, self.entered_trail) < (
                            self.trail_trigger) #+ trail_trigger.__class__(0.5))
                self.entered_trail = at_time
                if triggered:
                    print('trailing started: {}'.format(at_time))
                    self.entered_trail = at_time
                    next_manager = self.follow_and_move_trail(
                        request, 
                        the_trader,
                    )
                else:
                    next_manager = trail_manager_2
            return next_manager
        return trail_manager_2
                    
    def follow_and_move_trail(self, request, the_trader):      
        parent_name, parent_order_id = request.single_entry_order_tracker
        market_name, trail_id = request.single_trailing_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()  
        def trail_manager_3(at_time):
            trail_order_status = market.status_report(trail_id, at_time)
            parent_order_status = market.status_report(parent_order_id, at_time)
            if trail_order_status.stopped:
                next_manager = done
            #elif at_time - self.entered_trail >= self.move_trail_timedelta:
            elif at_time - self.move_trail_timedelta > r_dt.round_down(
                                 self.entered_trail, self.move_trail_timedelta):
                avg_in = parent_order_status.average_price
                action = trail_order_status.order.action
                contract = trail_order_status.order.contract
                if action == "sell":
                    new_stop = market.data_of_contracts.min_since(
                    contract, self.entered_trail) - 0.5 ### !!!!!! test !!!!!!!!!!!!
                else:
                    new_stop = market.data_of_contracts.max_since(
                    contract, self.entered_trail) + 0.5 ### !!!!!! test !!!!!!!!!!!!
                
                new_stop = avg_in.__class__(new_stop)
                market.change_existing_order(
                    trail_id,
                    'stop',
                    new_stop,
                    at_time,
                    self.min_tick
                )
                print('trail move to: {}'.format(new_stop))
                self.entered_trail = at_time
                next_manager = trail_manager_3
            else:
                next_manager = trail_manager_3
            return next_manager
        return trail_manager_3
    
class SingleManagedStop(ExitStrategy):
    
    name = "single_managed_stop"
    provides_locals = [
        'single_managed_order_tracker',
    ]
    required_locals = [
        'single_entry_order_tracker',
    ]
    
    def __init__(self,
            initial_safety_stop_ofset,
            initial_safety_stop_base='avg_parent_in',
            initial_stop_message='stopped out, initial stop',
            signal='move_stop_managed_order',
            stop_message='stopped out, moved',            
            min_tick = None,            
            ):
        ###
        ###
        (self.initital_safety_stop_base,
         self.initial_safety_stop_ofset, self.initial_stop_message,
         self.move_signal, self.stop_message, self.min_tick,
         self.min_tick
         ) = (initial_safety_stop_base,
              initial_safety_stop_ofset, initial_stop_message,
              signal, stop_message, min_tick,)
        self.trail_trigger = 0
        
    def arm(self, request, the_trader):
        parent_order_market, parent_order_id = request.single_entry_order_tracker
        managed_stop_id = '#'.join([request.id_, 'managed_stop'])
        action = 'close'
        parent = parent_order_id
        size = ('parent', 100) # 100% of parent order size
        contract = start = until = ''
        if self.stop_ofset:
            stop_stop = ('ofset', 
                         self.initital_safety_stop_base,
                         self.stop_ofset, self.min_tick)
            stop_message = self.initial_stop_message
        trail_order = Order(
            id=trail_id,
            action=action,
            size=size,
            contract=contract,
            parent_order_id=parent,
            start=start,
            until=until,
            type='stop',
            stop=stop_stop,
            message=stop_message,
        )
        ###
        request.single_managed_stop_tracker = (
            parent_order_market, managed_stop_id,
        )
        request.order_trackers['single_managed_stop'] = (parent_order_market, 
                                                         managed_stop_id)
        orders = {
            request.single_managed_stop_tracker: managed_stop_id,
        }
        managers = [self.check_if_parent_is_filled(request, the_trader)]
        return orders, managers
    
    def check_if_parent_is_filled(self, request, the_trader):
        market_name, order_id = request.single_entry_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()
        def manager_1(at_time):
            enter_info = market.status_report(order_id, at_time)
            if enter_info.filled is True:
                self.entered_managed_stop = at_time
                next_manager = self.check_if_managed_stop_is_triggered(
                    request, 
                    the_trader,
                )
            elif enter_info.stopped:
                next_manager = done
            else:
                next_manager = manager_1
            return next_manager
        return manager_1
    
    def check_if_managed_stop_is_signalled(self, request, the_trader):      
        parent_name, parent_order_id = request.single_entry_order_tracker      
        market_name, ms_id = request.single_managed_stop_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()  
        def manager_2(at_time):
            ms_status = market.status_report(ms_id, at_time)
            next_manager = manager_2
            if trail_order_status.stopped:
                next_manager = done
            elif ms_status.startswith(self.move_signal):
                foo, new_stop =(self.move_signal.split(': ')[1])
                new_stop = ms_status.average_price.__class__(new_stop)
                print('Stop moved to {}'.format(new_stop))
                market.change_existing_order(
                    ms_id,
                    'stop',
                    new_stop,
                    at_time,
                    self.min_tick
                )
            return next_manager
        return manager_2
    
class CloseEOD(ExitStrategy):
    
    name = 'close_eod'
    provides_locals = [
        'eod_order_tracker',
    ]
    required_locals = []
    
    def __init__(self,
            tracked_order_id,
            closing_time=None,
            eod_message='eod closed position @ {}'
            ):
        self.tracked_order_id, self.closing_time, self.message = (
                            tracked_order_id, closing_time, eod_message)
    
    def arm(self, request, the_trader):
        tracked_order_market, order_id = request.order_trackers[self.tracked_order_id]
        eod_id = '#'.join([request.id_, 'eod'])
        action = 'close'
        parent = order_id
        size = ('parent', 100) # 100% of parent order size
        contract = until = ''
        date = the_trader.last_official_timestamp.date()
        if not self.closing_time:
            self.closing_time = r_dt.timetodatetime(
                r_dt.time_operation_timedelta(
                    the_trader.end_of_day, '-', the_trader.last_out),
                date)
        eod_message = 'stopped out eod {}'.format(self.closing_time)
        eod_order = Order(
            id=eod_id,
            action=action,
            size=size,
            contract=contract,
            parent_order_id=parent,
            start=('gat', self.closing_time),
            until=until,
            type='market',
            message=eod_message,
        )
        ###
        request.eod_order_tracker = (tracked_order_market, eod_id)
        request.order_trackers['eod'] = (tracked_order_market, eod_id)
        orders = {
            request.eod_order_tracker: eod_order,
        }
        managers = [self.watch_eod_order(request, the_trader)]
        return orders, managers
    
    def watch_eod_order(self, request, the_trader):       
        market_name, order_id = request.eod_order_tracker
        market = the_trader.markets[market_name]
        done = self.strategy_finished()
        def exit_manager_1(at_time):
            eod_info = market.status_report(order_id, at_time)
            if eod_info.stopped is True:
                next_manager = done
        return exit_manager_1

def find_trail_trigger(order_status, fix, base, ofset, percentage):
    if fix:
        return fix
    if base == 'avg_parent_in':
        base = order_status.average_price
        if order_status.order.action == 'sell':
            if ofset:
                return base - base.__class__(ofset)
            else:
                return (base * (1-percentage/100))
        else:
            if ofset:
                return base + base.__class__(ofset)
            else:
                return (base * (1+percentage/100))
    raise error("can not find trail trigge with these settings")