#!/usr/bin/env python3
#
#  Copyright (c) 2012, 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from operator import itemgetter
from collections import namedtuple
from datetime import timedelta

#import mypy
#import position_manager2
import roc_output as r_out
import roc_string as r_string
import roc_datetime as r_dt
import evaluation_tests

#from tradingsystem import TradingSystem
from trader import TraderRequest, Trader #TraderStrategy
#from theotrader import TheoreticalSinglePositionTrader as TheoreticalTrader
import strategies
from multiinterval import MultiIntervalFramework, FVITAOriginal#, E_TESTS
import bar_list_studies as bls



########################################################
## stopped working becaus a lot of things changed
#class PermsTradingSystem_0(TradingSystem):
    #'''Simple Stop Management, In At Wavecount
       
       #supported traders: TheoreticalSinglePositionTrader
    #'''
    
    #def __init__(self, 
            #contract_name='', 
            #wavecount_in=2, 
            #reverse=False,
            #market=None,
            #**kw_d
        #):
        #self.contract_name = contract_name
        #if isinstance(wavecount_in, list):
            #self.wavecount_in = wavecount_in
        #else:
            #self.wavecount_in = [wavecount_in]
        #self.up_swing_comp = []
        #self.down_swing_comp = []
        #self.reverse = reverse
        #self.last_send_report_info = None
        #self.market_for_orders = market
        #super().__init__(**kw_d)
        
    #def check_setup(self):
        ## local checks
        #super().check_setup()
    
        
    #def register_perm_lines_event(self, perm_lines):
        #'''Register new perm lines and returns TraderRequests.'''
        ####
        #up_swing_components = self.up_swing_comp
        #down_swing_components = self.down_swing_comp
        ####
        #requests = self.register_perm_lines(
            #perm_lines,
            #up_swing_components,
            #down_swing_components,
        #)
        #for request in requests: 
            #self.export_object(request)
        #return requests
        
    #def register_virtual_perm_lines_event(self, perm_lines):   
        #'''Register virtual new perm lines and returns TraderRequests.'''
        ####
        #up_swing_components = self.up_swing_comp.copy()
        #down_swing_components = self.down_swing_comp.copy()
        ####
        #requests = self.register_perm_lines(
            #perm_lines,
            #up_swing_components,
            #down_swing_components,
        #)
        #for request in requests:
            #request.virtual = True
        #return requests
            
        
    #def register_perm_lines(self,
                #perm_lines,
                #up_swing_comp,
                #down_swing_comp,
        #):
        #perm_lines = sorted(perm_lines, key=itemgetter(1))
        #requests = []
        #for perm_line in perm_lines:
            #if ((len(down_swing_comp) == 0           and
                 #perm_line[0] == "down"              and
                 #not perm_line[1] == 0)
                #or
                #(len(up_swing_comp) == 0             and
                 #perm_line[0] == "up"                and
                 #not perm_line[1] == 0)
            #):
                #continue
            #request = self.register_perm_line(
                #perm_line,
                #up_swing_comp,
                #down_swing_comp
            #)
            #if request: requests.append(request)
        #return requests
            
    #def register_perm_line(self, perm_line, up_swing_comp, down_swing_comp):
        ####
        #(direction, wavecount, triad_top_time, triad_top_value,
         #triad_exit_time, triad_exit_value) = perm_line
        ####
        #swing_comp = up_swing_comp if direction == 'up' else down_swing_comp
        #del swing_comp[wavecount:]
        #swing_comp.append(triad_top_value)
        #request = None
        #if (wavecount in self.wavecount_in):
            #stop = swing_comp[0]
            #trade_direction = 'long' if direction == 'up' else 'short'
            #if wavecount % 2 == 1:
                #trade_direction = 'long' if trade_direction == 'short' else 'short'
                #stop = swing_comp[-1]
            #else:
                #stop = swing_comp[0]
            #if self.reverse:                
                #trade_direction = 'long' if trade_direction == 'short' else 'short'
                #if trade_direction == 'long':
                    #stop = 0
                #else:
                    #stop = 2 * swing_comp[0]
            #request = TraderRequest(
                            #id_=self.next_request_id(),
                            #contracts=self.contract_name,
                            #direction=trade_direction, 
                            #size=1,
                            #enter_strategy=TraderStrategy(
                                #name='now',
                                #mss='enter on wavercount {}'.format(wavecount),
                            #),
                            #exit_strategies=[
                                #TraderStrategy(
                                    #name='from trader init'
                                #),
                            #],
                            #markets=self.market_for_orders,
            #)
        #return request
class FixitTestTrader(Trader):
    
    def __init__(self, direction0, min_tick=None):
        self.id_count = 0
        self.direction = direction0
        self.min_tick = min_tick
        super().__init__()
        
    def next_id(self):
        self.id_count += 1
        return 'PBTT_{}'.format(self.id_count)
    
    def new_fixit_time(self, at_time):
        if self.active_requests:
            return 
    
    def new_fixitbar(self, new_bar, at_time):
        if self.active_requests:
            return
        request = self.create_requests(self.direction, at_time)
        if request:
            request.id_ = self.next_id()
            self.add_requests([request], request.created)
            self.next_action = None
        
    def create_requests(self, direction, at_time):
        ###
        if self.last_in: #checking for daytrader settings part I
            date = self.last_official_timestamp.date()
            last_in = r_dt.timetodatetime(
                r_dt.time_operation_timedelta(
                    self.end_of_day, '-', self.last_in),
                date)
            until = ('gtd', last_in)
            if last_in <= self.last_official_timestamp:
                return None
        else:
            until = ('gtc',)
        size = 1
        enter_strategy = strategies.SingleDefault(
            start=('now',),
            valid_until=until, 
            limit_price=0,
            message='new_try',
        )
        exit_strategy = [
            strategies.SingleStopProfitTaker(
                stop_base='avg_parent_in',
                #stop_percentage=0.25,
                stop_ofset=30,
                initial_stop_message='stopped out',
                profit_base='avg_parent_in',
                #profit_percentage=0.045,
                profit_ofset=5,
                profit_message='took profit',
                min_tick=self.min_tick
            )
            #strategies.SingleTrailingStop(
                #stop_base='avg_parent_in',
                #stop_percentage=0.17,
                #initial_stop_message='stopped out',
                #start_trailing_base='avg_parent_in',
                #start_trailing_percentage=0.035,
                #trailing_message='took trail profit',
                #move_trail_timedelta=timedelta(seconds=30),
                #min_tick=self.min_tick
            #)
        ]
        if self.last_out: # checking daytrader settings part II
            last_out = r_dt.timetodatetime(
                r_dt.time_operation_timedelta(
                    self.end_of_day, '-', self.last_out),
                date)
            l_o = strategies.CloseEOD(
                tracked_order_id='single_enter',
                closing_time=last_out, 
            )
            exit_strategy.append(l_o)
        created=at_time
        ###
        request = TraderRequest(
                        'not set yet', #id_,
                        direction=direction,
                        size=size,
                        enter_strategy=enter_strategy,
                        exit_strategies=exit_strategy,
                        created=created,
        )
        return request
    
class FastSwing():
    
    def __init__(self, avg_count):
        self.avg_count = avg_count * 2
        self.values = []
        
    def new_bar(self, a_bar):
        self.values.append(a_bar.high)
        self.values.append(a_bar.low)
        if len(self.values) > self.avg_count:
            self.values.pop(0)
            self.values.pop(0)
        if len(self.values) < self.avg_count:
            return None
        return sum(self.values) / len(self.values)
        

class FastSwingTestTrader(Trader):
    
    def __init__(self, avg_count, min_tick=None):
        self.id_count = 0
        self.fast_swing = FastSwing(avg_count)
        self.min_tick = min_tick
        self.avg_list = []
        self.curr_direction = None
        self.min_d = 2.5
        super().__init__()
        
        
    def next_id(self):
        self.id_count += 1
        return 'PBTT_{}'.format(self.id_count)
    
    def new_fixit_time(self, at_time):
        if self.active_requests:
            return 
    
    def new_fixitbar(self, new_bar, at_time):
        self.avg_list.append(self.fast_swing.new_bar(new_bar))
        if self.avg_list[-1] is None:
            self.avg_list.pop()
        if len(self.avg_list) > 10:
            self.avg_list.pop(0)
        if len(self.avg_list)< 3:
            return
        delta = self.avg_list[-1] - self.avg_list[-2] 
        if abs(delta) < self.min_d:
            return
        if delta == 0:
            return
        if self.curr_direction is None:
            if delta > 0:
                direction = 'long'
            elif delta < 0:
                direction = 'short'
        elif self.curr_direction == 'long':
            if delta < 0:
                direction = 'short'
            else:
                direction = 'long'
        else:
            if delta > 0:
                direction = 'long'
            else:
                direction = 'short'
        if not direction == self.curr_direction:
            if self.curr_direction:
                print('closing')
                self.set_signal_in_active_request('all', 'reverse', at_time)
                #request = self.create_requests(direction, at_time)
                #request.id_ = self.next_id()
                #self.add_requests([request], request.created)
            requesti = self.create_requests(direction, at_time)
            if requesti:
                requesti.id_ = self.next_id()
                self.add_requests([requesti], requesti.created)
                self.curr_direction = direction
        
    def create_requests(self, direction, at_time):
        ###
        if self.last_in: #checking for daytrader settings part I
            date = self.last_official_timestamp.date()
            last_in = r_dt.timetodatetime(
                r_dt.time_operation_timedelta(
                    self.end_of_day, '-', self.last_in),
                date)
            until = ('gtd', last_in)
            if last_in <= self.last_official_timestamp:
                return None
        else:
            until = ('gtc',)
        size = 1
        enter_strategy = strategies.SingleDefault(
            start=('now',),
            valid_until=until, 
            limit_price=0,
            message='new_try',
        )
        exit_strategy = [
            strategies.SingleStopProfitTaker(
                stop_base='avg_parent_in',
                #stop_percentage=0.25,
                stop_ofset=10,
                initial_stop_message='stopped out',
                profit_base='avg_parent_in',
                #profit_percentage=0.045,
                profit_ofset=500,
                profit_message='took profit',
                min_tick=self.min_tick
            )
            #strategies.SingleTrailingStop(
                #stop_base='avg_parent_in',
                #stop_percentage=0.17,
                #initial_stop_message='stopped out',
                #start_trailing_base='avg_parent_in',
                #start_trailing_percentage=0.035,
                #trailing_message='took trail profit',
                #move_trail_timedelta=timedelta(seconds=30),
                #min_tick=self.min_tick
            #)
        ]
        #exit_strategy = [
            #strategies.CloseOnSignal(
                #signal='reverse',
                #)
            
                ##stop_base='avg_parent_in',
                ###stop_percentage=0.25,
                ##stop_ofset=25,
                ##initial_stop_message='stopped out',
                ##profit_base='avg_parent_in',
                ###profit_percentage=0.045,
                ##profit_ofset=25,
                ##profit_message='took profit',
                ##min_tick=self.min_tick
            ##)
            ##strategies.SingleTrailingStop(
                ##stop_base='avg_parent_in',
                ##stop_percentage=0.17,
                ##initial_stop_message='stopped out',
                ##start_trailing_base='avg_parent_in',
                ##start_trailing_percentage=0.035,
                ##trailing_message='took trail profit',
                ##move_trail_timedelta=timedelta(seconds=30),
                ##min_tick=self.min_tick
            ##)
        #]
        exsi = strategies.CloseOnSignal(
                signal='reverse',
                )
        exit_strategy.append(exsi)
        if self.last_out: # checking daytrader settings part II
            last_out = r_dt.timetodatetime(
                r_dt.time_operation_timedelta(
                    self.end_of_day, '-', self.last_out),
                date)
            l_o = strategies.CloseEOD(
                tracked_order_id='single_enter',
                closing_time=last_out, 
            )
            exit_strategy.append(l_o)
        created=at_time
        ###
        request = TraderRequest(
                        'not set yet', #id_,
                        direction=direction,
                        size=size,
                        enter_strategy=enter_strategy,
                        exit_strategies=exit_strategy,
                        created=created,
        )
        return request
    
class MultiIntervalTestTrader(Trader):
    
    def __init__(self, *arg_l, min_tick=None, **kw_d):
        self.id_count = 0
        self.mitt = MultiIntervalFramework(*arg_l, **kw_d)
            #multi interval test trader
        interval = self.mitt.intervals[0]
        #interval.add_test('stochastic_moves', 'STOCHO_009_003_020')
        self.min_tick = min_tick
        super().__init__()
        
    def next_id(self):
        self.id_count += 1
        return 'FVITA_{}'.format(self.id_count)
        
    def new_fixitbar(self, bar, at_time):
        print('<<< {} >>>'.format(at_time))
        self.mitt.new_bar(bar)
        #self.mitt.print_studie_results(bls.Basics, 'BASICS 3')
        #self.mitt.print_studie_results(bls.MIO, 'MIO_005')
        #self.mitt.print_studie_results(bls.MIO, 'MIO_010')
        #self.mitt.print_studie_results(bls.ROC, 'ROCO_005')
        #self.mitt.print_studie_results(bls.ROC, 'ROCO_010')
        #self.mitt.print_studie_results(bls.RSI, 'RSIO_003_020')
        #self.mitt.print_studie_results(bls.RSI, 'RSIO_009_020')
        #self.mitt.print_studie_results(bls.RSI, 'RSIO_014_020')
        #self.mitt.print_studie_results(bls.STOCH, 'STOCHO_009_003_020')
        #self.mitt.print_studie_results(bls.SMA, 'SMATI_014')
        #self.mitt.print_studie_results(bls.LWMA, 'LWMATI_014')
        #self.mitt.print_studie_results(bls.ESMA, 'ESMATI_014')
        #self.mitt.print_studie_results(bls.MACD, 'MACDI_014_026_009')
        print()
        #self.mitt.print_list_lengths()
        #self.mitt.print_studies_and_tests(maximum=10)
        #r = self.mitt.get_evaluations_by_name(('bars', 120))
        #print('r:', r)
        #if r:
            #try:
                #trend = r['SMATI_014'][Evaluation.STANDARD_EVALUATION].trend
            #except KeyError:
                #trend = None
        #else:
            #trend = None
        #self.mitt.evaluate_studies(trend=trend)
        #print('\nEvaluations:')
        #self.mitt.print_studie_evaluations()
        #interm = ''
        #t = self.mitt.result_for(('bars', 60), 
                                  #'STOCH_AB_MOVES_FOR_STOCHO_009_003_020',
                                  #evaluation_tests.StochMoves.moved_from_A_GA_to_B_GB)
        #if t:
            #print('{} :A ---> B'.format(interm))
        #t = self.mitt.result_for(('bars', 60), 
                                  #'STOCH_AB_MOVES_FOR_STOCHO_009_003_020',
                                  #evaluation_tests.StochMoves.moved_from_B_GB_to_A_GA)
        #if t:
            #print('{} :B ---> A'.format(interm))
class FVITAOriginalTestTrader(Trader):
    
    def __init__(self, *arg_l, min_tick=None, **kw_d):
        self.id_count = 0
        self.fvita = FVITAOriginal(*arg_l)
        self.min_tick = min_tick
        super().__init__()
        
    def next_id(self):
        self.id_count += 1
        return 'FVITA_{}'.format(self.id_count)
        
    def new_fixitbar(self, bar, at_time):
        fvita = self.fvita
        fvita.new_bar(bar)
        #fvita.evaluate_studies()
        #e =self.fvita.get_evaluations_by_index(0)['BASICS']['STANDARD EVALUATION']
        #print('F ' if self.fvita.at_period_end[1] else 'I ', end='')
        #print('{:4} {:4} {:4} {:4} {:4} {:4}'.format(
            #e.strict_up, e.loose_up, e.r_up,
            #e.strict_down, e.loose_down, e.r_down,
        #)) 
        #if self.fvita.at_period_end[('bars', 60)]:
            #print('{:4} {:4} {:4} {:4} {:4} {:4} {:8} {:8}'.format(
                #e.strict_up, e.loose_up, e.r_up,
                #e.strict_down, e.loose_down, e.r_down,
                #e.resistance, e.support
            #))
        
class PermBasicTestTraderDev(Trader):
    
    def __init__(self, min_tick=None):
        self.id_count = 0
        self.min_tick = min_tick
        super().__init__()
        
    def next_id(self):
        self.id_count += 1
        return 'PBTT_{}'.format(self.id_count)
    
    def new_perms(self, perms, at_time):
        perms = sorted(perms, key=itemgetter(1))
        if self.active_requests:
            #print('@@@@@@@@@@')
            #curr_value = self.current_value_of_request(self.curr_id, at_time)
            #if curr_value > 2 or curr_value < -17:
                #self.set_signal_in_active_request('all', 'close_on_signal', at_time)
            #print('@@@@@@@@@@')                  
            #self.set_signal_in_active_request('all', 'close_on_signal', at_time)
            return 'in trade'
        for perm in perms:
            request = None
            perm_count = perm[1]
            if perm_count and perm_count % 2 == 0:
            #if perm_count and perm_count == 4:
                request = self.create_requests(perm, at_time)#, reverse=True)
            #else:
                #request = self.create_requests(perm, at_time, reverse=True)
            if request:
                request.id_ = self.next_id()
                self.add_requests([request], request.created)
                self.curr_id = request.id_
                break
                #return request.id_
        return None
                
    def virtual_new_perms(self, perms, at_time):
        perms = sorted(perms, key=itemgetter(1))
        if self.active_requests: 
            #print('@@@@@@@@@@')
            #curr_value = self.current_value_of_request(self.curr_id, at_time)
            #if curr_value > 2 or curr_value < -17:
                #self.set_signal_in_active_request('all', 'close_on_signal', at_time)
            #print('@@@@@@@@@@')             
            #self.set_signal_in_active_request('all', 'close_on_signal', at_time)
            return
        for perm in perms:
            perm_count = perm[1]
            if perm_count and perm_count % 2 == 0:
                request = self.create_requests(perm, at_time)
                if request:
                    request.id_ = '********** TRADE AHEAD ***********'
                    print(request)
                    break
        #perms = sorted(perms, key=itemgetter(1))
        #if self.active_requests:
            #return
        #for perm in perms:
            #perm_count = perm[1]
            #if perm_count and perm_count % 2 == 0:
                #request = self.create_requests(perm, at_time)
                #if request:
                    #request.id_ = self.next_id()
                    #self.add_requests([request], request.created)
                    #break
       
        
    def create_requests(self, perm, at_time, reverse=False):
        ###
        if self.last_in: #checking for daytrader settings part I
            date = self.last_official_timestamp.date()
            last_in = r_dt.timetodatetime(
                r_dt.time_operation_timedelta(
                    self.end_of_day, '-', self.last_in),
                date)
            until = ('gtd', last_in)
            if last_in <= self.last_official_timestamp:
                return None
        else:
            until = ('gtc',)
        (p_direction, p_count, 
         p_extreme_time, p_extreme_top, p_end_time, p_close) = perm
        #id_ = self.next_id()
        #print('new request: ', id_)
        direction = 'long' if p_direction == 'up' else 'short'
        if reverse:
            direction = 'long' if p_direction == 'down' else 'short'
        size = 1
        enter_strategy = strategies.SingleDefault(
            start=('now',),
            valid_until=until, 
            limit_price=0,
            message='perm count: {}'.format(perm[1]),
        )
        exit_strategy = [
            strategies.SingleStopProfitTaker(
                stop_base='avg_parent_in',
                stop_percentage=0.25, #dax 0.25 beter
                #stop_ofset=15.5, # dax, 16.5 beter dan 15.5
                #stop_percentage=0.32,
                #stop_ofset=10,
                initial_stop_message='stopped out',
                profit_base='avg_parent_in',
                profit_percentage=0.045, #dax
                #profit_ofset=4, #dax
                #profit_percentage=0.12,
                #profit_ofset=1,
                profit_message='took profit',
                min_tick=self.min_tick
            )
            #strategies.SingleTrailingStop(
                #stop_base='avg_parent_in',
                ##stop_ofset=16.5, # dax, beter 16.5
                #stop_percentage=0.25,
                #initial_stop_message='stopped out',
                #start_trailing_base='avg_parent_in',
                #start_trailing_percentage=0.045,
                ##start_trailing_ofset=6,
                #trailing_message='took trail profit',
                #move_trail_timedelta=timedelta(seconds=60),
                #min_tick=self.min_tick
            #)
        ]
        if self.last_out: # checking daytrader settings part II
            last_out = r_dt.timetodatetime(
                r_dt.time_operation_timedelta(
                    self.end_of_day, '-', self.last_out),
                date)
            max_trade_length = timedelta(seconds=60000)
            stop_trade_at = at_time + max_trade_length
            if last_out > stop_trade_at:
                last_out = stop_trade_at
            #print('[[[[[[[[[[[[[[[[{}]]]]]]]]]]]]]]]]'.format(last_out))
            l_o = strategies.CloseEOD(
                tracked_order_id='single_enter',
                closing_time=last_out, 
            )
            exit_strategy.append(l_o)
        exit_strategy.append(strategies.CloseOnSignal('single_enter'))
        created=at_time
        ###
        request = TraderRequest(
                        'not set yet', #id_,
                        direction=direction,
                        size=size,
                        enter_strategy=enter_strategy,
                        exit_strategies=exit_strategy,
                        created=created,
        )
        return request
        
        