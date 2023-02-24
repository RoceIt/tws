#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

from multiprocessing import Queue, Process, Manager
from queue import Empty

import tws
import TWSClient
from time import sleep

import mypy
from barData import ochlBar, ochl
from triads import Triad, TriadReducer#, ASCENDING, DESCENDING

IN_TRADE = '$IN_TRADE'
TRADE_DIRECTION = '$TRADE_DIRECTION'

SEND_ORDER = '$SEND_ORDER'
REVERSE_ORDER = '$REVERSE_ORDER'
UNSET_REVERSE_ORDER = '$UNSET_REVERSE_ORDER'

def get_settings():
    '''Setting, asking the settings for the program'''
    s = {}
    #s['server_ip'] = 'localhost' #'10.1.1.102'
    #s['server_port'] = 10911
    #s['server_client'] = 31
    #s['barSize'] = 180
    #s['contract'] = 'ESTX-50_FUT'
    #s['min_price_var'] = 1
    #s['nr_of_contracts'] = 1
    #s['initial_profit_gap'] = 10
    #s['min_stop'] = 12
    #s['max_stop'] = 15     #0.40
    #s['first_p_level'] = 5  #0.30
    #s['first_p_perc'] = 50
    #s['rev_gain_objective'] = 1
    
    s['server_ip'] = '10.1.1.102' 
    s['server_port'] = 10911
    s['server_client'] = 33
    s['barSize'] = 180  #240
    s['contract'] = 'euro-dollar'
    s['min_price_var'] = 0.00005
    s['nr_of_contracts'] = 100000
    s['initial_profit_gap'] = 0.005
    s['min_stop'] = 0.0006  # 0.0007
    s['max_stop'] = 0.0008  # 0.0008
    s['first_p_level'] = 0.0005  #0.0006
    s['first_p_perc'] = 60
    s['rev_gain_objective'] = 0.0002
    
    return s
    
    
class DataProcessor():
    '''gets data from data_in queue put it into bar_size bars
    and search for triads. If a triad is found it decides if it
    should be send to the trader'''
    
    def __init__(self,settings, data_feed, trader):
        self.processor = Process(target=processor,
                                 args=(settings, data_feed, trader))
        self.processor.daemon = True
        self.processor.start()
        
class Trader():
    
    def __init__(self, settings, data_feed):
        
        s = settings
        twss = TWSClient.TWSconnection(s['server_ip'], s['server_port'],
                                       client_id=s['server_client'])   
        self.trader_in = Queue()
        self.manager = Manager()
        self.status = self.manager.dict()
        self.trader = Process(target=trader,
                              args=(settings, data_feed,
                                    self.trader_in, self.status,
                                    twss))
        self.trader.daemon = True
        self.trader.start()
        
    @property
    def in_trade(self):
        print('in trader.in_trade')
        return self.status[IN_TRADE]
    
    @property
    def direction(self):
        return self.status[TRADE_DIRECTION]
    
    def place_order(self, triad):
        print('in place_order')
        self.trader_in.put((SEND_ORDER, triad))
        
    def reverse_order(self, triad):
        print('in reverse order')
        self.trader_in.put((REVERSE_ORDER, triad))        
    def unset_reversal(self, triad):
        print('in unset reversal')
        self.trader_in.put((UNSET_REVERSE_ORDER, triad))
        
        
def processor(settings, data_feed, trader):
    assert isinstance(data_feed, type(Queue()))
    bars = ochl('s', settings['barSize'])
    triad_list = TriadReducer(settings['barSize'])
    while 1:
        last = data_feed.get()
        foo, new_bar = bars.insert(last.time, last.open, last.close,
                                   last.high, last.low)
        if new_bar:
            last_bar = bars.last_finished_bar()
            if last_bar:
                new_triad = triad_list.insert(last_bar)
                if new_triad:
                    print(new_triad)
                    process_triad(new_triad, trader)
                    
def process_triad(triad, trader):
    if not trader.in_trade:
        trader.place_order(triad)
    elif triad.type_ == trader.direction:
        trader.unset_reversal(triad)
    else:
        trader.reverse_order(triad)
        
                    
def trader(settings, data_feed, comm_in, status, twss):
    assert isinstance(data_feed, type(Queue()))
    status[IN_TRADE] = False
    status[TRADE_DIRECTION] = None
    enter_trade_id = stop_id = profit_taker_id = None
    rev_enter_id = rev_profit_id = rev_stop_id = None
    last_quote = None
    triad = None
    trade_values = dict(entry_price=None,
                        stop=None, profit=None, 
                        r_stop=None, r_profit=None,
                        adjusted=None, reverse=False)
    while 1:
        try:
            new_quote = data_feed.get_nowait()
            last_quote = new_quote
        except Empty:
            new_quote = None
        try:
            new_instruction = comm_in.get_nowait()
            instruction = new_instruction[0]
            new_triad = new_instruction[1]
            triad = new_triad
            print('TTT : ', instruction)
            print(triad)
        except Empty:
            instruction = ('pass', None)
        if (instruction == SEND_ORDER
            or
            (trade_values['reverse'] and
             not enter_trade_id)):
            trade_values['reverse'] = False
            if enter_trade_id:
                enter_trade_id = remove_existing_trade(twss, enter_trade_id)
            if not enter_trade_id:
                trade_values['rev_printed'] = False
                e, p, s = send_order(twss, settings, trade_values,
                                     triad, last_quote)
                enter_trade_id, profit_taker_id, stop_id = e, p , s
                print('enter: {} | profit: {} | loss: {}'.
                      format(enter_trade_id, profit_taker_id, stop_id))
        elif instruction == UNSET_REVERSE_ORDER:
            trade_values['reverse'] = False
            trade_values['rev_printed'] = False
            if not enter_trade_id:
                print('asked to unset a reverse order but there\'s no'
                      ' reverse order, changing request to: \n'
                      '     SEND ORDER')              
                e, p, s = send_order(twss, settings, trade_values,
                                     triad, last_quote)
                enter_trade_id, profit_taker_id, stop_id = e, p , s
                print('enter: {} | profit: {} | loss: {}'.
                      format(enter_trade_id, profit_taker_id, stop_id))
            elif not rev_enter_id:
                print('asked to unset a reverse order but there\'s no'
                      ' reverse order, original trade is continued')
            else:
                e, p, s, re, rp, rs = unset_reversal(twss, settings, 
                                                     trade_values,
                                                     triad, last_quote,
                                                     enter_trade_id,
                                                     profit_taker_id,
                                                     stop_id,
                                                     rev_enter_id,
                                                     rev_profit_id,
                                                     rev_stop_id)
                enter_trade_id,  profit_taker_id, stop_id = e, p , s
                rev_enter_id, rev_profit_id, rev_stop_id = re, rp, rs
                print('removed reverse setup\n'
                      'enter: {} | profit: {} | loss: {}\n'.
                      format(enter_trade_id, profit_taker_id, stop_id))
        elif (instruction ==  REVERSE_ORDER
              or
              trade_values['reverse']):
            if not enter_trade_id:
                print('asked to set a reverse order but there\'s no'
                      ' active order, changing request to: \n'
                      '     SEND ORDER')              
                e, p, s = send_order(twss, settings, trade_values,
                                     triad, last_quote)
                enter_trade_id, profit_taker_id, stop_id = e, p , s
                print('enter: {} | profit: {} | loss: {}'.
                      format(enter_trade_id, profit_taker_id, stop_id))
            else:
                e, p, s, re, rp, rs =reverse_order(twss, settings, trade_values,
                                                   triad, last_quote,
                                                   enter_trade_id,
                                                   profit_taker_id,
                                                   stop_id)
                enter_trade_id,  profit_taker_id, stop_id = e, p , s
                rev_enter_id, rev_profit_id, rev_stop_id = re, rp, rs
                if not trade_values['rev_printed']:
                    print('reverse setup\n'
                          'enter: {} | profit: {} | loss: {}\n'
                          'reverse enter: {} | reverse profit {} | reverse {}'.
                          format(enter_trade_id, profit_taker_id, stop_id,
                                 rev_enter_id, rev_profit_id, rev_stop_id))
        elif not enter_trade_id :
            if new_quote:
                print('T: ',last_quote, ': ', instruction)
                if twss.err_list:
                    mypy.print_list(twss.err_list, 'ERROR LIST')
            continue
        if (enter_trade_id in twss.order_status.keys() and
            profit_taker_id in twss.order_status.keys() and
            stop_id in twss.order_status.keys()):
            st, e, p, s, re, rp, rs  = follow_up_trades(twss, trade_values,
                                                        enter_trade_id,
                                                        profit_taker_id,
                                                        stop_id,
                                                        rev_enter_id,
                                                        rev_profit_id,
                                                        rev_stop_id)
            status[IN_TRADE] = st
            if st:
                if trade_values['profit'] > trade_values['entry_price']:
                    status[TRADE_DIRECTION] = ASCENDING
                else:
                    status[TRADE_DIRECTION] = DESCENDING
            else:
                status[TRADE_DIRECTION] = None                
            enter_trade_id, profit_taker_id, stop_id = e, p, s
            rev_enter_id, rev_profit_id, rev_stop_id = re, rp, rs
            if status[IN_TRADE] and not rev_enter_id :
                adjust_stops(twss, settings, trade_values,
                             enter_trade_id, profit_taker_id, stop_id,
                             new_quote)                
        if new_quote:
            print('T: ',last_quote, ': ', instruction)
            #mypy.print_list(twss.err_list[-5:], 'ERROR LIST')
        
def send_order(twss, settings, trade_values, triad, last_quote):
    #send the order and don't forget to adjust the stop once the order is filled!!
    print('in send order') 
    contract = tws.contract_data(settings['contract'])
    nr_of_contracts = settings['nr_of_contracts']
    direction = 'BULL' if triad.type_ == ASCENDING else 'BEAR'
    df = 1 if triad.type_ == ASCENDING else -1 #directional factor
    initial_profit_taker = last_quote.close + df * settings['initial_profit_gap']
    initial_stop = mypy.d_round(calculate_stop(triad, settings),
                                settings['min_price_var'])
    trade_values['profit'] = mypy.d_round(initial_profit_taker, 
                                          settings['min_price_var'])
    trade_values['stop'] = mypy.d_round(initial_stop, 
                                        settings['min_price_var'])
    trade_values['adjusted'] = False
    order_settings = dict(number_of_contracts = nr_of_contracts,
                          direction = direction,
                          profit_limit = trade_values['profit'],
                          stop_aux = trade_values['stop'])
    bracket_order = tws.def_bracket_order(**order_settings)
    e, p, s, m = twss.place_bracket_order(contract, bracket_order)
    print('send trade ', e)
    return e, p, s

def reverse_order(twss, settings, trade_values, triad, last_quote,
                  enter_id, profit_id, stop_id):
    def profitable_position():
        if direction == 'BULL':
            unrealised_profit = last_quote.close - trade_values['entry_price']
        else:
            unrealised_profit = trade_values['entry_price'] - last_quote.close
        answer = unrealised_profit > settings['rev_gain_objective']
        return answer
            
    def reverse_in_profitable_situation(direction, stop_id):
        print('in reverse in profitable situation')
        trade_values['reverse'] = False
        trade_values['rev_printed'] = False
        twss.change_order(stop_id, aux=trade_values['profit'])
        e, p, s = send_order(twss, settings, trade_values, triad, last_quote) 
        enter_id, profit_id, stop_id = e, p , s
        rev_enter_id = rev_stop_id = rev_profit_id = None
        print('enter: {} | profit: {} | loss: {}'.
              format(enter_id, profit_id, stop_id))
        return (enter_id, profit_id, stop_id, 
                rev_enter_id, rev_profit_id, rev_stop_id)
    def reverse_in_losing_situation(direction):
        if not trade_values['rev_printed']:
            print('in reverse in losing situation')
            trade_values['rev_printed'] = True
        trade_values['reverse'] = True
        rev_enter_id = rev_stop_id = rev_profit_id = None
        return (enter_id, profit_id, stop_id, 
                rev_enter_id, rev_profit_id, rev_stop_id)
    if not trade_values['rev_printed']:
        print('in reverse order id')
    if trade_values['profit'] > trade_values['stop']:
        direction = 'BULL'
    else:
        direction = 'BEAR'
    if profitable_position():
        return reverse_in_profitable_situation(direction, stop_id)
    else:
        return reverse_in_losing_situation(direction)
def unset_reversal(twss, settings, trade_values, triad, last_quote,
                  enter_id, profit_id, stop_id,
                  rev_enter_id, rev_profit_id, rev_stop_id):
    print('in unset reversal id')
    trade_values['reverse'] = False
    trade_values['rev_printed'] = False
          
    #send the order and don't forget to adjust the stop once the order is filled!!
def adjust_stops(twss, settings, trade_values,
                 enter_id, profit_id, stop_id, 
                 new_quote):
    def adjust_stop(direction):
        print('entered trade {}, adjusting stops'.format(enter_id))
        trade_values['adjusted'] = True
        new_stop = False
        afp = trade_values['entry_price']
        if direction == 'BULL':
            if afp - settings['max_stop'] > trade_values['stop']:
                new_stop = afp - settings['max_stop']
        else:
            if afp + settings['max_stop'] < trade_values['stop']:
                new_stop = afp + settings['max_stop']
        if new_stop:
            try:
                new_stop = mypy.d_round(new_stop, 
                                        settings['min_price_var'])
                twss.change_order(stop_id, aux=new_stop)
                trade_values['stop'] = new_stop
                print('       stop @ {}'.format(new_stop))
            except TWSClient.TWSClientWarning:
                print('could not change stop?')
    def adjust_profit(direction):
        diff = 0
        new_profit = False
        afp = trade_values['entry_price']
        if direction == 'BULL':
            #print ('
            last_max = new_quote.high
            if last_max >= afp + settings['first_p_level']:
                diff = (last_max - afp) * settings['first_p_perc'] / 100
                if afp + diff > trade_values['stop']:
                    new_profit = afp + diff
                    max_profit = afp + settings['initial_profit_gap'] + diff
        else:
            last_min = new_quote.low
            if last_min <= afp - settings['first_p_level']:
                diff = (afp - last_min) * settings['first_p_perc'] / 100
                if afp - diff < trade_values['stop']:
                    new_profit = afp - diff
                    max_profit = afp - settings['initial_profit_gap'] - diff
        if new_profit:
            try:
                new_profit = mypy.d_round(new_profit, 
                                          settings['min_price_var'])        
                max_profit = mypy.d_round(max_profit, 
                                          settings['min_price_var'])
                twss.change_order(stop_id, aux=new_profit)
                trade_values['stop'] = new_profit
                print('       stop @ {}'.format(new_profit))                
                twss.change_order(profit_id, limit=max_profit)
                trade_values['profit'] = max_profit
                print('       stop @ {}'.format(max_profit))   
            except TWSClient.TWSClientWarning:
                print('could not change stop?')
    if trade_values['profit'] > trade_values['stop']:
        direction = 'BULL'
    else:
        direction = 'BEAR'
    if not trade_values['adjusted']:
        adjust_stop(direction)
    if new_quote:
        adjust_profit(direction)
    #try to get out with a profit!!!


def follow_up_trades(twss, trade_values,
                     enter_id, profit_id, stop_id,
                     rev_enter_id, rev_profit_id, rev_stop_id):
    if (enter_id not in twss.order_status.keys()
        or
        profit_id not in twss.order_status.keys()
        or
        stop_id not in twss.order_status.keys()):         
        return (False, 
                enter_id, profit_id, stop_id, 
                rev_enter_id, rev_profit_id, rev_stop_id)
    enter_status = twss.order_status[enter_id].status
    profit_status = twss.order_status[profit_id].status
    stop_status = twss.order_status[stop_id].status
    if enter_status == 'Filled':
        if (profit_status == 'Filled' 
            or
            stop_status == 'Filled'):
            print('trade {} stopped'.format(enter_id))
            enter_id = rev_enter_id
            trade_values['entry_price'] = None
            profit_id = rev_profit_id
            trade_values['profit'] = trade_values['r_profit']
            trade_values['r_profit'] = None
            stop_id = rev_profit_id
            trade_values['stop'] = trade_values['r_stop']
            trade_values['r_stop'] = None
            trade_values['adjusted'] = False
            if enter_id:
                st, e, p, s, re, rp, rs = follow_up_trades(twss, trade_values,
                                                           enter_id, profit_id, 
                                                           stop_id,
                                                           None, None, None)
                status = st
                enter_id, profit_id, stop_id = st, e, p
                rev_enter_id, rev_profit_id, rev_stop_id = re, rp, rs
            else:
                status = False
        else:
            if not trade_values['adjusted']:
                afp = twss.order_status[enter_id].avg_fill_price
                trade_values['entry_price'] = afp
                print('      entered @ {}'.format(afp))
            status = True
    #elif enter_status == 'Cancelled':
        
    else:
        status = False   
    return (status, 
            enter_id, profit_id, stop_id, 
            rev_enter_id, rev_profit_id, rev_stop_id)

def calculate_stop(triad, settings):
    t_top = triad.extreme_top
    if triad.type_ == ASCENDING:
        stop = max( t_top, triad.close - settings['max_stop'])
        if triad.close - stop < settings['min_stop']:
            stop = triad.close - settings['min_stop']
    else:
        stop = min( t_top, triad.close + settings['max_stop'])
        if stop - triad.close < settings['min_stop']:
            stop = triad.close + settings['min_stop']
    return stop

def remove_existing_trade(twss, enter_id, wait_for=2, interval=0.5):
    if enter_id in twss.order_status.keys():
        twss.cancel_order(enter_id)
        waiting_time = mypy.now()
        while twss.order_status[enter_id].status != 'Cancelled':
            sleep(interval)
            if twss.order_status[enter_id].status == 'Filled':
                break
            if (mypy.now() - waiting_time).seconds > wait_for:
                print('waiting for {} seconds to remove order {},'
                      '  ??? REMOVE ORDERS YOURSELF ???'.
                      format(enterval, enter_id))
                break
        else:
            print('trade {} removed'.format(enter_id))
            enter_id = None
    else:
        print('removed order {}, because I could not find it in'
              'the order list\n'
              '   !!! CHECK TWS !!!'.
              format(enter_id))
        enter_id = None
    return enter_id