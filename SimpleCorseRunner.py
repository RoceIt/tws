#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)

"""
This module discribes a testsimulator for processing intraday data
"""

import os.path
import pickle
from collections import namedtuple

import mypy
import barData
import TWSTrader_corseabc as Trader
#import OCHLBarTest as Test
#import TraderTest
#from Rule import Rule, Condition
from corse_watcher import corse_watcher


class SimulatorError(Exception):pass
class CorseFileNotFound(SimulatorError):pass
class ParameterError(SimulatorError):pass
class DataError(SimulatorError):pass

BEAR = '$BEAR'
BULL = '$BULL'

################################################################################
# sim signal structure
################################################################################
#
TIME = '$TIME'
ABC_CORR = '$ABC_CORRECTION'
STATUS = '$STATUS'
DATA = '$DATA'
TRADE_ID = '$TRADE_ID'
#
################################################################################

################################################################################
# status values for sim signals
################################################################################
#
MONITORING = '$MONITORING'
# MONITORING: waiting to cross A
IN_TRADE = '$IN_TRADE'
# IN_TRADE: in trade
INVALID = '$INVALID'
# INVALID: out of trade or max broken
NEW = '$NEW'
# NEW: just added to list
NO_C = '$NO_C'
# NO_C: no c set, only a and b
ACTIVE = ' $ACTIVE'
# ACTIVE: not in trade, but A has already been broken
REMOVE = '$REMOVE'
# REMOVE: ready for complete removal
#
################################################################################

################################################################################
# data values for sim signals 
################################################################################
D_REMOVE = '$D_REMOVE'
# remove: you are allowed to remove this trade when new corse's arive
#         values: True or False
#         if signal still exists in next round of CW signal it will not be
#         removed
CROSSED_A = '$CROSSED_A'
# time the simulater noticed the trade crossed the a entry
TRAILING_BAR_PRICE = '$TRAILING_BAR_PRICE'
ANNOUNCED = '$ANNOUNCED'
################################################################################

################################################################################
# restrictions
################################################################################
NO_NEW_TRADES_ALLOWED = '$NO_NEW_TRADES_ALLOWED'
NO_ACTIVE_TRADES_ALLOWED = '$NO_ACTIVE_TRADES_ALLOWED'
################################################################################

################################################################################
# data values for orders
################################################################################
CONTRACT = '$CONTRACT_ORDER'
NUMBER_OF_CONTRACTS = '$NUMBER_OF_CONTRACTS_ORDER'
ENTRY_TEST_VALUE = '$ENTRY_TEST_VALUE_ORDER'
PROFIT_TEST_VALUE = '$PROFIT_TEST_VALUE_ORDER'
STOP_TEST_VALUE = '$STOP_TEST_VALUE_ORDER'
ENTRY_PRICE = '$ENTRY_PRICE_ORDER'
PROFIT_PRICE = '$PROFIT_PRICE_ORDER'
STOP_PRICE = '$STOP_PRICE_ORDER'
STD_ORDER_SET = '$STD_ORDER_SET'
STOP_AFTER = '$STOP_AFTER'
################################################################################

################################################################################
# set info values
################################################################################
#
EORTH = '$EORTH_simplecorserunner'
REACTIVATE_SUSPENDED_TRADES = '$REACTIVATE_SUSPENDED_TRADES'
#
################################################################################

################################################################################
# messages
################################################################################
#
ABC_TEXT = 'ABC values:\n\ta: {}\n\tb: {}\n\tc: {}\n\n'
NEW_TRADE_NOT_ACTIVE = 'NEW TRADE {}, not active, wait XA\n'
NEW_TRADE_ACTIVE = 'NEW TRADE {}, active, XA @ {}\n'
ORDERS_REMOVED_PBAAC = ('TRADE {}, orders removed because previous '
                        'bar outside ac\n')
ORDERS_REMOVED_TBNP = ('TRADE {}, previous orders removed, new trailing '
                       'bar price\n')
TRAILING_BAR = 'TRAILING BAR ENTRY\n'
ABC_VALID_WARNING_TB = 'ABC IS VALID & ACTIVE: waiting for trailing bar opp.\n'
ACTIVE_ABC_NO_TRADER_ATT = '!!! ACTIVE ABC NO TRADER ATTACHED YET !!!\n'
#
################################################################################


#some vars for easier testing, these are not needed to run the simulator
spv = {'name': 'testfile',
       'contract': None, # the contract to trade
       'number_of_contracts': 0, # number of contracts to buy
       'new': None,             # If True start a new corse, if False load name
       'time_unit': None,       # only set when new is True
       'number_of_units': None, # only set when nrew is True
       'limit_b_perc': None, # leave poss if percentage of B is reached
       'maximal_stop': None, # Is the real stop once in trade
                             # if set this is the trade stop loss
       'leave_pos_before_eorth_in_s': None,  # If you don't want to trade ORTH
                                             # choose the time when you want to
                                             # close all your positions in
                                             # seconds beforte eorth
       'enter_pos_before_eorth_in_s': None,  # latest time you want to enter
                                             # enter a trade
                                             # If you enter nothing it wil be
                                             # set to leave_pos_before... X 2
                                             # or None
       'eorth': None, # End of regular trading hours, stander CET Nyse closing
                            # You can change this live with set_eorth
       'TWS_h': None, # TWSClient
       'future_gap': None, # if you are trading a future give the pair of
                           # TWS infoques that follow the gap
       'min_price_variation': 0.05, # min pricevariation of the product, used
                                    # to autocorrect the abc prices before send
       'reporter': None,
       'reporter_settings': None
       }

################################################################################
# Helper functions, try to keep things readable
################################################################################
#
def bear(signal):
    return signal[ABC_CORR].a > signal[ABC_CORR].b
#
################################################################################
#
def bull(signal):
    return signal[ABC_CORR].a < signal[ABC_CORR].b
#
################################################################################
#
def trend(signal):
    return BEAR if bear(signal) else BULL
#
################################################################################

def update_sim_signals(sim_list, cw_list, curr_time):
    '''update simulator signals list with new CW signals'''

    def new_signal(curr_time, signal):
        sim_signal = {TIME: curr_time,
                      ABC_CORR: signal,
                      STATUS: NEW,
                      DATA: {ANNOUNCED: False},
                      TRADE_ID: 0
                      }
        return sim_signal

    def check_for(signal):
        '''returns sim_list signal if cw_signal in list'''
        for sim_signal in sim_list:
            if sim_signal[ABC_CORR] == signal:
                return sim_signal
        return None

    for signal in cw_list:
        existing_sim_signal = check_for(signal)
        # If signal is already in the sim_list
        if existing_sim_signal:
            status = existing_sim_signal[STATUS]
            # and it has one of the following stati
            # make sure you don't remove them
            if (status == INVALID or
                status == NO_C or
                status == MONITORING or
                status == ACTIVE):
                existing_sim_signal[DATA][D_REMOVE]= False
        # If signal is not in the sim_list, add it 
        else:
            sim_list.append(new_signal(curr_time, signal))
    for sim_signal in sim_list:
        status = sim_signal[STATUS]
        # Make sure that you mark signals with the following
        # stati that are no longer in the cw list for removal
        if (status == INVALID or
            status == NO_C or
            status == MONITORING or
            status == ACTIVE):
            if sim_signal[DATA][D_REMOVE] == True:
                sim_signal[STATUS] = REMOVE
            else:
                sim_signal[DATA][D_REMOVE] = True
    updated_list = [x for x in sim_list if not x[STATUS] == REMOVE]
    removed_with_trader = [x for x in sim_list if (x[STATUS] == REMOVE
                                                   and x[TRADE_ID])]
    ann_without_trade = [x for x in sim_list if (x[STATUS] == REMOVE
                                                 and x[TRADE_ID] == 0
                                                 and x[DATA][ANNOUNCED])]
    return updated_list, removed_with_trader, ann_without_trade
     

class theRunner():
    parameterset = ['name',
                    'contract',
                    'number_of_contracts',
                    'new',
                    'time_unit',
                    'number_of_units',
                    'limit_b_perc',
                    'maximal_stop', 
                    'leave_pos_before_eorth_in_s',
                    'enter_pos_before_eorth_in_s',
                    'eorth',
                    'TWS_h',
                    'future_gap',
                    'min_price_variation',
                    'reporter',
                    'reporter_settings']

    trade_id = 'v1.1'

    def send_info(self, info, info_value):
        if info == EORTH and self.leave_pos_before_eorth_in_s :
            self.eorth = tt = info_value
            tt -= self.leave_pos_before_eorth_in_s
            self.close_all_positions_daily_at = tt
            #print('new eorth set: {}'.format(str(self.eorth)))
            #print('ets_arm: {}',self.close_all_positions_daily_at)
        if info == EORTH and self.enter_pos_before_eorth_in_s:
            self.eorth = tt = info_value
            tt -= self.enter_pos_before_eorth_in_s
            self.stop_taking_positions_daily_at = tt
            #print('new eorth set: {}'.format(str(self.eorth)))
            #print('dtp_arm: {}',self.close_all_positions_daily_at)
        if info == 'set_TWS_h':
            if self.TWS_h:
                if not mypy.get_bool('replace existing handler? ', False):
                    raise SimulatorError
            self.TWS_h = info_value
        if info == 'set_future_gap':            
            self.future_gap = info_value
        if info == 'set_contract_data':
            self.contract = info_value[0]
            self.number_of_contracts = info_value[1]
        if info == 'set_reporter':
            self.reporter = info_value[0]
            self.reporter_settings = info_value[1]
#        if info == 'set_contract':
#            self.contract = info_value
#        if info == 'set_noc':
#            self.number_of_contracts = info_value

    def make_filename(self):
        ell = [self.name, self.time_unit, str(self.number_of_units)]
        if self.limit_b_perc:
            ell.append('lbp{}'.format(self.limit_b_perc))
        if self.maximal_stop:
            ell.append('ms{}'.format(self.maximal_stop))
        if self.leave_pos_before_eorth_in_s:
            ell.append('capda')
        return '_'.join(ell).replace('.','l')

    def get_next_trade_id(self):
        self.trade_id_ +=1
        return self.trade_id_

    def __init__(self):
        pass

    def arm(self, parameters):
        '''Use this function to set all vars you use in run() 
        to initial value'''
        # Set all parameters
        for name in self.parameterset:
            self.__dict__[name] = parameters.getParameter(name)
        # Check if you are loading a file or creating a new corse
        if self.new:
            #print('in self.new')
            if self.time_unit and self.number_of_units:
                #print('Creating new corse instance')
                self.cwh = corse_watcher(self.time_unit, self.number_of_units)
            else:
                raise ParameterError('time_unit and number_of_units must be '
                                      'set when new is True')
        else:
            #print('not in self.new')
            if not self.time_unit and not self.number_of_units:
                self.cwh = _load_cw(self.name)
            else:
                raise ParameterError('time_unit and number_of_units can not '
                                      'be set when new is False')
        # Set the variables
        self.sim_bear_signals = []
        self.sim_bull_signals = []
        self.trade_list = []
        self.stopped_traders = []
        self.removed_adivices_with_trader_attached = []
        self.full_name = self.make_filename()
        print('eorth=', self.eorth)
        if self.leave_pos_before_eorth_in_s:
            if self.enter_pos_before_eorth_in_s is None:
                self.enter_pos_before_eorth_in_s = 2 *  self.leave_pos_before_eorth_in_s
            t = mypy.py_timedelta(self.leave_pos_before_eorth_in_s)
            self.leave_pos_before_eorth_in_s = t
#            tt = mypy.py_date_time(str(self.eorth), mypy.TIME_STR)
#            tt -= self.leave_pos_before_eorth_in_s
#            self.close_all_positions_daily_at = tt.time()#        
        else:
            self.close_all_positions_daily_at = None
        if self.enter_pos_before_eorth_in_s:
            t = mypy.py_timedelta(self.enter_pos_before_eorth_in_s)
            self.enter_pos_before_eorth_in_s = t
#            tt = mypy.py_date_time(str(self.eorth), mypy.TIME_STR)
#            tt -= self.enter_pos_before_eorth_in_s
#            self.stop_taking_positions_daily_at = tt.time()
            #print('stb_arm: {}',self.stop_taking_positions_daily_at)
        else:
            self.stop_taking_positions_daily_at = None
        self.trade_id_ = 1

    def _trade(self, trade_number):
        for trade in self.trade_list:
            if trade.name == trade_number:
                return trade
        return None

    def run(self, curr_data):

        def initialise_new(sim_signals):
            '''Checks for the initial state of new corses'''
            for signal in sim_signals:
                if signal[STATUS] == NEW:
                    # Set NO_C for corse's without a set C
                    if not signal[ABC_CORR].c:
                        signal[STATUS] = NO_C
                        signal[DATA][D_REMOVE] = True
                        continue
                    # bull signals
                    elif bull(signal): #signal[ABC_CORR].a < signal[ABC_CORR].b:
                        XA, zz = self.cwh.info(barData.FIRST_HIGH_HIGHER_THEN,
                                               value = signal[ABC_CORR].a,
                                               time_ = signal[ABC_CORR].c_time)
                        zz, M = self.cwh.info(barData.MAXIMUM,
                                              time_ = signal[ABC_CORR].c_time)
                        zz, m = self.cwh.info(barData.MINIMUM,
                                              time_ = signal[ABC_CORR].c_time)
                        # Invalidate new corse's that have already broken b or c
                        if ((M and M > signal[ABC_CORR].b) or
                            (m and m < signal[ABC_CORR].c)):
                            signal[STATUS] = INVALID
                            signal[DATA][D_REMOVE] = True
                            signal[DATA][CROSSED_A] = XA
                            continue
                    # bear signals
                    elif bear(signal): #signal[ABC_CORR].a > signal[ABC_CORR].b:
                        XA, zz = self.cwh.info(barData.FIRST_LOW_LOWER_THEN,
                                               value = signal[ABC_CORR].a,
                                               time_ = signal[ABC_CORR].c_time)
                        zz, M = self.cwh.info(barData.MAXIMUM,
                                              time_ = signal[ABC_CORR].c_time)
                        zz, m = self.cwh.info(barData.MINIMUM,
                                              time_ = signal[ABC_CORR].c_time)
                        # Invalidate new corse's that have already broken b or c
                        if ((m and m < signal[ABC_CORR].b) or
                            (M and M > signal[ABC_CORR].c)):
                            signal[STATUS] = INVALID
                            signal[DATA][D_REMOVE] = True
                            signal[DATA][CROSSED_A] = XA
                            continue
                    # If new corse already crossed A once, make it active
                    # else monitor it
                    if XA:
                        signal[STATUS] = ACTIVE
                    else:
                        signal[STATUS] = MONITORING
                    # general settings
                    signal[DATA][D_REMOVE] = True
                    signal[DATA][CROSSED_A] = XA

        def check_monitored_signals(sim_signals):
            '''Checks if the current data is triggering a monitored signal'''
            changed = False
            for signal in sim_signals:
                if True: # not signal[STATUS] is IN_TRADE :
                    trade_id = signal[TRADE_ID]
                    curr_trader = self._trade(trade_id)
                    if curr_trader:
                        trader_status = curr_trader.status
                        if (trader_status == Trader.IN_TRADE and
                            not signal[STATUS] is IN_TRADE):
                            signal[STATUS] = IN_TRADE
                            changed = True
                        elif trader_status in [Trader.STOPPED, Trader.STOPPING]:
                            signal[STATUS] = INVALID
                            signal[DATA][D_REMOVE] = True
                            changed = True  
                    elif signal[STATUS] is IN_TRADE:
                        signal[STATUS] = INVALID
                        signal[DATA][D_REMOVE] = True
                        changed = True                     
                    
                if signal[STATUS] == MONITORING:
                    # bull signals
                    if bull(signal): #signal[ABC_CORR].a < signal[ABC_CORR].b:
                        # b or c broken, corse is invalid
                        if ((curr_data.low < signal[ABC_CORR].c) or
                            (curr_data.high > signal[ABC_CORR].b)):
                            signal[STATUS] = INVALID
                            changed = True
                            #print('bull signal {} invalidated'
                            #      ''.format(signal[ABC_CORR].id))
                            continue
                        # crossed a, corse becomes valid
                        if curr_data.high > signal[ABC_CORR].a:
                            signal[STATUS] = ACTIVE
                            changed = True
                            signal[DATA][CROSSED_A] = curr_data.time
                            #print('made bull signal {} active'
                            #      ''.format(signal[ABC_CORR].id))
                    # bear signals
                    if bear(signal): #signal[ABC_CORR].a > signal[ABC_CORR].b:
                        # b or c broken, corse is invalid
                        if ((curr_data.low < signal[ABC_CORR].b) or
                            (curr_data.high > signal[ABC_CORR].c)):
                            signal[STATUS] = INVALID
                            changed = True
                            #print('bear signal {} invalidated'
                            #      ''.format(signal[ABC_CORR].id))
                            continue
                        # crossed a, corse becomes valid
                        if curr_data.low < signal[ABC_CORR].a:
                            signal[STATUS] = ACTIVE
                            changed = True
                            signal[DATA][CROSSED_A] = curr_data.time
                            #print('made bull signal {} active'
                            #      ''.format(signal[ABC_CORR].id))
            return changed


        def create_trader_for(sim_signals):
            '''Sets the rules for a trade with sim_signals valuea'''


            def call_new_trader(name):

                trader = Trader.Trader(name,
                                       b, c,
                                       self.TWS_h,
                                       self.maximal_stop,
                                       self.limit_b_perc,
                                       self.stop_taking_positions_daily_at,
                                       self.close_all_positions_daily_at,
                                       self.min_price_variation,
                                       self.future_gap,
                                       originator=self.full_name)
                if self.reporter:
                    trader.set_reporter(self.reporter, 
                                        *self.reporter_settings)
                return trader

            
            def send_order(trader, enter_price):

                if trader.status == Trader.EMPTY:
                    trader.send_order(self.contract, 
                                      self.number_of_contracts,
                                      enter_price,
                                      time_ = curr_data.time.time())
                elif trader.status == Trader.MONITORING:
                    trader.send_new_a_value(enter_price,
                                            time_ = curr_data.time.time())
                
                                      

            changed = ''
            for signal in sim_signals:
                trade_id = signal[TRADE_ID]
                a = signal[ABC_CORR].a
                b = signal[ABC_CORR].b
                c = signal[ABC_CORR].c
                new_trader = []
                #process signals that have not yet XA and have no trade rules 
                if trade_id == 0 and signal[STATUS] == MONITORING:
                    trade_id = self.get_next_trade_id()
                    new_trader = call_new_trader(trade_id)
                    signal[DATA][TRAILING_BAR_PRICE] = 0         
                    signal[TRADE_ID] = trade_id
                    send_order(new_trader, a)
                # process signals that already XA
                elif signal[STATUS] == ACTIVE:
                    if not trade_id == 0:
                        curr_trader = self._trade(trade_id)
                        if (not curr_trader
                            or not (curr_trader.status == Trader.MONITORING
                                    or curr_trader.status == Trader.EMPTY)):
                            continue 
                    if True:
                        last_bar = self.cwh.info('last_finished_ochl_bar')
                        if last_bar.outside_interval(a, c):
                            if (trade_id 
                                and not curr_trader.status == Trader.EMPTY):
                                curr_trader.remove_order()
                            if not trade_id:
                                trade_id = self.get_next_trade_id()
                                new_trader = call_new_trader(trade_id)
                                signal[TRADE_ID] = trade_id
                                signal[DATA][TRAILING_BAR_PRICE] = 0
                                self.trade_list.append(new_trader)
                            continue
                        curr_ochl_bar = self.cwh.info('current_ochl_bar')
                        if curr_ochl_bar.outside_interval(a,c):
                            continue
                        if trade_id == 0:
                            trade_id = self.get_next_trade_id()
                            new_trader = call_new_trader(trade_id)
                            signal[TRADE_ID] = trade_id
                            curr_trader = new_trader
                            signal[DATA][TRAILING_BAR_PRICE] = 0    
                        if bull(signal):
                            price = last_bar.high if last_bar.high < a else a
                        if bear(signal):
                            price = last_bar.low if last_bar.low > a else a
                        if not price == signal[DATA][TRAILING_BAR_PRICE]:
                                signal[DATA][TRAILING_BAR_PRICE] = price
                                send_order(curr_trader, price)
                if new_trader:
                    self.trade_list.append(new_trader)
            return changed
                        
                    
                    
                            
        changed = False
        changed_trader_rules = ''
        if not curr_data.__class__ == barData.ochlBar:
            raise DataError('Expecting an ochlBar')
            # it is possible to test for a float and make an ochlBar
            # so you can run it on tick data
        #Insert data in cwh and return
        cw_bull_signals = []
        cw_bear_signals = []
        if self.cwh.insert(curr_data.time, curr_data.open, curr_data.close,
                           curr_data.high, curr_data.low):
            cw_bear_signals, cw_bull_signals = self.cwh.info('get_hot_signals')
            self.sim_bear_signals, r, a = update_sim_signals(self.sim_bear_signals,
                                                          cw_bear_signals, 
                                                          curr_data.time)
            self.removed_adivices_with_trader_attached += r
            self.sim_bull_signals, r, a = update_sim_signals(self.sim_bull_signals,
                                                          cw_bull_signals, 
                                                          curr_data.time)
            self.removed_adivices_with_trader_attached += r
            initialise_new(self.sim_bear_signals)
            initialise_new(self.sim_bull_signals)
            
        for trader in self.trade_list:
            changed_trader_rules += trader.update(curr_data)

        changed |= check_monitored_signals(self.sim_bear_signals)
        changed |= check_monitored_signals(self.sim_bull_signals)
        new_trader_rules = create_trader_for(self.sim_bear_signals)
        changed_trader_rules += new_trader_rules
        changed |= bool(new_trader_rules)
        new_trader_rules = create_trader_for(self.sim_bull_signals)
        changed_trader_rules += new_trader_rules
        changed |= bool(new_trader_rules)
        self.trade_list = [x for x in self.trade_list if not x.status == Trader.STOPPED]
        if changed:
            print(changed)       
        return changed_trader_rules


    def eop_proc(self):
        
        print('EOD INSTRUCTIONS FOR TRADERS')
        print('****************************\n')
        for trader in self.trade_list:
            trader.remove_TWS_h()
            print('trader {}: {}'.format(trader.name, trader.status))
        print('****************************\n')
        self.TWS_h = self.future_gap = None
        return True



    
    def restart_traders(self):

        print(self.contract, self.number_of_contracts)
        for trader in self.trade_list:
            trader.set_TWS_h(self.TWS_h, self.future_gap)
            trader.set_trading_hours(self.stop_taking_positions_daily_at,
                                     self.close_all_positions_daily_at)
            if trader.status == Trader.MONITORING:
                trader.contract = self.contract
                trader.number_of_contracts = self.number_of_contracts
            if self.reporter:
                trader.set_reporter(self.reporter, *self.reporter_settings)

