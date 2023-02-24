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
import TWSTrader_corseabc2 as Trader

from corse_watcher import corse_watcher
from corse import ABCCorrection


class SimulatorError(Exception):pass
class CorseFileNotFound(SimulatorError):pass
class ParameterError(SimulatorError):pass
class DataError(SimulatorError):pass

BEAR = '$BEAR'
BULL = '$BULL'

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
SIM_SIGNAL_STATUS = (MONITORING, IN_TRADE, INVALID, NEW,
                     NO_C, ACTIVE, REMOVE)
#
################################################################################

################################################################################
# set info values
################################################################################
#
EORTH = '$EORTH_simplecorserunner'
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
       'reporter_settings': None,
       'trader_reports': True
       }

class SimSignal():
    '''Class that holds all information about a signal received from the 
    corse
    '''

    def __init__(self, curr_time, abc_correction):
        self.first_announced = curr_time
        self.correction = abc_correction
        if self.correction.a > self.correction.b:
            self.direction = BEAR
        else:
            self.direction = BULL
        self.status = NEW
        self.announced = False
        self.crossed_a = None
        self.trailing_bar_price = 0
        self.trader = None
        self.ready_for_removal = False
        
    def __str__(self):
        st = ('announced: {}\n'
              'corr: {}\n'
              'status: {}\n'
              'attached trader: {}\n'
              'crossed a: {}\n'.
              format(self.first_announced, self.correction, self.status,
                     self.trader, self.crossed_a))
        return st
        
        
    @property
    def correction(self):
        return self.__correction
    
    @correction.setter
    def correction(self, abc_correction):
        assert isinstance(abc_correction, ABCCorrection)
        self.__correction = abc_correction
        
    @property
    def status(self):
        return self.__status
    
    @status.setter
    def status(self, curr_status):
        assert curr_status in SIM_SIGNAL_STATUS
        self.__status = curr_status
        
    @property
    def nominal_min(self):
        return min(self.correction.b, self.correction.c)
    
    @property
    def nominal_max(self):
        return max(self.correction.b, self.correction.c)
        
        

def update_sim_signals(sim_list, cw_list, curr_time):
    '''update simulator signals list with new CW signals'''    
    monitored_corrections = [a.correction for a in sim_list]
    def find_sim_signal_for(correction):
        '''returns sim_signal from sim_list with correction'''
        position = monitored_corrections.index(correction)
        return sim_list[position]
    for new_correction in cw_list:
        # Check if an announced correction is already being processed
        # if not add it to the simulator list
        if new_correction in monitored_corrections:
            actif_sim_signal = find_sim_signal_for(new_correction)
            if not actif_sim_signal.status is REMOVE: 
                actif_sim_signal.ready_for_removal = False
        else:
            sim_list.append(SimSignal(curr_time, new_correction))
    for sim_signal in sim_list:
        # Make sure that you mark signals with the following
        # stati that are no longer in the cw list for removal
        if not sim_signal.status is NEW:
            if sim_signal.ready_for_removal:
                sim_signal.status = REMOVE
            else:
                sim_signal.ready_for_removal = True
    #update lists
    updated_list = [x for x in sim_list if not x.status is REMOVE]
    removed_with_trader = [x for x in sim_list if (x.status is REMOVE
                                                   and x.trader)]
    ann_without_trade = [x for x in sim_list if (x.status is REMOVE
                                                 and x.trader
                                                 and x.announced)]
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
                    'reporter_settings',
                    'trader_reports']

    trade_id = 'v1.1'

    def send_info(self, info, info_value):
        if info == EORTH and self.leave_pos_before_eorth_in_s :
            self.eorth = tt = info_value
            tt -= self.leave_pos_before_eorth_in_s
            self.close_all_positions_daily_at = tt
        if info == EORTH and self.enter_pos_before_eorth_in_s:
            self.eorth = tt = info_value
            tt -= self.enter_pos_before_eorth_in_s
            self.stop_taking_positions_daily_at = tt
        elif info == 'set_TWS_h':
            if self.TWS_h:
                if not mypy.get_bool('replace existing handler? ', False):
                    raise SimulatorError
            self.TWS_h = info_value
        elif info == 'set_future_gap':            
            self.future_gap = info_value
        elif info == 'set_contract_data':
            self.contract = info_value[0]
            self.number_of_contracts = info_value[1]
        elif info == 'set_reporter':
            self.reporter = info_value[0]
            self.reporter_settings = info_value[1]
        elif info == 'open_trader_reports_file':
            of = '.'.join([self.full_name, 'csv'])
            if not os.path.isfile(of):
                self.open_new_file_for_trader_reports()
            self.trader_report_handle = open(of, 'a', 
                                             buffering=1)

    def make_filename(self):
        ell = [self.name, self.time_unit, str(self.number_of_units)]
        if self.limit_b_perc:
            ell.append('lbp{}'.format(self.limit_b_perc))
        if self.maximal_stop:
            ell.append('ms{}'.format(self.maximal_stop))
        if self.leave_pos_before_eorth_in_s:
            ell.append('capda')
        return '_'.join(ell).replace('.','l')
    
    def open_new_file_for_trader_reports(self):
        '''creates a file with appropriate header for writing the
        trader reports'''
        #make sure that the header you create here is conform
        #to the data you write in 'write_report_for'
        columns = ['trade_id', 'adv_ann', 'cw_pos',
                   'a', 'a_time',
                   'b', 'b_time',
                   'c', 'c_time',
                   'min', 'min_time',
                   'max', 'max_time',
                   'XA',
                   'entered_trade', 'stopped_trade',
                   'min_in_trade', 'max_in_trade',
                   'result',
                   'enter_price', 'exit_price']
        of = '.'.join([self.full_name, 'csv'])
        with open(of, 'w') as ofh:
            ofh.write(','.join(columns))
            ofh.write('\n')
        
        
    def write_report_for(self, trader):
        '''outputs the info if this trade to ...'''
        FULL_REPORT = False
        def find_original_advice_for(trader):
            '''looks in the different advicelists for the original advice'''
            for adv in (self.removed_adivices_with_trader_attached +
                        self.sim_bear_signals + 
                        self.sim_bull_signals):
                if adv.trader == trader.name:
                    return adv
            print('Trader without advice???')
            raise
        def cond_date(inst):
            '''returns the date if inst not empty else '' '''
            if inst:
                answer = mypy.datetime2format(inst, 
                                              mypy.DATE_TIME_STR)
            else:
                answer = ''
            return answer
        advice = find_original_advice_for(trader)
        try:
            print('testing existings of trader report handel')
            self.trader_report_handle
            print('found: {} type {}'.format(self.trader_report_handle,
                                             type(self.trader_report_handle)))
        except (NameError, ValueError):
            print('self.trader_report_handle not defined')
            return
        if not trader.enter_time and not FULL_REPORT: 
            return
        info = (str(trader.name),
                mypy.datetime2format(advice.first_announced, 
                                     mypy.DATE_TIME_STR),
                str(advice.correction.id),
                str(advice.correction.a),
                mypy.datetime2format(advice.correction.a_time, 
                                     mypy.DATE_TIME_STR),
                str(advice.correction.b),
                mypy.datetime2format(advice.correction.b_time, 
                                     mypy.DATE_TIME_STR),
                str(advice.correction.c),
                mypy.datetime2format(advice.correction.c_time, 
                                     mypy.DATE_TIME_STR),
                str(advice.correction.min),
                mypy.datetime2format(advice.correction.min_time, 
                                     mypy.DATE_TIME_STR),
                str(advice.correction.max),
                mypy.datetime2format(advice.correction.max_time, 
                                     mypy.DATE_TIME_STR),
                cond_date(advice.crossed_a),
                cond_date(trader.enter_time),
                cond_date(trader.exit_time),
                str(trader.min_in_trade) if trader.min_in_trade else '0',
                str(trader.max_in_trade) if trader.max_in_trade else '0',
                str(trader.result) if trader.result else '',
                str(trader.enter_value) if trader.enter_value else '0',
                str(trader.exit_value) if trader.exit_value else '0')
        print(','.join(info), file=self.trader_report_handle)
 

    def get_next_trade_id(self):
        self.trade_id_ += 1
        return self.trade_id_
    
    def call_new_trader(self, name, correction, time_):
        '''Activate and return a new trader'''
        trader = Trader.Trader(name,
                               correction.b, 
                               correction.c,
                               self.TWS_h,
                               self.maximal_stop,
                               self.limit_b_perc,
                               self.stop_taking_positions_daily_at,
                               self.close_all_positions_daily_at,
                               self.min_price_variation,
                               self.future_gap,
                               originator=self.full_name,
                               time_=time_)
        if self.reporter:
            trader.set_reporter(self.reporter, 
                                *self.reporter_settings)
        return trader            

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
        #print('eorth=', self.eorth)
        if self.leave_pos_before_eorth_in_s:
            if self.enter_pos_before_eorth_in_s is None:
                self.enter_pos_before_eorth_in_s = 2 *  self.leave_pos_before_eorth_in_s
            t = mypy.py_timedelta(self.leave_pos_before_eorth_in_s)
            self.leave_pos_before_eorth_in_s = t      
        else:
            self.close_all_positions_daily_at = None
        if self.enter_pos_before_eorth_in_s:
            t = mypy.py_timedelta(self.enter_pos_before_eorth_in_s)
            self.enter_pos_before_eorth_in_s = t
        else:
            self.stop_taking_positions_daily_at = None
        if self.trader_reports:
            self.open_new_file_for_trader_reports()
            of = '.'.join([self.full_name, 'csv'])
            self.trader_report_handle = open(of, 'a', 
                                             buffering=1)
        else:
            self.trader_report_handle = None
        self.trade_id_ = 1
        ### for testing you can remove this anytime
        self.nr_of_sims_old = self.nr_of_tra_old = 0

    def _trade(self, trade_number):
        for trade in self.trade_list:
            if trade.name == trade_number:
                return trade
        return None

    def run(self, curr_data):

        def initialise_new(sim_signals):
            '''Checks for the initial state of new corses'''
            XA_test = {BULL: barData.FIRST_HIGH_HIGHER_THEN,
                       BEAR: barData.FIRST_LOW_LOWER_THEN}
            for signal in sim_signals:
                if signal.status is NEW:
                    # Set NO_C for corse's without a set C
                    if not signal.correction.c:
                        signal.status = NO_C
                    else:
                        #get M(ax) and m(in) since c was set and now
                        zz, M = self.cwh.info(barData.MAXIMUM,
                                              time_ = signal.correction.c_time)
                        zz, m = self.cwh.info(barData.MINIMUM,
                                              time_ = signal.correction.c_time)
                        #check if (and when) a was crossed
                        XA, zz = self.cwh.info(XA_test[signal.direction],
                                               value = signal.correction.a,
                                               time_ = signal.correction.c_time)
                        signal.crossed_a = XA
                        #set status
                        if ((M and M > signal.nominal_max) or
                            (m and m < signal.nominal_min)):
                            signal.status = INVALID
                        elif signal.crossed_a:
                            signal.status = ACTIVE
                        else:
                            signal.status = MONITORING
                    signal.ready_for_removal = True

        def check_monitored_signals(sim_signals):
            '''Checks if the current data is triggering a monitored signal'''
            for signal in sim_signals:
                curr_trader = self._trade(signal.trader)
                if curr_trader:
                    #if there is a trader attached make sure that the status of
                    #the simulator is in sync with the trader
                    trader_status = curr_trader.status
                    if trader_status is Trader.IN_TRADE:
                            signal.status = IN_TRADE
                    elif trader_status in [Trader.STOPPED, Trader.STOPPING]:
                        signal.status = INVALID
                elif signal.status is IN_TRADE:
                    #if no active trader exists but the simulator thinks he's 
                    #IN_TRADE, invalidate the signal
                        signal.status = INVALID
                if signal.status is MONITORING:
                    if ((curr_data.high > signal.nominal_max) or
                        (curr_data.low < signal.nominal_min)):
                        signal.status = INVALID
                    elif ((signal.direction is BULL and
                           curr_data.high > signal.correction.a)
                          or
                          (signal.direction is BEAR and
                           curr_data.low < signal.correction.a)):
                        signal.status = ACTIVE
                        signal.crossed_a = curr_data.time
                signal.ready_for_removal = True  


        def create_trader_for(sim_signals):
            '''Sets the rules for a trade with sim_signals valuea'''
            def send_order(trader, enter_price):
                '''make the trader send (change) an order'''
                if trader.status is Trader.EMPTY:
                    trader.send_order(self.contract, 
                                      self.number_of_contracts,
                                      enter_price,
                                      time_ = curr_data.time, # .time(),
                                      client='SCR2')
                elif trader.status is Trader.MONITORING:
                    trader.send_new_a_value(enter_price,
                                            client='SCR2',
                                            time_ = curr_data.time) # .time())
            ######
            #
            for signal in sim_signals:
                if not signal.trader and signal.status in (MONITORING, ACTIVE):
                    signal.trader = self.get_next_trade_id()
                    new_trader = self.call_new_trader(signal.trader,
                                                      signal.correction,
                                                      time_=curr_data.time)
                    self.trade_list.append(new_trader)
                curr_trader = self._trade(signal.trader)
                if not curr_trader:
                    continue
                if (signal.status is MONITORING and 
                    curr_trader.status is Trader.EMPTY):                    
                    send_order(new_trader, signal.correction.a)
                elif (signal.status is ACTIVE and
                      curr_trader.status in (Trader.EMPTY, Trader.MONITORING)):
                    last_bar = self.cwh.info('last_finished_ochl_bar')
                    curr_bar = self.cwh.info('current_ochl_bar')
                    if last_bar.outside_interval(signal.correction.a,
                                                 signal.correction.c):
                        if not curr_trader.status is Trader.EMPTY:
                            curr_trader.remove_order(client='SCR2', 
                                                     time_=curr_data.time)
                        signal.trailing_bar_price = 0
                    elif False: #not curr_bar.outside_interval(signal.correction.a,
                                #                       signal.correction.c):
                        if signal.trailing_bar_price == 0:
                            price = signal.correction.a
                        if signal.direction is BULL:
                            price = min(last_bar.high, 
                                        signal.trailing_bar_price)
                        else:
                            price = max(last_bar.low, signal.trailing_bar_price)
                        if not price == signal.trailing_bar_price:
                            signal.trailing_bar_price = price
                            send_order(curr_trader, price)
                    else:
                        if signal.trailing_bar_price == 0:
                            price = signal.correction.a
                        else:
                            price = signal.trailing_bar_price
                            if not curr_bar.outside_interval(signal.correction.a,
                                                             signal.correction.c):
                                if signal.direction is BULL:
                                    price = min(last_bar.high, price)
                                else:
                                    price = max(last_bar.low, price)
                                if price == signal.correction.c:
                                    #to catch problems with low volat...
                                    #if vol is to low it can happen that the
                                    #a value becomes equalto c this should never
                                    #happen then you would buy and sell at the
                                    #same time, maybe interesting to introduce
                                    #a variable with the minimum gap bhtween a
                                    #and c??
                                    price = signal.trailing_bar_price
                        if not price == signal.trailing_bar_price:
                            signal.trailing_bar_price = price
                            send_order(curr_trader, price)
                            

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
            

        check_monitored_signals(self.sim_bear_signals)
        check_monitored_signals(self.sim_bull_signals)            
        for trader in self.trade_list:
            trader.update(curr_data)
        create_trader_for(self.sim_bear_signals)
        create_trader_for(self.sim_bull_signals)
        ##### some info #####
        nr_of_sims = len(self.sim_bear_signals)+len(self.sim_bull_signals)
        nr_of_tra = len(self.trade_list)
        #for adv in rawat:
        #    print(adv)
        #    if trad and trad.status is Trader.STOPPED:
        #        adv.status = None
        #        print(adv)
        #rawat = [x for x in rawat if x.status] 
        rawat = self.removed_adivices_with_trader_attached               
        if not nr_of_sims == self.nr_of_sims_old or not nr_of_tra == self.nr_of_tra_old:
            #print('# traders: {}   # sims; {}'.format(nr_of_sims,nr_of_tra))
            #print('# stopped sims  with att trader: {}'.format(len(rawat)))
            #for x in rawat:
            #    print(x)
            #    print(x.trader)
            #    y=self._trade(x.trader)
            #    if y:
            #        print(y.status)
            #    else:
            #        print('trader lost')
            self.nr_of_sims_old = nr_of_sims
            self.nr_of_tra_old = nr_of_tra
            #self.trade_list = [x for x in self.trade_list if not x.status == Trader.STOPPED]
        for trade in self.trade_list:
            if trade.status is Trader.STOPPED:
                self.write_report_for(trade)
                trade.reported = True
        self.trade_list = [x for x in self.trade_list if not x.reported]
        foo = [x for x in rawat if self._trade(x.trader)] 
        self.removed_adivices_with_trader_attached = foo
        
        return True


    def eop_proc(self):
        
        #print('EOD INSTRUCTIONS FOR TRADERS')
        #print('****************************\n')
        for trader in self.trade_list:
            trader.remove_TWS_h()
            trader.reset_previous_bar_info()
            #print('trader {}: {}'.format(trader.name, trader.status))
        #print('****************************\n')
        self.TWS_h = self.future_gap = None
        return True



    
    def restart_traders(self):

        #print(self.contract, self.number_of_contracts)
        for trader in self.trade_list:
            trader.set_TWS_h(self.TWS_h, self.future_gap)
            trader.set_trading_hours(self.stop_taking_positions_daily_at,
                                     self.close_all_positions_daily_at)
            trader.previous_price = None
            if trader.status == Trader.MONITORING:
                trader.contract = self.contract
                trader.number_of_contracts = self.number_of_contracts
            if self.reporter:
                trader.set_reporter(self.reporter, *self.reporter_settings)

