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
import Trader
import OCHLBarTest as Test
import TraderTest
from Rule import Rule, Condition
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
EORTH = '$EORTH_simplecorsesim'
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
       'new': None,             # If True start a new corse, if False load name
       'time_unit': None,       # only set when new is True
       'number_of_units': None, # only set when nrew is True
       'condition_price_linked': True, # if condition and price are linked
                                       # it can influence the behaviour of
                                       # some other settins
       'export_trader_instructions': False, # set a filename if you want to
                                            # export the instructions to a
                                            # file
       'print_trader_instructions': False, # set to True to print 
       'std_trailing_bar_enter_strategy': True, # enter trade if last bar has quotes
                                                # between A and C, and current quote
                                                # crosses A or extreme of last bar
       'limit_b_perc': None, # leave poss if percentage of B is reached
       'maximal_c': None, # Even if other calculations are performed this is
                          # the final test that will reduce diff AC if 
                          # necessary !! trade is stopped if XC
       'maximal_stop': None, # Is the real stop once in trade
                             # if set this is the trade stop loss
       'std_stop_price': Trader.CLOSE, # If a trade gets stopped and the stop
                                       # price is not specified, this value or
                                       # or strategie(??) wil be used by the
                                       # trader to choose the sim exit price
       'leave_pos_before_eorth_in_s': None,  # If you don't want to trade ORTH
                                             # choose the time when you want to
                                             # close all your positions in
                                             # seconds beforte eorth
       'enter_pos_before_eorth_in_s': None,  # latest time you want to enter
                                             # enter a trade
                                             # If you enter nothing it wil be
                                             # set to leave_pos_before... X 2
                                             # or None
       'eorth': '17:30:00' # End of regular trading hours, stander CET Nyse closing
                           # You can change this live with set_eorth
       }

################################################################################
# rule makers
################################################################################
#
def R_stp_if_ll(testvalue):
    condition = Condition(Test.low_lower_then,
                          {Test.VALUE: testvalue})
    action = Trader.Action(Trader.STOP, {})
    rule = Rule()
    rule.add_condition(condition)
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_stp_if_hh(testvalue):
    condition = Condition(Test.high_higher_then,
                          {Test.VALUE: testvalue})
    action = Trader.Action(Trader.STOP, {})
    rule = Rule()
    rule.add_condition(condition)
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_buy_if_hh(testvalue, contract, quantity, price):
    condition = Condition(Test.high_higher_then,
                          {Test.VALUE: testvalue})
    buy_data= {Trader.NAME: contract,
               Trader.QUANTITY: quantity,
               Trader.VALUE: price}
    action = Trader.Action(Trader.BUY, buy_data)
    rule=Rule()
    rule.add_condition(condition)
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_sell_if_ll(testvalue, contract, quantity, price):
    condition = Condition(Test.low_lower_then,
                          {Test.VALUE: testvalue})
    buy_data= {Trader.NAME: contract,
               Trader.QUANTITY: quantity,
               Trader.VALUE: price}
    action = Trader.Action(Trader.SELL, buy_data)
    rule=Rule()
    rule.add_condition(condition)
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_close_pos_if_ll(testvalue, contract, price):
    condition = Condition(Test.low_lower_then,
                          {Test.VALUE: testvalue})
    data = {Trader.NAME: contract,
              Trader.VALUE: price}
    action = Trader.Action(Trader.CLOSE_POSITION,
                             data)
    rule = Rule()
    rule.add_condition(condition)
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_cl_pos_stp_if_ll(testvalue, contract, price):
    rule = R_close_pos_if_ll(testvalue, contract, price)
    action = Trader.Action(Trader.STOP, {})
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_cl_pos_stp_if_trading_ll(testvalue, contract, price):
    rule = R_cl_pos_stp_if_ll(testvalue, contract, price)
    condition = Condition(TraderTest.in_trade,{})
    rule.add_condition(condition)
    return rule
#
################################################################################
#
def R_close_pos_if_hh(testvalue, contract, price):
    condition = Condition(Test.high_higher_then,
                          {Test.VALUE: testvalue})
    data = {Trader.NAME: contract,
            Trader.VALUE: price}
    action = Trader.Action(Trader.CLOSE_POSITION,
                           data)
    rule = Rule()
    rule.add_condition(condition)
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_cl_pos_stp_if_hh(testvalue, contract, price):
    rule = R_close_pos_if_hh(testvalue, contract, price)
    action = Trader.Action(Trader.STOP, {})
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_cl_pos_stp_if_trading_hh(testvalue, contract, price):
    rule = R_cl_pos_stp_if_hh(testvalue, contract, price)
    condition = Condition(TraderTest.in_trade, {})
    rule.add_condition(condition)
    return rule
#
################################################################################
#
def R_close_pos_if_at(testtime, contract, price):
    condition = Condition(Test.bar_after,
                          {Test.VALUE: testtime})
    data = {Trader.NAME: contract,
            Trader.VALUE: price}
    action = Trader.Action(Trader.CLOSE_POSITION,
                           data)
    rule = Rule()
    rule.add_condition(condition)
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_cl_pos_stp_if_at(testtime, contract, price):
    rule = R_close_pos_if_at(testtime, contract, price)
    action = Trader.Action(Trader.STOP, {})
    rule.add_action(action)
    return rule
#
################################################################################
#
def R_cl_pos_stp_if_trading_at(testtime, contract, price):
    rule = R_cl_pos_stp_if_at(testtime, contract, price)
    condition = Condition(TraderTest.in_trade, {})
    rule.add_condition(condition)
    return rule
#
################################################################################


################################################################################
# order makers
################################################################################
#
def send_valid_range_to(trader, minimum, maximum):
    changed = ''
    exit_rule_1 = R_stp_if_ll(minimum)
    exit_rule_2 = R_stp_if_hh(maximum)
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule_1)
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule_2)
    return changed
    
#
################################################################################
#
def send_std_bull_order_to(trader, **data):
    changed = ''
    #bull buy @ XA
    entry_rule = R_buy_if_hh(data[ENTRY_TEST_VALUE],
                             data[CONTRACT],
                             data[NUMBER_OF_CONTRACTS],
                             data[ENTRY_PRICE])
    changed += trader.add_rule(Trader.ENTRY_LIST, 
                               entry_rule)
    #bull close positions @ XC & stop
    exit_rule_1 = R_cl_pos_stp_if_ll(data[STOP_TEST_VALUE],
                                     data[CONTRACT],
                                     data[STOP_PRICE])
    #bull close positions @ XB & stop
    exit_rule_2 = R_cl_pos_stp_if_hh(data[PROFIT_TEST_VALUE],
                                     data[CONTRACT],
                                     data[PROFIT_PRICE])
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule_1)
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule_2)
    return changed
#
################################################################################
#
def send_std_bear_order_to(trader, **data):
    changed = ''
    #bull buy @ XA
    entry_rule = R_sell_if_ll(data[ENTRY_TEST_VALUE],
                             data[CONTRACT],
                             data[NUMBER_OF_CONTRACTS],
                             data[ENTRY_PRICE])
    changed += trader.add_rule(Trader.ENTRY_LIST, 
                               entry_rule)
    #bull close positions @ XC & stop
    exit_rule_1 = R_cl_pos_stp_if_hh(data[STOP_TEST_VALUE],
                                     data[CONTRACT],
                                     data[STOP_PRICE])
    #bull close positions @ XB & stop
    exit_rule_2 = R_cl_pos_stp_if_ll(data[PROFIT_TEST_VALUE],
                                     data[CONTRACT],
                                     data[PROFIT_PRICE])
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule_1)
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule_2)
    return changed
#
################################################################################
#
def attach_bull_trade_stop_to(trader, **data):
    changed = ''
    exit_rule = R_cl_pos_stp_if_trading_ll(data[STOP_TEST_VALUE],
                                             data[CONTRACT],
                                             data[STOP_PRICE])
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule)
    return changed
#
################################################################################
#
def attach_bear_trade_profit_to(trader, **data):
    changed = ''
    exit_rule = R_cl_pos_stp_if_trading_ll(data[PROFIT_TEST_VALUE],
                                           data[CONTRACT],
                                           data[PROFIT_PRICE])
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule)
    return changed
#
################################################################################
#
def attach_bear_trade_stop_to(trader, **data):
    changed = ''
    exit_rule = R_cl_pos_stp_if_trading_hh(data[STOP_TEST_VALUE],
                                           data[CONTRACT],
                                           data[STOP_PRICE])
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule)
    return changed
#
################################################################################
#
def attach_bull_trade_profit_to(trader, **data):
    changed = ''
    exit_rule = R_cl_pos_stp_if_trading_hh(data[PROFIT_TEST_VALUE],
                                           data[CONTRACT],
                                           data[PROFIT_PRICE])
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule)
    return changed
#
################################################################################
#
def attach_time_stop_if_trading(trader, **data):
    changed = ''
    exit_rule = R_cl_pos_stp_if_trading_at(data[STOP_AFTER],
                                           data[CONTRACT],
                                           data[STOP_PRICE])
    changed += trader.add_rule(Trader.EXIT_LIST, exit_rule)
    return changed
#
################################################################################

def _load_cw(cw_name):
    '''Create a new corse'''
    cw_file_name = '.'.join((cw_name, 'corse'))
    #print (cw_file_name)
    if os.path.isfile(cw_file_name):
        #print('loading corse_watcher instance')
        with open(cw_file_name, 'rb') as ifh:
            return pickle.load(ifh)
    else:
        raise CorseFileNotFound()

################################################################################
# Helper functions, try to keep things readable
################################################################################
#
def limit_diff_xy_perc(x, y, percentage):
    '''returns y' that is percentage percent of the original diff'''
    perc = percentage / 100
    return x + (y - x) * perc
#
################################################################################
#
def limit_diff_xy_nominal(x, y, nominal):
    '''returns y' that is max dif of nominal value'''
    if abs(x - y) > nominal:
        y = x + (nominal if y > x else -nominal)
    return y
#
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
     

class theSimulator():
    parameterset = ['name',
                    'new',
                    'time_unit',
                    'number_of_units',
                    'condition_price_linked',
                    'export_trader_instructions',
                    'print_trader_instructions',
                    'std_trailing_bar_enter_strategy',
                    'limit_b_perc',
                    'maximal_c',
                    'maximal_stop',
                    'std_stop_price', 
                    'leave_pos_before_eorth_in_s',
                    'enter_pos_before_eorth_in_s',
                    'eorth']

    trade_id = 'v1.1'

    def send_info(self, info, info_value):
        if info == EORTH and self.close_all_positions_daily_at :
            self.eorth = info_value
            tt = mypy.py_date_time(str(self.eorth), mypy.TIME_STR)
            tt -= self.leave_pos_before_eorth_in_s
            self.close_all_positions_daily_at = tt.time()
            #print('new eorth set: {}'.format(str(self.eorth)))
            #print('ets_arm: {}',self.close_all_positions_daily_at)
        if info == EORTH and self.stop_taking_positions_daily_at :
            self.eorth = info_value
            tt = mypy.py_date_time(str(self.eorth), mypy.TIME_STR)
            tt -= self.enter_pos_before_eorth_in_s
            self.stop_taking_positions_daily_at = tt.time()
            #print('new eorth set: {}'.format(str(self.eorth)))
            #print('dtp_arm: {}',self.close_all_positions_daily_at)
        if info == REACTIVATE_SUSPENDED_TRADES:
            self.reactivate_suspended_trades()


    def make_filename(self):
        ell = [self.name, self.time_unit, str(self.number_of_units)]
        if self.std_trailing_bar_enter_strategy:
            ell.append('tbes')
        if self.limit_b_perc:
            ell.append('lbp{}'.format(self.limit_b_perc))
        if self.maximal_c:
            ell.append('mc{}'.format(self.maximal_c))
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
        if self.eorth:
            self.eorth = mypy.py_time(self.eorth)
        if self.export_trader_instructions:
            if self.export_trader_instructions is True:
                t = '.'.join([self.full_name,'taw'])
                self.export_trader_instructions = t
        if self.leave_pos_before_eorth_in_s:
            if self.enter_pos_before_eorth_in_s is None:
                self.enter_pos_before_eorth_in_s = 2 *  self.leave_pos_before_eorth_in_s
            t = mypy.py_timedelta(self.leave_pos_before_eorth_in_s)
            self.leave_pos_before_eorth_in_s = t
            tt = mypy.py_date_time(str(self.eorth), mypy.TIME_STR)
            tt -= self.leave_pos_before_eorth_in_s
            self.close_all_positions_daily_at = tt.time()
        else:
            self.close_all_positions_daily_at = None
        if self.enter_pos_before_eorth_in_s:
            t = mypy.py_timedelta(self.enter_pos_before_eorth_in_s)
            self.enter_pos_before_eorth_in_s = t
            tt = mypy.py_date_time(str(self.eorth), mypy.TIME_STR)
            tt -= self.enter_pos_before_eorth_in_s
            self.stop_taking_positions_daily_at = tt.time()
            #print('stb_arm: {}',self.stop_taking_positions_daily_at)
        else:
            self.stop_taking_positions_daily_at = None
        self.trade_id_ = 1

    def _trade(self, trade_number):
        for trade in self.trade_list:
            if trade.name == trade_number:
                return trade
        return None

    def reactivate_suspended_trades(self):
        text = ''
        for trade in self.trade_list:
            text += trade.reactivate_suspended_entry_rules()
        return text

    def run(self, curr_data):

        def set_restrictions():
            restrictions = []
            #print('IN RESTRICTION')
            #print('no entry', self.stop_taking_positions_daily_at)
            if (self.stop_taking_positions_daily_at and
                curr_data.time.time() > self.stop_taking_positions_daily_at):
                restrictions.append(NO_NEW_TRADES_ALLOWED)
            if (self.close_all_positions_daily_at and
                curr_data.time.time() > self.close_all_positions_daily_at):
                restrictions.append(NO_ACTIVE_TRADES_ALLOWED)
                #print('no trades',self.close_all_positions_daily_at) 
            self.restrictions = set(restrictions)
            #print(self.restrictions)

        def supend_all_entry_rules():
            text = ''
            for trade in self.trade_list:
                text += trade.suspend_entry_rules()
            return text

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
        def last_check(order_data):
            max_c = self.maximal_c
            cpl = self.condition_price_linked
            entry_price = order_data[ENTRY_PRICE]
            entry_test = order_data[ENTRY_TEST_VALUE]
            stop_price = order_data[STOP_PRICE]
            stop_test = order_data[STOP_TEST_VALUE]
            if self.maximal_c:
                entry_price = order_data[ENTRY_PRICE]
                stop_price = order_data[STOP_PRICE]
                diff = entry_price - stop_price
                if abs(diff) > max_c:
                    if diff > 0:
                        stop_price = entry_price - max_c
                        if cpl:
                            stop_test = entry_test - max_c
                    if diff < 0:
                        stop_price = entry_price + max_c
                        if cpl:
                            stop_test = entry_test + max_c
                order_data.update({STOP_PRICE: stop_price})
            if cpl:
                order_data.update({STOP_TEST_VALUE: stop_test})
            return order_data

        def set_valid_range(trader, value1, value2):
            if value1 > value2:
                value1, value2 = value2, value1
                trader_answer = ''
            trader_answer = send_valid_range_to(trader,
                                                value1,
                                                value2)
            return trader_answer
                
 
        def choose_ordertype():
            if self.maximal_stop:
                if self.limit_b_perc:
                    if self.close_all_positions_daily_at:
                        return std_order_with_limited_b_stop_capda
                    return std_order_with_limited_b_stop
                return std_order_with_stop
            if self.limit_b_perc:
                return std_order_with_limited_b
            return std_order

        def std_order(trader, bb, **data):
            send_order_to = {BULL: send_std_bull_order_to,
                             BEAR: send_std_bear_order_to}
            trader_answer = ''
            trader_answer = send_order_to[bb](trader, **data) 
            return trader_answer

        def std_order_with_limited_b(trader, bb, **data):
            attach_to = {BULL: attach_bull_trade_profit_to,
                         BEAR: attach_bear_trade_profit_to}
            limit = limit_diff_xy_perc
            trader_answer = ''
            if not STD_ORDER_SET in data:
                trader_answer += std_order(trader, bb, **data)
            data_ = dict(data)
            data_[PROFIT_PRICE] = limit(data_[ENTRY_PRICE],
                                        data_[PROFIT_PRICE],
                                        self.limit_b_perc)
            if self.condition_price_linked:
                data_[PROFIT_TEST_VALUE] = limit(data_[ENTRY_TEST_VALUE],
                                                 data_[PROFIT_TEST_VALUE],
                                                 self.limit_b_perc)
            trader_answer += attach_to[bb](trader, **data_)
            return trader_answer

        def std_order_with_stop(trader, bb, **data):
            attach_to = {BULL: attach_bull_trade_stop_to,
                         BEAR: attach_bear_trade_stop_to}
            limit = limit_diff_xy_nominal
            trader_answer = ''
            if not STD_ORDER_SET in data:
                trader_answer += std_order(trader, bb, **data)
            data_ = dict(data)
            data_[STOP_PRICE] = limit(data_[ENTRY_PRICE],
                                      data_[STOP_PRICE],
                                      self.maximal_stop)
            if self.condition_price_linked:
                data_[STOP_TEST_VALUE] = limit(data_[ENTRY_TEST_VALUE],
                                               data_[STOP_TEST_VALUE],
                                               self.maximal_stop)
            else:
                raise SimulatorError('No action set when conditions not linked')
            trader_answer += attach_to[bb](trader, **data_)
            return trader_answer

        def std_order_with_capda(trader, bb, **data):
            attach_to = attach_time_stop_if_trading
            trader_answer = ''
            if not STD_ORDER_SET in data:
                trader_answer += std_order(trader, bb, **data)
            data_ = dict(data)
            data_[STOP_PRICE] = self.std_stop_price
            trader_answer += attach_to(trader, **data_)
            return trader_answer

        def std_order_with_limited_b_stop(trader, bb, **data):
            trader_answer = ''
            trader_answer += std_order_with_stop(trader, bb, **data)
            data[STD_ORDER_SET] = True
            trader_answer += std_order_with_limited_b(trader, bb, **data)
            return trader_answer

        def std_order_with_limited_b_stop_capda(trader, bb, **data):
            trader_answer = ''
            trader_answer += std_order_with_limited_b_stop(trader, bb, **data)
            data[STD_ORDER_SET] = True
            trader_answer += std_order_with_capda(trader, bb, **data)
            return trader_answer

        def create_trader_for(sim_signals):
            '''Sets the rules for a trade with sim_signals valuea'''
            changed = ''
            send_order = choose_ordertype()
            for signal in sim_signals:
                trade_id = signal[TRADE_ID]
                a = signal[ABC_CORR].a
                b = signal[ABC_CORR].b
                c = signal[ABC_CORR].c
                order_data = {CONTRACT: 'foo', NUMBER_OF_CONTRACTS: 1,
                              ENTRY_TEST_VALUE: a, ENTRY_PRICE: a,
                              PROFIT_TEST_VALUE: b, PROFIT_PRICE: b,
                              STOP_TEST_VALUE: c, STOP_PRICE: c,
                              STOP_AFTER: self.close_all_positions_daily_at}
                abc_text = ABC_TEXT.format(a, b, c)
                new_trader =[]
                #process signals that have not yet XA and have no trade rules 
                if trade_id == 0 and signal[STATUS] == MONITORING:
                    trade_id = self.get_next_trade_id()
                    new_trader = Trader.Trader(trade_id)
                    if self.stop_taking_positions_daily_at:
                        new_trader.set_trading_hours(mypy.py_time('00:00:00'),
                                                     self.stop_taking_positions_daily_at,
                                                     self.close_all_positions_daily_at)
                    ann = NEW_TRADE_NOT_ACTIVE.format(trade_id)
                    changed += ann
                    changed += '\n'.join([len(ann) * '=',
                                          new_trader.trader_info(),
                                          abc_text])
                    #changed += len(ann) * '=' + '\n' + abc_text
                    signal[DATA][TRAILING_BAR_PRICE] = 0         
                    signal[TRADE_ID] = trade_id
                    trader_answer = send_order(new_trader,
                                               trend(signal),
                                               **last_check(order_data))
                    changed += new_trader.trader_info()
                    changed += trader_answer
                # process signals that already XA
                elif signal[STATUS] == ACTIVE:
                    if not trade_id == 0:
                        curr_trader = self._trade(trade_id)
                        if (not curr_trader
                            or not (curr_trader.status == Trader.MONITORING
                                    or curr_trader.status == Trader.EMPTY)):
                            continue 
                    if self.std_trailing_bar_enter_strategy:
                        last_bar = self.cwh.info('last_finished_ochl_bar')
                        if last_bar.outside_interval(a, c):
                            if (trade_id 
                                and not curr_trader.status == Trader.EMPTY):
                                changed += ORDERS_REMOVED_PBAAC.format(trade_id)
                                changed += curr_trader.clear_rules()
                                changed += ABC_VALID_WARNING_TB + abc_text
                                signal[DATA][TRAILING_BAR_PRICE] = 0
                                changed += set_valid_range(curr_trader, b, c)
                            if not trade_id:
                                trade_id = self.get_next_trade_id()
                                new_trader = Trader.Trader(trade_id)
                                if self.stop_taking_positions_daily_at:
                                    new_trader.set_trading_hours(mypy.py_time('00:00:00'),
                                                                 self.stop_taking_positions_daily_at,
                                                                 self.close_all_positions_daily_at)
                                ann = NEW_TRADE_ACTIVE.format(trade_id,
                                                              signal[DATA][CROSSED_A])
                                changed += ann
                                changed += '\n'.join([len(ann) * '=',
                                                      new_trader.trader_info(),
                                                      abc_text])
                                signal[TRADE_ID] = trade_id
                                signal[DATA][TRAILING_BAR_PRICE] = 0
                                changed += set_valid_range(new_trader, b, c)
                                self.trade_list.append(new_trader)
                            continue
                        curr_ochl_bar = self.cwh.info('current_ochl_bar')
                        if curr_ochl_bar.outside_interval(a,c):
                            continue
                        if trade_id == 0:
                            trade_id = self.get_next_trade_id()
                            new_trader = Trader.Trader(trade_id)
                            if self.stop_taking_positions_daily_at:
                                new_trader.set_trading_hours(mypy.py_time('00:00:00'),
                                                             self.stop_taking_positions_daily_at,
                                                             self.close_all_positions_daily_at)
                            ann = NEW_TRADE_ACTIVE.format(trade_id,
                                                          signal[DATA][CROSSED_A])
                            changed += ann
                            changed += '\n'.join([len(ann) * '=',
                                                  new_trader.trader_info(),
                                                  abc_text])
                            #changed += len(ann) * '=' + '\n' + abc_text
                            signal[TRADE_ID] = trade_id
                            curr_trader = new_trader
                            signal[DATA][TRAILING_BAR_PRICE] = 0    
                        if bull(signal):
                            price = last_bar.high if last_bar.high < a else a
                        if bear(signal):
                            price = last_bar.low if last_bar.low > a else a
                        try:
                            if not price == signal[DATA][TRAILING_BAR_PRICE]:
                                changed += curr_trader.trader_info()
                                changed += TRAILING_BAR
                                changed += ORDERS_REMOVED_TBNP.format(trade_id)
                                changed += curr_trader.clear_rules()
                                signal[DATA][TRAILING_BAR_PRICE] = price
                                order_data.update({ENTRY_TEST_VALUE: price,
                                                   ENTRY_PRICE: price})
                                trader_answer = send_order(curr_trader,
                                                           trend(signal),
                                                           **last_check(order_data))
                                changed += trader_answer
                        except:
                            print(signal)
                            print(curr_data)
                            raise
                if new_trader:
                    self.trade_list.append(new_trader)
            return changed
                        
                    
                    
                            
        changed = False
        changed_trader_rules = ''
        set_restrictions()
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
            
        data_dict = Trader.trader_data(curr_data)
        data_dict.update(Test.test_data(curr_data))
        for trader in self.trade_list:
            changed_trader_rules += trader.run_trader(**data_dict)

        changed |= check_monitored_signals(self.sim_bear_signals)
        changed |= check_monitored_signals(self.sim_bull_signals)
        if False: #NO_NEW_TRADES_ALLOWED in self.restrictions:
        #if NO_NEW_TRADES_ALLOWED in self.restrictions:
            new_trader_rules = supend_all_entry_rules()
        else:
            new_trader_rules = create_trader_for(self.sim_bear_signals)
            changed_trader_rules += new_trader_rules
            changed |= bool(new_trader_rules)
            new_trader_rules = create_trader_for(self.sim_bull_signals)
            changed_trader_rules += new_trader_rules
            changed |= bool(new_trader_rules)
        self.stopped_traders += [x for x in self.trade_list if x.status == Trader.STOPPED]
        self.trade_list = [x for x in self.trade_list if not x.status == Trader.STOPPED]
        if False: #changed:
            print('bear_after')
            for li in  self.sim_bear_signals:
                print(li or '***EMPTY LIST***')
            print()
            print('bull after')
            for li in self.sim_bull_signals:
                print(li or '***EMPTY LIST***')
            print('TRADES')
            print('******')
            for trader in self.trade_list:
                print(trader)

            points = number_of_trades = number_of_good_trades = 0
            for trader in self.stopped_traders:
                if trader.positions: 
                    number_of_trades += 1
                    if trader.value > 0:
                        number_of_good_trades += 1
                    points += trader.value
            if number_of_trades:
                print('SUMMARY\n')
                print('Number of trades: {}'.format(number_of_trades))
                print('perc of good trades: {}'.format(100 * number_of_good_trades / number_of_trades))
                print('points: {}'.format(points))
                    
        
        #for trader in self.trade_list:
        #    trader.run_trader(**Test.test_data(curr_data))
        #if changed_trader_rules and self.print_trader_instructions:
        #    print('NEW RULES')
        #    print('*********')
        #    print(changed_trader_rules)
        if changed_trader_rules and self.export_trader_instructions:
            with open(self.export_trader_instructions,'a') as ofh:
                ofh.write('CURRENT TIME: {}\n'.format(curr_data.time))
                ofh.write('CURRENT PRICE: {}\n\n'.format(curr_data.close))
                ofh.write(changed_trader_rules)
                ofh.write('\n' + 80 * '*' + '\n')
        #if changed_trader_rules:
        #    for tr in self.trade_list:
        #        print(tr.trader_info())
        
        return changed_trader_rules

    def make_csv_trade_file(self, of=None):
        if not of:
            of = '.'.join([self.full_name, 'csv'])
        members = ['trade_id', 'adv_ann', 'cw_pos',
                   'a', 'a_time',
                   'b', 'b_time',
                   'c', 'c_time',
                   'min', 'min_time',
                   'max', 'max_time',
                   'XA',
                   'entered_trade', 'stopped_trade',
                   'min_in_trade', 'max_in_trade',
                   'result']
        with open(of,'w') as ofh:
            ofh.write(','.join(members))
            ofh.write('\n')
            for adv in self.removed_adivices_with_trader_attached:
                for trader in self.stopped_traders:
                    if adv[TRADE_ID] == trader.name:
                        xa = adv[DATA][CROSSED_A]
                        if xa:
                            xats = mypy.date_time2format(xa, mypy.DATE_TIME_STR)
                        else:
                            xats = ''
                        ent = trader.entry_log[0][0] if trader.entry_log else ''
                        if ent:
                            entts = mypy.date_time2format(ent, mypy.DATE_TIME_STR)
                        else:
                            entts = ''
                        ext = trader.exit_log[-1][0] if trader.exit_log else ''
                        if ext:
                            extts = mypy.date_time2format(ext, mypy.DATE_TIME_STR)
                        else:
                            extts = ''
                        line_ell = [str(trader.name),
                                    mypy.date_time2format(adv[TIME],
                                                          mypy.DATE_TIME_STR),
                                    str(adv[ABC_CORR].id),
                                    str(adv[ABC_CORR].a),
                                    mypy.date_time2format(adv[ABC_CORR].a_time,
                                                          mypy.DATE_TIME_STR),
                                    str(adv[ABC_CORR].b),
                                    mypy.date_time2format(adv[ABC_CORR].b_time,
                                                          mypy.DATE_TIME_STR),
                                    str(adv[ABC_CORR].c),
                                    mypy.date_time2format(adv[ABC_CORR].c_time,
                                                          mypy.DATE_TIME_STR),
                                    str(adv[ABC_CORR].min),
                                    mypy.date_time2format(adv[ABC_CORR].min_time,
                                                          mypy.DATE_TIME_STR),
                                    str(adv[ABC_CORR].max),
                                    mypy.date_time2format(adv[ABC_CORR].max_time,
                                                          mypy.DATE_TIME_STR),
                                    xats,
                                    entts,
                                    extts,
                                    str(trader.min_in_trade),
                                    str(trader.max_in_trade),
                                    str(trader.value)]
                        if entts:
                            line = ','.join(line_ell)
                            line += '\n'
                            ofh.write(line)
                                    
                        #print(trader.entry_log, trader.exit_log)
                        #print()
