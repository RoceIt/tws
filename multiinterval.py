#!/usr/bin/env python3
#
#  Copyright (c) 2014 Rolf Camps (rolf.camps@scarlet.be)
#

import itertools

from sys import stdout
from collections import defaultdict
from time import sleep

import bar_list_studies as bls
import evaluation_tests
from roc_string import SerialLineCreator, SerialTextCreator
from roc_classes import DirLock, NoLock
from marketdata import DataBarComposer
    
STUDIES = {
    'basics': bls.Basics,
    'momentum_indicator_osc': bls.MomentumIndicatorOsc,
    'rate_of_change_osc': bls.RateOFChangeOsc,
    'relative_strength_indicator_osc': 
            bls.RelativeStrengthIndicatorOsc,
    'stochastic_osc': bls.StochasticOsc,
    'simple_moving_average_ti': bls.SimpleMovingAverageTI,
    'linearly_weighted_moving_average_ti': 
            bls.LinearlyWeightedMovingAverageTI,
    'exponantialy_smooted_moving_average_ti':
            bls.ExponentialySmootedMovingAverageTI,
    'macd_ti': bls.MACDTI,
    'bollinger_bands': bls.BOLLIBA,
}

E_TESTS = {
    'stochastic_moves': evaluation_tests.StochMoves,
}


            
def y_f_demo(value,bar):
    """Return a y value for current situation"""
    return bar.close

class MultiIntervalFramework():
    
    def __init__(self, *arg_l, **kw_d):
        if 'load_existing_mif' in kw_d:
            raise NotImplementedError(
                "loading MIF's not implemented")
        self.intervals = []
        self.interval_definition = arg_l[:]
        print('FVITA intervals: ', arg_l)
        self.prev_bar = None # for error 
        if len(arg_l) == 1:            
            input('WARNING: only 1 interval defined!!')
        for i, interval in enumerate(arg_l):
            self.intervals.append(Interval(interval))
        for studie, init_function in STUDIES.items():
            settings = kw_d.pop(studie, [])
            for interval in self.intervals:
                for setting in settings:
                    interval.add_studie(init_function, setting)
        print('FVITA interval studies:', self.intervals[0].studies)
        sleep(2)
        ii_keys = sorted([
            k for k in self.__class__.__dict__.keys() if k.endswith('_ii')
        ])
        self.inter_interval_functions = [
            self.__class__.__dict__[k] for k in ii_keys]
        self.export_file_base = None
        self.reset_export_files()

    @property
    def export_file_base(self):
        return self._export_file_base
    
    def set_export_lock(self):
        for interval in self.intervals:
            interval.set_export_lock()
    
    @export_file_base.setter        
    def export_file_base(self, base):
        for interval in self.intervals:
            interval.export_file_base = base
        self._export_file_base = base
        
    def add_export_item(self, studie, item, str_function=str):
        for interval in self.intervals:
            interval.add_export_item(studie, item, str_function)
        
    def add_ii_export_item(self, studie, item, str_function=str):
        for interval in self.intervals:
            interval.add_ii_export_item(studie, item, str_function)
            
    def add_event_export_item(self, studie, item, str_function=str, 
                              y_function=y_f_demo, rgb_t = (0, 0, 0),
                              permanent=False):
        for interval in self.intervals:
            interval.add_event_export_item(studie, item, str_function,
                                           y_function, rgb_t, permanent)
    def reset_export_files(self):
        # No local export files to reset
        for interval in self.intervals:
            # resetting interval export files
            interval.reset_export_files()
            
    def new_bar(self, a_bar):
        #print('using yielding bar')
        #print('\n\n***** ', a_bar)
        def use(yield_list, t_plus_time=False):
            top = not t_plus_time
            list_length = len(yield_list)
            #print(list_length, '| ',  end='')
            for t_time in yield_list[-1]:
                #print(t_time)
                if top:
                    if list_length == 1:
                        self.ii_evaluation()
                    else:    
                        t_plus_time = t_time
                        use(yield_list[:-1], t_plus_time)
                elif t_plus_time == t_time:
                    if list_length == 1:
                        #print('run inter interval functions (F)', t_time)
                        self.ii_evaluation()
                    else:
                        use(yield_list[:-1], t_plus_time)
                        #return
                        break
                elif t_plus_time > t_time:
                    if list_length == 1:
                        #print('run inter interval functions', t_time)
                        self.ii_evaluation()
                    else:
                        use(yield_list[:-1], t_time)
                else:
                    print('t_plus: ', t_plus_time)
                    print('t_time: ', t_time)
                    print('t: ', len(yield_list))
                    raise
        yielders = []
        for interval in self.intervals:
            yielders.append(interval.new_bar(a_bar))
        try:
            use(yielders)
        except Exception:
            print('prev bar:', self.prev_bar)
            print('fail on bar:', a_bar)
            raise
        self.prev_bar = a_bar
            
    def ii_evaluation(self):
        for f in self.inter_interval_functions:
            f(self)
        for i in self.intervals:
            i.ii_export_values()
            i.event_export_values()
            
    def get_interval_by_name(self, interval_def):
        for interval in self.intervals:
            if interval.name == interval_def:
                return interval
            
    def print_list_lengths(self):
        for interval in self.intervals:
            interval.print_list_lengths()
            
    def print_studie_results(self, studie_type, studie_name):
        for info in studie_type.info:
            print(info, '| ', end='')
            info_value = getattr(studie_type, info)
            for i in self.intervals:
                r = i.last(studie_name)
                if r:
                    print(r[info_value], ', ', end='')
            print()
            
    def print_studies(self, maximum=None):
        for interval in self.intervals:
            interval.print_studies(maximum)
                        
class Interval():
    '''Create an interval item.
    
    An interval is a period of time considered.
    
    for interval_def use tupples.
      ('bars', time in seconds)
    '''
    
    BARS = 'BARS'
    
    def __init__(self, interval_def):
        self.type_of_interval, *parameters = interval_def
        if self.type_of_interval == 'bars':
            self.old_start_time = None
            self.interval_bar_duration = parameters[0]
            self.interval_composer = DataBarComposer(
                    seconds=self.interval_bar_duration)
            if len(parameters) > 1:
                start_time = parameters[1]
                print('Setting startime to', start_time)
                self.interval_composer.start_time = start_time
            self.composing_bar = None
            self.name = interval_def
        self.interval_bars = []
        self.studies_dict = dict()
        self.studie_values = defaultdict(list)
        self.ii_values = defaultdict(list)
        self.at_end_of_period = True
        self.export_file_base = None
        self.export_lock = NoLock()
        self.export_items = []
        self.ii_export_items = []
        self.event_export_items = []
        self.efd = self.iifd = self.evfd = None
        
    def bar_nr_at(self, time):
        if not time:
            return time
        c = len(self.interval_bars)
        for bar in reversed(self.interval_bars):
            if bar.time <= time:
                return c
            c -= 1

    @property
    def export_file_base(self):
        return self._export_file_base
    
    def set_export_lock(self):
        self.export_lock = DirLock(self._export_file_base)
    
    @export_file_base.setter        
    def export_file_base(self, base):
        if base is not None:
            base = "{}_{}_{}".format(
                base, self.type_of_interval, self.interval_bar_duration)
        self._export_file_base = base
        
    def export_bar_data(self, file_handle):
        bar = self.interval_bars[-1]
        export = [str(x) for x in (
            len(self.interval_bars),  ##
            bar.time, 
            bar.open_, bar.low, bar.high, bar.close)]
        for studie, item, str_function in self.export_items:
            export.append(str_function(self.last(studie)[item]))
        with self.export_lock:
            print(",".join([str(x) for x in export]),
                  file=file_handle,
                  flush=True);
        
    def export_finished_bar_data(self):
        self.export_bar_data(self.efd)
        with self.export_lock:
            open(self.export_file_base + '_u', mode='w').close()
        
    def export_unfinished_bar_data(self):
        with open(self.export_file_base + '_u', mode='w') as ef_h:
            self.export_bar_data(ef_h)
            
    def export_ii_data(self, file_handle):
        if self.ii_export_items:
            bar = self.interval_bars[-1]
            export = [
            len(self.interval_bars), ##
             #   str(bar.time)
            ]
            for studie, item, str_function in self.ii_export_items:
                export.append(str_function(self.last(studie)[item]))
            with self.export_lock:
                print(",".join([str(x) for x in export]),
                      file=file_handle,
                      flush=True);
            
    def export_event_data(self, file_handle, perm_file_handle):
        # the perm_file_handle is to make it possible to write data to the
        # permanent file even when the bar is unfinished.
        if self.event_export_items:
            bar = self.interval_bars[-1]
            time = str(bar.time)
            for studie, item, str_f, y_f, color_int, perm in self.event_export_items:
                file_handle = perm_file_handle if perm else file_handle
                result = self.last(studie)[item]
                #print('result: ', result)
                if result:
                    result_str = str_f(result)
                    if result_str:
                        with self.export_lock:
                            print("{},{},{},{}".format(len(self.interval_bars), #time, 
                                                       y_f(result, bar), 
                                                       str_f(result), color_int),
                                  file=file_handle,
                                  flush=True);
            
    def ii_export_values(self):
        if self.at_end_of_period:
            self.ii_export_eop()
        else:
            self.ii_export_u()
            
    def ii_export_eop(self):
        self.export_ii_data(self.iifd)
        with self.export_lock:
            open(self.export_file_base + '_ii_u', mode='w').close()        
            
    def ii_export_u(self):
        with open(self.export_file_base + '_ii_u', mode='w') as ef_h:
            self.export_ii_data(ef_h)
            
    def event_export_values(self):
        if self.at_end_of_period:
            self.event_export_eop()
        else:
            self.event_export_u()
            
    def event_export_eop(self):
        self.export_event_data(self.evfd, self.evfd)
        with self.export_lock:
            open(self.export_file_base + '_event_u', mode='w').close()        
            
    def event_export_u(self):
        with open(self.export_file_base + '_event_u', mode='w') as ef_h:
            self.export_event_data(ef_h, self.evfd)
        
    def add_export_item(self, studie, item, str_function):
        self.export_items.append((studie, item, str_function))
        return len(self.export_items) + 5           
        
    def add_ii_export_item(self, studie, item, str_function):
        self.ii_export_items.append((studie, item, str_function))
        return len(self.ii_export_items) - 1 
    
    def add_event_export_item(self, 
                              studie, item, str_function, y_function, rgb_t,
                              permanent):
        color_int = 256*256*rgb_t[0] + 256*rgb_t[1] + rgb_t[2]
        self.event_export_items.append((studie, item, str_function,
                                        y_function, color_int, permanent))
        return len(self.ii_export_items) - 1
        
    def reset_export_files(self):
        if self.efd:
            self.efd.close()
            self.iifd.close()
            self.evfd.close()
        if self.export_file_base:
            self.efd = open(self.export_file_base, "w")
            self.iifd = open(self.export_file_base+'_ii', "w")
            self.evfd = open(self.export_file_base+'_events', "w")
        else:
            self.efd = open("/dev/null", "w")
            self.iifd = open("/dev/null", "w")
            self.evfd = open("/dev/null", "w")
            
    def close_export_files(self):
        self.efd.close()
        self.iifd.close()
        self.evfd.close()
        
    def add_studie(self, init_function, setting):
        studie = init_function(setting)
        studie.interval_name = self.name
        if studie.name not in self.studies_dict:
            self.studies_dict[studie.name] = studie 
        
    def new_bar(self, a_bar):
        self.studies_updated_after_new_bar = False
        if self.type_of_interval == 'bars':
            yield from self.new_bar_for_intraday_bars(a_bar)
    
    @property        
    def studies(self):
        return [x for x in sorted(self.studies_dict)] 
            
    def new_bar_for_intraday_bars(self, a_bar):
        start_time = a_bar.time
        new_intervals = []
        
        if (self.at_end_of_period is not True                         and
            self.old_start_time                                       and
            self.old_start_time.date() == start_time.date()
        ):
            self.remove_temp_results_from_unfinished_bars()
        if (self.old_start_time                                       and
            not self.old_start_time.date() == start_time.date()
        ):
            if self.composing_bar and self.composing_bar.duration:
                self.export_finished_bar_data()
            unread_data = self.interval_composer.reset_composer()
            self.at_end_of_period = True  # nodig??
        if (self.old_start_time                                             and
            start_time - self.old_start_time < a_bar.duration):
            # skip bars that come to soon, there must be something wrong
            # with them.
            print('!!! skipping this bar !!! duration problem {} - {} < {}'.
                  format(start_time, old_start_time, a_bar.duration))
            return
        self.composing_bar = self.interval_composer.insert_bar(a_bar)
        self.old_start_time = start_time
        while 1:
            new_bar = self.interval_composer.pop_complete_bar()
            new_intervals.append(new_bar)
            if not new_bar: 
                break
        if len(new_intervals) >= 1: new_intervals.pop() 
        #dont return the time if new data available
        for interval in new_intervals:
            self.interval_bars.append(interval)
            self.update_studies()
            self.at_end_of_period = True
            self.export_finished_bar_data()
            yield(interval.end_time()) #!!
        if self.composing_bar and self.composing_bar.duration:
            self.interval_bars.append(self.composing_bar)
            self.update_studies()
            self.at_end_of_period = False
            self.export_unfinished_bar_data()
            yield(self.composing_bar.end_time()) #!!
        #print(self.interval_bar_duration, ',', len(self.interval_bars),
              #',', self.interval_bars[-1])
        #self.old_start_time = start_time
        #!! return self.at_end_of_period        
        
    def update_studies(self):
        for k in self.studies:
            result = self.studies_dict[k].calculate(
                self.interval_bars,
                self.studie_values[k]
            )
            self.studie_values[k].append(result)
            
    def __getitem__(self, studiename):
        '''Returns the list with results from the ii studie or studies.'''
        if studiename in self.ii_values:
            return self.ii_values[studiename]
        if studiename is self.BARS:
            return self.interval_bars
        return self.studie_values[studiename]
    
    def last(self, studiename, n=1):
        '''return the n-th last values of the studiename
        default is last element, you can choose to use a
        positive or negative n, it's always counted backwards
        '''
        n = abs(n)
        s = self[studiename]
        r = s[-n] if (s and len(s) >= n) else []
        return r
    
    def add_ii_value(self, value_name, value):
        self.ii_values[value_name].append(value)        
            
    def remove_temp_results_from_unfinished_bars(self):
        '''Remove temp results from unfinished bars.'''
        self.interval_bars.pop()
        for k in self.studies:
            self.studie_values[k].pop()
        for k in self.ii_values:
            #print(k)
            self.ii_values[k].pop()
            
    def fell_min_n_bars_since(self, n, index):
        """Fell by n bars
        I implemented:
        you can find n bars since index whose closes are lower then
        the the lowes close before in the interval
        n times:  bar(n).close < bar(n-1).close
        """
        index = -abs(index)
        bar = self.interval_bars[index]
        count = 0
        for new_bar in self.interval_bars[ index + 1 :]:
            if new_bar.close < bar.close:
                count += 1
                bar = new_bar
        return count >= n
            
    def rose_min_n_bars_since(self, n, index):
        """Rose by n bars
        I implemented:
        you can find n bars since index whose closes are higher then
        the the lowes close before in the interval
        n times:  bar(n).close > bar(n-1).close
        """
        index = -abs(index)
        bar = self.interval_bars[index]
        count = 0
        for new_bar in self.interval_bars[ index + 1 :]:
            if new_bar.close > bar.close:
                count += 1
                bar = new_bar
        return count >= n
    
    def fell_below_n_after(self, min_low, index):
        index = -abs(index)
        for new_bar in self.interval_bars[ index + 1:]:
            if new_bar.low < min_low:
                #print('bar below min_low: {} < {}'.format(
                    #self.interval_bars[i].low, min_low))
                return True
        #print('fell below {} false'.format(min_low))
        return False
    
    def rose_above_n_after(self, max_high, index):
        index = -abs(index)
        for new_bar in self.interval_bars[ index + 1:]:
            if new_bar.high > max_high:
                #print('bar above max_high: {} < {}'.format(
                    #self.interval_bars[i].low, max_high))
                return True
        #print('rose_above {} false'.format(max_high))
        return False
            
            
    def print_list_lengths(self):
        print('\n', self.name)
        print('Interval list:', len(self.interval_bars))
        for k in self.studies:
            print('{}:'.format(k), len(self.studie_values[k]))
            
    def print_studies(self, maximum=None):
        print('\n', self.name, 'STUDIES')
        for k in self.studies:
            if maximum is None:
                maximum = len(self.studie_values)
            print('{}:'.format(k), self.studie_values[k][-maximum:])
            
class FVITAOriginal(MultiIntervalFramework):
    
    #
    # ii subclass names /categories
    #
    # R_AND_S: resistance and support levels
    #     RESISTANCE
    #         list of values    
    #     SUPPORT
    #         list of values
    # BALANCE_TRIGGERED: Balanced market info (loose up/down count)
    #     BT_TYPE
    #         BALANCED_AT_TOP
    #         BALANCED_AT_BOTTEM
    #     BT_REASON
    #         MAX_MOVE_UP
    #         MAX_MOVE_DOWN
    #         VIRTUAL_MAX_UP
    #         VIRTUAL_MAX_DOWN
    #         QUASI_MAX_UP
    #         QUASI_MAX_DOWN
    # BALANCE_TRIGGERED_WAVE_COUNT: Balanced market info (loose up/down count)
    #     BT_TYPE
    #         BALANCED_AT_TOP
    #         BALANCED_AT_BOTTEM
    #     BT_REASON
    #         MAX_MOVE_UP
    #         MAX_MOVE_DOWN
    #         VIRTUAL_MAX_UP
    #         VIRTUAL_MAX_DOWN
    #         QUASI_MAX_UP
    #         QUASI_MAX_DOWN
    # CONF_DIRECTION: Confirmed direction
    #     CD_TYPE
    #         CD_BULL_MARKET
    #         CD_BEAR_MARKET
    #     CD_REASON
    #         MACD_DIFF_TURNS_POSITIVE
    #         MACD_DIFF_TURNS_NEGATIVE
    #         PRICE_RISES_ABOVE_MA
    #         PRICE_FALLS_BELOW_MA
    #         BULL_BARS_TEST_1
    #         BEAR_BARS_TEST_1
    #         T_MINUS_2_BULL_SIGNAL
    #         T_MINUS_2_BEAR_SIGNAL
    #         STOCH_B_A_BULL_SIGNAL
    #         STOCH_A_B_BEAR_SIGNAL
    #         T_PLUS_1_BULL_SIGNAL
    #         T_PLUS_1_BEAR_SIGNAL
    # HIGHS_LOWS: Some high low information
    #     HL_HIGH
    #     HL_LOW
    #     HIGH_INDEX
    #     LOW_INDEX
    #     NEW_HIGH_P
    #     NOW_LOW_P
    # MARKET: what market om i in
    #     MKT_STATUS
    #         M_UNKNOWN
    #         M_BALANCED_AFTER_FALL
    #         M_BALANCED_AFTER_RISE
    #         M_BULL_CONFIRMED
    #         M_BEAR_CONFIRMED
    #     MKT_REASON
    #         any of the above mentioned reasons 
    
    #BULL_MARKET_CONFIRMED = 1
    #BEAR_MARKET_CONFIRMED = 2
    #MARKET_STATUS = 3
    #TRIGGERED_BALANCED_MARKET = 7
    #HIGH_LOW = 8
    #HIGH_LOW_INDEX = 9
    #NEW_HIGH_P = 10
    #NEW_LOW_P = 11
    
    # ii results
    #MACD_DIFF_TURNS_POSITIVE = 'MACD DIFF - -> +' #1
    #MACD_DIFF_TURNS_NEGATIVE = 'MACD DIFF + -> -' #2
    #PRICE_RISES_ABOVE_MA = 'PRICE < -> > MA' #3
    #PRICE_FALLS_BELOW_MA = 'PRICE > -> < MA' #4
    #BULL_BARS_TEST_1 = 'BULL BARS TEST1' #5
    #BEAR_BARS_TEST_1 = 'BEAR BARS TEST1' #6
    #T_MINUS_2_BULL_SIGNAL = 't-2 BULL' #7
    #T_MINUS_2_BEAR_SIGNAL = 't-2 BEAR' #8
    #STOCH_B_A_BULL_SIGNAL = 'STOCH B A SIGNAL' #9
    #STOCH_A_B_BEAR_SIGNAL = 'STOCH A B SIGNAL' #10
    #T_PLUS_1_BULL_SIGNAL = 't+1 BULL' #11
    #T_PLUS_1_BEAR_SIGNAL = 't+1 BEAR' #12
    
    # market stati
    #M_UNKNOWN = 'unknown'
    #M_BALANCED_AFTER_FALL = 'balanced fall'      
    #M_BALANCED_AFTER_RISE = 'balanced rise'
    #M_BULL_CONFIRMED = 'bull confirmed'
    #M_BEAR_CONFIRMED = 'bear confirmed'
    
    FVITA_INTERVAL_STUDIES = {
        'basics': (4,),
        'simple_moving_average_ti': (14,),
        'macd_ti': ((14, 26, 9),),
        'stochastic_osc': ((9, 3, 20),),
        'bollinger_bands': ((5, 2, 14),),
    }
    
    BASIC_INFO = bls.Basics.make_name(4)
    SMA_INFO = bls.SimpleMovingAverageTI.make_name(14)
    MACD_INFO =  bls.MACDTI.make_name(14, 26, 9)
    STOCH_INFO = bls.StochasticOsc.make_name(9, 3, 20)
    BOLLBA_INFO = bls.BOLLIBA.make_name(5, 2)
    
    def __init__(self, *arg_l):
        super().__init__(*arg_l, **self.FVITA_INTERVAL_STUDIES)
        #settings
        self.balanced_market_up_test = 8
        self.balanced_market_down_test = 8
        self.wave_tolerance = 0
        self.wave_tolerance_at_start = False
        #for stats & research, can be removed (everywhere)
        self.stats_confirmed_bull = defaultdict(int)
        self.stats_confirmed_bear = defaultdict(int)
        self.stats_balanced_market_triggers = defaultdict(int)
        self.stats_balanced_market_triggers_reasons = defaultdict(int)
        self.graph_dict = defaultdict(int)
        self.add_fvita_export_items()
        
    def add_fvita_export_items(self):
        self.add_export_item(self.BASIC_INFO,
                             bls.Basics.SPOTTED_PAUSE,
                             str_function=str)
        self.add_export_item(self.BASIC_INFO,
                             bls.Basics.W_DOWN,
                             str_function=str)
        self.add_export_item(self.BASIC_INFO,
                             bls.Basics.W_UP,
                             str_function=str)
        self.add_export_item(self.SMA_INFO,
                             bls.SMA.VALUE,
                             str_function=str)
        self.add_export_item(self.STOCH_INFO,
                             bls.STOCH.K_VALUE,
                             str_function=str)
        self.add_export_item(self.STOCH_INFO,
                             bls.STOCH.GHOST,
                             str_function=str)
        self.add_export_item(self.BOLLBA_INFO,
                             bls.BOLLIBA.LOWER_BAND,
                             str_function=str)
        self.add_export_item(self.BOLLBA_INFO,
                             bls.BOLLIBA.UPPER_BAND,
                             str_function=str)
        self.add_export_item(self.MACD_INFO,
                             bls.MACD.FAST,
                             str_function=str)
        self.add_export_item(self.MACD_INFO,
                             bls.MACD.SLOW,
                             str_function=str)
        self.add_export_item(self.MACD_INFO,
                             bls.MACD.DIFF,
                             str_function=str)
        self.add_export_item(self.MACD_INFO,
                             bls.MACD.DIFF_DELTA,
                             str_function=str)
        #self.add_export_item(self.BASIC_INFO,
                             #bls.Basics.W_UP_W_AND_P_TYPES,
                             #str_function=str)
        #self.add_export_item(self.BASIC_INFO,
                             #bls.Basics.W_UP_W_AND_P_LENGTHS,
                             #str_function=str)
        #self.add_export_item(self.BASIC_INFO,
                             #bls.Basics.W_UP_W_AND_P_INDEXES,
                             #str_function=str)
        #self.add_export_item(self.BASIC_INFO,
                             #bls.Basics.W_DOWN_W_AND_P_TYPES,
                             #str_function=str)
        #self.add_export_item(self.BASIC_INFO,
                             #bls.Basics.W_DOWN_W_AND_P_LENGTHS,
                             #str_function=str)
        self.add_ii_export_item(self.MARKET_STATUS,
                                self.MS_TYPE,
                                str_function=str)
        self.add_ii_export_item(self.BALANCE_TRIGGERED,
                                self.BT_DOWN_COUNT_USED,
                                str_function=str)
        self.add_ii_export_item(self.BALANCE_TRIGGERED,
                                self.BT_UP_COUNT_USED,
                                str_function=str)
        self.add_ii_export_item(
            self.R_AND_S,
            self.S_LEVELS,
            str_function=lambda v: str({x for x in v if x}).replace(',', '->'))
        self.add_ii_export_item(
            self.R_AND_S,
            self.R_LEVELS,
            str_function=lambda v: str({x for x in v if x}).replace(',', '->'))
        
        def st_str(string):
            tr = {
                bls.STOCHASTIC_A: 'A',
                bls.STOCHASTIC_B: 'B',
                bls.GHOST_A: 'a',
                bls.GHOST_B: 'b',
            }
            #t = 'u' if string == bls.UPPER_HOLDS else 'l'
            return tr[string]
        
        def st_y(value, bar):
            if value in (bls.STOCHASTIC_B, bls.GHOST_B):
                return bar.high + 2 * (bar.high / 10000)
            else:
                return bar.low - 2 * (bar.low / 10000)          
        
        self.add_event_export_item(
            self.STOCH_INFO,
            bls.STOCH.STOCHASTIC,
            str_function=st_str,
            y_function= st_y,
            #rgb_t=(122,55,139)
            rgb_t=(205,205,193))
        
        def p_str(string):
            t = '{}'
            b = '1' if '1+1' in string else '2'
            a = '^' if 'down' in string.lower() else '_'
            return t.format(b)
        
        def p_y(value, bar):
            if 'up' in value.lower():
                return bar.high + 0.5 * (bar.high / 10000)
            else:
                return bar.low - 0.5  * (bar.low / 10000)           
        
        self.add_event_export_item(
            self.BASIC_INFO,
            bls.Basics.SPOTTED_PAUSE,
            str_function=p_str,
            y_function= p_y,
            rgb_t=(205,145,158))
        
        def h_str(string):
            tr = {
                self.BOL_UP_BAND_2: 'U',
                self.BOL_UP_BAND_1: 'u',
                self.BOL_LOW_BAND_2: 'L',
                self.BOL_LOW_BAND_1: 'l',
            }
            #t = 'u' if string == bls.UPPER_HOLDS else 'l'
            return tr[string]
        
        def h_y(value, bar):
            if value in (self.BOL_UP_BAND_1, self.BOL_UP_BAND_2):
                return bar.high
            else:
                return bar.low               
        
        self.add_event_export_item(
            self.BOL_HOLD,
            self.BOHO_TYPE,
            str_function=h_str,
            y_function= h_y,
            #rgb_t=(122,55,139)
            rgb_t=(255,0,255))
        
        def ba_str(string):
            tr = {
                self.BA_PAUSE_UP: 'P',
                self.BA_PAUSE_DOWN: 'P',
                self.BA_TOPPING_OF: 'TTT',
                self.BA_BOTTOMING_UP: '___',
            }
            #t = 'u' if string == bls.UPPER_HOLDS else 'l'
            return tr[string]
        
        def ba_y(value, bar):
            if value in (self.BA_PAUSE_UP, self.BA_TOPPING_OF):
                return bar.high
            else:
                return bar.low               
        
        self.add_event_export_item(
            self.BOL_ADVICE,
            self.BA_ADVICE,
            str_function=ba_str,
            y_function= ba_y,
            #rgb_t=(122,55,139)
            rgb_t=(255,0,0))
        
        def move_str(string):
            tr = {
                self.MAX_MOVE_UP: 'M',
                self.MAX_MOVE_DOWN: 'M',
                self.VIRTUAL_MAX_UP: 'V',
                self.VIRTUAL_MAX_DOWN: 'V',
                self.QUASI_MAX_UP: 'Q',
                self.QUASI_MAX_DOWN: 'Q',
                self.R9_UP: 'R',
                self.R9_DOWN: 'R',
                self.BAR_COUNT_RESET: '#',
                self.LOW_BROKEN: 'X',
                self.HIGH_BROKEN: 'X',
            }
            #t = 'u' if string == bls.UPPER_HOLDS else 'l'
            #input('writing move: {}'.format(tr[string]))
            return tr[string]
        
        def move_y(value, bar):
            if value in (self.MAX_MOVE_UP, self.VIRTUAL_MAX_UP, 
                         self.QUASI_MAX_UP, self.R9_UP):
                return bar.high
            elif value in (self.MAX_MOVE_DOWN, self.VIRTUAL_MAX_DOWN, 
                           self.QUASI_MAX_DOWN, self.R9_DOWN):
                return bar.low
            else:
                return (bar.high + bar.low) / 2
        
        self.add_event_export_item(
            self.BALANCE_TRIGGERED,
            self.BT_REASON,
            str_function=move_str,
            y_function= move_y,
            #rgb_t=(122,55,139)
            rgb_t=(255,153,51))
        
        def confirmed_str(string):
            #input ('confirmed offered: {}'.format(string))
            tr = {
                self.CD_BULL_MARKET: 'B',
                self.CD_BEAR_MARKET: 'b',
            }
            #t = 'u' if string == bls.UPPER_HOLDS else 'l'
            #input('writing move: {}'.format(tr[string]))
            return tr[string]
        
        def confirmed_y(value, bar):
            avg = (bar.high + bar.low) / 2  
            if value == self.CD_BULL_MARKET:
                return (avg + bar.high) / 2             
            elif value == self.CD_BEAR_MARKET:
                return (avg + bar.low) / 2
        
        self.add_event_export_item(
            self.CONF_DIRECTION,
            self.CD_TYPE,
            str_function=confirmed_str,
            y_function= confirmed_y,
            #rgb_t=(122,55,139)
            #rgb_t=(255,153,51)
            rgb_t=(255,0,0))
        
        def capfloor_str(string):
            #input ('confirmed offered: {}'.format(string))
            tr = {
                self.T_MIN_2_M_STOCH_B_MACD_NEG: 'T',
                self.T_MIN_2_M_STOCH_B_UNDER_MA: 'T',
                self.T_MIN_1_RISE_STOCH_B_MACD_NEG: 'T',
                self.T_MIN_1_RISE_STOCH_B_UNDER_MA: 'T',
                self.T_MIN_2_R_9_TOPPING: 'T',
                self.T_MIN_2_M_STOCH_A_MACD_POS: '_',
                self.T_MIN_2_M_STOCH_A_ABOVE_MA: '_',
                self.T_MIN_2_R_9_BOTOMMING: '_',
                self.T_MIN_1_RISE_STOCH_A_MACD_POS: '_',
                self.T_MIN_1_RISE_STOCH_A_ABOVE_MA: '_',
            }
            #t = 'u' if string == bls.UPPER_HOLDS else 'l'
            #input('writing move: {}'.format(tr[string]))
            return tr[string]
        
        def capfloor_y(value, bar):
            avg = (bar.high + bar.low) / 2  
            return bar.close           
            if value == self.T_MIN_2_M_STOCH_B_MACD_NEG:
                return bar.close           
            elif value == self.T_MIN_2_M_STOCH_A_MACD_POS:
                return (avg + bar.low) / 2
        
        self.add_event_export_item(
            self.CAP_FLOOR_1,
            self.CF1_REASON,
            str_function=capfloor_str,
            y_function= capfloor_y,
            #rgb_t=(122,55,139)
            #rgb_t=(255,153,51)
            rgb_t=(255,0,0),
            permanent=True)
        
    
    ####################
    ## R & S
    ####################
    R_AND_S = 'R&S'
    S_LEVELS = 0
    R_LEVELS = 1
    def add_10_add_all_resistance_and_support_levels_to_interval_ii(self):
        support_l, resistance_l = [], []
        s_levels, r_levels = [], []
        last_s_level, last_r_level = None, None
        for i in self.intervals:
            support_l.append(i.last(self.BASIC_INFO)[bls.Basics.SUPPORT])
            resistance_l.append(i.last(self.BASIC_INFO)[bls.Basics.RESISTANCE])
        for support in support_l:
            if (support is not None                                   and
                (last_s_level is None
                 or 
                 last_s_level >= support)
            ):
                s_levels.append(support)
                last_s_level = support
            else:
                s_levels.append(None)            
        for resistance in resistance_l:
            if (resistance is not None                                and
                (last_r_level is None
                 or
                 last_r_level <= resistance)
            ):
                r_levels.append(resistance)
                last_r_level = resistance
            else:
                r_levels.append(None)
        for c, i in enumerate(self.intervals):
            i.add_ii_value(self.R_AND_S, (
                s_levels[c:],
                r_levels[c:],
            ))
            
    ####################
    ## BOL BAND HOLDS
    ####################
    BOL_HOLD = 'BOHO'
    BOHO_TYPE = 0
    BOL_UP_BAND_2 = 'bol upper + 2'
    BOL_UP_BAND_1 = 'bol upper + 1'
    BOL_LOW_BAND_2 = 'bol lower + 2'
    BOL_LOW_BAND_1 = 'bol lower + 1'
    def add_10_find_bollinger_holds_ii(self):
        holds = []
        for i in self.intervals:
            hold = i.last(self.BOLLBA_INFO)[bls.BOLLIBA.HOLDS]
            macd_hist = i.last(self.MACD_INFO)[bls.MACD.DIFF]
            if hold ==bls.UPPER_HOLDS:
                if macd_hist < 0:
                    holds.append(self.BOL_UP_BAND_2)
                else:
                    holds.append(self.BOL_UP_BAND_1)
            elif hold == bls.LOWER_HOLDS:
                if macd_hist > 0:
                    holds.append(self.BOL_LOW_BAND_2)
                else:
                    holds.append(self.BOL_LOW_BAND_1)
            else:
                holds.append(None)              
        for c, i in enumerate(self.intervals):
            i.add_ii_value(self.BOL_HOLD, (
                holds[c],
            ))
    
    ####################
    ## BALANCED
    ####################   
    BALANCE_TRIGGERED = 'BT'
    BT_TYPE = 0
    BT_REASON = 1
    BT_UP_COUNT_USED = 2
    BT_DOWN_COUNT_USED = 3
    BALANCED_AT_TOP = 'T' #1
    BALANCED_AT_BOTTEM = 'B' #2
    LOST_COUNT_FOR_DIRECTION = '?' #3
    DIRECTION_INVALIDATED = 'X' #4
    MAX_MOVE_UP = 'max move up' #1
    MAX_MOVE_DOWN = 'max move down' #2
    VIRTUAL_MAX_UP = 'virtual max up' #3
    VIRTUAL_MAX_DOWN = 'virtual max down' #4
    QUASI_MAX_UP = 'quasi max up' #5
    QUASI_MAX_DOWN = 'quasi  max down' #6
    R9_UP = 'R9 up'
    R9_DOWN = 'R9 down'
    BAR_COUNT_RESET = 'bar count reset' #7
    LOW_BROKEN = 'new low in conf bull'
    HIGH_BROKEN = 'new high in conf bear'
    def add_20_triggered_balanced_market_p_ii(self):
        '''Checks if a balance is triggered'''
        last_interval_to_check = len(self.intervals) - 1
        for c, i in enumerate(self.intervals):
            #########
            # gather information
            ##########
            # up, down
            up = i.last(self.BASIC_INFO)[bls.Basics.W_UP]
            down = i.last(self.BASIC_INFO)[bls.Basics.W_DOWN]
            r_up = i.last(self.BASIC_INFO)[bls.Basics.R_UP] or 1
            r_down = i.last(self.BASIC_INFO)[bls.Basics.R_DOWN] or 1
            # resistance / support
            resistance = support = None
            r_and_s = i.last(self.R_AND_S, 2)
            if r_and_s:
                r_l = r_and_s[self.R_LEVELS]
                s_l = r_and_s[self.S_LEVELS]
                resistance = list([x for x in r_l if x is not None])
                resistance = resistance[0] if resistance else None
                support = list([x for x in s_l if x is not None])
                support = support[0] if support else None
            # stoch move of interval t+1
            stoch_move_next_interval = None
            if c < last_interval_to_check:
                next_i = self.intervals[ c + 1 ]
                stoch_move_next_interval = (
                    next_i.last(self.STOCH_INFO)[bls.STOCH.LAST_MOVE]
                )
            #last bar
            last_bar = i.last(i.BARS)
            #hilos
            hilo = i.last(self.HI_LO)
            if hilo:
                last_low = hilo[self.HL_LOW]
                last_high = hilo[self.HL_HIGH]
            else:
                last_low =last_bar.low
                last_high = last_bar.high
            #########
            # adjust up and down
            #########
            if up > down:
                if up > self.balanced_market_up_test:
                    if (down > 2):
                        up = 0
            if down > up:
                if down > self.balanced_market_down_test:
                    if (up > 2):
                        down = 0
            #########
            # last known market status
            #########
            if i[self.MARKET_STATUS]:
                market_status = i.last(self.MARKET_STATUS)[self.MS_TYPE]
            else:
                market_status = self.M_UNKNOWN
                    
            #########
            # check for balanced market
            #########
            #triggered_balanced_market = True
            #if up > self.balanced_market_up_test:
            if (market_status is not self.M_BALANCED_AFTER_RISE       and
                market_status is not self.M_BEAR_CONFIRMED            and # new
                up >= self.balanced_market_up_test):  # moet worden >=
                triggered_balanced_market = self.BALANCED_AT_TOP
                r = self.MAX_MOVE_UP
            #elif down > self.balanced_market_down_test:            
            elif (market_status is not self.M_BALANCED_AFTER_FALL     and
                  market_status is not self.M_BULL_CONFIRMED          and # new
                  down >= self.balanced_market_down_test):  # moet worden >=
                triggered_balanced_market = self.BALANCED_AT_BOTTEM
                r = self.MAX_MOVE_DOWN
            elif (market_status is not self.M_BALANCED_AFTER_RISE     and
                  market_status is not self.M_BEAR_CONFIRMED          and # new
                  up > 2                                              and
                  stoch_move_next_interval == bls.STOCH_A_GA_TO_STOCH_B_GB
                  ):
                triggered_balanced_market = self.BALANCED_AT_TOP
                r = self.VIRTUAL_MAX_UP
            elif (market_status is not self.M_BALANCED_AFTER_FALL     and
                  market_status is not self.M_BULL_CONFIRMED          and # new
                  down > 2                                            and
                  stoch_move_next_interval == bls.STOCH_B_GB_TO_STOCH_A_GA
                  ):
                triggered_balanced_market = self.BALANCED_AT_BOTTEM
                r = self.VIRTUAL_MAX_DOWN
            elif (market_status is not self.M_BALANCED_AFTER_RISE     and
                  market_status is not self.M_BEAR_CONFIRMED          and # new
                  r_up > self.balanced_market_up_test
                  ):
                triggered_balanced_market = self.BALANCED_AT_TOP
                r = self.R9_UP
            elif (market_status is not self.M_BALANCED_AFTER_FALL     and
                  market_status is not self.M_BULL_CONFIRMED          and # new
                  r_down > self.balanced_market_down_test
            ):
                triggered_balanced_market = self.BALANCED_AT_BOTTEM
                r = self.R9_DOWN
            elif (market_status is not self.M_BALANCED_AFTER_RISE     and
                  market_status is not self.M_BEAR_CONFIRMED          and # new
                  resistance is not None                              and
                  up == self.balanced_market_up_test - 1              and
                  last_bar.high > resistance
            ):
                triggered_balanced_market = self.BALANCED_AT_TOP
                r = self.QUASI_MAX_UP
            elif (market_status is not self.M_BALANCED_AFTER_FALL     and
                  market_status is not self.M_BULL_CONFIRMED          and # new
                  support is not None                                 and
                  down == self.balanced_market_down_test - 1          and
                  last_bar.low < support
            ):
                triggered_balanced_market = self.BALANCED_AT_BOTTEM
                r = self.QUASI_MAX_DOWN
            ### new try out, not from book, to adjust strange market stati
            elif (market_status is self.M_BULL_CONFIRMED              and
                  up < 2
            ):
                triggered_balanced_market = self.LOST_COUNT_FOR_DIRECTION
                r = self.BAR_COUNT_RESET
            elif (market_status is self.M_BEAR_CONFIRMED              and
                  down < 2
            ):
                triggered_balanced_market = self.LOST_COUNT_FOR_DIRECTION
                r = self.BAR_COUNT_RESET
            elif (market_status is self.M_BULL_CONFIRMED              and
                  last_bar.low < last_low
            ):
                triggered_balanced_market = self.DIRECTION_INVALIDATED
                r = self.LOW_BROKEN
            elif (market_status is self.M_BEAR_CONFIRMED              and
                  last_bar.high > last_high
            ):
                triggered_balanced_market = self.DIRECTION_INVALIDATED
                r = self.HIGH_BROKEN
            else:
                triggered_balanced_market = None
                r = None
            i.add_ii_value(self.BALANCE_TRIGGERED, (
                triggered_balanced_market,
                r, up, down
            ))
            self.stats_balanced_market_triggers[triggered_balanced_market] += 1
            self.stats_balanced_market_triggers_reasons[r] += 1    
                       
    
    ####################
    ## CONF_DIRECTION
    ####################
    CONF_DIRECTION = 'CD'
    CD_TYPE = 0
    CD_REASON = 1
    CD_BULL_MARKET = 1
    CD_BEAR_MARKET = 2
    MACD_DIFF_TURNS_POSITIVE = 'MACD DIFF - -> +' #1
    MACD_DIFF_TURNS_NEGATIVE = 'MACD DIFF + -> -' #2
    PRICE_RISES_ABOVE_MA = 'PRICE < -> > MA' #3
    PRICE_FALLS_BELOW_MA = 'PRICE > -> < MA' #4
    BULL_BARS_TEST_1 = 'BULL BARS TEST1' #5
    BEAR_BARS_TEST_1 = 'BEAR BARS TEST1' #6
    T_MINUS_2_BULL_SIGNAL = 't-2 BULL' #7
    T_MINUS_2_BEAR_SIGNAL = 't-2 BEAR' #8
    STOCH_B_A_BULL_SIGNAL = 'STOCH B A SIGNAL' #9
    STOCH_A_B_BEAR_SIGNAL = 'STOCH A B SIGNAL' #10
    T_PLUS_1_BULL_SIGNAL = 't+1 BULL' #11
    T_PLUS_1_BEAR_SIGNAL = 't+1 BEAR' #12
    
    def add_21_confirmed_direction_p_ii(self):
        """A direction is confirmed
        -After interval rises/falls for ...
            I understood interval in a balanced market after rise/fall.
            
        """        
        for c, i in enumerate(self.intervals):        
            #########
            # gather information
            #########
            # current balanced market trigger
            balanced_market_triggered, last_bar = (
                i.last(self.BALANCE_TRIGGERED)[self.BT_TYPE],
                i.last(i.BARS)
            )
            #########
            # check for confirmed direction
            #########
            confirmed_direction = reason = None
            #print(curr_bar_triggered_balanced_market, end='')
            if (i[self.MARKET_STATUS]                                 and
                not balanced_market_triggered
            ):
                market_status = i.last(self.MARKET_STATUS)[self.MS_TYPE]
                #print('**',market_status,'**', end='')
                confirmed_direction = None
                if (market_status is self.M_BALANCED_AFTER_FALL       and
                    last_bar.open_ - last_bar.close <= 0):
                    reason = (
                        self.look_for_interval_bull_market_confirmation(c, i))
                    if reason:
                        confirmed_direction = self.CD_BULL_MARKET
                        self.stats_confirmed_bull[reason] +=1
                    #print(bull_market_confirmed)
                elif (market_status is self.M_BALANCED_AFTER_RISE     and
                      last_bar.open_ - last_bar.close >= 0):
                    reason = (
                        self.look_for_interval_bear_market_confirmation(c, i))
                    if reason:
                        confirmed_direction = self.CD_BEAR_MARKET
                        self.stats_confirmed_bear[reason] += 1
                    #print(bear_market_confirmed)
            i.add_ii_value(self.CONF_DIRECTION, (
                confirmed_direction,
                reason,
            ))
            
    def look_for_interval_bull_market_confirmation(self, c, i):
        #########
        # gather information
        #########
        up = i.last(self.BALANCE_TRIGGERED)[self.BT_UP_COUNT_USED]
        #print('up:', c, '|', up)
        if up >= self.balanced_market_up_test or up == 0:
            return
        if self.macd_rises_from_negative_to_positive(i):
            return self.MACD_DIFF_TURNS_POSITIVE
        if self.price_rises_above_ma(i):
            return self.PRICE_RISES_ABOVE_MA
        if self.last_4_bars_bull_test_1(i):
            return self.BULL_BARS_TEST_1
        if self.t_minus_2_signals_bull_market(c):
            return self.T_MINUS_2_BULL_SIGNAL
        if self.stoch_B_A_bull_signal(i):
            return self.STOCH_B_A_BULL_SIGNAL
        if self.t_plus_1_high_of_2_last_bars(c):
            return self.T_PLUS_1_BULL_SIGNAL
        return False
    
    def look_for_interval_bear_market_confirmation(self, c, i):
        #########
        # gather information
        #########
        down = i.last(self.BALANCE_TRIGGERED)[self.BT_DOWN_COUNT_USED]
        #print('down', c, '|', down)
        if down >= self.balanced_market_down_test or down == 0:
            return
        if self.macd_falls_from_positive_to_negative(i):
            return self.MACD_DIFF_TURNS_NEGATIVE
        if self.price_falls_below_ma(i):
            return self.PRICE_FALLS_BELOW_MA
        if self.last_4_bars_bear_test_1(i):
            return self.BEAR_BARS_TEST_1
        if self.t_minus_2_signals_bear_market(c):
            return self.T_MINUS_2_BEAR_SIGNAL
        if self.stoch_A_B_bear_signal(i):
            return self.STOCH_A_B_BEAR_SIGNAL
        if self.t_plus_1_low_of_2_last_bars(c):
            return self.T_PLUS_1_BEAR_SIGNAL
        return False
    
    def macd_rises_from_negative_to_positive(self, interval):
        macd_diff_turned_positive = (
            interval.last(self.MACD_INFO)[bls.MACD.DIFF_FLIP] == bls.TURNED_POS
        )
        return macd_diff_turned_positive
    
    def macd_falls_from_positive_to_negative(self, interval):
        macd_diff_turned_negative = (
            interval.last(self.MACD_INFO)[bls.MACD.DIFF_FLIP] == bls.TURNED_NEG
        )
        return macd_diff_turned_negative
    
    @staticmethod
    def price_rises_above_ma(interval):
        sma_info = interval.last(FVITAOriginal.SMA_INFO)
        trend = sma_info[bls.SMA.TREND]
        reversal = sma_info[bls.SMA.REVERSAL]
        price_rises_above_ma = trend is bls.RISING and reversal
        return price_rises_above_ma
    
    @staticmethod
    def price_falls_below_ma(interval):
        sma_info = interval.last(FVITAOriginal.SMA_INFO)
        trend = sma_info[bls.SMA.TREND]
        reversal = sma_info[bls.SMA.REVERSAL]
        price_falls_below_ma = trend is bls.FALLING and reversal
        return price_falls_below_ma
    
    def last_4_bars_bull_test_1(self,interval):
        """a bull bar test
        -Price line rises for four bars
           I understood the close of the last four bars was always up
           from the previous close.
        -fourth bar close up from the OPENING (c bear version) value
           I undersood the close of the fourth bar is higher then the
           open of the fourth bar.
        -fourth bar closes above the high of previous three bars
           I think this was clear
           
        """
        interval_bars = interval[interval.BARS]
        up = interval.last(self.BALANCE_TRIGGERED)[self.BT_UP_COUNT_USED]
        #if len(interval_bars) < 5:
            #return False
        #bbbbl, bbbl, bbl, bl, l = interval_bars[-5:]
        #if bbbbl.close < bbbl.close < bbl.close < bl.close < l.close:
            #close = l.close
            #for t in (l.open_, bl.high, bbl.high, bbbl.high):
                #if close < t:
                    #break
            #else:
                #return True
        #return False
        if up == 4:
            #print("#### UP ####")
            bbbl, bbl, bl, l = interval_bars[-4:]
            close = l.close
            for t in (l.open_, bl.high, bbl.high, bbbl.high):
                if close < t:
                    break
            else:
                #print("#### UP ####")
                return True
        return False
        
    def last_4_bars_bear_test_1(self,interval):
        """a bear bar test
        -Price line falls for four bars
           I understood the close of the last four bars was always
           below the previous close.
        -fourth bar close up from the STARTING (c bull version) value
           I undersood the close of the fourth bar is lower then the
           open of the fourth bar.
        -fourth bar closes below the low of previous three bars
           I think this was clear
           
        """
        interval_bars = interval[interval.BARS]
        down = interval.last(self.BALANCE_TRIGGERED)[self.BT_DOWN_COUNT_USED]
        #if len(interval_bars) < 5:
            #return False
        #bbbbl, bbbl, bbl, bl, l = interval_bars[-5:]
        #if bbbbl.close > bbbl.close > bbl.close > bl.close > l.close:
            #close = l.close
            #for t in (l.open_, bl.low, bbl.low, bbbl.low):
                #if close > t:
                    #break 
            #else:
                #return True
        #return False
        if down == 4:
            #print("#### DOWN ####")
            bbbl, bbl, bl, l = interval_bars[-4:]
            close = l.close
            for t in (l.open_, bl.low, bbl.low, bbbl.low):
                if close > t:
                    break 
            else:
                #print("#### DOWN ####")
                return True
        return False
    
    def t_minus_2_signals_bull_market(self, index):
        """a bull t-2 test
        -After interval t-2 rises for ...
            I understood t-2 in a balanced market after rise, or is
            confirmed bear (by def only exists after a balanced rise)
        -market t-2 falls by more then 2 bars without reaching the
         last low, then rebounds above the last high reached before the
         fall
            I implemented: when a new high is reached, check if you can
            find two lower bars and check you never set a new low between
            now and the last balanced market trigger.
        """
        t = index - 2
        if index < 0: #negative intervals can't exist
            return False
        interval = self.intervals[t]
        if not interval[self.MARKET_STATUS]:
            return False
        #########
        # gather information
        #########
        # curr bar in t - 2
        curr_bar_high = interval.last(interval.BARS).high
        # market status of i - 2  
        market_status = interval.last(self.MARKET_STATUS)[self.MS_TYPE]
        #last high
        last_high = interval.last(self.HI_LO)[self.HL_HIGH]
        #########
        # check signals
        #########
        if (market_status is self.M_BALANCED_AFTER_RISE               and
            curr_bar_high > last_high
        ):
            for c, hilo in enumerate(reversed(interval[self.HI_LO]), 2):
                if (interval.last(self.BALANCE_TRIGGERED, c)[self.BT_TYPE]
                    or 
                    hilo[self.NEW_HIGH_P]
                ):
                    if c == 2:
                        #print('prev bar set new high, no bull signal')
                        return False
                    break
            trigger_index = c
            #print(trigger_index, '|', interval.last(self.HI_LO, trigger_index))
            low = interval.last(self.HI_LO, trigger_index)[self.HL_LOW]
            if (interval.fell_min_n_bars_since(2, trigger_index)   and
                not interval.fell_below_n_after(low, trigger_index)
            ):
                #input('found t-minus_2_bull signal')
                return True
            #input("mbalanced, higher high, no signal")
        return False       
        
    def t_minus_2_signals_bear_market(self, index):
        """a bull t-2 test
        -After interval t-2 rises for ...
            I understood t-2 in a balanced market after fall, or is
            confirmed bull (by def only exists after a balanced fall)
        c bull
        """
        t = index - 2
        if t < 0: #negative intervals can't exist
            return False
        interval = self.intervals[t]
        if not interval[self.MARKET_STATUS]:
            return False
        #########
        # gather information
        #########
        # curr bar in t - 2
        curr_bar_low = interval.last(interval.BARS).low
        # market status of i - 2  
        market_status = interval.last(self.MARKET_STATUS)[self.MS_TYPE]  
        #last high, last low
        last_low = interval.last(self.HI_LO)[self.HL_LOW]
        #########
        # check signals
        #########
        if (market_status is self.M_BALANCED_AFTER_FALL               and
            curr_bar_low < last_low
        ):
            for c, hilo in enumerate(reversed(interval[self.HI_LO]), 2):
                if (interval.last(self.BALANCE_TRIGGERED, c)[self.BT_TYPE]
                    or 
                    hilo[self.NEW_LOW_P]
                ):
                    if c == 2:
                        #print('prev bar set new high, no bull signal')
                        return False
                    break
            trigger_index = c
            #print(trigger_index, len(curr_interv.subclass_values[self.HIGH_LOW]))
            high = interval.last(self.HI_LO, trigger_index)[self.HL_HIGH]
            if (interval.rose_min_n_bars_since(2, trigger_index)   and
                not interval.rose_above_n_after(high, trigger_index)
            ):
                #input('found t-minus_2_bear signal')
                return True
            #input("mbalanced, lower low, no signal")
        return False
    
    def stoch_B_A_bull_signal(self, interval):
        """a stoch b a bull signal
        -After falling from stochastic_B to stochastic_A
          Pretty wel defined, i guess
        -and by at least eight bars or virtual eight bars.
          because being in a balanced market was a precondition to
          this test, I don't really understand this (exclude the
          quasi eight bars?).
        -closing above the half way line between stochastic-A and
         stochastic_B.
          What is the halfway line? Stochastic crosses 50? the halfway
          between the high in stoch_B and the low in stoch-A? Something
          else? I implemented the second method. The halfway between the
          high and the low.
        """
        #########
        # gather information
        #########
        last_bar = interval.last(interval.BARS)
        # last close
        last_close = last_bar.close
        # last stochastic move
        stoch_info = interval.last(self.STOCH_INFO)
        last_move = stoch_info[bls.STOCH.LAST_MOVE]
        start_index = stoch_info[bls.STOCH.MOVE_START_INDEX]
        stop_index = stoch_info[bls.STOCH.MOVE_STOP_INDEX]            
        if last_move == bls.STOCH_B_GB_TO_STOCH_A_GA:
            start_value = interval.interval_bars[start_index].high
            end_value = interval.interval_bars[stop_index].low
            mid_value = (start_value + end_value) / 2
        else:
            last_move = False
        #########
        # check signals
        #########
        if last_move and last_close > mid_value:
            #input('ole bull')
            return True
        return False
    
    def stoch_A_B_bear_signal(self, interval):
        """a stoch a b bear signal
        -c stoch b a bull signal
        """
        #########
        # gather information
        #########
        last_bar = interval.last(interval.BARS)
        # last close
        last_close = last_bar.close
        # last stochastic move
        stoch_info = interval.last(self.STOCH_INFO)
        last_move = stoch_info[bls.STOCH.LAST_MOVE]
        start_index = stoch_info[bls.STOCH.MOVE_START_INDEX]
        stop_index = stoch_info[bls.STOCH.MOVE_STOP_INDEX]  
        if last_move == bls.STOCH_A_GA_TO_STOCH_B_GB:
            start_value = interval.interval_bars[start_index].low
            end_value = interval.interval_bars[stop_index].high
            mid_value = (start_value + end_value) / 2
        else:
            last_move = False
        #########
        # check signals
        #########
        if last_move and last_close < mid_value:
            #input('ole bear')
            return True
        return False
    
    def t_plus_1_high_of_2_last_bars(self, index):
        """a t plus 1 test
        -in interval t+1, current bar closes above the high of the last
         two bars before the low was reached.
          What is the last low? A good definition somewhere? Read the
          add_xx_high_low_ii for some more info.
        -The two last bars before the low?
          I took the two bars before the low, no tests not nothing.
          What if the before last was a high and the bblast a low,
          lower than this one. think, think, ...
        """
        last_close = None
        t = index + 1
        if t >= len(self.intervals): #last interval has no t + 1
            return False
        interval = self.intervals[t]
        #########
        # gather information
        #########
        # low & low index
        up = interval.last(self.BALANCE_TRIGGERED)[self.BT_UP_COUNT_USED]
        low = interval.last(self.HI_LO)[self.HL_LOW]
        if low and up and up < self.balanced_market_up_test:
            low_index = interval.last(self.HI_LO)[self.LOW_INDEX] - 1 # decrease it c add_xx_high_low:
            if low_index > 2:
                high = max(
                    interval.last(interval.BARS, low_index - 1).high,
                    interval.last(interval.BARS, low_index - 2).high,
                )
            else:
                high = low / 2
            last_close = interval.last(interval.BARS).close
        #########
        # check signals
        #########
        if low is not None and last_close is not None and last_close > high:
            return True
        return False
    
    def t_plus_1_low_of_2_last_bars(self, index):
        """a t plus 1 test
        c bull version
        """
        last_close = None
        t = index + 1
        if t >= len(self.intervals): #last interval has no t + 1
            return False
        interval = self.intervals[t]
        #########
        # gather information
        #########
        # low & low index
        down = interval.last(self.BALANCE_TRIGGERED)[self.BT_DOWN_COUNT_USED]
        high = interval.last(self.HI_LO)[self.HL_HIGH]
        if high and down and down < self.balanced_market_down_test:
            high_index = interval.last(self.HI_LO)[self.HIGH_INDEX] - 1 # decrease it c add_xx_high_low:
            if high_index > 2:
            #print('### HIGH interval#, index, value ###', t, high_index, high)
                low = min(
                    interval.last(interval.BARS, high_index - 1).low,
                    interval.last(interval.BARS, high_index - 2).low
                )
            else:
                low = high * 2
            last_close = interval.last(interval.BARS).close
            #print('### low, last close ###', low, last_close)
        #########
        # check signals
        #########
        if high is not None and last_close is not None and last_close < low:
            return True
        return False
    
    def add_22_higher_order_turns(self):
        """Higher order turns, also turn lower order intervals.
        -When interval turns from bear or balanced market to
         bull market
          I understood, from a balanced falling to a bull market,
          or from a balanced rising to a bear. But when?? is it when
          confirmed? can i state this true when confirmed, or only at
          the turning point. And maybe when confirmed in t, t-? already
          allready signaled it and moved on?
          All deficult questions, with a lot of room for improvement.
          for now, i skip this rule. I guess most lower order trades
          already moved on. room for imporvement??
          
        """
        pass
    
    ####################
    ## CAP & FLOOR RULE I
    ####################
    CAP_FLOOR_1 = 'CF_1'
    CF1_TYPE = 0
    CF1_REASON = 1
    CF1_TOPPING_OF = 1
    CF1_BOTTOM_UP = 2
    T_MIN_2_M_STOCH_B_MACD_NEG = 'RULE 1'
    T_MIN_2_M_STOCH_B_UNDER_MA = 'RULE 2'
    T_MIN_1_RISE_STOCH_B_MACD_NEG = 'RULE 3'
    T_MIN_1_RISE_STOCH_B_UNDER_MA = 'RULE 4'
    T_MIN_2_M_STOCH_B_3_WAVES_IN_T_MIN_2_2 = 'RULE 5'
    T_MIN_2_R_9_TOPPING = 'RULE 6'
    T_MIN_2_M_STOCH_A_MACD_POS = 'RULE 1'
    T_MIN_2_M_STOCH_A_ABOVE_MA = 'RULE 2'
    T_MIN_1_RISE_STOCH_A_MACD_POS = 'RULE 3'
    T_MIN_1_RISE_STOCH_A_ABOVE_MA = 'RULE 4'
    T_MIN_2_M_STOCH_A_3_WAVES_IN_T_MIN_2_2 = 'RULE 5'
    T_MIN_2_R_9_BOTOMMING = 'RULE 6'
    
    def add_23_cap_floor_rule_1_ii(self):
        '''Check for marke cap or floor rule 1'''
        for c, i in enumerate(self.intervals):
            #########
            # gather information
            ##########
            if i[self.MARKET_STATUS]:
                last_market_status = i.last(self.MARKET_STATUS)[self.MS_TYPE]
            else:
                last_market_status = self.M_UNKNOWN
            curr_balance = i.last(self.BT_TYPE)
            curr_conf_direction = i.last(self.CONF_DIRECTION)[self.CD_TYPE]
            #########
            # Check for cap rules
            #########
            if ((last_market_status == self.M_BEAR_CONFIRMED          and
                curr_balance == self.BALANCED_AT_BOTTEM)
                or
                curr_conf_direction == self.CD_BEAR_MARKET
            ):
                print('{}/ last_market_status {} | curr_bal {} | curr_conf_dir {}'.format(
                    c, last_market_status, curr_balance, curr_conf_direction))
                rule, reason = self.check_for_bear_market_cap_rule_1(c, i)
            elif ((last_market_status == self.M_BULL_CONFIRMED        and
                   curr_balance == self.BALANCED_AT_TOP)
                  or
                  curr_conf_direction == self.CD_BULL_MARKET
            ):
                rule, reason = self.check_for_bull_market_floor_rule_1(c,i)
            else:
                rule, reason = None, None
            i.add_ii_value(self.CAP_FLOOR_1, (
                rule,
                reason,
            ))
    
    def check_for_bear_market_cap_rule_1(self, c, i):
        rule, reason = None, None
        curr_bar = i.last(i.BARS)
        i_sma = i.last(self.SMA_INFO)[bls.SMA.VALUE]
        i_macd_diff = i.last(self.MACD_INFO)[bls.MACD.DIFF]
        if c >= 2:
            i_min_2 = self.intervals[c-2]
            if i_min_2.at_end_of_period:
                r_up = i_min_2.last(self.BASIC_INFO)[bls.Basics.R_UP] or 1
                i_min_2_balanced = (
                    i_min_2.last(self.BALANCE_TRIGGERED)[self.BT_TYPE]
                )  
                i_min_2_stochastic = (
                    i_min_2.last(self.STOCH_INFO)[bls.STOCH.STOCHASTIC]
                )
                if (i_macd_diff < 0                                  and
                    i_min_2_balanced == self.BALANCED_AT_TOP         and #or
                    i_min_2_stochastic in (bls.STOCHASTIC_B, bls.GHOST_B)
                ):
                    print('{}/cap rule 1: balanced {} | stoch {} | macd {}'.format(
                        c, i_min_2_balanced, i_min_2_stochastic, i_macd_diff,))
                    rule, reason = self.CF1_TOPPING_OF, self.T_MIN_2_M_STOCH_B_MACD_NEG
                elif (i_sma and curr_bar.close < i_sma               and
                      i_min_2_balanced == self.BALANCED_AT_TOP       and
                      i_min_2_stochastic in (bls.STOCHASTIC_B, bls.GHOST_B)
                ):
                    rule, reason = self.CF1_TOPPING_OF, self.T_MIN_2_M_STOCH_B_UNDER_MA
                    print('{}/cap rule 1: balanced {} | stoch {} | sma {}'.format(
                        c, i_min_2_balanced, i_min_2_stochastic, i_sma))
                elif (r_up == self.balanced_market_up_test + 1):
                    rule, reason = self.CF1_TOPPING_OF, self.T_MIN_2_R_9_TOPPING
                    print('{}/cap rule 1: balanced {} | stoch {} | R_UP {}'.format(
                        c, i_min_2_balanced, i_min_2_stochastic, r_up))                    
                ### rule 5 not implemented, 3 waves down??
        if not rule and c > 0:   
            i_min_1 = self.intervals[c-1]
            if i_min_1.at_end_of_period:
                i_min_strict_up = i_min_1.last(self.BASIC_INFO)[bls.Basics.LOOSE_UP]
                print('strict up: ', i_min_strict_up)
                i_min_stochastic = (
                    i_min_1.last(self.STOCH_INFO)[bls.STOCH.STOCHASTIC]
                )
                if (i_macd_diff < 0                                       and
                    i_min_strict_up == 4                                  and
                    i_min_stochastic in (bls.STOCHASTIC_B, bls.GHOST_B)
                ):
                    print('{}/cap rule 1: up count {} | stoch {} | macd {}'.format(
                        c, i_min_strict_up, i_min_stochastic, i_macd_diff,))
                    rule, reason = self.CF1_TOPPING_OF, self.T_MIN_1_RISE_STOCH_B_MACD_NEG
                elif (i_sma and curr_bar.close < i_sma                    and
                      i_min_strict_up == 4                                and
                      i_min_stochastic in (bls.STOCHASTIC_B, bls.GHOST_B)
                ):
                    rule, reason = self.CF1_TOPPING_OF, self.T_MIN_1_RISE_STOCH_B_UNDER_MA
                    print('{}/cap rule 1: up count {} | stoch {} | sma {}'.format(
                        c, i_min_strict_up, i_min_stochastic, i_sma))                
        return rule, reason
    
    def check_for_bull_market_floor_rule_1(self, c, i):
        rule, reason = None, None
        curr_bar = i.last(i.BARS)
        i_sma = i.last(self.SMA_INFO)[bls.SMA.VALUE]
        i_macd_diff = i.last(self.MACD_INFO)[bls.MACD.DIFF]
        if c >= 2:
            i_min_2 = self.intervals[c-2]
            if i_min_2.at_end_of_period:
                r_down = i_min_2.last(self.BASIC_INFO)[bls.Basics.R_DOWN] or 1
                i_min_2_balanced = (
                    i_min_2.last(self.BALANCE_TRIGGERED)[self.BT_TYPE]
                )  
                i_min_2_stochastic = (
                    i_min_2.last(self.STOCH_INFO)[bls.STOCH.STOCHASTIC]
                )
                if (i_macd_diff > 0                                   and
                    (i_min_2_balanced == self.BALANCED_AT_BOTTEM
                     and #or
                     i_min_2_stochastic in (bls.STOCHASTIC_A, bls.GHOST_A))
                ):
                    rule, reason = self.CF1_BOTTOM_UP, self.T_MIN_2_M_STOCH_A_MACD_POS
                    print('{}/floor rule 1: balanced {} | stoch {} | macd {}'.format(
                        c, i_min_2_balanced, i_min_2_stochastic, i_macd_diff))
                elif (i_sma and curr_bar.close > i_sma                 and
                      i_min_2_balanced == self.BALANCED_AT_BOTTEM     and
                      i_min_2_stochastic in (bls.STOCHASTIC_A, bls.GHOST_A)
                ):
                    rule, reason = self.CF1_BOTTOM_UP, self.T_MIN_2_M_STOCH_A_ABOVE_MA
                    print('{}/floor rule 1: balanced {} | stoch {} | sma {}'.format(
                        c, i_min_2_balanced, i_min_2_stochastic, i_sma))
                elif (r_down == self.balanced_market_down_test + 1):
                    rule, reason = self.CF1_BOTTOM_UP, self.T_MIN_2_R_9_BOTOMMING
                    print('{}/floor rule 1: balanced {} | stoch {} | R_DOWN {}'.format(
                        c, i_min_2_balanced, i_min_2_stochastic, r_down))
                ### rule 5 not implemented, 3 waves up??
        if not rule and c > 0:                
            i_min_1 = self.intervals[c-1]
            if i_min_1.at_end_of_period:
                i_min_strict_down = i_min_1.last(self.BASIC_INFO)[bls.Basics.LOOSE_DOWN]
                print('strict down: ', i_min_strict_down)
                i_min_stochastic = (
                    i_min_1.last(self.STOCH_INFO)[bls.STOCH.STOCHASTIC]
                )
                if (i_macd_diff > 0                                       and
                    i_min_strict_down == 4                                and #or
                    i_min_stochastic in (bls.STOCHASTIC_A, bls.GHOST_A)
                ):
                    rule, reason = self.CF1_BOTTOM_UP, self.T_MIN_1_RISE_STOCH_A_MACD_POS
                    print('{}/floor rule 1: down count {} | stoch {} | macd {}'.format(
                        c, i_min_strict_down, i_min_stochastic, i_macd_diff))
                elif (i_sma and curr_bar.close > i_sma                    and
                      i_min_strict_down == 4                              and
                      i_min_stochastic in (bls.STOCHASTIC_A, bls.GHOST_A)
                ):
                    rule, reason = self.CF1_BOTTOM_UP, self.T_MIN_1_RISE_STOCH_A_ABOVE_MA
                    print('{}/floor rule 1: down count {} |stoch {} | sma {}'.format(
                        c, i_min_strict_down, i_min_stochastic, i_sma))                
        return rule, reason
    
    ####################
    ## HIGH LOW
    ####################    
    HI_LO = 'HL'
    HL_HIGH = 0
    HL_LOW = 1
    HIGH_INDEX = 2
    LOW_INDEX = 3
    NEW_HIGH_P = 4
    NEW_LOW_P = 5
    def add_90_high_low_ii(self):
        """Adding a high and low value.
        Setting it as one of the last values, becaus previous ii are
        probably only interested in het last(previous) values.
        As a result the index that is returned is one of
        !! decrease the index by one (it's negative) if you are using the
           index in the nex run!!
        The term is often used but not well defined so far.
        I implemented:
        if a stable_market is triggerd the high and low of the interval
        are set to the highest and lowest values in the bars that triggered
        the stable market.
        When the market is not a stable market, the high and low will be
        the max (min) of the initial values and the new bars.
        So max and min are (re)set when the stable market is triggered and
        eventualy moved with the other bars.
        For a stable market rising. I use all the bars from the last until
        i find a bar with a higher high then the one before. For a stable
        market falling it are the bars until i find a bar with a lower low
        then the one before. There may be room for improvement.
        """
        for c, interval in enumerate(self.intervals):
            new_high_p = new_low_p = False
            last_bar = interval.last(interval.BARS)
            #########
            # gather information
            #########
            # confirmed direction
            confirmed_direction = (
                interval.last(self.CONF_DIRECTION)[self.CD_TYPE]
            )
            # balanced market triggered
            balanced_market_triggered = (
                interval.last(self.BALANCE_TRIGGERED)[self.BT_TYPE]
            )
            # get bars
            bars = interval.interval_bars
            # last high low
            if interval[self.HI_LO]:
                last_high = interval.last(self.HI_LO)[self.HL_HIGH]
                last_low = interval.last(self.HI_LO)[self.HL_LOW]
                last_high_index = interval.last(self.HI_LO)[self.HIGH_INDEX]
                last_low_index = interval.last(self.HI_LO)[self.LOW_INDEX]
            else:
                last_high = last_low = last_high_index = last_low_index = None
            high, low, high_index, low_index = (
                last_high, last_low, last_high_index, last_low_index) 
                
            #########
            # search high & low
            #########
            if (confirmed_direction == self.CD_BULL_MARKET
                or
                balanced_market_triggered == self.BALANCED_AT_TOP
            ):
                #print('interval: ', c)
                used_up_count = interval.last(
                    self.BALANCE_TRIGGERED)[self.BT_UP_COUNT_USED]
                #print('  used up count: ', used_up_count)
                low = bars[-used_up_count].low
                #print('  low: ', low)
                #print('  nr of bars: ', len(bars))
                #print('  prev low: ', bars[-used_up_count -1])
                if (len(bars) > used_up_count                         and
                    bars[-used_up_count -1].low < low
                ):
                    used_up_count += 1
                    low = bars[-used_up_count].low
                high, high_index = max(
                    [(x.high, i) 
                     for i, x in enumerate(bars[-used_up_count:])])
                low_index = used_up_count
                high_index = used_up_count - high_index
                
            elif (confirmed_direction == self.CD_BEAR_MARKET
                  or
                  balanced_market_triggered == self.BALANCED_AT_BOTTEM
            ):
                used_down_count = interval.last(
                    self.BALANCE_TRIGGERED)[self.BT_DOWN_COUNT_USED]
                high = bars[-used_down_count].high
                if (len(bars) > used_down_count                         and
                    bars[-used_down_count -1].high < high
                ):
                    used_down_count += 1
                    high = bars[-used_down_count].high
                low, low_index =  min(
                    [(x.low, i) 
                     for i,x in enumerate(reversed(bars[-used_down_count:]),1)])
                high_index = used_down_count 
            elif last_high:
                if last_bar.high > last_high:
                    high = last_bar.high
                if last_bar.low < last_low:
                    low = last_bar.low
                low_index = last_low_index - 1
                high_index = last_high_index - 1   
            interval.add_ii_value(self.HI_LO, (
                high, 
                low,
                high_index,
                low_index,
                not high == last_high,
                not low == last_low,
            ))              
            #if balanced_market_triggered:
                #last_low, last_high= last_bar.low, last_bar.high
                #last_low_index = last_high_index = -1
                #new_high_p = new_low_p = True
                #if balanced_market_triggered == self.BALANCED_AT_TOP:
                    #for c, new_bar in enumerate(
                        #reversed(interval.interval_bars[:-1]), 2
                    #):
                        #if new_bar.high > last_bar.high:
                            #break
                        #if new_bar.low < last_low:
                            #last_low = new_bar.low
                            #last_low_index = -c                    
                        #last_bar = new_bar                
                #elif balanced_market_triggered == self.BALANCED_AT_BOTTEM:
                    #for c, new_bar in enumerate(
                        #reversed(interval.interval_bars[:-1]), 2
                    #):
                        #if new_bar.low < last_bar.low:
                            #break
                        #if new_bar.high > last_high:
                            #last_high = new_bar.high
                            #last_high_index = -c
                        #last_bar = new_bar
                #new_low, new_high = last_low, last_high
            #elif last_high:
                #if last_bar.high > last_high:
                    #new_high = last_bar.high
                    #new_high_p = True
                    #last_high_index = -1
                #else:
                    #new_high = last_high
                    #last_high_index -= 1
                #if last_bar.low < last_low:
                    #new_low = last_bar.low
                    #new_low_p = True
                    #last_low_index = -1
                #else:
                    #new_low = last_low
                    #last_low_index -= 1 
            #else:
                #new_high = new_low = None
            #interval.add_ii_value(self.HI_LO, (
                #new_high, 
                #new_low,
                #last_high_index,
                #last_low_index,
                #new_high_p,
                #new_low_p,
            #)) 
    
    ####################
    ## MARKET_STATUS
    ####################   
    MARKET_STATUS = 'MS'
    MS_TYPE = 0
    MS_REASON = 1
    M_UNKNOWN = 'unknown'
    M_BALANCED_AFTER_FALL = 'balanced fall'      
    M_BALANCED_AFTER_RISE = 'balanced rise'
    M_BULL_CONFIRMED = 'bull confirmed'
    M_BEAR_CONFIRMED = 'bear confirmed'
    
            
    def add_98_market_status_ii(self):
        """Set the market stati for the intervals.
        
        I dont remove the market status if the start value of the rise
        or fall are broken. Should I?
        """
        for interval in self.intervals:
            #print('adding interval market status')
            #########
            # gather information
            #########
            # prev status
            prev_status = interval.last(self.MARKET_STATUS)
            # confirmed direction
            confirmed_direction = (
                interval.last(self.CONF_DIRECTION)[self.CD_TYPE]
            )
            balanced_market_triggered = (
                interval.last(self.BALANCE_TRIGGERED)[self.BT_TYPE]
            )
            #########
            # set market_status
            #########
            reason = '--'
            if not prev_status:
                status = self.M_UNKNOWN
            else:
                status = prev_status[self.MS_TYPE]
                if balanced_market_triggered:
                    reason = (
                        interval.last(self.BALANCE_TRIGGERED)[self.BT_REASON]
                    )
                    if balanced_market_triggered is self.BALANCED_AT_TOP:
                        status = self.M_BALANCED_AFTER_RISE
                    elif balanced_market_triggered is self.BALANCED_AT_BOTTEM:
                        status = self.M_BALANCED_AFTER_FALL
                    elif balanced_market_triggered is self.LOST_COUNT_FOR_DIRECTION:
                        status = self.M_UNKNOWN
                    elif balanced_market_triggered is self.DIRECTION_INVALIDATED:
                        status = self.M_UNKNOWN
                elif confirmed_direction:
                    reason = (
                        interval.last(self.CONF_DIRECTION)[self.CD_REASON]
                    )
                    if confirmed_direction is self.CD_BULL_MARKET:
                        status = self.M_BULL_CONFIRMED
                    elif confirmed_direction is self.CD_BEAR_MARKET:
                        status = self.M_BEAR_CONFIRMED     
            #print('start')    
            interval.add_ii_value(self.MARKET_STATUS, (
                status, 
                reason,
            ))   
            #print('done')    
    
    ####################
    ## BOL ANALYSIS
    ####################   
    BOL_ADVICE = 'BOLADV'
    BA_ADVICE = 0
    BA_PAUSE_UP = 'upper band as pausing point'
    BA_PAUSE_DOWN = 'lower band as pausing point'
    BA_TOPPING_OF = 'bear market caps (R2)'
    BA_BOTTOMING_UP = 'bull market floor (R2)'
            
    def add_99_bol_analysis_ii(self):     
        result = [None,]
        for c, i in enumerate(self.intervals[1:], 1):
            last_market_status = i.last(self.MARKET_STATUS)[self.MS_TYPE]
            ip = self.intervals[c + 1] if c + 1 < len(self.intervals) else i
            i_ = self.intervals[c - 1]
            i__ = self.intervals[c - 2] if c > 1 else i_
            ibolhold = i.last(self.BOL_HOLD)[self.BOHO_TYPE]
            ipbolhold = ip.last(self.BOL_HOLD)[self.BOHO_TYPE]
            i_bolhold = i_.last(self.BOL_HOLD)[self.BOHO_TYPE]
            i__bolhold = i__.last(self.BOL_HOLD)[self.BOHO_TYPE]
            i_stoch = i_.last(self.STOCH_INFO)[bls.STOCH.STOCHASTIC]
            i__stoch = i__.last(self.STOCH_INFO)[bls.STOCH.STOCHASTIC]
            i__balanced = i__.last(self.BALANCE_TRIGGERED)[self.BT_TYPE]
            if (len(self.intervals) > 2                                 and
                last_market_status == self.M_BEAR_CONFIRMED             and
                (self.BOL_UP_BAND_2 in (i_bolhold, i__bolhold)     and
                 i__balanced == self.BALANCED_AT_TOP)
            ):
                #input('3333333333333333333333333333333333333333333333')
                result.append(self.BA_TOPPING_OF)
            elif (len(self.intervals) > 2                                 and
                last_market_status == self.M_BULL_CONFIRMED               and
                (self.BOL_LOW_BAND_2 in (i_bolhold, i__bolhold)     and
                 i__balanced == self.BALANCED_AT_BOTTEM)
            ):
                #input('4444444444444444444444444444444444444444444444')
                result.append(self.BA_BOTTOMING_UP)
            elif (last_market_status == self.M_BEAR_CONFIRMED           and
                (i_stoch in (bls.STOCHASTIC_B, bls.GHOST_B)
                 or
                 i__stoch in (bls.STOCHASTIC_B, bls.GHOST_B))           and
                ibolhold in (self.BOL_UP_BAND_1, self.BOL_UP_BAND_2)):
                result.append(self.BA_PAUSE_UP)
            elif (last_market_status == self.M_BULL_CONFIRMED           and
                (i_stoch in (bls.STOCHASTIC_B, bls.GHOST_B)
                 or
                 i__stoch in (bls.STOCHASTIC_B, bls.GHOST_B))           and
                ibolhold in (self.BOL_LOW_BAND_1, self.BOL_LOW_BAND_2)):
                result.append(self.BA_PAUSE_DOWN)
            else:
                result.append(None)           
        for c, i in enumerate(self.intervals):
            i.add_ii_value(self.BOL_ADVICE, (
                result[c],
            ))
                
            
    def add_99z_export_up_wave_for_graph_ii(self):
        """???
        """
        if not self.export_file_base:
            return
        for i in self.intervals:
            time_info = i.last(self.BASIC_INFO)[bls.Basics.W_UP_W_AND_P_TIMES]
            filename = "_".join([i.export_file_base, "upwave"])
            val_info = i.last(self.BASIC_INFO)[bls.Basics.W_UP_W_AND_P_EXTREMES]
            if not time_info[-1] == self.graph_dict[filename]:
                self.graph_dict[filename] = time_info[-1]
                with open(filename, 'w') as o_fd:
                    with i.export_lock:
                        for c, dt in enumerate(time_info):
                            print("{},{},{}".format(c, i.bar_nr_at(dt), val_info[c]),
                                  file=o_fd)  
            
    def add_99z_export_down_wave_for_graph_ii(self):
        """???
        """
        if not self.export_file_base:
            return
        for i in self.intervals:
            time_info = i.last(self.BASIC_INFO)[bls.Basics.W_DOWN_W_AND_P_TIMES]
            filename = "_".join([i.export_file_base, "downwave"])
            val_info = i.last(self.BASIC_INFO)[bls.Basics.W_DOWN_W_AND_P_EXTREMES]
            if not time_info[-1] == self.graph_dict[filename]:
                self.graph_dict[filename] = time_info[-1]
                with open(filename, 'w') as o_fd:
                    with i.export_lock:
                        for c, dt in enumerate(time_info):
                            print("{},{},{}".format(c, i.bar_nr_at(dt), val_info[c]),
                                  file=o_fd)  
            
    ########
    #
    # vanalles dumpen of the checken
    #
    #
    
    def export_intervalnames(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            line.add_chunk(chunk_format.format(interval.name))
        print(str(line), file=file)
        
    def export_end_of_bar_status(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            status = 'END' if interval.at_end_of_period else ''
            line.add_chunk(chunk_format.format(status))
        print(str(line), file=file)
        
    
    def export_barstart(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            last_bar = interval.interval_bars[-1]
            time = last_bar.time.time()
            line.add_chunk(chunk_format.format(str(time)))
        print(str(line), file=file)
    
    def export_barvalue(self, name, width=17, file=stdout, mode='txt'):
        '''value name in open_, close, high, low '''
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            last_bar = interval.interval_bars[-1]
            line.add_chunk(chunk_format.format(getattr(last_bar, name)))
        print(str(line), file=file)
    
    def export_balanced_market(self, 
                               field='all', width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            last_bm = interval.last(self.BALANCE_TRIGGERED)
            if not field == 'all':
                last_bm = last_bm[field]
                last_bm = last_bm if last_bm is not None else ''
            line.add_chunk(chunk_format.format(last_bm))
        print(str(line), file=file)
    
    def export_r_levels(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            last_rs = interval.last(self.R_LEVELS)[self.R_LEVELS]
            line.add_chunk(chunk_format.format(last_rs))
        print(str(line), file=file)
    
    def export_s_levels(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            last_sl = interval.last(self.R_AND_S)[self.S_LEVELS]
            line.add_chunk(chunk_format.format(last_sl))
        print(str(line), file=file)
        
    def export_high(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':         
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            high = interval.last(self.HI_LO)[self.HL_HIGH]
            line.add_chunk(chunk_format.format(high))
        print(str(line), file=file)
        
    def export_high_index(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':         
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            high = interval.last[self.HI_LO][self.HIGH_INDEX]
            line.add_chunk(chunk_format.format(high))
        print(str(line), file=file)
        
    def export_low(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':         
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            low = interval.last(self.HI_LO)[self.HL_LOW]
            line.add_chunk(chunk_format.format(low))
        print(str(line), file=file)
        
    def export_low_index(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':         
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            low = interval.last[self.HI_LO][self.LOW_INDEX]
            line.add_chunk(chunk_format.format(low))
        print(str(line), file=file)
            
        
    def export_market_status(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            last_s = interval.last(self.MARKET_STATUS)[self.MS_TYPE]
            line.add_chunk(chunk_format.format(last_s))
        print(str(line), file=file)
        
    def export_market_status_reason(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            last_r = interval.last(self.MARKET_STATUS)[self.MS_REASON]
            line.add_chunk(chunk_format.format(last_r))
        print(str(line), file=file)
        
    def export_last_stoch_move(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            stinfo = interval.last(self.STOCH_INFO)
            last_move = stinfo[bls.STOCH.LAST_MOVE]
            start_index = stinfo[bls.STOCH.MOVE_START_INDEX]
            stop_index = stinfo[bls.STOCH.MOVE_STOP_INDEX]
            line.add_chunk(chunk_format.format('{}|{}|{}'.format(
                last_move, start_index, stop_index)))
        print(str(line), file=file)
        
    def export_stoch_result(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            k, d, r = interval.studie_values[self.STOCH_INFO][-1]
            if isinstance(d, float):
                line.add_chunk(chunk_format.format(
                    '{:.2f}|{:.2f}|{:.2f}'.format(k, d, r)))
        print(str(line), file=file)
        
    def export_last_move_stoch_result(self, width=17, file=stdout, mode='txt'):
        if mode == 'txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:^{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for interval in self.intervals:
            stinfo = interval.last(self.STOCH_INFO)
            last_move = stinfo[bls.STOCH.LAST_MOVE]
            start_index = stinfo[bls.STOCH.MOVE_START_INDEX]
            stop_index = stinfo[bls.STOCH.MOVE_STOP_INDEX]
            if last_move:
                start_value = (
                    interval.last(
                        self.STOCH_INFO, start_index)[bls.STOCH.STOCHASTIC]
                )
                stop_value = (
                    interval.last(
                        self.STOCH_INFO, start_index)[bls.STOCH.STOCHASTIC]
                )
                line.add_chunk(chunk_format.format(
                    '{:.2f}|{:.2f}'.format(start_value, stop_value)))
        print(str(line), file=file)
        
    def export_basic_moves(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            #fill = ' ' * (width // 2 - 6) 
            fill = ''
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            rel_pos = i.last(self.BASIC_INFO)[bls.Basics.RELBAR]
            two_bar_move = i.last(self.BASIC_INFO)[bls.Basics.SPOTTED_MOVE]
            pause = i.last(self.BASIC_INFO)[bls.Basics.SPOTTED_PAUSE]
            two_bar_move = pause if pause else two_bar_move
            if two_bar_move is False:
                two_bar_move = ''
            info = '{} | {}'.format(rel_pos, two_bar_move)
            line.add_chunk(chunk_format.format(fill + info))
        print(str(line), file=file)
        
    def export_waves_down_len(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_DOWN_W_AND_P_LENGTHS]
            line.add_chunk(chunk_format.format('D '+str(down)))
        print(str(line), file=file)
        
    def export_waves_up_len(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_UP_W_AND_P_LENGTHS]
            line.add_chunk(chunk_format.format('U '+str(down)))
        print(str(line), file=file)
        
    def export_waves_down_types(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_DOWN_W_AND_P_TYPES]
            line.add_chunk(chunk_format.format('D '+str(down)))
        print(str(line), file=file)
        
    def export_r_counts(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.R_DOWN]
            up = i.last(self.BASIC_INFO)[bls.Basics.R_UP]
            line.add_chunk(chunk_format.format(
                'Ur:{}|Dr:{}'.format(up, down)))
        print(str(line), file=file)
        
    def export_waves_up_types(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_UP_W_AND_P_TYPES]
            line.add_chunk(chunk_format.format('U '+str(down)))
        print(str(line), file=file)
        
    def export_waves_down_extremes(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_DOWN_W_AND_P_EXTREMES]
            line.add_chunk(chunk_format.format('D '+str(down)))
        print(str(line), file=file)
        
    def export_waves_up_extremes(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_UP_W_AND_P_EXTREMES]
            line.add_chunk(chunk_format.format('U '+str(down)))
        print(str(line), file=file)
        
    def export_waves_down_index(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_DOWN_W_AND_P_INDEXES]
            line.add_chunk(chunk_format.format('D '+str(down)))
        print(str(line), file=file)
        
    def export_waves_up_index(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            down = i.last(self.BASIC_INFO)[bls.Basics.W_UP_W_AND_P_INDEXES]
            line.add_chunk(chunk_format.format('U '+str(down)))
        print(str(line), file=file)
        
    def export_up_down_rule(self, width=17, file=stdout, mode='txt'):
        if mode =='txt':            
            line = SerialLineCreator(separator=' ')
            chunk_format='{{:{}}}'.format(width)
        elif mode == 'csv':
            line = SerialLineCreator(separator=',')
            chunk_format='{}'
        for i in self.intervals:
            rule = i.last(self.BASIC_INFO)[bls.Basics.USED_UP_DOWN_RULE]
            line.add_chunk(chunk_format.format(str(rule)))
        print(str(line), file=file)
        