#!/usr/bin/env python3
#
#  Copyright (c) 2014 Rolf Camps (rolf.camps@scarlet.be)
#
import itertools
from roc_string import SerialTextCreator


# TWO_FALLING_BARS p71-p73
TWO_FB_CASE1 = '2F_1' #1
TWO_FB_CASE2 = '2F_2' #2
TWO_FB_CASE3 = '2F_3' #3
TWO_FB_CASE4 = '2F_4' #4
TWO_FB_CASE5 = '2F_5' #5
TWO_FB_CASE6 = '2F_6' #6
TWO_FALLING_BARS = (
    TWO_FB_CASE1, 
    TWO_FB_CASE2, 
    TWO_FB_CASE3, 
    TWO_FB_CASE4, 
    TWO_FB_CASE5, 
    TWO_FB_CASE6, 
)
# TWO_RISING_BARS p74
TWO_RB_CASE1 = '2R_1' #1
TWO_RB_CASE2 = '2R_2' #2
TWO_RB_CASE3 = '2R_3' #3
TWO_RB_CASE4 = '2R_4' #4
TWO_RB_CASE5 = '2R_5' #5
TWO_RB_CASE6 = '2R_6' #6
TWO_RISING_BARS = (
    TWO_RB_CASE1, 
    TWO_RB_CASE2, 
    TWO_RB_CASE3, 
    TWO_RB_CASE4, 
    TWO_RB_CASE5, 
    TWO_RB_CASE6, 
)

# PAUSES BETWEEN WAVES p80-81
ONE_PLUS_ONE_PAUSE_UP = '1+1 P_UP'
ONE_PLUS_ONE_PAUSE_DOWN = '1+1 P_DOWN'
TWO_PLUS_TWO_PAUSE_UP_1 = '2+2 P_UP1b'
TWO_PLUS_TWO_PAUSE_DOWN_1 = '2+2 P_DOWN1b'
TWO_PLUS_TWO_PAUSE_UP_2 = '2+2 P_UP2b'
TWO_PLUS_TWO_PAUSE_DOWN_2 = '2+2 P_DOWN2b'
PAUSE_UPS = (
    ONE_PLUS_ONE_PAUSE_UP,
    TWO_PLUS_TWO_PAUSE_UP_1,
    TWO_PLUS_TWO_PAUSE_UP_2,)
PAUSE_DOWNS = (
    ONE_PLUS_ONE_PAUSE_DOWN,
    TWO_PLUS_TWO_PAUSE_DOWN_1,
    TWO_PLUS_TWO_PAUSE_DOWN_2,)

# PAUSES HELPERS
TRIGGERED_BY_ONE_BAR = 0 #'one bar'
TRIGGERED_BY_TWO_BARS = 1 #'two bars'

# PAUSE ANALYSIS
P_OK = 'P CONFIRMED'
P_STARTED_BEFORE_WAVE = 'P BEFORE W'
P_STARTED_BEFORE_SWAVE = 'P BEFORE SW'
P_STARTED_BEFORE_SWAVE_CAN = 'P BEFORE SWc'
P_STARTED_AT_WRONG_INDEX = 'P @ WRONG I'
P_WAVE_TO_OLD = 'P WAVE OLD'
NO_P_SWAVE_OK = 'NO P SW OK'
NO_P_START_MISMATCH = 'NO P <> STRT'

#SWAVE TYPES
SWAVE_UP_CANDIDATE = 'swave up ?'
SWAVE_UP = 'swave up'
SWAVE_DOWN_CANDIDATE = 'swave down ?'
SWAVE_DOWN = 'swave down'
SWAVE_PAUSE = 'swave pause'

# MARKET
DECREASING = 'decreasing'
RISING = 'rising'
NEUTRAL = 'neutral'
OVERBOUGHT = 'overbought'
OVERSOLD = 'oversold'

# MARKET RATE OF CHANGE
INCREASING = 'increasing'
SLOWING = 'slowing'
CONSTANT = 'constant'
ACCELARATING = 'accelarating'
DECELARATING = 'decelarating'

# MARKET FORECAST
TOPPING_OF = 'topping of'

# TREND
RISING = 'rising'
FALLING = 'falling'

# STOCHASTIC
STOCHASTIC_A = 'A'
STOCHASTIC_B = 'B'
GHOST_A = 'g_A'
GHOST_B = 'g_B'
STOCH_A_GA_TO_STOCH_B_GB = 'A TO B' # 0
STOCH_B_GB_TO_STOCH_A_GA = 'B TO A' # 1

# MACD
TURNED_POS = 'postive'
TURNED_NEG = 'negative'
PULLBACK_AFTER_RISING_W_OR_T = 'pullback after rising wave or thrust'
REBOUND_AFTER_FALLING_W_OR_T = 'rebound after falling wave or thrust'

# BOLIBA
UPPER_HOLDS = 'upper'
LOWER_HOLDS = 'lower'

# SOME SELF INVENTED ORDERING OF BARS, compare curr with previous
BASIC_UP_BAR = 'U'      # curr_bar > prev_bar
BASIC_DOWN_BAR = 'D'    # curr_bar < prev_bar
BASIC_SAME_BAR = '='    # curr.high = prev.high & curr.low = prev.low
BASIC_OPEN_BAR = 'O'    # curr.high > prev.high & curr.low < prev.low
BASIC_ENCAPSULATED_BAR = '-'  # curr.high < prev.high & curr.low >prev.low

CP_UPWAVE_DEBUG = 1
CP_DOWNWAVE_DEBUG = 2
CP_WAVE_DEBUG = 3 # SET WITH UPWAVE AND DOWNWAVE DEBUG !!
CI_AFTER_CALCULATE = 4
CI_WARNING = 5

CONDITIONAL_PRINT = {
    #CP_UPWAVE_DEBUG, 
    #CP_DOWNWAVE_DEBUG,
    #CP_WAVE_DEBUG,
}

def cond_print(flag, *arg_l, **kw_d):
    if flag in CONDITIONAL_PRINT:
        print(*arg_l, **kw_d)
        
def cond_input(flag, *arg_l, **kw_d):
    if flag in CONDITIONAL_PRINT:
        input(*arg_l, **kw_d)
        
class Basics():
    
    LEN = 0
    SUPPORT = 1
    RESISTANCE =2
    RELBAR = 3
    SPOTTED_MOVE = 5
    STRICT_UP = 6    # <
    LOOSE_UP = 7     # < keep these in order and consecutive number
    R_UP = 8         # < check:
    STRICT_DOWN = 9  # <    caclulate_nr_of_directional_moves
    LOOSE_DOWN = 10  # < if changed
    R_DOWN = 11      # <
    W_UP = 23
    W_DOWN = 24
    SPOTTED_PAUSE = 12
    W_UP_W_AND_P_EXTREMES = 13
    W_UP_W_AND_P_LENGTHS = 14
    W_UP_W_AND_P_TYPES = 15
    W_UP_W_AND_P_INDEXES = 16
    W_DOWN_W_AND_P_EXTREMES = 17
    W_DOWN_W_AND_P_LENGTHS = 18
    W_DOWN_W_AND_P_TYPES = 19
    W_DOWN_W_AND_P_INDEXES = 20
    W_UP_W_AND_P_TIMES = 21
    W_DOWN_W_AND_P_TIMES = 22
    W_UP = 23
    W_DOWN = 24
    USED_UP_DOWN_RULE = 25
  
    
    info = [
        'LEN',
        'SUPPORT', 
        'RESISTANCE', 
        'RELBAR',
        'SPOTTED_MOVE',
        'STRICT_UP',
        'LOOSE_UP',
        'R_UP',
        'STRICT_DOWN',
        'LOOSE_DOWN',
        'R_DOWN',
        'SPOTTED_PAUSE',
        'W_UP_START_INDEX',
        'W_UP_LOW',
        'W_UP_HIGH',
        'W_UP_W_AND_P_LENGTHS',
        'W_UP_W_AND_P_EXTREMES',
        'W_UP_SWAVE_HIGH',
        'W_UP_SWAVE_LOW',
        'W_UP_W_AND_P_TYPES',
        'W_UP',
        'W_DOWN',
        'USED_UP_DOWN-RULE',
    ]
    
    def __init__(self, r):
        #self.name = 'BASICS'
        self.r = r  # lookback for r count
        self.interval_name = None
        self.name = self.make_name(self.r)
        self.tolerance = 0
    
    @staticmethod    
    def make_name(r):
        return 'BASICS {}'.format(r)
        
    def calculate(self, bar_list, prev_results):
        cond_print(CP_WAVE_DEBUG, "<< {} >>".format(self.interval_name))
        cond_print(CP_WAVE_DEBUG, bar_list[-1])
        nr_of_bars_available = len(bar_list)
        #)
        strict_up, strict_down, loose_up, loose_down, r_up, r_down = (
            self.caclulate_nr_of_directional_moves(
                bar_list, prev_results, self.r, nr_of_bars_available)
        )
        rel_bar_position, i_list = (
            self.calculate_rel_bar_postition(bar_list, prev_results)
        )
        spotted_move = self.spot_move(bar_list, nr_of_bars_available)
        #)
        spotted_pause, pause_start = (
            self.spot_pause(
                bar_list, prev_results, spotted_move, nr_of_bars_available)
        )        
        support, resistance = (
            self.calculate_support_resistance(
                bar_list, prev_results, spotted_move, nr_of_bars_available)
        )
        (wu_waves_and_pauses_extremes, wu_waves_and_pauses_lengths, 
         wu_waves_and_pauses_types, wu_waves_and_pauses_indexes,
         wu_waves_and_pauses_times, wu_pause_analysis) = (
             self.calculate_wave_up_info(
                 bar_list, prev_results, 
                 spotted_move, spotted_pause, pause_start, self.tolerance)
        )
        if (wu_waves_and_pauses_types[0]):
            cond_print(CP_WAVE_DEBUG,'    ',wu_waves_and_pauses_types)
            cond_print(CP_WAVE_DEBUG,'    ',wu_waves_and_pauses_indexes)
            cond_print(CP_WAVE_DEBUG,'    ',wu_waves_and_pauses_extremes)
            cond_print(CP_WAVE_DEBUG,'    ',wu_waves_and_pauses_lengths)
            if not len(wu_waves_and_pauses_extremes) - 1 == len(wu_waves_and_pauses_types) == len(wu_waves_and_pauses_lengths):
                raise Exception('wrong list lengths')
        (du_waves_and_pauses_extremes, du_waves_and_pauses_lengths, 
         du_waves_and_pauses_types, du_waves_and_pauses_indexes,         
         du_waves_and_pauses_times, du_pause_analysis) = (
             self.calculate_wave_down_info(
                 bar_list, prev_results, 
                 spotted_move, spotted_pause, pause_start, self.tolerance)
        )
        if (du_waves_and_pauses_types[0]):
            cond_print(CP_WAVE_DEBUG,'    ',du_waves_and_pauses_types)
            cond_print(CP_WAVE_DEBUG,'    ',du_waves_and_pauses_indexes)
            cond_print(CP_WAVE_DEBUG,'    ',du_waves_and_pauses_extremes)
            cond_print(CP_WAVE_DEBUG,'    ',du_waves_and_pauses_lengths)
            if not len(du_waves_and_pauses_extremes) - 1 == len(du_waves_and_pauses_types) == len(du_waves_and_pauses_lengths):
                raise Exception('wrong list lengths')
        w_up, w_down, up_down_rule = self.calculate_wavecounts_up_and_down_tryout(
            wu_waves_and_pauses_types, wu_waves_and_pauses_indexes,
            du_waves_and_pauses_types, du_waves_and_pauses_indexes,
        )
        cond_input(CI_AFTER_CALCULATE, '')
        return (
            nr_of_bars_available, 
            support, resistance, 
            rel_bar_position, i_list,
            spotted_move,
            strict_up, loose_up, r_up,
            strict_down, loose_down, r_down,
            spotted_pause,
            wu_waves_and_pauses_extremes, 
            wu_waves_and_pauses_lengths,
            wu_waves_and_pauses_types,
            wu_waves_and_pauses_indexes,
            du_waves_and_pauses_extremes, 
            du_waves_and_pauses_lengths,
            du_waves_and_pauses_types,
            du_waves_and_pauses_indexes,
            wu_waves_and_pauses_times,
            du_waves_and_pauses_times,
            w_up, w_down, up_down_rule,
        )
    
    @staticmethod
    def caclulate_nr_of_directional_moves(
            bar_list, prev_results, r, nr_of_bars_available):
        if prev_results:
            s_u, s_d, l_u, l_d, r_u, r_d = (
                prev_results[-1][Basics.STRICT_UP:Basics.R_DOWN + 1])
        else:
            return 0, 0, 0, 0, 0, 0
        before_last_bar, last_bar = bar_list[-2], bar_list[-1]
        r_bar = bar_list[-r] if nr_of_bars_available >= r else False
        if last_bar > before_last_bar:
            s_u, s_d = s_u + 1, 0
        if last_bar >= before_last_bar:
            l_u += 1
        if r_bar and last_bar.close > r_bar.close:
            r_u, r_d = r_u + 1, 0
        if last_bar < before_last_bar:
            s_u, s_d = 0, s_d + 1
        if last_bar <= before_last_bar:
            l_d += 1
        if r_bar and last_bar.close < r_bar.close:
            r_u, r_d = 0, r_d + 1
        if l_u > l_d:
            l_d = 0
        else:
            l_u = 0
        #if r_u == 9 or r_d == 9:
            #input('R9!!')
        return s_u, s_d, l_u, l_d, r_u, r_d
    
    @staticmethod
    def calculate_wavecounts_up_and_down(
            u_types, u_indexes, d_types, d_indexes):
        up_count = down_count = 0
        if u_types:
            #print('UP')
            #print(u_types, u_indexes)
            for x, count in zip(reversed(u_types), reversed(u_indexes)):
                if x == 'swave up':
                    up_count = count
                    #print('.....', up_count)
                    break
        if d_types:
            #print('DOWN')
            #print(d_types, d_indexes)
            for x, count in zip(reversed(d_types), reversed(d_indexes)):
                if x == 'swave down':
                    down_count = count
                    #print('.....', down_count)
                    break
        if 0 < up_count < down_count:
            down_count = 0
        if 0 < down_count < up_count:
            up_count = 0
        Basics.calculate_wavecounts_up_and_down_tryout(
                    u_types, u_indexes, d_types, d_indexes)       
        print('sending down: {}    up:{}'.format(down_count, up_count))
        return up_count, down_count
    
    @staticmethod
    def calculate_wavecounts_up_and_down_tryout(
            u_types, u_indexes, d_types, d_indexes):
        def select_from(*bar_nr_list):
            l = list(bar_nr_list)
            l.sort()
            while (len(l) > 1                               and
                   (l[0] < 3 
                    or 
                    l[0] + 2 == l[1]
                    or
                    l[0] == l[1])
            ):
                l.pop(0)
            return l[0] if l else 0
        def nnnn():
            return 0, 0, 'all None'
        def nnnu():
            ud_selection = 'nnnu'
            up = select_from(
                u_indexes[0],
            )
            down = 0
            return up, down, ud_selection
        def nnud():
            ud_selection = 'nnud'
            long_u_list = len(u_indexes) > 2
            up = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_list else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_list else 0,
            )
            return up, down, ud_selection
        def nndu():
            ud_selection = 'nndu'
            long_u_list = len(u_indexes) > 3
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_list else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_list else 0,
                )
            return up, down, ud_selection
        def udnn():
            ud_selection = 'udnn'
            long_d_list = len(d_indexes) > 3
            up = select_from(
                d_indexes[-2],
                d_indexes[-4] if long_d_list else 0,
            )
            down = select_from(
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_list else 0,
            )
            return up, down, ud_selection
        def udud():
            ud_selection = 'udud'
            long_u_list = len(u_indexes) > 3
            long_d_list = len(d_indexes) > 3
            up = select_from(
                d_indexes[-2],
                d_indexes[-4] if long_d_list else 0,
                u_indexes[-2],
                u_indexes[-4] if long_u_list else 0,
            )
            down = select_from(
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_list else 0,
                u_indexes[-1],
                u_indexes[-3] if long_u_list else 0,
            )
            return up, down, ud_selection
        def udu_():
            ud_selection = 'udu_'
            long_u_list = len(u_indexes) > 2
            long_d_list = len(d_indexes) > 3
            up = select_from(
                #u_indexes[-1],
                u_indexes[-2],
                u_indexes[-4] if long_u_list else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_list else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_list else 0,
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_list else 0,
            )
            return up, down, ud_selection
        def udd_():
            ud_selection = 'udd_'
            long_u_list = len(u_indexes) > 3
            long_d_list = len(d_indexes) > 3
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_list else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_list else 0,                          
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_list else 0,
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_list else 0,
            )
            return up, down, ud_selection
        def nnu_():
            ud_selection = 'nnu_'  
            long_u_list = len(u_indexes) > 2
            up = select_from(
                #u_indexes[-1],
                u_indexes[-2],
                u_indexes[-4] if long_u_list else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_list else 0,
            )
            return up, down, ud_selection
        def nnd_():
            ud_selection = 'nnd_'
            long_u_list = len(u_indexes) > 3
            up = select_from(
                #u_indexes[-1],
                u_indexes[-2],
                u_indexes[-5] if long_u_list else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_list else 0,
            )
            return up, down, ud_selection
        def ndnn():
            ud_selection = 'ndnn'
            up = 0
            down = select_from(
                d_indexes[-1],
            )
            return up, down, ud_selection
        def ndud():
            ud_selection = 'ndud'
            long_u_selection = len(u_indexes) > 2
            up = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_selection else 0,
                d_indexes[-1],
            )
            return up, down, ud_selection
        def ndu_():
            ud_selection = 'ndu_'
            long_u_selection = len(u_indexes) > 2
            up = select_from(
                #u_indexes[-1],
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_selection else 0,
                d_indexes[-1],
            )
            return up, down, ud_selection
        def ndd_():
            ud_selection = 'ndd_'
            long_u_selection = len(u_indexes) > 3
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_selection else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-1],
            )
            return up, down, ud_selection
        def u_nn():
            ud_selection = 'u_nn'
            long_d_selection = len(d_indexes) > 3
            up = select_from(
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            down = select_from(
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def u_nu():
            ud_selection = 'u_nu'
            long_d_selection = len(d_indexes) > 3
            up = select_from(
                u_indexes[-1],
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            down = select_from(
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_selection else 0,)
            return up, down, ud_selection
        def u_ud():
            ud_selection = 'u_ud'
            long_u_selection = len(u_indexes) > 2
            long_d_selectoin = len(d_indexes) > 3
            up = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selectoin else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_selectoin else 0,
            )
            return up, down, ud_selection
        def dunu():
            ud_selection = 'dunu'
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-1],
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def d_nn():
            ud_selection = 'd_nn'
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def d_nu():
            ud_selection = 'd_nu'
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-1],
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )   
            return up, down, ud_selection
        def duu_():
            ud_selection = 'duu_'
            long_u_selection = len(u_indexes) > 2
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def dudu():
            ud_selection = 'dudu'
            long_u_selection = len(u_indexes) > 3
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def dud_():
            ud_selection = 'dud_'
            long_u_selection = len(u_indexes) > 3
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def d_ud():
            ud_selection = 'd_ud'
            long_u_selection = len(u_indexes) > 2
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def u_u_():
            ud_selection = 'u_u_'
            long_u_selection = len(u_indexes) > 2
            long_d_selection = len(d_indexes) > 3
            up = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def u_du():
            ud_selection = 'u_du'
            long_u_selection = len(u_indexes) > 3
            long_d_selection = len(d_indexes) > 3
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def u_d_():
            ud_selection = 'u_d_'
            long_u_selection = len(u_indexes) > 3
            long_d_selection = len(d_indexes) > 3
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3],
                d_indexes[-5] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def dunn():
            ud_selection = 'dunn'
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                d_indexes[-2],
                d_indexes[-4] if long_d_selection > 2 else 0,
            )
            return up, down, ud_selection
        def d_u_():
            ud_selection = 'd_u_'
            long_u_selection = len(u_indexes) > 2
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-1],
                u_indexes[-3] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def d_du():
            ud_selection = 'd_du'
            long_u_selection = len(u_indexes) > 3
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        def d_d_():
            ud_selection = 'd_d_'
            long_u_selection = len(u_indexes) > 3
            long_d_selection = len(d_indexes) > 2
            up = select_from(
                u_indexes[-1],
                u_indexes[-3],
                u_indexes[-5] if long_u_selection else 0,
                d_indexes[-1],
                d_indexes[-3] if long_d_selection else 0,
            )
            down = select_from(
                u_indexes[-2],
                u_indexes[-4] if long_u_selection else 0,
                d_indexes[-2],
                d_indexes[-4] if long_d_selection else 0,
            )
            return up, down, ud_selection
        ########################################################################
        ud_dict = {
        #   (d-2, d-1, u-2,u-1),
            (None, None, None, None): nnnn,
            (None, None, None, 'swave up'): nnnu,
            (None, None, 'swave up', 'swave down'): nnud,
            (None, None, 'swave up', 'swave up ?'): nnu_,
            (None, None, 'swave down', 'swave up'): nndu,
            (None, None, 'swave down', 'swave up ?'): nnd_,
            (None, 'swave down', None, None): ndnn,
            (None, 'swave down', 'swave up', 'swave down'): ndud,
            (None, 'swave down', 'swave up', 'swave up ?'): ndu_,
            (None, 'swave down', 'swave down', 'swave up ?'): ndd_,
            ('swave up', 'swave down', None, None): udnn,
            ('swave up', 'swave down', 'swave up', 'swave down'): udud,
            ('swave up', 'swave down', 'swave up', 'swave up ?'): udu_,
            ('swave up', 'swave down', 'swave down', 'swave up ?'): udd_,
            ('swave up', 'swave down ?', None, None): u_nn,
            ('swave up', 'swave down ?', None, 'swave up'): u_nu,
            ('swave up', 'swave down ?', 'swave up', 'swave down'): u_ud,
            ('swave up', 'swave down ?', 'swave up', 'swave up ?'): u_u_,
            ('swave up', 'swave down ?', 'swave down', 'swave up'): u_du,
            ('swave up', 'swave down ?', 'swave down', 'swave up ?'): u_d_,
            ('swave down', 'swave up', None, None): dunn,
            ('swave down', 'swave up', None, 'swave up'): dunu,
            ('swave down', 'swave up', 'swave up', 'swave up ?'): duu_,
            ('swave down', 'swave up', 'swave down', 'swave up'): dudu,
            ('swave down', 'swave up', 'swave down', 'swave up ?'): dud_,
            ('swave down', 'swave down ?', None, None): d_nn,
            ('swave down', 'swave down ?', None, 'swave up'): d_nu,
            ('swave down', 'swave down ?', 'swave up', 'swave down'): d_ud,
            ('swave down', 'swave down ?', 'swave up', 'swave up ?'): d_u_,
            ('swave down', 'swave down ?', 'swave down', 'swave up'): d_du,
            ('swave down', 'swave down ?', 'swave down', 'swave up ?'): d_d_,
        }
        try:
            up, down, ud_selecion = ud_dict[
                (d_types[-2] if len(d_types) > 1 else None,
                 d_types[-1],
                 u_types[-2] if len(u_types) > 1 else None,
                 u_types[-1])]()
            if not (isinstance(up, int) and isinstance(down, int)):
                print('selection: {} | up: {} | down: {}'.format(
                                                ud_selecion, up, down))
                raise KeyError('whawhawha')
        except KeyError:
            print(
                (d_types[-2] if len(d_types) > 1 else None,
                 d_types[-1],
                 u_types[-2] if len(u_types) > 1 else None,
                 u_types[-1]))
            print('D:', d_types, d_indexes, '\nU:',u_types, u_indexes)
            exit()
        return up, down, ud_selecion
        ########################################################################
        last_u_type, last_d_type = u_types[-1], d_types[-1]
        last_u_index, last_d_index = u_indexes[-1], d_indexes[-1]
        #print(u_types, '|', u_indexes)
        #print(d_types, '|', d_indexes)
        if last_d_type is None and last_u_type is None:
            up = down = 0
            ud_rule = 'None None'
        elif last_u_type == 'swave down':
            up = u_indexes[-2]
            if last_d_type == 'swave down' and len(d_types) == 1 and last_d_index > 2:
                down = last_d_index
                ud_rule = 'A'
            elif (last_d_type == 'swave down ?' and d_types[-2] == 'swave down' and
                  (last_u_index - d_indexes[-2]) > 2):
                down = d_indexes[-2]
                ud_rule = 2
            elif (last_d_type == 'swave down ?' and d_types[-2] == 'swave down' and
                  (last_u_index - last_d_index) > 2):
                down = last_d_index if last_d_index > 1 else last_u_index
                ud_rule = '2_1'
            elif (last_d_type== 'swave down ?' and u_types[-2] == 'swave up' and
                  (u_indexes[-2] - d_indexes[-2]) < 3):
                up, down = u_indexes[-2], last_u_index
                ud_rule = '2_2'
            else:
                down = last_u_index
                ud_rule = 3
        elif last_d_type == 'swave up':
            down = d_indexes[-2]
            if last_u_type == 'swave up' and len(u_types) == 1 and last_u_index > 2:
                up = last_u_index
                ud_rule = 4
            elif (last_u_type == 'swave up ?' and u_types[-2] == 'swave up' and
                  (last_d_index - u_indexes[-2]) > 2):
                up = u_indexes[-2]
                ud_rule = 5
            elif (last_u_type == 'swave up ?' and u_types[-2] == 'swave up' and
                  (last_d_index - last_u_index) > 2):
                up = last_u_index if last_u_index > 2 else last_d_index
                ud_rule = '5_1'
            elif (last_u_type== 'swave up ?' and d_types[-2] == 'swave down' and
                  (d_indexes[-2] - u_indexes[-2]) < 3):
                up, down = last_d_index, d_indexes[-2]
                ud_rule = '5_2'
            else:
                up = last_d_index
                ud_rule = 6
        elif last_d_type is None and not len(u_types) % 2:
            up, down = u_indexes[-2], last_u_index
            ud_rule = 7
        elif last_u_type is None and not len(d_types) % 2:
            up, down = last_d_index, d_indexes[-2]
            ud_rule = 8
        elif last_d_type is None and len(u_types) > 1:
            if (last_u_type == 'swave up ?'                           and
                u_types[-2] == 'swave down'):
                up, down = last_u_index, u_indexes[-2]
                ud_rule = 9
            else:
                up, down = 0, u_indexes[-2]
                ud_rule = 10
        elif last_u_type is None and len(d_types) > 1:
            if (last_d_type == 'swave down ?'                         and
                d_types[-2] == 'swave up'):
                up, down = d_indexes[-2], last_d_index
                ud_rule = 11
            else:
                up, down = d_indexes[-2], 0
                ud_rule = 12
        elif last_u_type == 'swave up ?' and last_u_index == 1:
            #print(u_types)
            if not len(u_types) % 2:
                if last_d_type == 'swave down ?':
                    up, down = last_d_index, d_indexes[-2]
                    ud_rule = 13
                else:
                    up = u_indexes[-2]
                    down = u_indexes[-3] if len(u_indexes) > 2 else 0
                    ud_rule = 14
            else:
                if last_d_type == 'swave down ?':
                    up, down = u_indexes[-3], u_indexes[-2]
                    ud_rule = 141
                else:
                    down = u_indexes[-2]
                    up = u_indexes[-3]
                    ud_rule = 15
        elif last_d_type == 'swave down ?' and last_d_index == 1:
            #print(d_types)
            if not len(d_types) % 2:
                if last_u_type == 'swave up ?':
                    up, down = u_indexes[-2], last_u_index
                    ud_rule = 16
                else:
                    down = d_indexes[-2]
                    up = d_indexes[-3] if len(d_indexes) > 2 else 0
                    ud_rule = 17
            else:
                if last_u_type == 'swave up ?':
                    up, down = u_indexes[-2], d_indexes[-3]
                    ud_rule = 171
                else:
                    up = d_indexes[-2]
                    down = d_indexes[-3]
                    ud_rule = 172
        elif last_d_type == None and last_u_type == 'swave up':
            up, down = last_u_index, 0 
            ud_rule = 18
        elif last_u_type == None and last_d_type == 'swave down':
            up, down = 0, last_d_index
            ud_rule = 19
        elif last_d_type == 'swave down' and last_u_type == 'swave up ?':
            up, down = last_u_index, last_d_index
            ud_rule = 20
        elif last_u_type == 'swave up' and last_d_type == 'swave down ?':
            up, down = last_u_index, last_d_index
            ud_rule = 21
        elif last_d_type == 'swave down ?' and last_u_type == 'swave up ?':
            if d_types[-2] == 'swave up':
                up = d_indexes[-2]
                if (u_types[-2] == 'swave down'                       and
                    (last_d_index - u_indexes[-2]) > 2):
                    down = u_indexes[-2]
                    ud_rule = 22
                elif (u_types[-2] == 'swave up'                       and
                      (up - u_indexes[-2]) > 2):
                    up, down = u_indexes[-2], last_d_index
                    ud_rule = 221
                else:
                    down = last_d_index
                    ud_rule = 222
            elif u_types[-2] == 'swave down':
                if (d_types[-2] == 'swave down'                       and
                      (u_indexes[-2] - d_indexes[-2]) > 2):
                    up, down = last_u_index, d_indexes[-2]
                    ud_rule = 23
                else:
                    up, down = last_u_index, u_indexes[-2]
                    ud_rule = 231
            else:
                #input('check ? ?')
                up, down = u_indexes[-1], d_indexes[-1]
                ud_rule = 24
        else:
            input('check')
            up = down = '???'
            ud_rule = '???'
        #print('try down: {}    up:{}'.format(down, up))
        return up, down, ud_rule
        
        
    @staticmethod
    def spot_move(bar_list, nr_of_bars_available):
        spotted_move = False
        if nr_of_bars_available > 2:
            a, b, c = bar_list[-3:]
            spotted_move = (
                Basics.two_bars_down_p(a, b, c)
                or 
                Basics.two_bars_up_p(a, b, c)
            )
        return spotted_move
    
    @staticmethod
    def spot_pause(bar_list, prev_results, spotted_move, nr_of_bars_available):
        spotted_pause = first_cond_index = False
        if nr_of_bars_available > 2:
            a, b, c = bar_list[-3:]
            spotted_pause, first_cond_index = (
                Basics.pause_up_1_plus_1_p(a, b, c) 
                or 
                Basics.pause_down_1_plus_1_p(a, b, c)
            )
        if nr_of_bars_available > 5 and not spotted_pause:
            spotted_pause, first_cond_index = (
                (spotted_move in TWO_RISING_BARS                       and
                 Basics.two_plus_two_pause_up_p(bar_list, prev_results))
                or
                (spotted_move in TWO_FALLING_BARS                      and
                 Basics.two_plus_two_pause_down_p(bar_list, prev_results))
                or
                (False, False)
            )
        return spotted_pause, first_cond_index
        
        
    @staticmethod    
    def calculate_support_resistance(
            bar_list, prev_results, spotted_move, nr_of_bars_available):
        resistance, support = None, None
        if prev_results:
            resistance = prev_results[-1][Basics.RESISTANCE]
            support = prev_results[-1][Basics.SUPPORT]
        last_bar = bar_list[-1]
        if resistance and last_bar.high > resistance:
            resistance = None
        if support and last_bar.low < support:
            support = None
        if spotted_move in TWO_FALLING_BARS:
            new_resistance = 0
            for c, bar in enumerate(reversed(bar_list), 1):
                if c == nr_of_bars_available:
                    break
                new_resistance = max(new_resistance, bar.high)
                c_move = prev_results[-c][Basics.SPOTTED_MOVE]
                if c_move in TWO_FALLING_BARS:
                    break
                if c_move in TWO_RISING_BARS:
                    resistance = max(new_resistance,
                                     bar_list[-c-1].high, 
                                     bar_list[-c-2].high)
                    break
        if spotted_move in TWO_RISING_BARS:
            new_support = last_bar.low
            for c, bar in enumerate(reversed(bar_list), 1):
                if c == nr_of_bars_available:
                    break
                new_support = min(new_support, bar.low)
                c_move = prev_results[-c][Basics.SPOTTED_MOVE]
                if c_move in TWO_RISING_BARS:
                    break
                if c_move in TWO_FALLING_BARS:
                    support = min(new_support,
                                  bar_list[-c-1].low,
                                  bar_list[-c-2].low)
                    break
        return support, resistance
    
    @staticmethod    
    def calculate_rel_bar_postition(bar_list, prev_results):
        i_list = prev_results[-1][4] if prev_results else [-2,]
        new_i_list = []
        rel_pos = ''
        curr_bar = bar_list[-1]
        if len(bar_list) == 1:
            return ' ', i_list
        for index in i_list:
            control_bar = bar_list[index]
            if curr_bar > control_bar:
                rel_pos += BASIC_UP_BAR
                break
            if curr_bar < control_bar:
                rel_pos += BASIC_DOWN_BAR
                break
            if control_bar.high_low_equal(curr_bar):
                rel_pos += BASIC_SAME_BAR
                break
            if curr_bar.spans(control_bar):
                rel_pos += BASIC_OPEN_BAR
                break
            rel_pos += BASIC_ENCAPSULATED_BAR
            new_i_list.append(index -1)
        new_i_list.append(-2)
        return rel_pos, new_i_list
    
    @staticmethod
    def calculate_wave_up_info(
            bar_list, prev_results, spotted_move, 
            spotted_pause, pause_start, tolerance):
        #return Basics.no_wave()
        last_bar = bar_list[-1]
        if not prev_results:
            return Basics.no_wave()
        prev_result = list(prev_results[-1])
        ####
        waves_and_pauses_extremes = prev_result[Basics.W_UP_W_AND_P_EXTREMES]
        waves_and_pauses_lengths = prev_result[Basics.W_UP_W_AND_P_LENGTHS]
        waves_and_pauses_types = prev_result[Basics.W_UP_W_AND_P_TYPES]
        waves_and_pauses_indexes = prev_result[Basics.W_UP_W_AND_P_INDEXES]
        waves_and_pauses_times = prev_result[Basics.W_UP_W_AND_P_TIMES]
        prev_result[Basics.W_UP_W_AND_P_EXTREMES] = waves_and_pauses_extremes[:]
        prev_result[Basics.W_UP_W_AND_P_LENGTHS] = waves_and_pauses_lengths[:]
        prev_result[Basics.W_UP_W_AND_P_TYPES] = waves_and_pauses_types[:]
        prev_result[Basics.W_UP_W_AND_P_INDEXES] = waves_and_pauses_indexes[:]
        prev_result[Basics.W_UP_W_AND_P_TIMES] = waves_and_pauses_times[:]
        #########
        # run studie
        ##########
        ####
        swave_type = waves_and_pauses_types[-1]
        pause_analysis = None
        if swave_type is None:
            if spotted_move in TWO_RISING_BARS:
                return Basics.start_up_wave(bar_list)
            else:
                return Basics.no_wave()
        # SWAVE UP
        elif swave_type is SWAVE_UP:
            if spotted_pause in PAUSE_DOWNS:
                pause_analysis = NO_P_SWAVE_OK
            if spotted_move in TWO_RISING_BARS:
                return Basics.uw_usw_add_up_bar(
                    bar_list, prev_result, pause_analysis)
            if spotted_move in TWO_FALLING_BARS:
                return Basics.uw_usw_add_two_falling_bars(
                    bar_list, prev_result, tolerance, pause_analysis)
            return Basics.uw_usw_undefined_bar(
                bar_list, prev_result, tolerance, pause_analysis)
        # SWAVE UP CANDIDATE
        elif swave_type is SWAVE_UP_CANDIDATE:            
            if spotted_pause in PAUSE_DOWNS:
                prev_move_index = waves_and_pauses_indexes[
                    -2 if waves_and_pauses_types[-2] == SWAVE_DOWN else -1]
                index_ok = pause_start == prev_move_index                    
                pause_analysis = P_OK if index_ok else NO_P_START_MISMATCH
            if spotted_move in TWO_RISING_BARS:
                return Basics.uw_uswc_add_up_bar(
                    bar_list, prev_result, pause_analysis)
            if spotted_move in TWO_FALLING_BARS:
                return Basics.uw_uswc_add_down_bar(
                    bar_list, prev_result, tolerance, pause_analysis)
            return Basics.uw_uswc_undefined_bar(
                bar_list, prev_result, tolerance, pause_analysis)
        # SWAVE DOWN
        elif swave_type is SWAVE_DOWN:
            if spotted_pause in PAUSE_DOWNS:
                prev_move_index = waves_and_pauses_indexes[-1]
                index_ok = pause_start == prev_move_index                    
                pause_analysis = P_OK if index_ok else NO_P_START_MISMATCH
            if spotted_move in TWO_RISING_BARS:
                return Basics.uw_dsw_add_two_rising_bars(
                    bar_list, prev_result, tolerance, pause_analysis)
            if spotted_move in TWO_FALLING_BARS:
                return Basics.uw_dsw_add_down_bar(
                    bar_list, prev_result, tolerance, pause_analysis)
            return Basics.uw_dsw_undefined_bar(
                bar_list, prev_result, tolerance, pause_analysis)
        raise Exception('kaboem wave up')
    
    @staticmethod
    def calculate_wave_down_info(
            bar_list, prev_results, spotted_move, 
            spotted_pause, pause_start, tolerance):
        #return Basics.no_wave()
        last_bar = bar_list[-1]
        if not prev_results:
            return Basics.no_wave()
        last_bar = bar_list[-1]
        prev_result = list(prev_results[-1])
        ####
        waves_and_pauses_extremes = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES]
        waves_and_pauses_lengths = prev_result[Basics.W_DOWN_W_AND_P_LENGTHS]
        waves_and_pauses_types = prev_result[Basics.W_DOWN_W_AND_P_TYPES]
        waves_and_pauses_indexes = prev_result[Basics.W_DOWN_W_AND_P_INDEXES]
        waves_and_pauses_times = prev_result[Basics.W_DOWN_W_AND_P_TIMES]
        prev_result[Basics.W_DOWN_W_AND_P_EXTREMES] = waves_and_pauses_extremes[:]
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS] = waves_and_pauses_lengths[:]
        prev_result[Basics.W_DOWN_W_AND_P_TYPES] = waves_and_pauses_types[:]
        prev_result[Basics.W_DOWN_W_AND_P_INDEXES] = waves_and_pauses_indexes[:]
        prev_result[Basics.W_DOWN_W_AND_P_TIMES] = waves_and_pauses_times[:]
        #########
        # run studie
        ##########
        ####
        swave_type = waves_and_pauses_types[-1]
        pause_analysis = None
        if swave_type is None:
            if spotted_move in TWO_FALLING_BARS:
                return Basics.start_down_wave(bar_list)
            else:
                return Basics.no_wave()
        # SWAVE DOWN
        elif swave_type is SWAVE_DOWN:
            if spotted_pause in PAUSE_UPS:
                pause_analysis = NO_P_SWAVE_OK
            if spotted_move in TWO_FALLING_BARS:
                return Basics.dw_dsw_add_down_bar(
                    bar_list, prev_result, pause_analysis)
            if spotted_move in TWO_RISING_BARS:
                return Basics.dw_dsw_add_two_rising_bars(
                    bar_list, prev_result, tolerance, pause_analysis)
            return Basics.dw_dsw_undefined_bar(
                bar_list, prev_result, tolerance, pause_analysis)
        # SWAVE DOWN CANDIDATE
        elif swave_type is SWAVE_DOWN_CANDIDATE:
            #prev_move = waves_and_pauses_types[-2]
            #prev_move_index = waves_and_pauses_indexes[-2]
            if spotted_pause in PAUSE_UPS:
                prev_move_index = waves_and_pauses_indexes[
                    -2 if waves_and_pauses_types[-2] == SWAVE_DOWN else -1]
                index_ok = pause_start == prev_move_index                    
                pause_analysis = P_OK if index_ok else NO_P_START_MISMATCH
            if spotted_move in TWO_FALLING_BARS:
                return Basics.dw_dswc_add_down_bar(
                    bar_list, prev_result, pause_analysis)
            if spotted_move in TWO_RISING_BARS:
                return Basics.dw_dswc_add_up_bar(
                    bar_list, prev_result, tolerance, pause_analysis)
            return Basics.dw_dswc_undefined_bar(
                bar_list, prev_result, tolerance, pause_analysis)
        # SWAVE UP
        elif swave_type is SWAVE_UP:
            if spotted_pause in PAUSE_UPS:
                prev_move_index = waves_and_pauses_indexes[-1]
                index_ok = pause_start == prev_move_index                    
                pause_analysis = P_OK if index_ok else NO_P_START_MISMATCH
            if spotted_move in TWO_FALLING_BARS:
                return Basics.dw_usw_add_two_falling_bars(
                    bar_list, prev_result, tolerance, pause_analysis)
            if spotted_move in TWO_RISING_BARS:
                return Basics.dw_usw_add_up_bar(
                    bar_list, prev_result, tolerance, pause_analysis)
            return Basics.dw_usw_undefined_bar(
                bar_list, prev_result, tolerance, pause_analysis)
        raise Exception('kaboem wave down {}'.format(swave_type))
                
    @staticmethod
    def two_bars_down_p(b1, b2, b3):
        """Returns True when countermove detected.
        ctrl bars must be three tuples (direction, bar)
        """
        last_low, before_last_low = b3.low, b2.low
        last_high, before_last_high, third_last_high = b3.high, b2.high, b1.high
        last_close, before_last_close, third_last_close = (
                                                    b3.close, b2.close, b1.close)
        last_open, before_last_open, third_last_open = b3.open_, b2.open_, b1.open_
        # CASE 1
        if b3.is_falling_bar:
            if (last_high < before_last_high                              and
                last_open < before_last_open                              and
                b2.is_falling_bar
            ):
                if last_close < before_last_close:
                    return TWO_FB_CASE1 
        # CASE 2
                if last_low < before_last_low:
                    return TWO_FB_CASE2
        # CASE 3
            if (third_last_high > before_last_high                        and
                third_last_high > last_high
            ):
                if last_close < before_last_close:  
                    return TWO_FB_CASE3
        # CASE 4
                if last_low < before_last_low:
                    return TWO_FB_CASE4
        #CASE 5
        if (third_last_high > before_last_high                            and
            third_last_high > last_high
        ):
            if last_close < before_last_close < third_last_close:
                return TWO_FB_CASE5
        #CASE 6
            if last_open < before_last_open < third_last_open:
                return TWO_FB_CASE6
        return False
    
    @staticmethod
    def two_bars_up_p(b1, b2, b3):
        """Returns True when countermove detected.
        ctrl bars must be three tuples (direction, bar)
        """
        last_high, before_last_high = b3.high, b2.high
        last_low, before_last_low, third_last_low = b3.low, b2.low, b1.low
        last_open, before_last_open, third_last_open = b3.open_, b2.open_, b1.open_
        last_close, before_last_close, third_last_close = (
                                                      b3.close, b2.close, b1.close)
        # CASE 1
        if b3.is_rising_bar:
            if (last_low > before_last_low                                and
                last_open > before_last_open                              and
                b2.is_rising_bar
            ):
                if last_close > before_last_close:
                    return TWO_RB_CASE1 
        # CASE 2
                if last_high > before_last_high:
                    return TWO_RB_CASE2
        # CASE 3
            if (third_last_low < before_last_low                          and
                third_last_low < last_low
            ):
                if last_close > before_last_close:  
                    return TWO_RB_CASE3
        # CASE 4
                if last_high > before_last_high:
                    return TWO_RB_CASE4
        #CASE 5
        if (third_last_low < before_last_low                              and
            third_last_low < last_low
        ):
            if last_close > before_last_close > third_last_close:
                return TWO_RB_CASE5
        #CASE 6
            if last_open > before_last_open > third_last_open:
                return TWO_RB_CASE6
        return False
    
    @staticmethod
    def pause_up_1_plus_1_p(b1, b2, b3):
        """Returns True when countermove detected.
        ctrl bars must be three tuples (direction, bar)
        """
        if (b1.is_rising_bar                                          and
            b2.is_falling_bar                                         and
            b3.is_rising_bar                                          and
            b2.low > b1.low                                           and
            b3.high < b1.high
        ):
            #print("AND >>>>> 1 + 1 p UP returned")
            return ONE_PLUS_ONE_PAUSE_UP, 2
        return False, False
    
    @staticmethod
    def pause_down_1_plus_1_p(b1, b2, b3):
        """Returns True when countermove detected.
        ctrl bars must be three tuples (direction, bar)
        """
        if (b1.is_falling_bar                                         and
            b2.is_rising_bar                                          and
            b3.is_falling_bar                                         and
            b2.high < b1.high                                         and
            b3.low > b1.low 
        ):
            #print("AND >>>>> 1 + 1 p DOWN returned")
            return ONE_PLUS_ONE_PAUSE_DOWN, 2
        return False, False
    
    @staticmethod
    def two_plus_two_pause_up_p(bar_list, prev_results):
        '''Returns True when 2+2 pause detected
        Only call this function when the currently detected move is 
        2 bars rising.
        '''
        if prev_results[-1][Basics.SPOTTED_MOVE] in TWO_FALLING_BARS:
            t, trigger = -1, TRIGGERED_BY_TWO_BARS
        elif prev_results[-2][Basics.SPOTTED_MOVE] in TWO_FALLING_BARS:
            t, trigger = -2, TRIGGERED_BY_TWO_BARS
        elif bar_list[-3].is_falling_bar:
            t, trigger = -2, TRIGGERED_BY_ONE_BAR
        else:
            return False, False
        if prev_results[t - 1][Basics.SPOTTED_MOVE] in TWO_RISING_BARS:
            tt = t - 1
        elif (trigger == 2                                            and
              prev_results[t - 2][Basics.SPOTTED_MOVE] in TWO_RISING_BARS
        ):
            tt = t - 2
        else:
            return False, False
        pre, ini_1, ini_2 = bar_list[tt-3], bar_list[tt-2], bar_list[tt-1]
        low = min(pre.low, ini_1.low, ini_2.low)
        high = max(ini_1.high, ini_2.high)
        for i in range(tt, 0):
            bar = bar_list[i]
            if bar.low < low or bar.high > high:
                t_plus_t = False
                break
        else:
            t_plus_t = True
        #print('T_PLUS_T P UP' if t_plus_t else 'P UP FAILED')
        #print('triggered by:', trigger)
        #print('end falling bars:', t-1)
        #print('end first rising bars', tt-1)
        #for j in range(tt-3, 0):
            #if j < -1:
                #dd = prev_results[j+1][Basics.SPOTTED_MOVE]
            #else:
                #dd = '   '
            #print(dd, '>>>', bar_list[j])
        #print('H',bar.high, high)
        #print('L',bar.low, low)
        ##input()
        if trigger == TRIGGERED_BY_ONE_BAR:
            return TWO_PLUS_TWO_PAUSE_UP_1, -(tt - 1)
        return TWO_PLUS_TWO_PAUSE_UP_2, -(tt - 1)
    
    @staticmethod
    def two_plus_two_pause_down_p(bar_list, prev_results):
        '''Returns True when 2+2 pause detected
        Only call this function when the currently detected move is 
        2 bars rising.
        '''        
        if prev_results[-1][Basics.SPOTTED_MOVE] in TWO_RISING_BARS:
            t, trigger = -1, TRIGGERED_BY_TWO_BARS
        elif prev_results[-2][Basics.SPOTTED_MOVE] in TWO_RISING_BARS:
            t, trigger = -2, TRIGGERED_BY_TWO_BARS
        elif bar_list[-3].is_rising_bar:
            t, trigger = -2, TRIGGERED_BY_ONE_BAR
        else:
            return False, False
        if prev_results[t - 1][Basics.SPOTTED_MOVE] in TWO_FALLING_BARS:
            tt = t - 1
        elif (trigger == TRIGGERED_BY_TWO_BARS                        and
              prev_results[t - 2][Basics.SPOTTED_MOVE] in TWO_FALLING_BARS
        ):
            tt = t - 2
        else:
            return False, False
        #pre, ini_1, ini_2 = bar_list[tt-3], bar_list[tt-2], bar_list[tt-1]
        low = min([b.low for b in bar_list[tt-1:-2]])
        high = max([b.high for b in bar_list[tt-2:-3]])
        for i in range(tt, 0):
            bar = bar_list[i]
            if bar.low < low or bar.high > high:
                t_plus_t = False
                break
        else:
            t_plus_t = True
        #print('T_PLUS_T P DOWN' if t_plus_t else 'P DOWN FAILED')
        #print('triggered by:', trigger)
        #print('end rising bars:', t-1)
        #print('end first falling bars', tt-1)
        #for j in range(tt-3, 0):
            #if j < -1:
                #dd = prev_results[j+1][Basics.SPOTTED_MOVE]
            #else:
                #dd = '   '
            #print(dd, '>>>', bar_list[j])
        #print('H',bar.high, high)
        #print('L',bar.low, low)
        ###input()
        if t_plus_t:
            if trigger == TRIGGERED_BY_ONE_BAR:
                return TWO_PLUS_TWO_PAUSE_DOWN_1, -(tt - 1)
            return TWO_PLUS_TWO_PAUSE_DOWN_2, -(tt - 1)
        return False, False
    
    @staticmethod
    def no_wave():
        return (
             [None], # waves_and_pauses_extremes
             [None], # waves_and_pauses_lengths
             [None], # waves_and_pauses_types
             [None], # waves and pauses indexes
             [None], # waves and pauses times
             None, # pause_confirmed
        )
        
    @staticmethod
    def start_up_wave(bar_list):
        # TODO think about:
        # altough it is possible that the third last bar has a
        # lower low then the last two bars i decided to use the
        # the low of two rising bars to be the initial low.
        # No special reason, just arbitrary.
        last_bar, bl_bar = bar_list[-1], bar_list[-2]
        low = min(last_bar.low, bl_bar.low)
        high = max(last_bar.high, bl_bar.high)
        if not last_bar.high == high:
            cond_print(CP_UPWAVE_DEBUG, 'NEW WAVE, second bar lower')
            return (
                [low, high, last_bar.low],
                [1, 1],
                [SWAVE_UP, SWAVE_UP_CANDIDATE],
                [2,1],
                [bl_bar.time, last_bar.time],
                None,
            )
        cond_print(CP_UPWAVE_DEBUG, 'NEW WAVE, 2 up')
        return (
             [low, high], # waves_and_pauses_extremes
             [2], # waves_and_pauses_lengths
             [SWAVE_UP], # waves_and_pauses_types
             [2],
             [bl_bar.time],
             None,
        )
    
        
    @staticmethod
    def start_down_wave(bar_list):
        # TODO think about:
        # altough it is possible that the third last bar has a
        # lower low then the last two bars i decided to use the
        # the low of two rising bars to be the initial low.
        # No special reason, just arbitrary.
        last_bar, bl_bar = bar_list[-1], bar_list[-2]
        low = min(last_bar.low, bl_bar.low)
        high = max(last_bar.high, bl_bar.high)
        if not last_bar.low == low:
            cond_print(CP_DOWNWAVE_DEBUG, 'NEW WAVE, second bar higher')
            return (
                [high, low, last_bar.high],
                [1, 1],
                [SWAVE_DOWN, SWAVE_DOWN_CANDIDATE],
                [2,1],
                [bl_bar.time, last_bar.time],
                None,
            )
        cond_print(CP_DOWNWAVE_DEBUG, 'NEW WAVE, 2 down')
        return (
             [high, low], # waves_and_pauses_extremes
             [2], # waves_and_pauses_lengths
             [SWAVE_DOWN], # waves_and_pauses_types
             [2],
             [bl_bar.time,],
             None,
        )
    
    @staticmethod
    def increase_indexes(a_result, up_or_down):
        '''Helper to increase the indexes '''
        if up_or_down is SWAVE_UP:
            a_result[Basics.W_UP_W_AND_P_INDEXES] = [
                n + 1 for n in a_result[Basics.W_UP_W_AND_P_INDEXES]]
        else:
            a_result[Basics.W_DOWN_W_AND_P_INDEXES] = [
                n + 1 for n in a_result[Basics.W_DOWN_W_AND_P_INDEXES]]
        
    @staticmethod
    def uw_usw_add_up_bar(bar_list, prev_result, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_usw_add_up_bar')
        cond_print(CP_UPWAVE_DEBUG, 
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_high = last_bar.high
        if curr_high > prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1]:
            cond_print(CP_UPWAVE_DEBUG, 'new high', curr_high)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_high
        else:
            cond_print(CP_UPWAVE_DEBUG, 'no new high')
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(last_bar.low)
            prev_result[Basics.W_UP_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_UP_W_AND_P_TYPES].append(SWAVE_UP_CANDIDATE)
            prev_result[Basics.W_UP_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_UP_W_AND_P_TIMES].append(last_bar.time)
        prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS], 
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        )       
        
    @staticmethod
    def dw_dsw_add_down_bar(bar_list, prev_result, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_dsw_add_downbar')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ',prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_low = last_bar.low
        if curr_low < prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1]:
            cond_print(CP_DOWNWAVE_DEBUG, 'new low', curr_low)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_low
        else:
            cond_print(CP_DOWNWAVE_DEBUG, 'no new low')
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(last_bar.high)
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_TYPES].append(SWAVE_DOWN_CANDIDATE)
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_TIMES].append(last_bar.time)
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        )
    
    @staticmethod
    def uw_uswc_add_up_bar(bar_list, prev_result, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_uswc_add_up_bar')
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        prev_type = prev_result[Basics.W_UP_W_AND_P_TYPES][-2]
        curr_high = bar_list[-1].high
        wave_high = prev_result[Basics.W_UP_W_AND_P_EXTREMES][
                                    -2 if prev_type is SWAVE_UP else -3]
        cond_print(CP_DOWNWAVE_DEBUG, 'wave high:', wave_high)
        if curr_high > wave_high:
            cond_print(CP_UPWAVE_DEBUG, 'new high', curr_high)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].pop()
            if prev_type is SWAVE_UP:
                cond_print(CP_UPWAVE_DEBUG, 'previous s wave up')
                prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_high
                canditate_len = prev_result[Basics.W_UP_W_AND_P_LENGTHS].pop()
                prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += canditate_len
                prev_result[Basics.W_UP_W_AND_P_TYPES].pop()
                prev_result[Basics.W_UP_W_AND_P_INDEXES].pop()
                prev_result[Basics.W_UP_W_AND_P_TIMES].pop()
            elif prev_type is SWAVE_DOWN:
                cond_print(CP_UPWAVE_DEBUG, 'CAND IS SWAVE UP')
                prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(curr_high)
                prev_result[Basics.W_UP_W_AND_P_TYPES][-1] = SWAVE_UP
            else:
                cond_input(CI_WARNING, 'You should not get here!')
        else:
            cond_print(CP_UPWAVE_DEBUG, 'no swave UP yet')
        prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS],
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        ) 
        
    @staticmethod
    def dw_dswc_add_down_bar(bar_list, prev_result, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_dswc_add_down_bar')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        prev_type = prev_result[Basics.W_DOWN_W_AND_P_TYPES][-2]
        curr_low = bar_list[-1].low
        wave_low = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][
                                    -2 if prev_type is SWAVE_DOWN else -3]
        cond_print(CP_DOWNWAVE_DEBUG, 'wave low:', wave_low)
        if curr_low < wave_low:
            cond_print(CP_DOWNWAVE_DEBUG, 'new low', curr_low)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].pop()
            if prev_type is SWAVE_DOWN:
                cond_print(CP_DOWNWAVE_DEBUG, 'previous s wave down')
                prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_low
                canditate_len = prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].pop()
                prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += canditate_len
                prev_result[Basics.W_DOWN_W_AND_P_TYPES].pop()
                prev_result[Basics.W_DOWN_W_AND_P_INDEXES].pop()
                prev_result[Basics.W_DOWN_W_AND_P_TIMES].pop()
            elif prev_type is SWAVE_UP:
                cond_print(CP_DOWNWAVE_DEBUG, 'CAND IS SWAVE DOWN')
                prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(curr_low)
                prev_result[Basics.W_DOWN_W_AND_P_TYPES][-1] = SWAVE_DOWN
            else:
                cond_input(CI_WARNING, 'You should not get here!')
        else:
            cond_print(CP_DOWNWAVE_DEBUG, 'no swave DOWN yet')
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        ) 
        
    @staticmethod
    def uw_usw_add_two_falling_bars(bar_list, prev_result, tolerance, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_usw_add_two_falling_bars')
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_high = last_bar.high
        swave_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][-2] - tolerance
        two_bar_low = min(last_bar.low, bar_list[-2].low)
        if two_bar_low < swave_low:
            cond_print(CP_UPWAVE_DEBUG,
                       'END OF WAVE: 2 bar low {} < {} swave low'.format(
                           two_bar_low, swave_low))
            return Basics.no_wave()
        cond_print(CP_UPWAVE_DEBUG,'NEW DOWN SWAVE')
        if curr_high > prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1]:
            for bar in bar_list[-6:]:
                cond_print(CP_UPWAVE_DEBUG, bar)
            cond_input(CI_WARNING, 'A new high with 2 bar down, normal?')
            prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_high
            prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(two_bar_low)
        prev_result[Basics.W_UP_W_AND_P_LENGTHS].append(2)
        prev_result[Basics.W_UP_W_AND_P_TYPES].append(SWAVE_DOWN)
        prev_result[Basics.W_UP_W_AND_P_INDEXES].append(1)
        prev_result[Basics.W_UP_W_AND_P_TIMES].append(bar_list[-2].time)
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS],
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        ) 
        
    @staticmethod
    def dw_dsw_add_two_rising_bars(bar_list, prev_result, tolerance, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_dsw_add_two_rising_bars')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_low = last_bar.low
        swave_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-2] + tolerance
        two_bar_high = max(last_bar.high, bar_list[-2].high)
        if two_bar_high > swave_high:
            cond_print(CP_DOWNWAVE_DEBUG,
                       'END OF WAVE: 2 bar high {} > {} swave high'.format(
                           two_bar_high, swave_high))
            return Basics.no_wave()
        cond_print(CP_DOWNWAVE_DEBUG, 'NEW UP SWAVE')
        if curr_low < prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1]:
            for bar in bar_list[-6:]:
                cond_print(CP_UPWAVE_DEBUG, bar)
            cond_input(CI_WARNING, 'A new low with 2 bar up, normal?')
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_low
            prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(two_bar_high)
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].append(2)
        prev_result[Basics.W_DOWN_W_AND_P_TYPES].append(SWAVE_UP)
        prev_result[Basics.W_DOWN_W_AND_P_INDEXES].append(1)
        prev_result[Basics.W_DOWN_W_AND_P_TIMES].append(bar_list[-2].time)
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        ) 
        
    @staticmethod
    def uw_dsw_add_two_rising_bars(bar_list, prev_result, tolerance, ps):
        # I don't check the low of the 2 bars up, could do it, but
        # decided not to.
        cond_print(CP_UPWAVE_DEBUG, 'uw_dsw_add_two_rising_bars')
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        swave_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1]
        last_bar = bar_list[-1]
        curr_low = last_bar.low
        two_bar_high = max(last_bar.high, bar_list[-2].high)
        if curr_low < prev_result[Basics.W_UP_W_AND_P_EXTREMES][0] - tolerance:
            cond_print(CP_UPWAVE_DEBUG, 'curr low under wave low, new upwave')
            return Basics.start_up_wave(bar_list)
        if curr_low < swave_low:
            cond_print(CP_UPWAVE_DEBUG, 'low < swave low', curr_low)
            swave_low = curr_low
            prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_low
            prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        if two_bar_high > prev_result[Basics.W_UP_W_AND_P_EXTREMES][-2]:
            cond_print(CP_UPWAVE_DEBUG, 'NEW SWAVE: UP', two_bar_high)
            prev_result[Basics.W_UP_W_AND_P_TYPES].append(SWAVE_UP)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(two_bar_high)
            prev_result[Basics.W_UP_W_AND_P_INDEXES].append(1)
            prev_result[Basics.W_UP_W_AND_P_LENGTHS].append(2)
            prev_result[Basics.W_UP_W_AND_P_TIMES].append(bar_list[-2].time)
        else:
            cond_print(CP_UPWAVE_DEBUG, 'no new high, candidate status')
            prev_result[Basics.W_UP_W_AND_P_TYPES].append(SWAVE_UP_CANDIDATE)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(swave_low)
            prev_result[Basics.W_UP_W_AND_P_INDEXES].append(1)
            prev_result[Basics.W_UP_W_AND_P_LENGTHS].append(2)
            prev_result[Basics.W_UP_W_AND_P_TIMES].append(bar_list[-2].time)
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS],
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def dw_usw_add_two_falling_bars(bar_list, prev_result, tolerance, ps):
        # I don't check the low of the 2 bars up, could do it, but
        # decided not to.
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_usw_add_two_falling_bars')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        swave_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1]
        last_bar = bar_list[-1]
        curr_high = last_bar.high
        two_bar_low = min(last_bar.low, bar_list[-2].low)
        if curr_high > prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][0] + tolerance:
            cond_print(CP_UPWAVE_DEBUG, 
                       'curr high above wave high, new downwave')
            return Basics.start_down_wave(bar_list)
        if curr_high > swave_high:
            cond_print(CP_DOWNWAVE_DEBUG, 'high > swave high', curr_high)
            swave_high = curr_high
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = swave_high
            prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        if two_bar_low <  prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-2]:
            cond_print(CP_DOWNWAVE_DEBUG, 'NEW SWAVE: DOWN', two_bar_low)
            prev_result[Basics.W_DOWN_W_AND_P_TYPES].append(SWAVE_DOWN)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(two_bar_low)
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES].append(1)
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].append(2)
            prev_result[Basics.W_DOWN_W_AND_P_TIMES].append(bar_list[-2].time)
        else:
            cond_print(CP_DOWNWAVE_DEBUG, 'no new low, candidate status')
            prev_result[Basics.W_DOWN_W_AND_P_TYPES].append(SWAVE_DOWN_CANDIDATE)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(swave_high)
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES].append(1)
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].append(2)
            prev_result[Basics.W_DOWN_W_AND_P_TIMES].append(bar_list[-2].time)
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def uw_uswc_add_down_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_uswc_add_down_bar')
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        curr_low = bar_list[-1].low
        prev_type = prev_result[Basics.W_UP_W_AND_P_TYPES][-2]
        swave_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][
                            -3 if prev_type is SWAVE_UP else -4] - tolerance
        cond_print(CP_UPWAVE_DEBUG, 'last upwave low:', swave_low)
        if curr_low < swave_low:
            cond_print(CP_UPWAVE_DEBUG, 
                       'END OF WAVE: curr_low {} < {} last up swave low'.format(
                       curr_low, swave_low))
            return Basics.no_wave()
        if prev_type is SWAVE_DOWN:
            cond_print(CP_UPWAVE_DEBUG, 'previous bar down')
            local_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][-2]
            cond_print(CP_UPWAVE_DEBUG, 'last downwave low:', local_low)
            if curr_low < local_low:
                cond_print(CP_UPWAVE_DEBUG, 'SWAVE DOWN CONTINUES')
                prev_result[Basics.W_UP_W_AND_P_EXTREMES].pop()
                prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_low
                candidate_len = prev_result[Basics.W_UP_W_AND_P_LENGTHS].pop()
                prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += candidate_len
                prev_result[Basics.W_UP_W_AND_P_TYPES].pop()
                prev_result[Basics.W_UP_W_AND_P_INDEXES].pop()
                prev_result[Basics.W_UP_W_AND_P_TIMES].pop()
            else:
                cond_print(CP_UPWAVE_DEBUG, 'CANDIDATE CONT')
                pass
        elif prev_type == SWAVE_UP:
            cond_print(CP_UPWAVE_DEBUG, 'previous bar up')
            if curr_low < bar_list[-2].low:
                cond_print(CP_UPWAVE_DEBUG, "2 bar low, making it swave down")
                prev_result[Basics.W_UP_W_AND_P_TYPES][-1] = SWAVE_DOWN
                prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_low
            else:
                cond_print(CP_UPWAVE_DEBUG, 'CANDIDATE CONT')
                pass                
        else:
            cond_input(CI_WARNING, 'How did i get here?')
            pass
        prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS],
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def dw_dswc_add_up_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_dswc_add_up_bar')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        curr_high = bar_list[-1].high
        prev_type = prev_result[Basics.W_DOWN_W_AND_P_TYPES][-2]
        swave_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][
                            -3 if prev_type is SWAVE_DOWN else -4] + tolerance
        cond_print(CP_UPWAVE_DEBUG, 'last downwave high:', swave_high)
        if curr_high > swave_high:
            cond_print(CP_UPWAVE_DEBUG, 
                       'END OF WAVE: curr_high {} > {} '
                       'last down swave high'.format(
                           curr_high, swave_high))
            return Basics.no_wave()
        if prev_type == SWAVE_UP:
            cond_print(CP_DOWNWAVE_DEBUG, 'previous bar up')
            local_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-2]
            cond_print(CP_UPWAVE_DEBUG, 'last upwave high:', local_high)
            if curr_high > local_high:
                cond_print(CP_UPWAVE_DEBUG, 'SWAVE UP CONTINUES')
                prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].pop()
                prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_high
                candidate_len = prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].pop()
                prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += candidate_len
                prev_result[Basics.W_DOWN_W_AND_P_TYPES].pop()
                prev_result[Basics.W_DOWN_W_AND_P_INDEXES].pop()
                prev_result[Basics.W_DOWN_W_AND_P_TIMES].pop()
            else:
                cond_print(CP_UPWAVE_DEBUG, 'CANDIDATE CONT')
                pass
        elif prev_type == SWAVE_DOWN:
            cond_print(CP_DOWNWAVE_DEBUG, 'previous bar down')
            if curr_high > bar_list[-2].high:                
                prev_result[Basics.W_DOWN_W_AND_P_TYPES][-1] = SWAVE_UP
                prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_high
            else:
                cond_print(CP_UPWAVE_DEBUG, 'CANDIDATE CONT')
                pass  
        else:
            cond_input(CI_WARNING, 'How did i get here?')
            pass     
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS],
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def uw_dsw_add_down_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_dsw_add_down_bar')
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        curr_low = bar_list[-1].low
        min_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][-3] - tolerance
        if curr_low < min_low:
            cond_print(CP_UPWAVE_DEBUG, 
                       'END OF WAVE: curr_low {} < {} min low'.format(
                           curr_low, min_low))
            return Basics.no_wave()
        if curr_low < prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1]:
            cond_print(CP_UPWAVE_DEBUG, 'going deeper')
            prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_low
        cond_print(CP_UPWAVE_DEBUG, 'more down bars')
        prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS], 
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def dw_usw_add_up_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_usw_add_up_bar')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        curr_high = bar_list[-1].high
        max_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-3] + tolerance
        if curr_high > max_high:
            cond_print(CP_UPWAVE_DEBUG, 
                       'END OF WAVE: curr_high {} > {} max high'.format(
                           curr_high, max_high))
            return Basics.no_wave()
        if curr_high > prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1]:
            cond_print(CP_DOWNWAVE_DEBUG, 'going higher')
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_high
        cond_print(CP_DOWNWAVE_DEBUG, 'more up bars')
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def uw_usw_undefined_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_usw_undefined_bar')
        cond_print(CP_UPWAVE_DEBUG, 
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_low, curr_high = last_bar.low, last_bar.high
        min_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][-2] - tolerance
        if curr_low < min_low:
            cond_print(CP_UPWAVE_DEBUG, 'END OF WAVE: low < last up swave low')
            return Basics.no_wave()
        if curr_high > prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1]:
            cond_print(CP_UPWAVE_DEBUG, 'new high', curr_high)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_high
        else:            
            cond_print(CP_UPWAVE_DEBUG, 'no new high, candidate status')
            prev_result[Basics.W_UP_W_AND_P_TYPES].append(SWAVE_UP_CANDIDATE)
            prev_result[Basics.W_UP_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(curr_low)
            prev_result[Basics.W_UP_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_UP_W_AND_P_TIMES].append(last_bar.time)
        prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS], 
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def dw_dsw_undefined_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_dsw_undefined_bar')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_low, curr_high = last_bar.low, last_bar.high
        max_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-2] + tolerance
        if curr_high > max_high:
            cond_print(CP_DOWNWAVE_DEBUG,
                       'END OF WAVE: high > last down swave high')
            return Basics.no_wave()
        if curr_low < prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1]:
            cond_print(CP_DOWNWAVE_DEBUG, 'new low', curr_low)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_low
        else:            
            cond_print(CP_DOWNWAVE_DEBUG, 'no new low, candidate status')
            prev_result[Basics.W_DOWN_W_AND_P_TYPES].append(SWAVE_DOWN_CANDIDATE)
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(curr_high)
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_TIMES].append(last_bar.time)
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        )
        
    @staticmethod
    def uw_uswc_undefined_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_uswc_undefined_bar')
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_low = last_bar.low
        curr_high = last_bar.high
        prev_type = prev_result[Basics.W_UP_W_AND_P_TYPES][-2]
        max_high = prev_result[Basics.W_UP_W_AND_P_EXTREMES][
                            -2 if prev_type is SWAVE_UP else -3]
        swave_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][
                            -3 if prev_type is SWAVE_UP else -4] - tolerance
        if curr_low < swave_low:
            cond_print(CP_UPWAVE_DEBUG, 
                       'END OF WAVE: curr_low {} < {} last up swave low'.format(
                       curr_low, swave_low))
            return Basics.no_wave()
        if curr_high > max_high:
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].pop()
            cond_print(CP_UPWAVE_DEBUG, 'new high', curr_high)
            if prev_type is SWAVE_UP:
                cond_print(CP_UPWAVE_DEBUG, 'previous s wave up')
                prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_high
                canditate_len = prev_result[Basics.W_UP_W_AND_P_LENGTHS].pop()
                prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += canditate_len
                prev_result[Basics.W_UP_W_AND_P_TYPES].pop()
                prev_result[Basics.W_UP_W_AND_P_INDEXES].pop()
                prev_result[Basics.W_UP_W_AND_P_TIMES].pop()
            elif prev_type is SWAVE_DOWN:
                cond_print(CP_UPWAVE_DEBUG, 'NEW SWAVE: previous s wave down or pause')
                prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(curr_high)
                prev_result[Basics.W_UP_W_AND_P_TYPES][-1] = SWAVE_UP
        else:
            cond_print(CP_UPWAVE_DEBUG, 'no swave up yet')
        prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS],
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        ) 
        
    @staticmethod
    def dw_dswc_undefined_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_dswc_undefined_bar')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_low = last_bar.low
        curr_high = last_bar.high
        prev_type = prev_result[Basics.W_DOWN_W_AND_P_TYPES][-2]
        min_low = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][
                            -2 if prev_type is SWAVE_DOWN else -3]
        swave_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][
                            -3 if prev_type is SWAVE_DOWN else -4] + tolerance
        if curr_high > swave_high:
            cond_print(CP_DOWNWAVE_DEBUG, 
                       'END OF WAVE: curr_high {} > {}'
                       'last down swave high'.format(
                           curr_high, swave_high))
            return Basics.no_wave()
        if curr_low < min_low:
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].pop()
            cond_print(CP_DOWNWAVE_DEBUG, 'new low', curr_low)
            if prev_type is SWAVE_DOWN:
                cond_print(CP_DOWNWAVE_DEBUG, 'previous s wave down')
                prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_low
                canditate_len = prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].pop()
                prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += canditate_len
                prev_result[Basics.W_DOWN_W_AND_P_TYPES].pop()
                prev_result[Basics.W_DOWN_W_AND_P_INDEXES].pop()
                prev_result[Basics.W_DOWN_W_AND_P_TIMES].pop()
            elif prev_type is SWAVE_UP:
                cond_print(CP_DOWNWAVE_DEBUG, 'NEW SWAVE: previous s wave down or pause')
                prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(curr_low)
                prev_result[Basics.W_DOWN_W_AND_P_TYPES][-1] = SWAVE_DOWN
        else:
            cond_print(CP_DOWNWAVE_DEBUG, 'no swave down yet')
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        )       
    
    @staticmethod
    def uw_dsw_undefined_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_UPWAVE_DEBUG, 'uw_dsw_undefined_bar')
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_TYPES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_INDEXES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_EXTREMES])
        cond_print(CP_UPWAVE_DEBUG,
                   '    ', prev_result[Basics.W_UP_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_low = last_bar.low
        curr_high = last_bar.high
        min_low = prev_result[Basics.W_UP_W_AND_P_EXTREMES][-3] - tolerance
        cond_print(CP_UPWAVE_DEBUG, "min low):", min_low)
        if curr_low < min_low:
            cond_print(CP_UPWAVE_DEBUG, 'END OF WAVE: low < last up swave low')
            return Basics.no_wave()
        if curr_high > prev_result[Basics.W_UP_W_AND_P_EXTREMES][-2]:
            cond_print(CP_UPWAVE_DEBUG, 'NEW SWAVE: UP', curr_high)
            prev_result[Basics.W_UP_W_AND_P_TYPES].append(SWAVE_UP)
            prev_result[Basics.W_UP_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(curr_high)
            prev_result[Basics.W_UP_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_UP_W_AND_P_TIMES].append(last_bar.time)
        elif curr_low < prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1]:
            cond_print(CP_UPWAVE_DEBUG, 'going deeper', curr_low)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES][-1] = curr_low
        else:
            cond_print(CP_UPWAVE_DEBUG, 'no swave up yet, but candidate')
            prev_result[Basics.W_UP_W_AND_P_TYPES].append(SWAVE_UP_CANDIDATE)
            prev_result[Basics.W_UP_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_UP_W_AND_P_EXTREMES].append(curr_low)
            prev_result[Basics.W_UP_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_UP_W_AND_P_TIMES].append(last_bar.time)
        prev_result[Basics.W_UP_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_UP)
        return (
            prev_result[Basics.W_UP_W_AND_P_EXTREMES],
            prev_result[Basics.W_UP_W_AND_P_LENGTHS], 
            prev_result[Basics.W_UP_W_AND_P_TYPES],
            prev_result[Basics.W_UP_W_AND_P_INDEXES],
            prev_result[Basics.W_UP_W_AND_P_TIMES],
            ps
        )            
    
    @staticmethod
    def dw_usw_undefined_bar(bar_list, prev_result, tolerance, ps):
        cond_print(CP_DOWNWAVE_DEBUG, 'dw_usw_undefined_bar')
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_TYPES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_INDEXES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_EXTREMES])
        cond_print(CP_DOWNWAVE_DEBUG,
                   '    ', prev_result[Basics.W_DOWN_W_AND_P_LENGTHS])
        last_bar = bar_list[-1]
        curr_high = last_bar.high
        curr_low = last_bar.low
        max_high = prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-3] + tolerance
        cond_print(CP_UPWAVE_DEBUG, "max high):", max_high)
        if curr_high > max_high:
            cond_print(CP_DOWNWAVE_DEBUG, 'END OF WAVE: high > last up swave high')
            return Basics.no_wave()
        if curr_low < prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-2]:
            cond_print(CP_DOWNWAVE_DEBUG, 'NEW SWAVE: DOWN', curr_low)
            prev_result[Basics.W_DOWN_W_AND_P_TYPES].append(SWAVE_DOWN)
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(curr_low)
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_TIMES].append(last_bar.time)
        elif curr_high > prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1]:
            cond_print(CP_DOWNWAVE_DEBUG, 'going higher', curr_high)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES][-1] = curr_high
        else:
            cond_print(CP_DOWNWAVE_DEBUG, 'no swave down yet, but candidate')
            prev_result[Basics.W_DOWN_W_AND_P_TYPES].append(SWAVE_DOWN_CANDIDATE)
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES].append(curr_high)
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS].append(0)
            prev_result[Basics.W_DOWN_W_AND_P_TIMES].append(last_bar.time)
        prev_result[Basics.W_DOWN_W_AND_P_LENGTHS][-1] += 1
        Basics.increase_indexes(prev_result, SWAVE_DOWN)
        return (
            prev_result[Basics.W_DOWN_W_AND_P_EXTREMES],
            prev_result[Basics.W_DOWN_W_AND_P_LENGTHS], 
            prev_result[Basics.W_DOWN_W_AND_P_TYPES],
            prev_result[Basics.W_DOWN_W_AND_P_INDEXES],
            prev_result[Basics.W_DOWN_W_AND_P_TIMES],
            ps
        )
    
    @staticmethod
    def len_up_wave(prev_results):
        indexes = prev_results[-1][Basics.W_UP_W_AND_P_INDEXES]
        len_ = indexes[0]
        return len_ if len_ is not None else 0
    
    @staticmethod
    def len_down_wave(prev_results):
        indexes = prev_results[-1][Basics.W_DOWN_W_AND_P_INDEXES]
        len_ = indexes[0]
        return len_ if len_ is not None else 0
        
class MomentumIndicatorOsc():
    '''Used to indicate the reversal of short term movements
    and the return to the direction of the trend.
    
    MIO = alias class 
    '''
    
    VALUE = 0
    MARKET = 1
    RATE_OF_CHANGE = 2
    FORECAST = 3
    
    info = [
        'VALUE',
        'MARKET',
        'RATE_OF_CHANGE',
        'FORECAST',
    ]
    
    def __init__(self, periods_time_span):
        self.time_span = periods_time_span
        self.name = self.make_name(self.time_span)
        
    @staticmethod
    def make_name(periods_time_span):
        return 'MIO_{:03}'.format(periods_time_span)
        
    def calculate(self, bar_list, prev_results):        
        nr_of_bars_available = len(bar_list)
        ###
        mio = self.calculate_mio(bar_list, self.time_span, nr_of_bars_available)
        #)
        market, rate_of_change = self.evaluate_market(mio, prev_results)
        #)
        forecast = self.make_forecast(mio, prev_results, nr_of_bars_available)
        #)
        return (
            mio,
            market, rate_of_change,
            forecast,
        )
        
    @staticmethod
    def calculate_mio(bar_list, lookback, nr_of_bars_available):
        mio = None
        if nr_of_bars_available >= lookback:
            last_close = bar_list[-1].close
            lookback_close = bar_list[-lookback].close
            mio = last_close - lookback_close
        return mio
    
    @staticmethod
    def evaluate_market(mio, prev_results):
        before_last_result = (
            prev_results[-1][MIO.VALUE] if prev_results else None
        )
        rate_of_change = market = None
        if mio is not None:
            if mio < 0:
                market = DECREASING
                if before_last_result is not None:
                    if mio < before_last_result:
                        rate_of_market_change = INCREASING
                    elif mio > before_last_result:
                        rate_of_market_change = SLOWING
                    else:
                        rate_of_market_change = CONSTANT
            elif mio > 0:
                market = RISING
                if before_last_result is not None:
                    if mio > before_last_result:
                        rate_of_market_change = ACCELARATING
                    elif mio < before_last_result:
                        rate_of_market_change = DECELARATING
                    else:
                        rate_of_market_change = CONSTANT
            else:
                market = NEUTRAL
        return market, rate_of_change
    
    @staticmethod
    def make_forecast(mio, prev_results, nr_of_bars_available):
        forecast = None
        if nr_of_bars_available > 2:
            bbl = prev_results[-2][MIO.VALUE]
            bl = prev_results[-1][MIO.VALUE]
            if bbl is not None:
                previous_rise = bl - bbl
                current_rise = mio - bl        
                if (previous_rise > 0                                 and
                    current_rise > 0                                  and
                    current_rise < previous_rise
                ):
                    forecast = TOPPING_OF
        return forecast
    
MIO = MomentumIndicatorOsc
                
class RateOFChangeOsc():
    '''Used to indicate the reversal of short term movements
    and the return to the direction of the trend.
    '''
    
    VALUE = 0
    MARKET = 1
    RATE_OF_CHANGE = 2
    
    info = [
        'VALUE',
        'MARKET',
        'RATE_OF_CHANGE',
    ]
    
    def __init__(self, periods_time_span):
        self.time_span = periods_time_span
        self.name = self.make_name(self.time_span)
        
    @staticmethod
    def make_name(periods_time_span):
        return 'ROCO_{:03}'.format(periods_time_span)
        
    def calculate(self, bar_list, prev_results):        
        nr_of_bars_available = len(bar_list)
        ###
        roc = self.calculate_roc(bar_list, self.time_span, nr_of_bars_available)
        #)
        market, rate_of_change = self.evaluate_market(roc, prev_results)
        #)
        return (
            roc,
            market, rate_of_change,
        )
        
    @staticmethod
    def calculate_roc(bar_list, lookback, nr_of_bars_available):
        roc = None
        if nr_of_bars_available >= lookback:
            last_close = bar_list[-1].close
            lookback_close = bar_list[-lookback].close
            roc = 100 * (last_close / lookback_close)
        return roc
    
    @staticmethod
    def evaluate_market(roc, prev_results):
        before_last_result = (
            prev_results[-1][ROC.VALUE] if prev_results else None
        )
        rate_of_change = market = None
        if roc is not None:
            if roc < 100:
                market = DECREASING
                if before_last_result is not None:
                    if roc < before_last_result:
                        rate_of_market_change = INCREASING
                    elif roc > before_last_result:
                        rate_of_market_change = SLOWING
                    else:
                        rate_of_market_change = CONSTANT
            elif roc > 100:
                market = RISING
                if before_last_result is not None:
                    if roc > before_last_result:
                        rate_of_market_change = ACCELARATING
                    elif roc < before_last_result:
                        rate_of_market_change = DECELARATING
                    else:
                        rate_of_market_change = CONSTANT
            else:
                market = NEUTRAL
        return market, rate_of_change
    
ROC = RateOFChangeOsc
        
class RelativeStrengthIndicatorOsc():
    '''simple version with just an average of last n period changes.
    better? version defined with a exponentialy smooted moving average
    of period changes.
    '''
    
    VALUE = 0
    MARKET = 1
    
    info = [
        'VALUE',
        'MARKET',
    ]
    
    def __init__(self, periods_time_span_and_overbought_threshold):
        self.time_span,threshold = periods_time_span_and_overbought_threshold
        if threshold > 50:
            self.thresholds = [100 - threshold, threshold]
        else:
            self.thresholds = [threshold, 100 - threshold]
        self.name = self.make_name(self.time_span, self.thresholds[0])
        
    @staticmethod
    def make_name(time_span, threshold):
        if threshold > 50:
            threshold = 100 - threshold
        return 'RSIO_{:03}_{:03}'.format(time_span, threshold)
        
    def calculate(self, bar_list, prev_results):        
        nr_of_bars_available = len(bar_list)
        ###
        rsi = self.calculate_rsi(bar_list, self.time_span, nr_of_bars_available)
        #)
        market = self.evaluate_market(rsi, self.thresholds)
        #)
        return(
            rsi,
            market,
        )
    
    @staticmethod    
    def calculate_rsi(bar_list, lookback, nr_of_bars_available):
        rsi = None
        if nr_of_bars_available > lookback:
            d_up, d_down = [], []
            for i in range(-lookback, 0):
                d = bar_list[i].close - bar_list[i-1].close
                d_up.append(d if d >= 0 else 0)
                d_down.append(-d if d <= 0 else 0)
            up_avg = sum(d_up) / lookback
            down_avg = sum(d_down) / lookback
            if up_avg == down_avg:
                rs = 1
            elif down_avg == 0:
                rs = False #infinit
            else:
                rs = up_avg / down_avg
            if rs is False: #infinit:
                rsi = 100
            else:
                rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def evaluate_market(rsi, thresholds):
        low, high = thresholds
        market = None
        if rsi is not None:            
            if rsi < low:
                market = OVERSOLD
            if rsi > high:
                market = OVERBOUGHT
        return market
        
RSI = RelativeStrengthIndicatorOsc
        
class StochasticOsc():
    
    K_VALUE = 0
    D_VALUE = 1
    GHOST = 2
    K_MARKET = 3
    D_MARKET = 4
    STOCHASTIC = 5
    GHOST_STOCHASTIC = 6
    MOVE = 7
    LAST_MOVE = 8
    MOVE_START_INDEX = 9
    MOVE_STOP_INDEX = 10
    
    info = [
        'K_VALUE',
        'D_VALUE',
        'GHOST',
        'K_MARKET',
        'D_MARKET',
        'STOCHASTIC',
        'GHOST_STOCHASTIC',
        'MOVE',
        'LAST_MOVE',
        'MOVE_START_INDEX',
        'MOVE_STOP_INDEX',
    ]    
    
    def __init__(self, 
                 periods_time_span_and_periods_D_and_overbought_threshold):
        self.time_span, self.d_span, threshold = (
            periods_time_span_and_periods_D_and_overbought_threshold)
        if threshold > 50:
            self.thresholds = [100 - threshold, threshold]
        else:
            self.thresholds = [threshold, 100 - threshold]
        self.name = self.make_name(self.time_span, 
                                   self.d_span, self.thresholds[0])
    
    @staticmethod
    def make_name(time_span, d_span, threshold):        
        if threshold > 50:
            threshold = 100 - threshold
        return 'STOCHO_{:03}_{:03}_{:03}'.format(time_span, d_span, threshold)
        
    def calculate(self, bar_list, prev_results):
        nr_of_bars_available = len(bar_list)
        ###
        k, d, ghost = (
            self.calculate_stochastic_values(
                bar_list, self.time_span, self.d_span, nr_of_bars_available)
        )
        k_market, d_market, stochastic, ghost_stochastic = (
            self.evaluate_values(k, d, ghost, self.thresholds)
        )
        move, last_move, start_index, stop_index = (
            self.find_move(stochastic, ghost_stochastic, prev_results)
        )
        return (
            k, d, ghost,
            k_market,
            d_market,
            stochastic, ghost_stochastic,
            move,
            last_move, start_index, stop_index,
        )
    
    @staticmethod
    def calculate_stochastic_values(
            bar_list, k_span, d_span, nr_of_bars_available):
        k = d = g = None
        if nr_of_bars_available > k_span:
            last_bar = bar_list[-1]
            d_close, d_max_min, lows, highs = [], [], [], []
            if nr_of_bars_available > k_span + d_span - 1:
                d_calc = d_span
            else:
                d_calc = 1
            for corr in range(-d_calc, 0):
                high = 0
                low = None
                close = bar_list[corr].close
                for i in range(k_span):
                    bar = bar_list[corr-i]
                    low = min(low, bar.low) if low else bar.low 
                    high = max(high, bar.high)
                lows.append(low)
                highs.append(high)
                d_close.append(close - low)
                d_max_min.append(high - low)
            if d_max_min[-1] == 0:
                k = 50
            else:
                k = 100 * d_close[-1] / d_max_min[-1]
            if lows[-1] == last_bar.low:
                g = 0
            elif highs[-1] == last_bar.high:
                g = 100
            else:
                g = k
            adc = sum(d_close[:]) / d_span
            amm = sum(d_max_min[:]) / d_span
            if d_calc == d_span:
                if amm == 0:
                    d = 50
                else:
                    d = 100 * adc / amm
        return k, d, g
            
    @staticmethod
    def evaluate_values(k, d, ghost, threshold):
        low, high = threshold
        k_market = d_market = stochastic = ghost_stoch = None
        if k is not None:            
            if k < low:
                k_market = OVERSOLD
                stochastic = STOCHASTIC_A if k == 0 else None
            elif k > high:
                k_market = OVERBOUGHT 
                stochastic = STOCHASTIC_B if k == 100 else None
        if d is not None:            
            if d < low:
                d_market = OVERSOLD
            elif d > high:
                d_market = OVERBOUGHT
        if ghost == 0:
            ghost_stoch = GHOST_A
        elif ghost == 100:
            ghost_stoch = GHOST_B
        stochastic = stochastic or ghost_stoch
        return k_market, d_market, stochastic, ghost_stoch
   
    @staticmethod
    def find_move(stochastic, ghost_stoch, prev_results):
        prev_result = prev_results[-1] if prev_results else None
        start = stop = move = last_move = None
        if prev_result:
            if ghost_stoch == GHOST_A or stochastic == STOCHASTIC_A:
                start = STOCH.find_last_stoch_if_B_or_GB(prev_results)
                move = STOCH_B_GB_TO_STOCH_A_GA if start else None
            if ghost_stoch == GHOST_B or stochastic == STOCHASTIC_B:
                start = STOCH.find_last_stoch_if_A_or_GA(prev_results)
                move = STOCH_A_GA_TO_STOCH_B_GB if start else None
            if move is not None:
                start -= 1 # correct by one because prev_results lag 1
                stop = -1
                last_start, last_stop, last_move = start, stop, move
            else:
                last_move = prev_result[STOCH.MOVE] 
                if last_move is not None:
                    start = prev_result[STOCH.MOVE_START_INDEX] - 1
                    stop = prev_result[STOCH.MOVE_STOP_INDEX] - 1
        return move, last_move, start, stop
    
    @staticmethod
    def find_last_stoch_if_B_or_GB(prev_results):
        index = False
        for c, r in enumerate(reversed(prev_results), 1):
            stoch = r[STOCH.STOCHASTIC]
            ghost = r[STOCH.GHOST]
            if stoch == STOCHASTIC_B or ghost == GHOST_B:
                index = -c
                break
            if stoch == STOCHASTIC_A or ghost == GHOST_A:
                break
        return index
    
    @staticmethod
    def find_last_stoch_if_A_or_GA(prev_results):
        index = False
        for c, r in enumerate(reversed(prev_results), 1):
            stoch = r[STOCH.STOCHASTIC]
            ghost = r[STOCH.GHOST]
            if stoch == STOCHASTIC_A or ghost == GHOST_A:
                index = -c
                break
            if stoch == STOCHASTIC_B or ghost == GHOST_B:
                break
        return index
        
            
STOCH = StochasticOsc
                    
class SimpleMovingAverageTI():
    
    VALUE = 0
    TREND = 1
    REVERSAL = 2
    
    info = [
        'VALUE',
        'TREND',
        'REVERSAL',
    ]
    
    def __init__(self, periods_time_span):
        self.time_span = periods_time_span
        self.name = self.make_name(self.time_span)
        
    @staticmethod
    def make_name(periods_time_span):
        return 'SMATI_{:03}'.format(periods_time_span)
        
    def calculate(self, bar_list, prev_results):
        nr_of_bars_available = len(bar_list)
        ###
        sma = self.calculate_sma(bar_list, self.time_span, nr_of_bars_available)
        #)
        trend, reversal = (
            self.evaluate_sma(sma, bar_list, prev_results, nr_of_bars_available)
        )
        return (
            sma,
            trend,
            reversal,
        )
        
    @staticmethod
    def calculate_sma(bar_list, lookback, nr_of_bars_available):
        smi = None
        if nr_of_bars_available >= lookback:
            total = sum([i.close for i in bar_list[-lookback:]])
            smi = total / lookback
        return smi
    
    @staticmethod
    def evaluate_sma(sma, bar_list, prev_results, nr_of_bars_available):
        trend = reversal = None
        if sma is not None and prev_results:
            prev_result = prev_results[-1]
            prev_trend = prev_result[SMA.TREND]
            last_close = bar_list[-1].close
            if last_close > sma:
                trend = RISING
                reversal = prev_trend is FALLING
            elif last_close < sma:
                trend = FALLING
                reversal = prev_trend is RISING
            else:
                trend = prev_trend
        return trend, reversal    
            
SMA = SimpleMovingAverageTI
            
class LinearlyWeightedMovingAverageTI():
    
    VALUE = 0
    TREND = 1
    REVERSAL = 2
    
    info = [
        'VALUE',
        'TREND',
        'REVERSAL',
    ]
    
    def __init__(self, periods_time_span):
        self.time_span = periods_time_span
        self.denom = sum([i + 1 for i in range(self.time_span)])
        self.name = self.make_name(self.time_span)
        
    @staticmethod
    def make_name(periods_time_span):
        return 'LWMATI_{:03}'.format(periods_time_span)
        
    def calculate(self, bar_list, prev_results):
        nr_of_bars_available = len(bar_list)
        ###
        lwma = (
            self.calculate_lwma(
                bar_list, self.time_span, self.denom, nr_of_bars_available)
        )
        trend, reversal = (
            SMA.evaluate_sma(lwma, bar_list, prev_results, nr_of_bars_available)
        )
        return (
            lwma,
            trend,
            reversal,
        )
        
    @staticmethod
    def calculate_lwma(bar_list, lookback, denom, nr_of_bars_available):
        lwma = None
        if nr_of_bars_available >= lookback:
            total = sum(
                [c * i.close for c, i in enumerate(bar_list[-lookback:], 1)]
            )
            lwma = total / denom
        return lwma
        
LWMA = LinearlyWeightedMovingAverageTI
            
class ExponentialySmootedMovingAverageTI():
    '''Simplified version, partly something a la Robers (wiki?)
    it checks for bar_lists of the same size and resets the last_ESMATI
    to the before_last asmatie
    When the list has the same length as the previous it is handeled as an
    update if the last value (previous result was intermediate) if the list is
    shorter 
    '''
    
    VALUE = 0
    TREND = 1
    REVERSAL = 2
    
    info = [
        'VALUE',
        'TREND',
        'REVERSAL',
    ]
    
    
    def __init__(self, periods_time_span):
        self.time_span = periods_time_span
        self.exp_function = 2 / (periods_time_span + 1)
        self.name = self.make_name(self.time_span)
        self.before_last_ESMATI = None
        self.last_ESMATI = None
        
    @staticmethod
    def make_name(periods_time_span):
        return 'ESMATI_{:03}'.format(periods_time_span)
        
    def calculate(self, bar_list, prev_results):
        nr_of_bars_available = len(bar_list)
        ###
        esma = (
            self.calculate_esma(
                bar_list, self.exp_function, prev_results)
        )
        trend, reversal = (
            SMA.evaluate_sma(esma, bar_list, prev_results, nr_of_bars_available)
        )
        return (
            esma,
            trend,
            reversal,
        )
        
    @staticmethod
    def calculate_esma(bar_list, exp_function, prev_results):
        esma = last_bar_close = bar_list[-1].close
        if prev_results:
            prev_esma = prev_results[-1][ESMA.VALUE]            
            t1 = exp_function * last_bar_close
            t2 = (1 - exp_function) * prev_esma
            esma = t1 + t2
        return esma
        
        
ESMA = ExponentialySmootedMovingAverageTI
            
class MACDTI():
    
    FAST = 0
    SLOW = 1
    DIFF = 2
    TREND = 3
    REVERSAL = 4
    CONFIRMED = 5
    DIVERGANCE = 6
    DIFF_FLIP = 7
    DIFF_DELTA = 10
       
    BASIC_1 = 8
    BASIC_2 = 9
    
    info = [
        'FAST',
        'SLOW',
        'DIFF', 
        'TREND',
        'REVERSAL', 
        'CONFIRMED',
        'DIVERGANCE',
        'DIFF_FLIP',
        'BASIC_1',
        'BASIC_2',
        'DIFF_DELTA',
    ]
    
    def __init__(self, basic1_and_basic2_and_slow_period_time_spans):
        basic1, basic2, self.slow = (
            basic1_and_basic2_and_slow_period_time_spans)
        self.basic1 = ExponentialySmootedMovingAverageTI(basic1)
        self.basic2 = ExponentialySmootedMovingAverageTI(basic2)
        self.name = self.make_name(basic1, basic2, self.slow)
        self.fast_MACDs = []
        self.last_reported_st_trend = None
        self.last_non_neutral_diff = None
        
    @staticmethod
    def make_name(basic1, basic2, slow):
        return 'MACDI_{:03}_{:03}_{:03}'.format(basic1, basic2, slow)
        
    def calculate(self, bar_list, prev_results):
        result1, result2 = (
            self.calculate_basic_results(
                bar_list, self.basic1, self.basic2, prev_results)
        )
        fast, slow, diff, diff_delta = (
            self.calculate_macds(
                bar_list, prev_results, result1, result2, self.slow)
        )
        trend, reversal, confirmed, divergance, flip = (
            self.evaluate_macd(fast, slow, diff, bar_list, prev_results)
        )
        return [
            fast, slow, diff,
            trend, reversal, confirmed,
            divergance, flip,
            result1, result2,
            diff_delta,
        ]
    
    @staticmethod
    def calculate_basic_results(bar_list, basic1, basic2, prev_results): 
        prev_result1 = prev_result2 = []    
        if prev_results:
            pr = prev_results[-1]
            if pr is not None:
                prev_result1 = [pr[MACD.BASIC_1]]
                prev_result2 = [pr[MACD.BASIC_2]]
        result1 = basic1.calculate(bar_list, prev_result1)
        result2 = basic2.calculate(bar_list, prev_result2)
        return result1, result2
    
    @staticmethod
    def calculate_macds(bar_list, prev_results, result1, result2, slow_):
        basic1 = result1[ESMA.VALUE]
        basic2 = result2[ESMA.VALUE]
        basic = slow = diff_histogram = diff_delta = None
        if basic2 is not None:
            basic = basic1 - basic2
        if prev_results and len(prev_results) > slow_ - 2:
            t = sum([r[MACD.FAST] for r in prev_results[-slow_ + 1:]])
            t += basic
            slow = t / slow_
            if slow is None:
                diff_histogram = None
            else:
                diff_histogram = basic - slow
            prev_hist = prev_results[-1][MACD.DIFF]
            if prev_hist:
                diff_delta = (diff_histogram - prev_hist) * 10
        return basic, slow, diff_histogram, diff_delta
    
    @staticmethod
    def evaluate_macd(fast, slow, diff, bar_list, prev_results):
        trend = reversal = confirmed = divergance = flip = None
        prev_trend = prev_results[-1][MACD.TREND] if prev_results else None
        prev_not_zero_diff = None
        for r in  reversed(prev_results):
            prev_not_zero_diff = r[MACD.DIFF]
            if not prev_not_zero_diff == 0:
                break
        if diff is not None:
            if diff > 0:
                trend = RISING
                if prev_trend and prev_trend is FALLING:
                    reversal = True
                if (prev_not_zero_diff                                and
                    prev_not_zero_diff < 0                            and
                    fast > 0                                          and
                    slow > 0
                ):
                    confirmed = True
            elif diff < 0:
                trend = FALLING
                if prev_trend and prev_trend is RISING:
                    reversal = True
                if (prev_not_zero_diff                                and
                    prev_not_zero_diff > 0                            and
                    fast < 0                                          and
                    slow < 0
                ):
                    confirmed = True
            else:
                trend = prev_trend
        bl_diff = prev_results[-1][MACD.DIFF] if prev_results else None
        if bl_diff is not None:
            last_close = bar_list[-1].close
            before_last_close = bar_list[-2].close
            if last_close > before_last_close:
                if not diff > bl_diff:
                    divergence = PULLBACK_AFTER_RISING_W_OR_T
            elif last_close < before_last_close:
                if not diff < bl_diff:
                    devergence = REBOUND_AFTER_FALLING_W_OR_T
            if (prev_not_zero_diff                                     and
                prev_not_zero_diff * diff < 0):
                flip = TURNED_POS if prev_not_zero_diff < 0 else TURNED_NEG
        return trend, reversal, confirmed, divergance, flip
    
MACD = MACDTI

class BOLLIBA():
    
    AVG = 0
    UPPER_BAND = 1
    LOWER_BAND = 2
    HOLDS = 3
    
    info = [
        'AVG',
        'UPPER_BAND',
        'LOWER_BAND',
        'HOLDS'
    ]
    
    def __init__(self, lookback_and_sigma_mulitplier_and_sma_for_hold):
        self.lookback, self.multiplier, self.sma_to_hold = (
                            lookback_and_sigma_mulitplier_and_sma_for_hold)
        self.name = self.make_name(self.lookback, self.multiplier)
        
    @staticmethod
    def make_name(lookback, multiplier):
        return 'BOLLIBA_{:03}_{:03}'.format(lookback, multiplier)
        
    def calculate(self, bar_list, prev_results):
        avg, upper_band, lower_band = (
            self.calculate_bands(
                bar_list, prev_results)
        )
        holds = self.bol_holds(
                bar_list, upper_band, lower_band)
        return [
            avg, upper_band, lower_band, holds
        ]        
        
    def calculate_bands(self, bar_list, prev_results):
        ll = len(bar_list)
        lookback = self.lookback if ll > self.lookback else ll
        closes = [x.close for x in bar_list[-lookback:]]
        avg = sum(closes)/lookback
        sigma = pow(sum([pow(x - avg, 2) for x in closes])/lookback, 1/2)
        upper_band = avg + self.multiplier * sigma
        lower_band = avg - self.multiplier * sigma
        return avg, upper_band, lower_band
    
    def bol_holds(self, bar_list, upper_band, lower_band):
        if len(bar_list) < self.sma_to_hold:
            return None     
        last_bar = bar_list[-1] 
        if ((upper_band <= last_bar.high                            and
            lower_band >= last_bar.low)
            or
            (upper_band > last_bar.high                             and
             lower_band < last_bar.low)
        ):
            return None  
        closes = [x.close for x in bar_list[-self.sma_to_hold:]]
        avg = sum(closes)/self.sma_to_hold
        if (upper_band <= last_bar.high                            and
            upper_band < avg):
            return UPPER_HOLDS
        if (lower_band >= last_bar.low                             and
            lower_band > avg):
            return LOWER_HOLDS
            