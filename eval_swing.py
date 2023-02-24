#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)

import csv
import math
import os.path
import sys
import pickle
from datetime import timedelta

import mypy

time_ = lambda t:mypy.py_date_time(t, "%Y-%m-%d %H:%M:%S")

################################################################################
# row items
################################################################################
# imported
TRADE_ID = 'trade_id'
ANNOUNCED = 'adv_ann'
CW_POS = 'cw_pos'
A = 'a'
A_TIME = 'a_time'
B = 'b'
B_TIME = 'b_time'
C = 'c'
C_TIME = 'c_time'
MIN = 'min'
MIN_TIME = 'min_time'
MAX = 'max'
MAX_TIME = 'max_time'
XA = 'XA'
ENTER_PRICE = 'price_in'
EXIT_PRICE = 'price_out'
ENTERED = 'entered_trade'
STOPPED = 'stopped_trade'
REASON_IN = 'reason_in'
REASON_OUT = 'reason_out'
MIN_IN_TRADE = 'min_in_trade'
MAX_IN_TRADE = 'max_in_trade'
RESULT = 'result'
DIRECTION = 'direction'
################################################################################
# caculated
CUMM_RESULT = 'cumm_result'
LOOSING_STREAK = 'loosing_streak'
WINNING_STREAK = 'winning_streak'
PERC_GOOD_TRADES = 'perc_good_trades'
MAX_TOTAL_PROFIT_DD = 'max_total_profit_dd'
DRAWDOWN_PERIOD = 'drawdown_period'
TRADE_DURATION = 'trade_duration'
GOOD_TRADES = 'good_trades'
BAD_TRADES = 'bad_trades'
NOMINAL_GAINS = 'nominal_gains'
NOMINAL_LOSSES = 'nominal_losses'
CONSECUTIVE_GAIN = 'consecutive_gain'
CONSECUTIVE_LOSS = 'consecutive_loss'
BULL_TOTAL = 'bull_total'
BEAR_TOTAL = 'bear_total'
BULL_TRADES = 'bull_trades'
WIN_BULL_TRADES = 'winning_bull_trades'
BEAR_TRADES = 'bear_trades'
WIN_BEAR_TRADES = 'winning_bear_trades'

ALL_PARAMETERS = [
                  #TRADE_ID, ANNOUNCED, CW_POS, A, A_TIME, B, B_TIME,
                  #C, C_TIME, MIN, MIN_TIME, MAX, MAX_TIME, XA,
                  ENTERED, STOPPED, 
                  #MIN_IN_TRADE, MAX_IN_TRADE, 
                  ENTER_PRICE, EXIT_PRICE, RESULT,
                  CUMM_RESULT, 
                  REASON_IN, REASON_OUT, 
                  LOOSING_STREAK, WINNING_STREAK, PERC_GOOD_TRADES,
                  MAX_TOTAL_PROFIT_DD, DRAWDOWN_PERIOD, TRADE_DURATION,
                  GOOD_TRADES, BAD_TRADES, NOMINAL_GAINS, NOMINAL_LOSSES,
                  CONSECUTIVE_GAIN, CONSECUTIVE_LOSS, BULL_TOTAL,
                  BEAR_TOTAL, BULL_TRADES, WIN_BULL_TRADES, BEAR_TRADES, 
                  WIN_BEAR_TRADES]

conversions = {TRADE_ID: int,
               ANNOUNCED: time_,
               CW_POS: int,
               A: float,
               B: float,
               C: float,
               A_TIME: time_,
               B_TIME: time_,
               C_TIME: time_,
               MIN: float,
               MAX: float,
               MIN_TIME: time_,
               MAX_TIME: time_,
               XA: time_,
               ENTERED: time_,
               STOPPED: time_,
               MIN_IN_TRADE: float,
               MAX_IN_TRADE: float,
               RESULT: float
               }

available_text_ev=[#('Error in the sample size', 'sample_size_error'),
                   #('Number of quest. trades', 'doubtful_trades'),
                   #('Percentage of quest. trades', 'doubtful_trade_percentage'),
                   #('Quest. trades profit', 'doubtful_profit'),
                   ('Number of trades', 'number_of_trades'),
                   ('Number of good trades', 'total_good_trades'),
                   ('Number of bad trades', 'total_bad_trades'),
                   ('Average good trade', 'average_gain'),
                   ('Average bad trade', 'average_loss'),
                   ('Biggest consecutive gain', 'biggest_consecutive_gain'),
                   ('Biggest consecutive loss', 'biggest_consecutive_loss'),
                   ('Total percentage of good trades',
                    'total_perc_good_trades'),
                   ('Total profit', 'total_profit'),
                   ('Longest loosing streak', 'longest_loosing_streak'),
                   ('Longest Winning streak', 'longest_winning_streak'),
                   ('Biggest total profit ever' , 'biggest_total_profit'),
                   ('Longest drawdown period', 'longest_drawdown'),
                   ('Current drawdown period', 'current_drawdown_period'),
                   ('Biggest drawdown', 'biggest_drawdown'),
                   ('Current drawdown', 'current_drawdown'),
                   ('Biggest loss', 'biggest_loss'),
                   ('Biggest gain', 'biggest_gain'),
                   ('Longest_trade', 'longest_trade'),
                   ('Number of one bar trades', 'one_bar_trades'),
                   ('Number of bear trades', 'number_of_bear_trades'),
                   ('Number of winning bear trades', 
                    'number_of_winning_bear_trades'),
                   ('Percentage of winning bear trades', 
                    'percentage_of_winning_bear'),
                   ('Number of bull trades', 'number_of_bull_trades'),
                   ('Number of winning bull trades',
                    'number_of_winning_bull_trades'),
                   ('Percentage of winning bull trades', 
                    'percentage_of_winning_bull'),
                   ('Profit on bear trades', 'profit_on_bear_trades'),
                   ('Profit on bull trades', 'profit_on_bull_trades')
                   ]


def main():
    filenames = sys.argv[1:]
    days_in_sim = mypy.get_int('Simulator period in days: ',
                               minimum=0)
    multiplier = mypy.get_int('Multiplier (1): ', minimum=1, default=1)
    price_bs = mypy.get_float('Price to buy and sell 1 contract (6): ',
                            minimum=0, default=6)
    margin = mypy.get_int('Margin of contract: ', minimum=0)
    p_max_loss_per_trade = mypy.get_int('Maximal percentage loss per trade (5):',
                                        minimum=1, maximum=100, default=5)
    p_max_loss_on_capital = mypy.get_int('Maximal percentage loss on capital (33):',
                                         minimum=1, maximum=100, default=33)
    pre_filter_on_neg_time_trades = mypy.get_bool(
        'remove trades with a negative time length (Y/n): ', default=True)
    pre_filter_on_length = mypy.get_int(
        'remove trades longer then x seconds: ', default=0)
    strategies = []
    while 1:
        c = [mypy.get_int('pre strategiecode (0 for stop): ',default=0)]
        if not c == [0]:
            while 1:
                a = mypy.get_int('arg (0 for stop): ',default=0)
                if a:
                    c.append(a)
                else:
                    break
            strategies.append(c)
        else:
            break
    write_results = mypy.get_bool('Export info (Y/N)? ', default=False)
    info_exp = ALL_PARAMETERS #[STOPPED, BULL_TOTAL, BEAR_TOTAL] 
    for filename in filenames:
        print('EVALUATING: {}\n'.format(filename))
        e = evalTAW(
            filename,
            remove_negative_time_trades=pre_filter_on_neg_time_trades,
            remove_trades_on_length=pre_filter_on_length,
            enter_strategies_based_on_passed_trades_results=strategies,
        )
        e.set_parameters(days_in_sim,
                         multiplier=multiplier,
                         price_bs=price_bs,
                         margin=margin,
                         p_max_loss_per_trade=p_max_loss_per_trade,
                         p_max_loss_on_capital=p_max_loss_on_capital,
        )
        for info, source in available_text_ev:
            try:
                info += ': {}'.format(eval('e.'+source))
                print(info)
            except ZeroDivisionError:
                continue
        print('\n')
        if multiplier > 0:
            e.print_capital_info()
        if write_results:
            e.write_to_file(info_exp)
        print('\n\n')
            
    #print('Number of trades: {}'.format(e.number_of_trades))
    #print('total percentage of good trades: {}'.format(e.total_perc_good_trades))
    #print('total_profit: {}'.format(e.total_profit))
    #print('longest loosing streak: {}'
          

def transl(row):
    r = dict()
    new_row = {k: (conversions[k](v) if v else None) for k, v in row.items()
               if k in conversions}
    return new_row

def add_basic_info(sheet):
    cumm_sum = 0
    good_trades = bad_trades = 0
    loosing_streak = winning_streak = 0
    consec_gain = consec_loss = 0
    nominal_gains = nominal_losses = 0
    bull_result = bear_result = 0
    bull_trades = bear_trades = 0
    win_bull_trades = win_bear_trades = 0
    max_total_profit_dd = None
    for row in sheet:
        LOSS = row[RESULT] < 0
        # cummulatif sum
        cumm_sum += row[RESULT]
        row[CUMM_RESULT] = cumm_sum
        # bad/good trades
        # winning/loosing streak
        # percentage good trades
        if LOSS:
            bad_trades += 1
            loosing_streak += 1
            winning_streak = 0
            nominal_losses += row[RESULT]
            consec_loss += row[RESULT]
            consec_gain = 0
        else:
            good_trades += 1
            loosing_streak = 0
            winning_streak += 1
            nominal_gains += row[RESULT]
            consec_gain += row[RESULT]
            consec_loss = 0
        row[GOOD_TRADES] = good_trades
        row[BAD_TRADES] = bad_trades
        row[LOOSING_STREAK] = loosing_streak
        row[WINNING_STREAK] = winning_streak
        row[PERC_GOOD_TRADES] = good_trades / ( good_trades + bad_trades)
        row[NOMINAL_GAINS] = nominal_gains
        row[NOMINAL_LOSSES] = nominal_losses
        row[CONSECUTIVE_GAIN] = consec_gain
        row[CONSECUTIVE_LOSS] = consec_loss
        # maximum historical profit
        if not max_total_profit_dd or cumm_sum > max_total_profit_dd:
            max_total_profit_dd = cumm_sum
            max_total_profit_time = row[STOPPED]        
        row[MAX_TOTAL_PROFIT_DD] = max_total_profit_dd
        # time since last maximum profit
        row[DRAWDOWN_PERIOD] = row[STOPPED] - max_total_profit_time
        # length of the trade
        row[TRADE_DURATION] = row[STOPPED] - row[ENTERED]
        if row[DIRECTION] == "long":
            #bull trade
            bull_result += row[RESULT]
            bull_trades += 1
            win_bull_trades += 1 if not LOSS else 0
        else:
            #bear trade
            bear_result += row[RESULT]
            bear_trades += 1
            win_bear_trades += 1 if not LOSS else 0            
        row[BULL_TOTAL] = bull_result
        row[BEAR_TOTAL] = bear_result
        row[BULL_TRADES] = bull_trades
        row[BEAR_TRADES] = bear_trades
        row[WIN_BULL_TRADES] = win_bull_trades
        row[WIN_BEAR_TRADES] = win_bear_trades

def clean(trade_list):
    
    return clean_list, doubt_list
        
        

class evalTAW():
    
    ONLY_ENTER_IF_PREVIOUS_GAIN = 1
    NOMINAL_IN_OUT_MAX_MIN = 2
    
    def __init__(self,filename,
                 remove_negative_time_trades,
                 remove_trades_on_length,
                 enter_strategies_based_on_passed_trades_results):
        if not os.path.exists(filename):
            raise('File doesn\'t exist')
        if filename.endswith('.pck'):
            with open(filename, 'rb') as pickle_file:
                d = pickle.load(pickle_file)
            for x in d:
                print(x)
        else:
            d = []
            with open(filename, 'r') as csvfile:
                c = csv.reader(open(filename))
                for row in c:
                    d.append(row)
        self.trade_list = []
        p_in = False
        current_trade = dict()
        #with open(filename, 'r') as csvfile:
            #d = csv.reader(open(filename))
        for row in d:
            if not p_in:
                p_in = True
                current_trade[ENTER_PRICE] = float(row[5])
                try:
                    current_trade[ENTERED] = time_(row[4])
                except TypeError:
                    current_trade[ENTERED] = row[4]
                current_trade[DIRECTION] = row[2]
                current_trade[REASON_IN] = row[6]
                continue
            if row[2] == current_trade[DIRECTION]:
                print(row[4])
                print("In & out error, 2 X the same direction")
                raise Exception
            current_trade[EXIT_PRICE] = float(row[5])
            current_trade[RESULT] = (current_trade[ENTER_PRICE] -
                                        current_trade[EXIT_PRICE])
            current_trade[RESULT] *= -1 if current_trade[DIRECTION] == 'long' else 1
            try:
                current_trade[STOPPED] = time_(row[4])
            except TypeError:
                current_trade[STOPPED] = row[4]
            current_trade[REASON_OUT] = row[6]
            self.trade_list.append(current_trade)
            current_trade = dict()
            p_in = False
        #self.trade_list.sort(key=lambda x: x[STOPPED])
        print('*** remove strange trades ***')
        if remove_negative_time_trades:
            orig_length = len(self.trade_list)
            self.trade_list = [x for x in self.trade_list if
                               x[STOPPED] > x[ENTERED]]
            removed = orig_length - len(self.trade_list)
            if removed:
                print('{} trades removed for negative trade duration'.
                      format(removed))
            else:
                print('No negative trade durations found')
        if not remove_trades_on_length == 0:
            orig_length = len(self.trade_list)
            self.trade_list = [x for x in self.trade_list if
                    (x[STOPPED] - x[ENTERED]) < timedelta(seconds=remove_trades_on_length)]
            removed = orig_length - len(self.trade_list)
            if removed:
                print('{} trades removed for overtime'.
                      format(removed))
            else:
                print('No to long trades found')                
        print('*****************************')
        for strat in enter_strategies_based_on_passed_trades_results:
            if strat[0] == self.ONLY_ENTER_IF_PREVIOUS_GAIN:
                orig_length = len(self.trade_list)
                print('ONLY_ENTER_IF_PREVIOUS_GAIN')
                new_list = []
                prev_trade_result = self.trade_list.pop(0)[RESULT]
                for trade in self.trade_list:
                    if prev_trade_result > 0:
                        new_list.append(trade)
                    prev_trade_result = trade[RESULT]
                self.trade_list = new_list
                removed = orig_length - len(self.trade_list)
                if removed:
                    print('{} trades not entered becaus previous was loss'.
                          format(removed))
            if strat[0] == self.NOMINAL_IN_OUT_MAX_MIN:
                orig_length = len(self.trade_list)
                print('INOUTMAXMIN')
                stop_trading = strat[1]
                resume_trading = strat[2]
                new_list = []
                trading_alowed = True
                minimum = maximum = total = 0
                for trade in self.trade_list:
                    total += trade[RESULT]
                    if not trading_alowed:
                        minimum = min([minimum, total])
                        if total > minimum + resume_trading:
                            trading_alowed = True
                            maximum = total
                    else:
                        new_list.append(trade)
                        maximum = max([maximum, total])
                        if total < maximum - stop_trading:
                            trading_alowed = False
                            minimum = total
                self.trade_list = new_list
                removed = orig_length - len(self.trade_list)
                               
        
        #self.trade_list, self.d_trades = clean(self.trade_list)
        add_basic_info(self.trade_list)

    def write_to_file(self, column_names=ALL_PARAMETERS, filename='evalTAWout.csv'):
        with open(filename, 'w') as ofh:
            header = {x:x for x in column_names}
            dw = csv.DictWriter(ofh, column_names, extrasaction='ignore')
            dw.writerow(header)
            dw.writerows(self.trade_list)
        
        

    def set_parameters(self,
                       days_in_sim=None,
                       multiplier=None,
                       price_bs=None,
                       margin=None,
                       p_max_loss_per_trade=None,
                       p_max_loss_on_capital=None):
        self.days_in_sim=days_in_sim
        self.multiplier = multiplier
        self.price_bs=price_bs
        self.margin=margin
        self.p_max_loss_per_trade = p_max_loss_per_trade
        self.p_max_loss_on_capital = p_max_loss_on_capital

    @property
    def sample_size_error(self):
        return 1/math.sqrt(len(self.trade_list))

    @property
    def doubtful_trades(self):
        return len(self.d_trades)

    @property
    def doubtful_trade_percentage(self):
        dt = self.doubtful_trades
        return dt / (dt + len(self.trade_list))

    @property
    def doubtful_profit(self):
        return sum([x[RESULT] for x in self.d_trades])

    @property
    def number_of_trades(self):
        return len(self.trade_list)

    @property
    def total_good_trades(self):
        return self.trade_list[-1][GOOD_TRADES]

    @property
    def total_bad_trades(self):
        return self.trade_list[-1][BAD_TRADES]

    @property
    def average_gain(self):
        le = self.trade_list[-1]
        return le[NOMINAL_GAINS] / le[GOOD_TRADES]

    @property
    def average_loss(self):
        le = self.trade_list[-1]
        return le[NOMINAL_LOSSES] / le[BAD_TRADES]

    @property
    def biggest_consecutive_loss(self):
        return min([x[CONSECUTIVE_LOSS] for x in self.trade_list])

    @property
    def biggest_consecutive_gain(self):
        return max([x[CONSECUTIVE_GAIN] for x in self.trade_list])

    @property
    def total_perc_good_trades(self):
        return self.trade_list[-1][PERC_GOOD_TRADES]

    @property
    def total_profit(self):
        return self.trade_list[-1][CUMM_RESULT]

    @property    
    def longest_loosing_streak(self):
        return max([x[LOOSING_STREAK] for x in self.trade_list])

    @property
    def longest_winning_streak(self):
        return max([x[WINNING_STREAK] for x in self.trade_list])

    @property
    def biggest_total_profit(self):
        return self.trade_list[-1][MAX_TOTAL_PROFIT_DD]

    @property
    def longest_drawdown(self):
        return max([x[DRAWDOWN_PERIOD] for x in self.trade_list])

    @property
    def current_drawdown_period(self):
        return self.trade_list[-1][DRAWDOWN_PERIOD]

    @property
    def biggest_drawdown(self):
        h = [x[MAX_TOTAL_PROFIT_DD] - x[CUMM_RESULT] for x in self.trade_list]
        return max(h)

    @property
    def current_drawdown(self):
        le = self.trade_list[-1]
        return le[MAX_TOTAL_PROFIT_DD] - le[CUMM_RESULT]

    @property
    def biggest_loss(self):
        return min([x[RESULT] for x in self.trade_list])

    @property
    def biggest_gain(self):
        return max([x[RESULT] for x in self.trade_list])

    @property
    def longest_trade(self):
        return max([x[TRADE_DURATION] for x in self.trade_list])

    @property
    def one_bar_trades(self):
        return len([1 for x in self.trade_list if not x[TRADE_DURATION]])

    @property
    def profit_on_bull_trades(self):
        return self.trade_list[-1][BULL_TOTAL]

    @property
    def profit_on_bear_trades(self):
        return self.trade_list[-1][BEAR_TOTAL]

    @property
    def number_of_bear_trades(self):
        return self.trade_list[-1][BEAR_TRADES]

    @property
    def number_of_winning_bear_trades(self):
        return self.trade_list[-1][WIN_BEAR_TRADES]

    @property
    def percentage_of_winning_bear(self):
        return self.number_of_winning_bear_trades / self.number_of_bear_trades

    @property
    def number_of_bull_trades(self):
        return self.trade_list[-1][BULL_TRADES]

    @property
    def number_of_winning_bull_trades(self):
        return self.trade_list[-1][WIN_BULL_TRADES]

    @property
    def percentage_of_winning_bull(self):
        return self.number_of_winning_bull_trades / self.number_of_bull_trades
    
    @property
    def current_drawdown_cost(self):
        cost = self.price_bs
        cost *= self.price_bs * (self.longest_drawdown.days +1) / self.days_in_sim
        return cost

    @property
    def cap_for_max_loss_p_per_trade(self):
        cap = self.biggest_loss * self.multiplier * -1
        cap *= 100 / self.p_max_loss_per_trade
        return cap

    @property
    def cap_for_max_loss_on_capital(self):
        cap = self.biggest_drawdown * self.multiplier
        cap += self.current_drawdown_cost
        cap *= 100 / self.p_max_loss_on_capital
        return cap

    @property
    def cap_for_keeping_margin(self):
        cap = self.margin
        cap += self.biggest_drawdown * self.multiplier
        cap += self.current_drawdown_cost
        return cap

    @property
    def capital_to_allocate(self):
        a = self.cap_for_max_loss_p_per_trade
        b = self.cap_for_max_loss_on_capital
        c = self.cap_for_keeping_margin
        cap = max([a, b, c])
        return cap

    @property
    def sim_gain_after_costs(self):
        profit = self.total_profit * self.multiplier
        profit -= self.number_of_trades * self.price_bs
        return profit

    @property
    def sim_gain_after_costs_per_year(self):
        profit = self.sim_gain_after_costs * 365 / self.days_in_sim
        return profit

    def print_capital_info(self):
        print('CAPITAL INFO')
        print('------------')
        print('capital for max loss per trade: {:10.2f}'.format(self.cap_for_max_loss_p_per_trade))
        print('capital for max loss on capital: {:10.2f}'.format(self.cap_for_max_loss_on_capital))
        print('captial for keepint margin: {:10.2f}'.format(self.cap_for_keeping_margin))
        print('CAPITAL TO ALLOCATE: {:10.2f}'.format(self.capital_to_allocate))
        print('profit in sim after costs {:10.2f}'.format(self.sim_gain_after_costs))
        print('sim gain total: {:10.2f}'.format(self.sim_gain_after_costs))
        print('SIM PROFIT PER YEAR: {:10.2f}'.format(self.sim_gain_after_costs_per_year))
        print('RENDEMENT: {:10.2f}%'.format(self.sim_gain_after_costs_per_year / self.capital_to_allocate * 100))
    

if __name__ == '__main__':
    main()

