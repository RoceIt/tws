#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

import csv
import pickle
from datetime import datetime, timedelta
from collections import defaultdict, namedtuple
import os.path

import mypy
import roc_output as r_output
from barData import ochlBar, ochl

class NoNewInsertAllowed(Exception):pass
class BlokCodeError(Exception):pass


class Triad():
    '''a triad is a clear turningpoint in bar chart
    triads properties are defined by the top and the
    direction bar.
    The triad_bars are all the bars that form the triad the 
    top bar and direction bar are the indexes of the 
    respective bars in the triad bars list'''
    
    ASCENDING = 1
    DESCENDING = 2
    def __init__(self, triad_bars, 
                 extreme_bar, relative_extreme_bar, bar_size, complete=None):
        self.triad_bars = triad_bars[:]
        self.extreme_bar_index = extreme_bar
        self.relative_extreme_bar_index = relative_extreme_bar
        self.direction_bar_index = len(self.triad_bars) - 1
        self.complete = complete #there is a real first bar
        self.bar_size = bar_size
        if self.extreme_bar.high < self.direction_bar.high:
            self.type_ = self.ASCENDING
            self.power_triad = self.direction_bar.close > self.first_bar.high
        else:
            self.type_ = self.DESCENDING
            self.power_triad = self.direction_bar.close < self.first_bar.low
            
    def __str__(self):
        type_text = {self.ASCENDING: 'ASCENDING',
                     self.DESCENDING: 'DESCENDING'}
        msg = ['{} Triad ({}secs) {} --> {}: rel_count={}'
               .format(type_text[self.type_], self.bar_size,
                       mypy.date_time2format(self.start_time,
                                             mypy.DATE_TIME_STR),
                       mypy.date_time2format(self.end_time,
                                             mypy.DATE_TIME_STR),
                       self.relative_extreme_bar_index)]
        msg.append('Extreme bar: {}'.format(self.extreme_bar_index + 1))
        if not self.complete:
            msg.append('NO valid front bar!')
        if self.power_triad:
            msg.append('POWER triad!')
        msg.append('close to extreme: {}'.format(self.extreme2close))
        msg.append('close to small extreme: {}'.format(self.small_extreme2close))
        msg.append('close in directional: {}'.format(self.direction2close))
        bar_txt = [str(x) for x in self.triad_bars]
        for count, member in enumerate(bar_txt):
            pre = '  ' if count != self.extreme_bar_index else 'E '
            bar_txt[count] = pre + bar_txt[count]
        msg += bar_txt
        return '\n'.join(msg)
                 
    @property
    def extreme2close(self):
        '''returns the diff between the extreme top and the triad close'''
        e_bar = self.extreme_bar
        if e_bar.size == 0:
            return 100
        d_bar = self.direction_bar
        direction = self.type_
        if direction is self.ASCENDING:
            v1= (d_bar.close - e_bar.low) / e_bar.size
        else:
            v1= (e_bar.high - d_bar.close) / e_bar.size
        return v1
    
    @property
    def small_extreme2close(self):
        '''returns the diff between the extreme bar directional end
        and the triad close'''
        e_bar = self.extreme_bar
        if e_bar.size == 0:
            return 100
        d_bar = self.direction_bar
        direction = self.type_
        if direction is self.ASCENDING:
            v1= (d_bar.close - e_bar.high) / e_bar.size
        else:
            v1= (e_bar.low - d_bar.close) / e_bar.size
        return v1
    
    @property
    def direction2close(self):
        '''returns the position of the close in the directional bar'''
        d_bar = self.direction_bar
        return d_bar.close_perc
    
    @property
    def nominal_diffs(self):
        '''returns the diff between the directional close and the
        directional end closest to the top and the diff between
        the directional close and the triad's top '''
        d_bar = self.direction_bar
        if self.type_ is self.ASCENDING:
            small_diff = d_bar.close - d_bar.low
            big_diff = d_bar.close - self.extreme_top
        else:
            small_diff = d_bar.high - d_bar.close
            big_diff = self.extreme_top - d_bar.close
        return small_diff, big_diff
        
    @property
    def extreme_bar(self):
        '''returns the extreme ochlBar'''
        return self.triad_bars[self.extreme_bar_index]
    
    @property
    def extreme_top(self):
        '''returns the highest(lowest) top in the extreme bar'''
        e_bar = self.extreme_bar
        top = e_bar.low if self.type_ is self.ASCENDING else e_bar.high
        return top
    
    @property
    def extreme_time(self):
        '''returns the timestamp of the extreme bar'''
        e_bar = self.extreme_bar
        return e_bar.time
    
    @property
    def direction_bar(self):
        '''return the direction ochlBar'''
        return self.triad_bars[self.direction_bar_index]
    
    @property
    def first_bar(self):
        '''return the first bar of the triad'''
        return self.triad_bars[0]
    
    @property
    def start_time(self):
        '''returns the datetime of the first bar'''
        return self.triad_bars[0].time
        
    @property
    def end_time(self):
        '''returns the estimated datetime of the end of the last bar'''
        end = self.triad_bars[-1].time + timedelta(seconds = self.bar_size)
        return end
    
    @property
    def close(self):
        '''returns the close value of the last triad bar'''
        return self.triad_bars[-1].close
    
    def to_csv_writer(self, csv_writer):
            csv_writer.writerow([2] + [self.extreme_time] + 8 * [''] +
                             [self.extreme_top])
            if self.type_ is Triad.DESCENDING:
                fill_a, fill_b = 4, 1
            else:
                fill_a, fill_b = 0, 5
            for bar in self.triad_bars:
                #info = list(bar)
                info = list(bar[0:5])
                csv_writer.writerow([1] + [info[0]] + fill_a * [''] +
                                 info[1:] + fill_b * [''])
                
    def to_csv(self, csv_writer):
        self.to_csv_writer(csv_writer)
        
        
            
class TriadReducer(r_output.AddExportSystem):
    '''Takes ochlbars and tuns it into a list of triads'''
    
    def __init__(self, bar_size):
        self.bar_size = bar_size  # in seconds
        #a list to keep the bars necessary for the triad discovery
        self.bars = []
        #counts the total number of bars received,
        self.relative_bar_count = 0
        self.last_pivot_bar_count = 0
        #the list with all triads
        #self.triad_list = []
        self.use_bar_validation = False
        self.last_triad = None
        super().__init__()
        
    #def __getitem__(self, k):
        #'''returns the k-th item of the self.triad_list'''
        #return self.triad_list[k]
        
    def find_descending_triad(self):
        '''function searches in a list of ochlBars for a
        descending triad'''
        ###
        UNDEFINED = '$UNDIFINED'
        bars = self.bars
        found_triad = None
        if len(bars) > 2:
            pivot_bar_index = 0
            for i, bar in enumerate(bars):
                if bar.high > bars[pivot_bar_index].high:
                    pivot_bar_index = i
            if (pivot_bar_index in (0, len(bars) - 1) or
                not bars[-1] < bars[pivot_bar_index]):
                return None, None
            complete = False
            first_triad_bar_index = 0
            for i, bar in enumerate(bars[:pivot_bar_index]):
                if bar < bars[pivot_bar_index]:
                    complete = True
                    first_triad_bar_index = i
            found_triad = Triad(bars[first_triad_bar_index:],
                                pivot_bar_index - first_triad_bar_index,
                                pivot_bar_index -len(bars) + 1 + self.relative_bar_count,
                                self.bar_size,
                                complete)
            remaining = bars[pivot_bar_index:]
        if not found_triad:
            remaining = None
        ###
        return found_triad, remaining
    
                                    
    def find_ascending_triad(self):
        '''function searches in a list of ochlBars for a
        ascending triad'''
        ###
        UNDEFINED = '$UNDIFINED'
        bars = self.bars
        found_triad = None
        if len(bars) > 2:
            pivot_bar_index = 0
            for i, bar in enumerate(bars):
                if bar.low < bars[pivot_bar_index].low:
                    pivot_bar_index = i
            if (pivot_bar_index in (0, len(bars) - 1) or
                not bars[-1] > bars[pivot_bar_index]):
                return None, None
            complete = False
            first_triad_bar_index = 0
            for i, bar in enumerate(bars[:pivot_bar_index]):
                if bar > bars[pivot_bar_index]:
                    complete = True
                    first_triad_bar_index = i
            found_triad = Triad(bars[first_triad_bar_index:],
                                pivot_bar_index - first_triad_bar_index,
                                pivot_bar_index -len(bars) + 1 + self.relative_bar_count,
                                self.bar_size,
                                complete)
            remaining = bars[pivot_bar_index:]
        if not found_triad:
            remaining = None
        ###
        return found_triad, remaining
    
    def find_triad(self, bar):
        ###
        last_triad = self.last_triad
        if not last_triad:
            new_triad, remaining_bars = self.find_ascending_triad()
            if not new_triad:
                new_triad, remaining_bars = self.find_descending_triad()
        elif last_triad.type_ is Triad.ASCENDING:
            new_triad, remaining_bars = self.find_descending_triad()
        else:
            new_triad, remaining_bars = self.find_ascending_triad()
        ###
        return new_triad, remaining_bars
        
                
    def insert(self, bar):
        '''Takes an ochl bar and searches for triads,
        if a (next) triad is found the triad is added to the
        list. returns None if no new triad found else the triad
        If unfinished bar is true, it is just for checking if a triad
        might be forming. It wil return the triad as it is now to allert,
        but nothing will change for the triad list!!'''
        ###
        ###
        self.bars.append(bar)
        self.relative_bar_count += 1
        new_triad, remaining_bars = self.find_triad(bar)
        if new_triad:
            self.last_triad = new_triad
            self.bars = remaining_bars
            self.export_object(new_triad)
        return new_triad

    def virtual_insert(self, bar):
        '''Like insert doesn't change the reducer.
        
        check what would happen if you inserted the bar bar now. Use it to
        try to predict the future a little bit.
        '''
        self.bars.append(bar)
        self.relative_bar_count += 1
        new_triad, remaining_bars = self.find_triad(bar)
        new_triad, remaining_bars = self.find_triad(bar)
        self.bars.pop()
        self.relative_bar_count -= 1
        return new_triad
        
    
    @property
    def last_extreme(self):
        '''returns the index of the last extreme bar of the last found trial
        or 0 if no last bar found'''
        last_t = self.last_triad
        return last_t.extreme_bar_index if last_t else 0
    
    @property
    def last_directional(self):
        '''returns the index of directional bar of the last found triad
        if no last triad found it returns 0'''
        last_t = self.last_triad
        return last_t.direction_bar_index if last_t else 0
             
    @property
    def last_triad(self):
        '''returns the last triad in the triad list or None if
        no last triad is found'''
        return self.__last_triad
    
    @last_triad.setter
    def last_triad(self, a_triad):
        self.__last_triad = a_triad
    

        
class Swing():
    
    NEW, UP, DOWN, IN_DUBIO = 'new', 'up', 'down', 'in dubio'
    D_FINISHED, D_REMOVABLE = 1, 2
    
    def __init__(self, bar_size, start_triangle, primary_swing=True):
        self.id = start_triangle.relative_extreme_bar_index
        self.bar_size = bar_size
        self.primary_swing = primary_swing
        self.triad_list = [start_triangle]
        self.pivot_list = [start_triangle.extreme_top]
        self.type = Swing.NEW
        self.first_move = None
        self.first_dubio_move = None
        self.last_pure_directional_move = 0
        self.dubio_status = None
        self.confirmed = False
        self.finished = False
        self.warning_sended = False
        
    def __str__(self):
        out = 'barsize: {}\n '
        out += 'start: {}\n'
        out += 'type: {} | confirmed: {} | finished {}\n'
        out += 'dubio status: {}\npivots:'
        out = out.format(self.bar_size, self.start_time,
                         self.type, self.confirmed, self.finished,
                   self.dubio_status)
        for value in self.pivot_list:
            out+= str(value)+', '
        return out
    
    def __len__(self):
        return len(self.triad_list)
    
    def append(self, swing):
        if not isinstance(swing, Swing):
            raise TypeError('can only add swings')
        if not self.bar_size == swing.bar_size:
            raise TypeError('swings must have the same bar_size')
        if not self.type == swing.type:
            raise Exception('swings must have the same size')
        if self.end_time > swing.start_time:
            #print(self)
            #print(swing)
            raise Exception('swing 2 must start when or after swing 1 is finished')
        elif self.end_time == swing.start_time:
            self.triad_list += swing.triad_list[1:]
            self.pivot_list += swing.pivot_list[1:]
        else:
            self.triad_list += swing.triad_list
            self.pivot_list += swing.pivot_list
        
    
    def insert_triad(self, new_triad):
        if self.finished:
            return
            #raise NoNewInsertAllowed('Swing is finished')
        self.triad_list.append(new_triad)
        self.pivot_list.append(new_triad.extreme_top) 
        recent_pattern, full_patern = self.recent_pattern() 
        if self.type is Swing.NEW:
            self.type = recent_pattern
            self.first_move = recent_pattern
            self.last_pure_directional_move += 1
        elif self.type is Swing.UP:
            if recent_pattern is Swing.IN_DUBIO:
                self.first_dubio_move = len(self.triad_list) - 1
                if (self.confirmed
                    or
                    len(self.pivot_list) == 5):
                    self.finished = True
                    self.triad_list.pop()
                    self.pivot_list.pop()
                    if not len(self.pivot_list) % 2 == 0:
                        self.triad_list.pop()
                        self.pivot_list.pop()
                else:
                    self.type = recent_pattern
            else:
                self.last_pure_directional_move += 1                
                if full_patern:
                    self.confirmed = True
        elif self.type is Swing.DOWN:
            if recent_pattern is Swing.IN_DUBIO:
                self.first_dubio_move = len(self.triad_list) - 1
                if (self.confirmed
                    or
                    len(self.pivot_list) == 5):
                    self.finished = True
                    self.triad_list.pop()
                    self.pivot_list.pop()
                    if not len(self.pivot_list) % 2 == 0:
                        self.triad_list.pop()
                        self.pivot_list.pop()
                else:
                    self.type = recent_pattern  
            else:
                self.last_pure_directional_move += 1                
                if full_patern:
                    self.confirmed = True     
        
    def recent_pattern(self):
        number_of_pivots = len(self.pivot_list)
        full_start_pattern = False
        if self.type is Swing.IN_DUBIO:
                pattern = Swing.IN_DUBIO
        elif number_of_pivots == 2:
            if self.pivot_list[0] < self.pivot_list[1]:
                return Swing.UP, False
            else:
                return Swing.DOWN, False
        elif number_of_pivots == 3:
            p1, p2 , p3 = (x for x in self.pivot_list)
            if (p3 - p2) * (p3 - p1) < 0: #p3 between p1 & p2
                pattern = Swing.UP if p1 < p2 else Swing.DOWN
            else:
                pattern = Swing.IN_DUBIO
        else:
            p1, p2 = self.pivot_list[-3], self.pivot_list[-1]
            if ((self.type is Swing.UP and p2 >= p1)
                or
                (self.type is Swing.DOWN and p2 <= p1)):
                pattern = self.type
                full_start_pattern = len(self.pivot_list) >= 5
            else:
                pattern = Swing.IN_DUBIO
        return pattern, full_start_pattern
    
    @property
    def start_time(self):
        return self.triad_list[0].extreme_time
    
    @property
    def end_time(self):
        return self.triad_list[-1].extreme_time
    
    @property
    def start_value(self):
        return self.triad_list[0].extreme_top
    
    @property
    def end_value(self):
        return self.triad_list[-1].extreme_top
    
    def announcement_time_of_move(self, move, primary_alert_off=False):
        if not primary_alert_off and not self.primary_swing:
            raise Exception('announcement time unreliable on non primary swings')
        try:
            answer = self.triad_list[move].end_time
        except IndexError:
            answer  = ''
        return answer
    
    def announcement_time_quote_of_move(self, move, primary_alert_off=False):
        if not primary_alert_off and not self.primary_swing:
            raise Exception('announcement time quote unreliable on non primary swings')
        try:
            answer = self.triad_list[move].close
        except IndexError:
            answer  = ''
        return answer
    
    @property
    def nr_of_bars(self):
        rel_start = self.triad_list[0].relative_extreme_bar_index
        rel_end = self.triad_list[-1].relative_extreme_bar_index
        return rel_end - rel_start +1
    
    @property
    def nr_of_moves(self):
        return len(self.pivot_list) -1
    
    @property
    def points(self):
        return abs(self.start_value - self.end_value)
    
    @property
    def points_percentage(self):
        return self.points / self.start_value

    def pivot_changes(self, *xtra_pivots):
        nom = []
        perc = []
        pivots = self.pivot_list + list(xtra_pivots)
        for i in range(len(pivots)-1):
            nom.append(pivots[i+1] - pivots[i])
            perc.append(pivots[i+1] / pivots[i] - 1)
        return nom, perc
    
class Perm(list):    
    
    def __init__(self, *ell):
        self.extend(ell)
        
    def to_csv(self, csv_writer):
        csv_writer.writerow(self)

    
class SwingCountingByArgs(r_output.AddExportSystem):
    
    def __init__(self, 
                 special_reset=True, max_contratrend_triads=4):
        #base setttings
        self.up_list = []
        self.up_tops = []
        self.down_list = []
        self.down_tops = []
        self.up_last_export = self.down_last_export = None
        #arg_settings
        ## SPECIAL RESET STRATEGY
        self.special_reset = special_reset
        self.max_contratrend_triads = max_contratrend_triads
        super().__init__()
    
    def register(self, triad):

        self.up_list, self.up_tops, self.down_list, self.down_tops = (
            self.basic_counting(
                uplist=self.up_list,
                upswing_tops=self.up_tops,
                downlist=self.down_list,
                downswing_tops=self.down_tops,
                new_triad=triad,
        ))
        if self.special_reset:
            self.up_list, self.up_tops, self.down_list, self.down_tops = (
                self.check_special_reset(
                    uplist=self.up_list,
                    up_tops=self.up_tops,
                    downlist=self.down_list,
                    down_tops=self.down_tops,
                    max_contratrend_triads=self.max_contratrend_triads,
        ))
        new_perms, self.down_last_export, self.up_last_export = (
            self.extract_new_perms(
                down_list=self.down_list,
                last_exported_down_perm_time=self.down_last_export,
                up_list=self.up_list,
                last_exported_up_perm_time=self.up_last_export,
        ))
        for perm in new_perms:            
            self.export_object(perm)
        return new_perms
    
    def virtual_register(self, triad):

        up_list, up_tops, down_list, down_tops = (
            self.basic_counting(
                uplist=self.up_list,
                upswing_tops=self.up_tops,
                downlist=self.down_list,
                downswing_tops=self.down_tops,
                new_triad=triad,
        ))
        if self.special_reset:
            up_list, up_tops, down_list, down_tops = (
                self.check_special_reset(
                    uplist=up_list,
                    up_tops=up_tops,
                    downlist=down_list,
                    down_tops=down_tops,
                    max_contratrend_triads=self.max_contratrend_triads,
        ))
        new_perms, foo, bar = (
            self.extract_new_perms(
                down_list=down_list,
                last_exported_down_perm_time=self.down_last_export,
                up_list=up_list,
                last_exported_up_perm_time=self.up_last_export,
        ))
        return new_perms
        
    
    @staticmethod
    def extract_new_perms(
            down_list, last_exported_down_perm_time,
            up_list, last_exported_up_perm_time,
    ):
        '''Return the new perms and the times of the last exported perms.
        
        Arguments:
            down_list -- list with down perms
            last_exported_down_perm_time -- time of the last exported down perm
            up_list -- list with up perms
            last_exported_up_perm_time -- time of the last exported up perm
        '''
         
        ###
        new_perms_from = SwingCountingByArgs.new_perms_from
        new_perms = []
        uplist_size, downlist_size = len(up_list), len(down_list) 
        if ((uplist_size < 3) and 
            (downlist_size < 3)
        ):
            if uplist_size < downlist_size:
                new_perms, last_exported_down_perm_time = new_perms_from(
                    perm_list=down_list,
                    list_direction='down',
                    last_exported_triad_time=last_exported_down_perm_time,
                )
            else:
                new_perms, last_exported_up_perm_time = new_perms_from(
                    perm_list=up_list,
                    list_direction='up',
                    last_exported_triad_time=last_exported_up_perm_time,
                )
        else:
            if downlist_size > 2: 
                new_perms, last_exported_down_perm_time = new_perms_from(
                    perm_list=down_list, 
                    list_direction='down', 
                    last_exported_triad_time=last_exported_down_perm_time,
                )
            if uplist_size > 2: 
                other_perms, last_exported_up_perm_time=new_perms_from(
                    perm_list=up_list, 
                    list_direction='up', 
                    last_exported_triad_time=last_exported_up_perm_time,
                )
                new_perms.extend(other_perms) 
        ###
        return (
            new_perms, 
            last_exported_down_perm_time, 
            last_exported_up_perm_time,
        )
       
    
    @staticmethod
    def new_perms_from(perm_list, list_direction, last_exported_triad_time):
        '''Returns the not yet exported perms and the last exported time.
        
        Arguments:
          perm_list -- a list of triads
          list_direction -- 'up' or 'down', a str
          last_exported_triad_time -- a datetiem 
        '''
        
        ###
        not_exported_perms_list = []
        for count, triad in enumerate(perm_list):
            if (not last_exported_triad_time
                or
                triad.extreme_time > last_exported_triad_time
            ):
                last_exported_triad_time = triad.extreme_time
                not_exported_perms_list.append(
                    Perm(list_direction, count, triad.extreme_time, 
                         triad.extreme_top, triad.end_time, triad.close,
                ))
        ###
        return not_exported_perms_list, last_exported_triad_time
    
    @staticmethod
    def basic_counting(
            uplist, upswing_tops, downlist, downswing_tops, new_triad):
        '''Returns the updated versions of the first 4 parameters.'''
        ###
        count_up = SwingCountingByArgs.basic_uplist_counting
        count_down = SwingCountingByArgs.basic_downlist_counting
        uplist_c = uplist[:]
        downlist_c = downlist[:]
        upswing_tops_c = upswing_tops[:]
        downswing_tops_c = downswing_tops[:]
        ###
        uplist_c, upswing_tops_c = count_up(
            uplist=uplist_c, 
            tops=upswing_tops_c,
            new_triad=new_triad,
        )
        downlist_c, downswing_tops_c = count_down(
            downlist=downlist_c, 
            tops=downswing_tops_c,
            new_triad=new_triad,
        )
        return uplist_c, upswing_tops_c, downlist_c, downswing_tops_c
    
    @staticmethod
    def basic_uplist_counting(uplist, tops, new_triad):
        '''Returns  the new triad list and new triad tops list.'''
        if len(uplist) > len(tops):
            print('uplist', uplist, tops)
        ###
        uplist_size = len(uplist)
        new_triad_top = new_triad.extreme_top
        ###
        if uplist_size == 0:
            if new_triad.type_ is Triad.DESCENDING:
                return uplist, tops
        elif uplist_size == 1:
            if new_triad.type_ is Triad.ASCENDING:
                raise Exception('Two ups in a row?')
            #else add the new triad
        elif new_triad.type_ == Triad.DESCENDING:
            if uplist_size % 2 == 0:
                raise Exception('Two downs in a row?')
            elif not new_triad_top > max(tops):
                return uplist, tops
            #else add the new triad
        elif not new_triad_top < tops[-1]:
            return uplist, tops
        elif not uplist_size % 2 == 0:
            uplist.pop()
            tops.pop()
        if uplist and new_triad.type_ is Triad.ASCENDING:
            if new_triad_top < min(tops):
                uplist.clear()
                tops.clear()
            else:
                while (len(uplist) > 2 and
                       new_triad_top < tops[-2]
                ):
                    uplist.pop(-2); uplist.pop(-2)
                    tops.pop(-2); tops.pop(-2)
        uplist.append(new_triad)
        tops.append(new_triad_top)
        return uplist, tops
    
    @staticmethod
    def basic_downlist_counting(downlist, tops, new_triad):
        '''Returns  the new triad list and new triad tops list.'''
        ###
        downlist_size = len(downlist)
        new_triad_top = new_triad.extreme_top
        ###
        if downlist_size == 0:
            if new_triad.type_ is Triad.ASCENDING:
                return downlist, tops
        elif downlist_size == 1:
            if new_triad.type_ is Triad.DESCENDING:
                raise Exception('Two downs in a row?')
            #else add the new triad
        elif new_triad.type_ == Triad.ASCENDING:
            if downlist_size % 2 == 0:
                raise Exception('Two ups in a row?')
            elif not new_triad_top < min(tops):
                return downlist, tops
            #else add the new triad
        elif not new_triad_top > tops[-1]:
            return downlist, tops
        elif not downlist_size % 2 == 0:
            downlist.pop()
            tops.pop()
        if downlist and new_triad.type_ is Triad.DESCENDING:
            if new_triad_top > max(tops):
                downlist.clear()
                tops.clear()
            else:
                while (len(downlist) > 2 and
                       new_triad_top > tops[-2]
                ):
                    downlist.pop(-2); downlist.pop(-2)
                    tops.pop(-2); tops.pop(-2)
        downlist.append(new_triad)
        tops.append(new_triad_top)
        return downlist, tops
    
    @staticmethod
    def check_special_reset(
            uplist, up_tops, downlist, down_tops, max_contratrend_triads):
        ###
        uplist_size = len(uplist)
        downlist_size = len(downlist)
        if (uplist_size > downlist_size and
            downlist_size == max_contratrend_triads
        ):
            r_up, r_down = uplist[-1:], downlist
            r_up_tops, r_down_tops = up_tops[-1:], down_tops
        elif (uplist_size < downlist_size and
            uplist_size == max_contratrend_triads
        ):
            r_down, r_up = downlist[-1:], uplist
            r_down_tops, r_up_tops = down_tops[-1:], up_tops
        else:
            r_up, r_up_tops = uplist, up_tops
            r_down, r_down_tops = downlist, down_tops
        return r_up, r_up_tops, r_down, r_down_tops
    
class SwingCountingByRules():
    
    #def __init__(self, rules_script, output_file):    
    def __init__(self, rules_script=None):
        #self.permanent_swing_count_file = os.path.join(mypy.TMP_LOCATION,
                            
        #open(self.permanent_swing_count_file, 'w').close()
        if rules_script: self.make_rule_book(rules_script)  #creates self.rule_book
        self.up_list = []
        self.down_list = []
        self.perm_list = []
        self.up_last_export = self.down_last_export = None
        
    def make_rule_book(self, script):
        #
        def smart_split(line):
            #print("proc lin: ", line)
            line, foo, bar = line.partition('#')
            if not line or line.isspace(): return []
            STRING = "__$_$_$__"
            strings = []
            line = line.split('|||')
            if len(line) > 1:
                if line[-1] == line[-2] == '': line.pop()
                for i in range(2, len(line)):
                    if line[i] == '':
                        strings.append(line[i-1])
                        line[i-1] = STRING
            line = "".join(line)
            level = 0
            while line[0] == ' ':
                level += 1
                line = line[1:]
            ell = line.strip().split(' ')
            ell = [x.strip() for x in ell if x]
            if ell: ell.insert(0, level)
            ell__ = []
            for e in ell:
                if e == STRING:
                    e = strings.pop(0)
                ell__.append(e)
            return ell__
        #
        def format_rules(rule_list, min_blok_level=-1):
            blok_instructions = {"if", "case", "loop"}
            blok_level = rule_list[0][0]
            if blok_level <= min_blok_level:
                raise BlokCodeError('blok must indent')
            codeblok = []
            while rule_list:
                if rule_list[0][0] < blok_level: break
                if rule_list[0][0] > blok_level:
                    raise BlokCodeError("blokcode must be on the same level")
                #print(rule_list[0])
                foo, curr_instruction, *parameters = rule_list.pop(0)
                codeline = [curr_instruction, parameters]
                if curr_instruction in blok_instructions:
                    codeline.append(format_rules(rule_list, blok_level))
                codeblok.append(codeline)
            return codeblok            
        #
        code_text = []
        with open(script, "r") as rules_book:
            for line in rules_book:
                line_ell = smart_split(line)
                if line_ell: code_text.append(line_ell)
        self.rule_book = format_rules(code_text)
    
    def register(self, triad):
        UPLIST = 1
        DOWNLIST = 2
        new_perms = []
        #def export(export_list):
            #if export_list is UPLIST: 
                #li, last_time = self.up_list, self.up_last_export
                #prefix = "up"
            #else:
                #li, last_time = self.down_list, self.down_last_export
                #prefix = "down"
            #count = 0
            #with open(self.permanent_swing_count_file, 'a') as ofh:
                #for tr in li:
                    #if not last_time or tr.extreme_time > last_time:
                        #last_time = tr.extreme_time
                        #ofh.write("{},{},{},{},{},{}\n".format(prefix, count, 
                                                    #last_time, tr.extreme_top,
                                                    #tr.end_time, tr.close))
                    #count += 1
            #if export_list is UPLIST:
                #self.up_last_export = last_time
            #else:
                #self.down_last_export = last_time
                
        def downlist_perms():
            perms_list = []
            count = 0
            for tr in self.down_list:
                if (not self.down_last_export
                    or
                    tr.extreme_time > self.down_last_export):
                    self.down_last_export = tr.extreme_time
                    perms_list.append(['down', count, tr.extreme_time,
                                       tr.extreme_top, tr.end_time, tr.close])
                count += 1
            return perms_list
                
        def uplist_perms():
            perms_list = []
            count = 0
            for tr in self.up_list:
                if (not self.up_last_export
                    or
                    tr.extreme_time > self.up_last_export):
                    self.up_last_export = tr.extreme_time
                    perms_list.append(['up', count, tr.extreme_time,
                                       tr.extreme_top, tr.end_time, tr.close])
                count += 1
            return perms_list
            
                    
        ns = {"__COMMANDS__": self.commands,
              "__TESTS__": self.tests,
              "__INFO__": self.info,
              "__TRIAD__": triad,
              "__UP_LIST__": self.up_list,
              "__DOWN_LIST__": self.down_list}
        #print("\nSTART REGISTER")
        run_data = self.run_blok(self.rule_book, ns)
        #print("ran {} commands".format(run_data["__COMMANDS_COUNTER__"]))
        #print(self.up_list)
        #print(self.down_list)
        #mypy.get_bool('druk ergens op enter of zo', default=True)
        #print("=====================================================")        
        uplist_size, downlist_size = len(self.up_list), len(self.down_list)
        # Dit gedeelte kan er misschien voor zorgen dat de telling
        # iets anders gebeurt omdat niet alle resets van de lijsten
        # gemeld worden, alleen als ze groter zijn dan 3 moet je 
        # toch eens uittesten.
        if ((uplist_size < 3) and (downlist_size < 3)):
            if uplist_size < downlist_size:
                new_perms = downlist_perms()
                #export(DOWNLIST)
            else:
                new_perms = uplist_perms()
                #export(UPLIST)
        else:
            if downlist_size > 2: new_perms = downlist_perms() #export(DOWNLIST)
            if uplist_size > 2: new_perms.extend(uplist_perms()) #export(UPLIST)
        if new_perms:
            self.perm_list.extend(new_perms)
        return new_perms   
    
    def save_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        outputfile = os.path.join(location, filename)
        info = (self.rule_book, self.up_list, self.down_list, 
                self.up_last_export, self.down_last_export)
        mypy.export_pickle(info, outputfile, id_="perm: minimal_restart_info")
        
    def load_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        if not self.perm_list == []:
            raise Exception("trying to load data in a running swing counter")
        inputfile = os.path.join(location, filename)
        (self.rule_book, self.up_list, self.down_list, 
         self.up_last_export, self.down_last_export) = mypy.import_pickle(
                                    inputfile, id_="perm: minimal_restart_info")
        #print(self.rule_book)
        #print(self.up_list)
        #print(self.down_list)
        #print(self.up_last_export)
        #print(self.down_last_export)
                
    def save_full_perm_history(self, filename, location=mypy.TMP_LOCATION): 
        outputfile = os.path.join(location, filename)
        info = self.perm_list
        mypy.export_pickle(info, outputfile, id_="full_perm_history")
        
    def load_full_bar_history(self, filename, location=mypy.TMP_LOCATION):
        if not self.triad_list == []:
            raise Exception("trying to load data in a running swing counter")
        inputfile = os.path.join(location, filename)
        self.perm_list = mypy.import_pickle(inputfile, 
                                            id_="full_perm_history")
    
    def export_full_perm_list(self, filename, location=mypy.TMP_LOCATION):
        outputfile = os.path.join(location, filename)
        with open(outputfile, 'w', newline='') as ofh:
            csv_writer = csv.writer(ofh)
            self.perm_list_to_csv_writer(self.perm_list, csv_writer)
            
    def perm_list_to_csv_writer(self, perm_list, csv_writer):
            for line in perm_list:
                csv_writer.writerow(line) 
        
                    
    def run_blok(self, blok, ns):
        blok = blok[:]
        blok_ns = {"__LAST_COMMAND__": None,
                   "__COMMANDS_COUNTER__": 0,}
        commands_ran = 0
        for command, *parameters in blok:
            #print("\n",ns["__COMMANDS__"][command])
            i = ns["__COMMANDS__"][command](self, parameters, ns, blok_ns)
            blok_ns["__COMMANDS_COUNTER__"] += i
            if "__STOP__" in ns: break
            blok_ns["LAST_COMMAND"] = command
        return blok_ns 
            
    ########
    # COMMANDS
    ########
    
    def sr_stop(self, parameters, ns, blok_ns):
        ns["__STOP__"] = True
        return 1
    
    def sr_set(self, parameters, ns, blok_ns):
        #print("in sr set")
        if len(parameters) > 1:
            raise BlokCodeError("set: no blok part needed")
        parameters = parameters[0]
        if len(parameters) < 3:
            #print(parameters)
            err = "set use: set [local|global] name function parameters"
            raise BlokCodeError(err)
        scope, *parameters = parameters
        if scope == "local": i = self.p_set(blok_ns, parameters, ns, blok_ns)
        elif scope == "global": i = self.p_set(ns, parameters, ns, blok_ns)
        else: raise BlokCodeError("set must have local or global attribute")
        return i
        
    def sr_if(self, parameters, ns, blok_ns):
        if len(parameters) > 2:
            raise BlokCodeError("if: ??? 3 parameters")
        if len(parameters) < 2:
            raise BlokCodeError("if: needs blok part")
        test, blok = parameters
        blok = blok[:]
        #print("    ",test)
        #print("    ",blok)
        if self.test_result(test, ns, blok_ns) == True:
            nr_of_comm = self.run_blok(blok, ns)["__COMMANDS_COUNTER__"]
            blok_ns["__LAST_IF_SUCCESFULL__"] = True
            return nr_of_comm + 1
        blok_ns["__LAST_IF_SUCCESFULL__"] = False
        return 1
    
    def sr_compare(self, parameters, ns, blok_ns):               
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")        
        parameters = parameters[0]
        try:
            at_at = parameters.index('&')
        except ValueError:
            raise BlokCodeError("compare needs '&' ell")
        val1 = self.get_info(parameters[0:at_at], ns, blok_ns)
        val2 = self.get_info(parameters[at_at+1:], ns, blok_ns)
        try:
            if val1 == val2: result = 0
            elif val1 > val2: result = 1
            else: result = 2
        except TypeError:
            raise BlokCodeError("compare: uncomparable types")
        #print("{}/{} comp {}/{}: {}".format(type(val1), val1, 
                                            #type(val2), val2, result))
        blok_ns["__LAST_COMPARE__"] = result
        return 3
        
    
    def sr_case(self, parameters, ns, blok_ns):
        if len(parameters) > 2:
            raise BlokCodeError("case: ??? 3 parameters")
        if len(parameters) < 2:
            raise BlokCodeError("case: needs blok part")
        options, blok = parameters
        blok = blok[:]
        #print("    ",options)
        #print("    ",blok)
        if_in_case = False
        nr_of_comm = 0
        while blok:
            case_blok = [blok.pop(0)]
            while blok:
                if not case_blok[-1][0] == "if":
                    case_blok.append(blok.pop(0))
                else: break
            run_data = self.run_blok(case_blok, ns)
            nr_of_comm += run_data["__COMMANDS_COUNTER__"]
            try:
                if run_data["__LAST_IF_SUCCESFULL__"]:
                    break
                else: if_in_case = True
            except KeyError:
                if if_in_case:
                    err = "case: no commands allowed after last if"
                    raise BlokCodeError(err)
                else:
                    raise BlokCodeError("case: if commonds required")
        return nr_of_comm
    
    def sr_loop(self, parameters, ns, blok_ns):        
        if len(parameters) > 2:
            raise BlokCodeError("case: ??? 3 parameters")
        if len(parameters) < 2:
            raise BlokCodeError("case: needs blok part")
        nr_of_comm = 0
        repeat, blok = parameters
        repeat = self.get_info(repeat, ns, blok_ns)        
        blok = blok[:]
        #print("    max repeat {}".format(repeat))
        #print("    ",blok)
        for i in range(repeat):
            run_data = self.run_blok(blok, ns)
            nr_of_comm += run_data["__COMMANDS_COUNTER__"]
            #print (ns)
            if "__EXIT_LOOP__" in ns:
                ns.pop("__EXIT_LOOP__")
                blok_ns["__FULL_LOOP__"] = False
                break
        else: blok_ns["__FULL_LOOP"] = True 
        return nr_of_comm
    
    def sr_exit_loop(self, parameters, ns, blok_ns):     
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")
        parameters = parameters[0]
        ns["__EXIT_LOOP__"] = True
        return 0
        
    def sr_print(self, parameters, ns, blok_ns):        
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")
        parameters = parameters[0]
        val = self.get_info(parameters, ns, blok_ns)
        #print(val)
        return 1

    def r_register_triad(self, parameters, ns, blok_ns):
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")
        parameters = parameters[0]
        target = parameters[-1]
        #print("    ", parameters)
        #print("    target", target)
        if target == "uplist":
            #print('    reg in uplist')
            ns["__UP_LIST__"].append(ns["__TRIAD__"])
        elif target == "downlist":
            #print('    reg in downlist')
            ns["__DOWN_LIST__"].append(ns["__TRIAD__"])
        else:
            raise BlokCodeError("register_triad: unknown destination")
        return 1
    
    def r_clear(self, parameters, ns, blok_ns):
        if not len(parameters) == 1:
            raise BlokCodeError("new: no blok part allowed")
        parameters = parameters[0]
        listname = parameters[0]
        if listname == "uplist": self.p_clear_list(ns["__UP_LIST__"])
        elif listname == "downlist": self.p_clear_list(ns["__DOWN_LIST__"])
        else: raise BlokCodeError("clear: don't know what to clear?")
        return 1
    
    def r_remove_triad(self, parameters, ns, blok_ns):
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")        
        parameters = parameters[0]
        listname, index = parameters
        index = int(index)
        if listname == "uplist": ns["__UP_LIST__"].pop(index)
        elif listname == "downlist": ns["__DOWN_LIST__"].pop(index)
        else: raise BlokCodeError("remove_triad: don't know what to remove?")
        return 1
        
        
    commands = {"stop": sr_stop,
                "set": sr_set,
                "if": sr_if,
                "loop": sr_loop,
                "exit_loop": sr_exit_loop,
                "compare": sr_compare,
                "case": sr_case,
                "print": sr_print,
                "register_triad": r_register_triad,
                "clear": r_clear,
                "remove_triad": r_remove_triad,}
    
    def p_set(self, target_ns, parameters, ns, blok_ns ):
        name, *parameters = parameters
        #print(parameters)
        target_ns[name] = self.get_info(parameters, ns, blok_ns)
        #print(target_ns)\
        return 1
        
    def p_clear_list(self, a_list):
        while a_list: a_list.pop()
        
        
            
    ########
    # TESTS
    ########
    
    FROM_PARAMETERS = 1
    OPTIONAL = 2

    def test_result(self, test, ns, blok_ns):
        test, *parameters = test
        #print("      test: {}, with para: {}".format(test, str(parameters)))
        test, ns_vars = ns["__TESTS__"][test]
        if ns_vars == "NS":
            args = [[ns, blok_ns], parameters]
        else:
            args = []
            optional = False
            for var in ns_vars:
                popped = False
                if var is self.OPTIONAL:
                    optional = True
                    continue
                if var is self.FROM_PARAMETERS: 
                    try:
                        var = parameters.pop(0)
                        popped = True
                    except IndexError:
                        if not optional:
                            err = "{}: missing arguments".format(reader_)
                            raise BlokCodeError(err)
                        else:
                            optional = False
                            continue
                try:
                    if var.startswith("G:"): 
                        v = ns[var[2:]]
                    elif var in blok_ns: 
                        v = blok_ns[var]                    
                    elif var in ns:
                        v = ns[var]
                    else: raise IndexError()
                except IndexError:
                    if not optional:
                        err = "{}: unknown var".format(reader_)
                        raise BlokCodeError(err)
                    else:
                        if popped: parameters.insert(0, var)
                        optional = False
                        continue
                args.append(v)
                optional = False
            args +=  parameters
        #print("      test: {}, with args: {}".format(test, str(args)))
        return test(self,*args)
    
    def st_not(self, nss, test):
        return not self.test_result(test, nss[0], nss[1]) 
    
    def st_collection_size(self, list, *parameters):
        test = parameters[0]
        if test in {"empty", "even", "odd"}:
            if not len(parameters) == 1:
                err = "list test {}: no parameters allowed".format(test)
                raise BlokCodeError(err)
        elif test in {"==", ">", "<"}:
            if not len(parameters) == 2:
                err = "list test use: list {} number".format(test)
                raise BlokCodeError(err)
        #print("len test list: {}".format(len(list)))
        if test == "empty": return len(list) == 0
        if test == "even": return len(list) % 2 == 0
        if test == "odd": return len(list) % 2 == 1
        if test == "==": return len(list) == int(parameters[1])
        if test == '>': return len(list) > int(parameters[1])
        if test == '<': return len(list) < int(parameters[1])
        raise BlokCodeError("list test: unknown args")
    
    def st_compare_result(self, result, *parameters):
        test_val = {"==": 0, ">":1, "<": 2,
                    "equal": 0,}
        if result == "is":
            raise BlokCodeError(
                "compare_results: no compare data, run compare first!")
        compare_value = test_val[parameters[-1]]
        return result == compare_value

    def t_triad_up(self, triad, *parameters):
        if parameters:
            raise BlokCodeError('triad_up takes no parameters')
        return triad.type_ == Triad.ASCENDING

    def t_triad_down(self, triad, *parameters):
        if parameters:
            raise BlokCodeError('triad_down takes no parameters')
        return triad.type_ == Triad.DESCENDING
  
    tests = {"not": (st_not, "NS"),
             "compare_result": (st_compare_result, 
                                [OPTIONAL, FROM_PARAMETERS,
                                 OPTIONAL, "__LAST_COMPARE__"]),
             "triad_up": (t_triad_up, ["__TRIAD__"]),
             "triad_down": (t_triad_down, ["__TRIAD__"]),
             "uplist": (st_collection_size, ["__UP_LIST__"]),
             "downlist": (st_collection_size, ["__DOWN_LIST__"]),
             }    
    
    ########
    # INFO
    ########    

    
    def get_info(self, reader_chunk, ns, blok_ns):
        reader_, *parameters = reader_chunk
        if not reader_ in ns["__INFO__"]:
            parameters.insert(0, reader_)
            reader_ = "var"
        reader, ns_vars = ns["__INFO__"][reader_]
        #print("*i*",reader, ": ", parameters)
        args = []
        for var in ns_vars:
            if var is self.FROM_PARAMETERS:
                try:
                    var = parameters.pop(0)
                except IndexError:
                    err = "{}: missing arguments".format(reader_)
                    raise BlokCodeError(err)
            try:
                if var.startswith("G:"): v = ns[var[2:]]
                elif var in blok_ns: v = blok_ns[var]
                elif var in ns: v = ns[var]
                else: raise IndexError()
            except IndexError:
                err = "{}: unknown var".format(reader_)
                raise BlokCodeError(err)
            args.append(v)
        args += parameters
        val = reader(self, *args)
        #print("*i*result: ", val)
        return val;
    
    def si_read(self, value, *parameters):
        return value
    
    def si_int(self, value, *parameters):
        return int(value)
    
    def si_collection_info(self, collection, *parameters):
        test, *parameters = parameters
        try:
            if test == "size": return len(collection)
            if test == "max": return max(collection)
            if test == "min": return min(collection)
            if test == "index":
                #i = self.get_info(reader_chunk, ns, blok_ns)
                i = parameters[0]
                return collection[i]
        except TypeError:
            raise BlokCodeError("collection info: unorderable collection")
        raise BlokCodeError("collection info: unknown request")
    
    def i_triad(self, triad, *parameters):
        test, *parameters = parameters
        if test == "top":
            return triad.extreme_top
        raise BlokCodeError("triad: unknown request")
    
    def i_u_d_list(self, u_d_list, *parameters):
        test = parameters[0]
        if test in {"min", "max", "last_top", "index"}:
            test_collection = [t.extreme_top for t in u_d_list]
            if test == "last_top":
                parameters = ["index", -1]
            elif test == "index":
                i = int(parameters[1])
                parameters = ["index", i]
        elif test in {"last_time"}:
            test_collection = [t.extreme_time for t in u_d_list]
            if test == "last_time":
                parameters = ["index", -1]                
        elif test in {"size"}:
            test_collection = u_d_list 
        else: raise BlokCodeError("list info, unknown request")
        return self.si_collection_info(test_collection, *parameters)
    
    info = {"var": (si_read, [FROM_PARAMETERS]),
            "string": (si_read, []),
            "int": (si_int, []),
            "triad": (i_triad, ["__TRIAD__"]),
            "uplist": (i_u_d_list, ["__UP_LIST__"]),
            "downlist": (i_u_d_list, ["__DOWN_LIST__"]),
            }
    

class SwingCountingByRulesEM(SwingCountingByRules):
#class SwingCountingByRulesEM(SwingCountingByArgs):   
    def register(self, *parameters, finished=True):
        if not finished:        
            orig_up_list = self.up_list
            orig_down_list = self.down_list
            orig_up_l_e = self.up_last_export
            orig_down_l_e = self.down_last_export
            orig_perm_list_size = len(self.perm_list)
        new_perms = super().register(*parameters)
        if new_perms:
            if finished and hasattr(self, "finished_new_perm_filename"):
                with open(self.finished_new_perm_filename, 'a', newline='') as ofh: 
                    writer = csv.writer(ofh)
                    self.perm_list_to_csv_writer(new_perms, writer)
            if finished and hasattr(self, "easy_restart_filename"):
                self.save_minimal_restart_info(self.easy_restart_filename)
            if not finished:
                if hasattr(self, "unfinished_new_perm_filename"):
                    with open(self.unfinished_new_perm_filename, 'w', newline='') as ofh: 
                        writer = csv.writer(ofh)
                        self.perm_list_to_csv_writer(new_perms, writer)
                self.up_last_export = orig_up_l_e
                self.down_last_export = orig_down_l_e 
                while len(self.perm_list) > orig_perm_list_size:
                    self.perm_list.pop()
        else:
            if not finished:
                open(self.unfinished_new_perm_filename, 'w').close()
        if not finished:      
            self.up_list = orig_up_list
            self.down_list = orig_down_list
        return new_perms
    
    def no_unfinished_triad(self):        
        open(self.unfinished_new_perm_filename, 'w').close()
    
    def hot_start(self, minimal_restart_info, mri_location=mypy.TMP_LOCATION,
                  full_perm_history=None, fph_location=mypy.TMP_LOCATION):
        self._mri = minimal_restart_info
        self._mri_location = mri_location
        self.load_minimal_restart_info(minimal_restart_info, mri_location)
        if full_perm_history:
            self.full_perm_history_filename = full_perm_history
            self.full_perm_history_location = fph_location
            self.load_full_triad_history(full_perm_history, fph_location)
        self._hot_start = True
        
    def clean_exit(self):
        if hasattr(self, "_ufb_file"):
            self._ufb_file.close()
            #print("unfinished bar report file closed")
        #if (hasattr(self, "_hot_start") and 
        #print("bar_extra_modes clean exit"http://fsfe.org/)
    
    def text_output(self, 
                    finished_new_perm_file=None, fp_location=mypy.TMP_LOCATION,
                    unfinished_new_perm_file=None, up_location=mypy.TMP_LOCATION):
        if finished_new_perm_file == None and unfinished_new_perm_file == None:
            raise Exception("Live data mode started without files to export to")
        if finished_new_perm_file:
            self.finished_new_perm_filename = os.path.join(fp_location, 
                                                       finished_new_perm_file)
            if not hasattr(self, "_hot_start"):
                open(self.finished_new_perm_filename, 'w').close()
        if unfinished_new_perm_file == True:
            unfinished_new_perm_file = '.'.join([finished_new_perm_file, "unfinished"])
            up_location = fp_location
        if unfinished_new_perm_file:
            self.unfinished_new_perm_filename = os.path.join(up_location,
                                                    unfinished_new_perm_file)
            
    def safe_restart_mode(self, easy_restart_file=None, 
                          er_location=mypy.TMP_LOCATION):
        if easy_restart_file == None:
            if hasatrr(self, "_mri"):
                self.easy_restart_filename = self._mri,
                self.easy_restart_location = self._mri_location
                return
            else:
                raise("bardata, no easy restart filename known")
        else:
            self.easy_restart_filename = easy_restart_file
            self.easy_restart_location = er_location

            
    
class LiveSwingCounting():
    
    def __init__(self, output_file):
        if output_file:
            self.recent_swing_count_file = os.path.join(mypy.TMP_LOCATION,
                                              '.'.join([output_file, 'resc']))
            #self.permanent_swing_count_file = os.path.join(mypy.TMP_LOCATION,
                                              #'.'.join([output_file, 'pesc']))
        else:
            self.recent_swing_count_file = self.permanent_swing_count_file = None
        open(self.recent_swing_count_file, 'w').close()
        #open(self.permanent_swing_count_file, 'w').close()
        self.watch_list = []
        #self.up_count = self.up_max = self.up_reset = 0
        #self.down_count = self.down_min = self.down_reset = 0
        
    def update(self, curr_active_swing_list):
        for swing in curr_active_swing_list:
            if not swing.type == Swing.IN_DUBIO:                
                with open(self.recent_swing_count_file, 'w') as ofh, open(self.permanent_swing_count_file, 'a') as ofh2:
                    count = 0
                    #for triad in swing.triad_list[1:]:
                        #count += 1
                    for triad in swing.triad_list:
                        ofh.write('{},{},{},{}\n'.format(swing.type, count, 
                                                    triad.extreme_time,
                                                    triad.extreme_top))
                        count += 1
                    ############
                    return 0
                    ############
                    if count > 0:
                        output_count = False
                        count -= 1
                        if count == 0:
                            ###hist_correction
                            #  No historical correction, there is no history
                            #  before the starting point. 
                            ###counter_settings
                            #  I think I will only get here once and counters
                            #  are already set @ init. Following code is just
                            #  to check this assumption.
                            if hasattr(self, "count_zero_visited"):
                                raise Exception("Second time in zero visited")
                            else:
                                self.count_zero_visited = 0
                                
                        elif count == 1:
                            fp, last_type, last_count, last_triad = self.watch_list[-1]
                            ###counter_settings
                            if swing.type == Swing.UP:
                                if(triad.extreme_top < self.up_reset
                                   or
                                   self.up_reset == 0):
                                    self.up_count = 1
                                    self.up_max = triad.extreme_top
                                    self.up_reset = last_triad.extreme_top
                                    output_count = self.up_count
                                #elif triad.extreme_top > self.up_max:
                                    #self.up_max = triad.extreme_top
                                    #self.up_count += 1
                                    #output_count = self.up_count
                                else:
                                    output_count = 1
                            elif swing.type == Swing.DOWN:
                                if triad.extreme_top > self.down_reset:
                                    self.down_count = 1
                                    self.down_min = triad.extreme_top
                                    self.down_reset = last_triad.extreme_top
                                    output_count = self.up_count
                                #elif triad.extreme_top < self.down_min:
                                    #self.down_max = triad.extreme_top
                                    #self.down_count += 1
                                    #output_count = self.down_count
                                #output_count = self.down_count
                                else:
                                    output_count = 1
                            ###hist_correction
                            if last_type == Swing.NEW:
                                # I should get here only once (see count == 0)
                                self.watch_list.pop()
                                ofh2.seek(fp)
                                ofh2.truncate()
                                self.watch_list.append((fp, swing.type, 0, 
                                                        last_triad))
                                ofh2.write('{},{},{},{}\n'.format(swing.type, 
                                                    0, last_triad.extreme_time,
                                                    last_triad.extreme_top))
                            elif output_count == 1:
                                # if this is one, the previous must be starting
                                # point. Number the previous as 0-move
                                fp = ofh2.tell()
                                self.watch_list.append((fp, swing.type, 0,
                                                        last_triad))
                                ofh2.write('*{},{},{},{}\n'.format(swing.type,
                                                    0, last_triad.extreme_time,
                                                    last_triad.extreme_top))
                        elif count == 2:
                            fp, last_type, last_count, last_triad = self.watch_list[-1]
                            (p_fp, p_last_type, p_last_count, p_last_triad) = self.watch_list[-2]
                            ###counter_settings
                            if swing.type == Swing.UP:
                                if p_last_triad.extreme_top < self.up_reset:
                                    self.up_count = 2
                                    self.up_min = last_triad.extreme_top
                                    self.up_reset = p_last_triad.extreme_top
                                    output_count = 2
                                if triad.extreme_top < self.up_reset:
                                    self.up_count = 2
                                    self.up_max = last_triad.extreme_top
                                    self.up_reset = p_last_triad.extreme_top
                                    output_count = 2
                                elif last_triad.extreme_top > self.up_max:
                                    self.up_max = last_triad.extreme_top
                                    self.up_count += 1 if last_count == 1 else 2
                                    output_count = self.up_count
                                elif last_count > 2:
                                    output_count = 2
                                elif last_count == 2:
                                    if p_last_count >= 2:
                                        self.up_count += 1
                                elif last_count == 1:
                                    if last_type == Swing.UP:
                                        self.up_count = 2
                                        output_count = 2
                                else:
                                    #print("Unhandeled upswing count 2")
                                    #print("Triad top {}".format(triad.extreme_top))
                                    #print("co_ma_re {}|{}|{})".format(
                                           #self.up_count, self.up_max, self.up_reset))
                                    #print("la_pla {}|{}".format(last_count, p_last_count))
                                    mypy.get_bool("presspres", default=True)
                            elif swing.type == Swing.DOWN:
                                if p_last_triad.extreme_top > self.down_reset:
                                    self.down_count = 2
                                    self.down_min = last_triad.extreme_top
                                    self.down_reset = p_last_triad.extreme_top
                                    output_count = 2
                                elif triad.extreme_top > self.down_reset:
                                    self.down_count = 2
                                    self.down_min = last_triad.extreme_top
                                    self.down_reset = p_last_triad.extreme_top
                                    output_count = 2
                                elif last_triad.extreme_top < self.down_min:
                                    self.down_min = last_triad.extreme_top
                                    self.down_count += 1 if last_count == 1 else 2
                                    output_count = self.down_count
                                elif last_count > 2:
                                    output_count = 2
                                elif last_count == 2:
                                    if p_last_count >= 2:
                                        self.down_count += 1
                                elif last_count == 1:
                                    if last_type == Swing.DOWN:
                                        self.down_count = 2
                                        output_count = 2
                                else:
                                    #print("Unhandeled downswing count 2")
                                    #print("Triad top {}".format(triad.extreme_top))
                                    #print("co_mi_re {}|{}|{})".format(
                                        #self.down_count, self.down_min, self.down_reset))
                                    #print("la_pla {}|{}".format(last_count, p_last_count))
                                    mypy.get_bool("presspres", default=True)
                            ###hist correction
                            if p_last_count == 2:
                                pass
                                #output_count = False
                            elif last_count >= 2:
                                fp = ofh2.tell()
                                #self.watch_list.append((fp, swing.type, 0,
                                                        #p_last_triad))
                                ofh2.write('*{},{},{},{}\n'.format(swing.type,
                                                    0, p_last_triad.extreme_time,
                                                    p_last_triad.extreme_top))
                                fp = ofh2.tell()
                                #self.watch_list.append((fp, swing.type, 0,
                                                        #last_triad))
                                ofh2.write('*{},{},{},{}\n'.format(swing.type,
                                                    1, last_triad.extreme_time,
                                                    last_triad.extreme_top)) 
                                
                        fp = ofh2.tell() if output_count == False else None
                        self.watch_list.append((fp, swing.type, count, triad))
                        if output_count:  
                            ofh2.write('{},{},{},{}\n'.format(swing.type, 
                                                        output_count+90, 
                                                        triad.extreme_time,
                                                        triad.extreme_top))
                    break
        
        
    
    
    
class SwingAnalyser():
    
    def __init__(self, bar_size, output_file='out', level=0):
        self.level = level
        self.bar_size = bar_size
        self.active_swing_list = []
        self.swing_list = []
        self.last_registered_swing = None
        self.recent_triads = []
        self.derivative = None
        self.output_file_name = output_file
        #self.alt_swing_count = LiveSwingCounting(output_file)
        self.alt_swing_count = SwingCountingByRules("counting_rules.cr",
                                                    output_file)
        if output_file:
            self.swing_output_file = os.path.join(mypy.TMP_LOCATION, 
                                            output_file+'.swa_swi')
            self.dubio_output_file = os.path.join(mypy.TMP_LOCATION, 
                                            output_file+'.swa_dubio')
            self.plot_data_output_file = os.path.join(mypy.TMP_LOCATION, 
                                            output_file+'.plot_data')
            self.trade_alert_file = os.path.join(mypy.TMP_LOCATION,
                                             '.'.join([output_file, 'alert']))
            self.trade_alert_plot_file = os.path.join(mypy.TMP_LOCATION,
                                             '.'.join([output_file, 'pl_al']))
            self.trade_alert_live_file = os.path.join(mypy.TMP_LOCATION,
                                             '.'.join([output_file, 'li_al']))
            open(self.swing_output_file, 'w').close()
            open(self.dubio_output_file, 'w').close()
            open(self.plot_data_output_file, 'w').close()
            open(self.trade_alert_file, 'w').close()
            open(self.trade_alert_plot_file, 'w').close()
        else:
            self.swing_output_file = None
            self.dubio_output_file = None
            self.plot_data_output_file = None
            self.trade_alert_file = None
            
    def insert_triad(self, triad):
        if triad in self.recent_triads:
            return
        self.recent_triads.append(triad)
        self.alt_swing_count.register(triad)
        for swing in self.active_swing_list:
            swing.insert_triad(triad)
        self.active_swing_list.append(Swing(self.bar_size, triad))
        curr_swing_index = 0
        while curr_swing_index < len(self.active_swing_list) - 2:
            curr_swing = self.active_swing_list[curr_swing_index]
            assert isinstance(curr_swing, Swing)
            if curr_swing.finished:                
                if (not swing.type == Swing.IN_DUBIO and
                    not len(swing.pivot_list) % 2 == 0):
                    print('toch nodig'); exit()
                    swing.triad_list.pop()
                    swing.pivot_list.pop()
                print(curr_swing)
                self.register_swing(curr_swing_index)
                self.active_swing_list.pop(curr_swing_index)
                continue
            if (curr_swing.type is Swing.IN_DUBIO or
                curr_swing.finished):
                self.check_dubio_status(curr_swing_index)
                if curr_swing.dubio_status is Swing.D_FINISHED:
                    self.register_swing(curr_swing_index)
                    self.active_swing_list.pop(curr_swing_index)
                elif curr_swing.dubio_status is Swing.D_REMOVABLE:
                    self.active_swing_list.pop(curr_swing_index)
                else:
                    curr_swing_index += 1
                continue
            #if curr_swing.finished:                
                #if (not swing.type == Swing.IN_DUBIO and
                    #not len(swing.pivot_list) % 2 == 0):
                    #swing.triad_list.pop()
                    #swing.pivot_list.pop()
                #print(curr_swing)
                #self.register_swing(curr_swing_index)
                #self.active_swing_list.pop(curr_swing_index)
                #continue
            if curr_swing.type is Swing.UP and curr_swing.confirmed:
                print('l: {} ******confirmed direction********'.format(self.level))
                print('  ', len(self.active_swing_list) - curr_swing_index)
                ##mypy.get_bool('hit enter', default=True)
                if len(self.active_swing_list) - curr_swing_index == 6:
                    print('  popping ', curr_swing_index + 1, curr_swing_index + 2)
                    print('  length swinglist: ', len(self.active_swing_list))
                    self.active_swing_list.pop(curr_swing_index + 2)
                    self.active_swing_list.pop(curr_swing_index + 1)
                    print('  length swinglist: ', len(self.active_swing_list))
                
            if curr_swing.type is Swing.DOWN and curr_swing.confirmed:
                print('l: {} ********confirmed direction********'.format(self.level))
                print('  ', len(self.active_swing_list) - curr_swing_index)
                ##mypy.get_bool('hit enter', default=True)
                if len(self.active_swing_list) - curr_swing_index == 6:
                    print('  popping ', curr_swing_index + 1, curr_swing_index + 2)
                    print('  length swinglist: ', len(self.active_swing_list))
                    self.active_swing_list.pop(curr_swing_index + 2)
                    self.active_swing_list.pop(curr_swing_index + 1)
                    print('  length swinglist: ', len(self.active_swing_list))
            break
        print('l: {} ANALYSIS'.format(self.level))
        warning_sended = False
        for swing in self.active_swing_list:
            nr_of_triads = len(swing)
            print(nr_of_triads, swing)
            if (not warning_sended and
                not swing.warning_sended and
                swing.type in (Swing.UP, Swing.DOWN) and
                nr_of_triads == 4):
                self.send_warning(swing)
                warning_sended = True
            if (not warning_sended and
                not swing.warning_sended == 'triggered' and
                swing.type in (Swing.UP, Swing.DOWN) and
                nr_of_triads == 5):
                self.send_triggered(swing)
                warning_sended = True
            if (not warning_sended and 
                swing.warning_sended): # and
                #swing.type in (Swing.UP, Swing.DOWN)):
                warning_sended = True
        print('nr of backup triads: ', len(self.recent_triads))
        print('===')
        #self.alt_swing_count.update(self.active_swing_list)
                    
    
    def check_dubio_status(self, swing_index):
        '''to test this function marks every in dubio swing that
        has an ancester that is in dubio Swing.D_REMOVABLE. If the 
        swing is on position 0, it asks the user what to do
        '''
        curr_swing = self.active_swing_list[swing_index]
        if curr_swing.dubio_status:
            return
        #if swing_index == 0:
            #for i, future_swing in enumerate(self.active_swing_list[1:]):
        if True:
            for i, future_swing in enumerate(self.active_swing_list[1:]):
                if (future_swing.type in (Swing.UP, Swing.DOWN) and
                    future_swing.confirmed):
                    if (self.last_registered_swing and
                        future_swing.type == self.last_registered_swing.type):
                        curr_swing.dubio_status = Swing.D_REMOVABLE
                    else:
                        curr_swing.dubio_status = Swing.D_FINISHED
                    return
            return
        #while swing_index > 0:
            #swing_index -= 1
            #if (self.active_swing_list[swing_index].type is Swing.IN_DUBIO and
                #:
                #curr_swing.dubio_status = Swing.D_REMOVABLE
                #break
            
    def register_swing(self, swing, forced=False):
        if not isinstance(swing, Swing):
            swing = self.active_swing_list[swing]
        if swing.warning_sended:
            self.send_done(swing)
        print('!!!!!!!' * (self.level + 1))
        print('l: {} registering swing ___'.format(self.level))
        print(swing)
        if self.swing_output_file:
            if (forced
                or
                not self.last_registered_swing
                or
                #True):
                swing.start_time > self.last_registered_swing.start_time):
                if (self.last_registered_swing and
                    swing.start_time > self.last_registered_swing.end_time):
                    if swing.type == Swing.UP:
                        print('swing up')
                        if (self.last_registered_swing.type == Swing.DOWN and
                            swing.start_value <= self.last_registered_swing.end_value):
                            print('last swing down, start not== to end last swing')
                            extended = False
                            for triad in self.recent_triads:
                                tt, tv = triad.extreme_time, triad.extreme_top
                                if triad.extreme_time <= self.last_registered_swing.end_time:
                                    print('l: {} skipping'.format(self.level))
                                    print(triad)
                                    continue
                                if (swing.start_time < tt
                                    or
                                    swing.start_value > tv
                                    or
                                    tv > self.last_registered_swing.start_value):
                                    print('l: {} breaking on'.format(self.level))
                                    print(triad)
                                    print('l: {} ++++++'.format(self.level))
                                    break
                                self.last_registered_swing.pivot_list.append(tv)
                                self.last_registered_swing.triad_list.append(triad)
                                print('l: {} @@@@@@@@@@@@ extended lrs with '.format(self.level), tv)
                                extended = True
                            if extended:
                                print('l: {} cr swing down/up extended: '.format(self.level), self.last_registered_swing)
                                #mypy.get_bool('enter', default=True)
                                self.register_swing(self.last_registered_swing, forced=True)
                                self.register_swing(swing)
                                return
                            else:
                                print('l: {} could not extend last registered swing, adding new one'.format(self.level))
                                insert_swing = Swing(swing.bar_size,
                                                     self.last_registered_swing.triad_list[-1])
                                for triad in self.recent_triads:                            
                                    if triad.extreme_time > insert_swing.start_time:
                                        insert_swing.insert_triad(triad)
                                        break
                                print('l: {} cr swing down/up inserted: '.format(self.level), insert_swing)
                                #mypy.get_bool('enter', default=True)
                                self.register_swing(insert_swing)
                                self.register_swing(swing)
                                return
                        elif self.last_registered_swing.type == Swing.DOWN:
                            print('last swing down, no gap with last swing end')
                            insert_swing = Swing(swing.bar_size,
                                                 self.last_registered_swing.triad_list[-1])
                            for triad in self.recent_triads:                            
                                if triad.extreme_time > insert_swing.start_time:
                                    insert_swing.insert_triad(triad)
                                    break
                            self.register_swing(insert_swing)
                            self.register_swing(swing)
                            return
                        elif self.last_registered_swing.type == Swing.UP:
                            print('last swing up')
                            if (swing.start_value >= self.last_registered_swing.pivot_list[-2] and
                                swing.end_value > self.last_registered_swing.end_value):
                                print('version 1')
                                self.last_registered_swing.append(swing)
                                self.register_swing(self.last_registered_swing, forced=True)
                                return
                            else:
                                print('version 2')
                                insert_swing = Swing(swing.bar_size,
                                                     self.last_registered_swing.triad_list[-1])
                                for triad in self.recent_triads:                            
                                    if triad.extreme_time > insert_swing.start_time:
                                        insert_swing.insert_triad(triad)
                                        break
                                self.register_swing(insert_swing)
                                self.register_swing(swing)
                                return
                            
                    elif swing.type == Swing.DOWN:
                        print('swing down')
                        if (self.last_registered_swing.type == Swing.UP and
                            swing.start_value >= self.last_registered_swing.end_value):
                            print('last swing up, start not== to end last swing')
                            extended = False
                            for triad in self.recent_triads:
                                tt, tv = triad.extreme_time, triad.extreme_top
                                if triad.extreme_time <= self.last_registered_swing.end_time:
                                    print('l: {} skipping'.format(self.level))
                                    print(triad)
                                    continue
                                if (swing.start_time < tt
                                    or
                                    swing.start_value < tv
                                    or
                                    tv < self.last_registered_swing.start_value):
                                    print('l: {} breaking on'.format(self.level))
                                    print(triad)
                                    print('l: {} ++++++'.format(self.level))
                                    break
                                self.last_registered_swing.pivot_list.append(tv)
                                self.last_registered_swing.triad_list.append(triad)
                                print('l: {} @@@@@@@@@@@@ extended lrs with '.format(self.level), tv)
                                extended = True
                            if extended:
                                print('l: {} cr swing up/down extended: '.format(self.level), self.last_registered_swing)
                                self.register_swing(self.last_registered_swing, forced=True)
                                self.register_swing(swing)
                                return
                            else:
                                print('l: {} could not extend last registered swing, adding new one'.format(self.level))
                                insert_swing = Swing(swing.bar_size,
                                                     self.last_registered_swing.triad_list[-1])
                                for triad in self.recent_triads:                            
                                    if triad.extreme_time > insert_swing.start_time:
                                        insert_swing.insert_triad(triad)
                                        break
                                print('l: {} cr swing up/down insert: '.format(self.level), insert_swing)
                                self.register_swing(insert_swing)
                                self.register_swing(swing)
                                return
                        elif self.last_registered_swing.type == Swing.UP:
                            print('last swing up, no gap with last swing end')
                            insert_swing = Swing(swing.bar_size,
                                                 self.last_registered_swing.triad_list[-1])
                            for triad in self.recent_triads:                            
                                if triad.extreme_time > insert_swing.start_time:
                                    insert_swing.insert_triad(triad)
                                    break
                            self.register_swing(insert_swing)
                            self.register_swing(swing)
                            return
                            
                        elif self.last_registered_swing.type == Swing.DOWN:
                            print('last swing up')
                            if (swing.start_value <= self.last_registered_swing.pivot_list[-2] and
                                swing.end_value < self.last_registered_swing.end_value):
                                self.last_registered_swing.append(swing)
                                self.register_swing(self.last_registered_swing, forced=True)
                                return
                            else:
                                insert_swing = Swing(swing.bar_size,
                                                     self.last_registered_swing.triad_list[-1])
                                for triad in self.recent_triads:                            
                                    if triad.extreme_time > insert_swing.start_time:
                                        insert_swing.insert_triad(triad)
                                        break
                                self.register_swing(insert_swing)
                                self.register_swing(swing)
                                return
                        else:
                            print(self.last_registered_swing.type,
                                  'end', swing.end_value, 'last', self.last_registered_swing.end_value)
                    if not swing.type == Swing.IN_DUBIO:
                        mypy.get_bool('I should not get here!!', default=True)
                        with open(self.plot_data_output_file, 'a') as of:
                            csv_out = csv.writer(of)                      
                            export = [swing.start_time,'','','','','','',swing.start_value]
                            csv_out.writerow(export)
                else:
                    if (self.last_registered_swing and
                        not swing.type == Swing.IN_DUBIO and
                        swing.type == self.last_registered_swing.type and
                        swing.start_time == self.last_registered_swing.end_time):
                        self.last_registered_swing.append(swing)
                        self.register_swing(self.last_registered_swing, forced=True)
                        return
                    print('hohohoho')
                    #mypy.get_bool('I should not get here!!', default=True)
                    print(swing)
                    with open(self.plot_data_output_file, 'a') as of:
                        csv_out = csv.writer(of)                      
                        export = [swing.start_time,'','','','','','',swing.start_value]
                #if (not swing.type == Swing.IN_DUBIO and
                    #not len(swing.pivot_list) == 1 and
                    #not len(swing.pivot_list) % 2 == 0):
                    #swing.triad_list.pop()
                    #swing.pivot_list.pop()
                with open(self.swing_output_file, 'a') as of:
                    of.write('REGISTER SWING\n')
                    of.write('==============\n')
                    of.write(str(swing))
                    of.write('\n')
                if not swing.type == Swing.IN_DUBIO:
                    if self.derivative == None:
                        self.derivative = SwingAnalyser(self.bar_size,
                                                        self.output_file_name+'_',
                                                        level=self.level+1)
                    self.last_registered_swing = swing
                    if (self.swing_list and
                        swing.start_time == self.swing_list[-1].start_time):
                        self.swing_list[-1] = swing
                    else:
                        self.swing_list.append(swing)
                    while self.recent_triads[0].extreme_time < self.last_registered_swing.start_time:
                        self.recent_triads.pop(0)
                    self.derivative.insert_triad(swing.triad_list[0])
                self.update_plot_data(swing)
            
            else:
                with open(self.dubio_output_file, 'a') as of:
                    of.write('OUTLIER DUBIO SWING\n')
                    of.write('==============\n')
                    of.write(str(swing))
                    of.write('\n')  
        print('l: {} registering swing ___'.format(self.level))
        print(swing)
        print('!!!!!!!' * (self.level + 1))  
            
                    
    def update_plot_data(self, swing):
        if not isinstance(swing, Swing):
            swing = self.active_swing_list[swing]
        if swing.type == Swing.UP:
            position = 1
        elif swing.type == Swing.DOWN:
            position = 2
        else:
            position = 5
        with open(self.plot_data_output_file, 'a') as of:
            csv_out = csv.writer(of)
            exported_start_of_swing = False
            for triad in swing.triad_list:
                export = ['','','','','','','']
                multiplier = -1 if triad.type_ is Triad.ASCENDING else 1
                correction = multiplier * position * 0.07
                export[0]=triad.extreme_time
                export[position] = triad.extreme_top + correction
                if not exported_start_of_swing:
                    start_position = position + 2 if position < 3 else 6
                    export[start_position] = triad.extreme_top + correction
                    exported_start_of_swing = True
                csv_out.writerow(export)
                
    def send_warning(self, swing):
        assert isinstance(swing, Swing)
        if swing.type == Swing.UP:
            mess = 'L{} {}: Next pivot up above {} confirms UPSWING'.format(
                  self.level, swing.id,
                  swing.pivot_list[2])
            plot_info = [swing.id, swing.triad_list[2].extreme_time,
                         swing.triad_list[-1].end_time - timedelta(seconds=self.bar_size),
                         swing.pivot_list[2], '', '',
                         swing.pivot_list[2],'','','']
        elif swing.type == Swing.DOWN:
            mess = 'L{} {}: Next pivot down below {} confirms DOWNSWING'.format(
                  self.level,swing.id,
                  swing.pivot_list[2])
            plot_info = [swing.id, swing.triad_list[2].extreme_time,
                         swing.triad_list[-1].end_time - timedelta(seconds=self.bar_size),
                         swing.pivot_list[2], '', '',
                         '',swing.pivot_list[2], '','']
        else:
            raise Exception('I don\'t wont to be here')
        with open(self.trade_alert_file, 'a') as output_file:
            print(mess, file=output_file)
        with open(self.trade_alert_plot_file, 'a') as output_file:
            cvs_out = csv.writer(output_file)
            cvs_out.writerow(plot_info)
        swing.warning_sended = True
                
    def send_triggered(self, swing):
        assert isinstance(swing, Swing)
        if swing.type == Swing.UP:
            mess = ('L{} {}: Found pivot above {} with close {}, points already used {:4.2f}'
                   ', stop {:4.2f}'.format(
                self.level,swing.id,
                swing.pivot_list[2], swing.triad_list[4].close,
                abs(swing.start_value - swing.triad_list[4].close),
                abs(swing.triad_list[4].close - swing.pivot_list[4])))
            plot_info = [swing.id, swing.triad_list[-1].end_time, '',
                         '', swing.triad_list[-1].direction_bar.close, swing.pivot_list[2],
                         '', '', '', '']
        elif swing.type == Swing.DOWN:
            mess = ('L{} {}: Found pivot below {} with above {}, points already used {:4.2f}'
                   ', stop {:4.2f}'.format(
                self.level, swing.id,
                swing.pivot_list[2], swing.triad_list[4].close,
                abs(swing.start_value - swing.triad_list[4].close),
                abs(swing.triad_list[4].close - swing.pivot_list[4])))
            plot_info = [swing.id, swing.triad_list[-1].end_time, '',
                         '', swing.triad_list[-1].direction_bar.close, swing.pivot_list[2],
                         '', '', '', '']
        with open(self.trade_alert_file, 'a') as output_file:
            print(mess, file=output_file)
        with open(self.trade_alert_plot_file, 'a') as output_file:
            cvs_out = csv.writer(output_file)
            cvs_out.writerow(plot_info)
        swing.warning_sended = 'triggered'
    
    def send_done(self, swing):
        if swing.warning_sended == 'done':
            return
        swing.warning_sended = 'done'
        mess = 'L{} {}: done'.format(self.level, swing.id)
        with open(self.trade_alert_file, 'a') as output_file:
            print(mess, file=output_file)
    
class MultiTriadReducer():
    
    def __init__(self, base_bar_size, *reductions,
                 output_file=None):
        """Initiate multi triad reducer
        
        base_bar_size: the size of the bar that the reducer will
                       consider a 'tick'. The open high low close 
                       is stored in the instance events_log
        reductions: bar sizes to use for the  triad reducers, must all
                    be multipliers of the base_bar_size
        As always these barsizes are in seconds.
        If you specify an output file all the events will be written to
        that file to.
        
        """
        self.base_bar_size = base_bar_size
        self.base_ochl = ochl('s', base_bar_size)
        self.reduction_order = reductions
        self.reduction = {}
        for reduction in reductions:
            if not reduction % self.base_bar_size == 0:
                raise ValueError('reduction must be multiplier of base_bar_size')
            self.reduction[reduction] = {'bars': ochl('s', reduction),
                                         'triads': TriadReducer(reduction)}
            self.reduction[reduction]['triads'].swing_analyser = SwingAnalyser(reduction)
        if output_file:
            self.output_file = os.path.join(mypy.TMP_LOCATION, output_file)
            self.csv_file = open(self.output_file, 'w', buffering=1)
            self.csv_out = csv.writer(self.csv_file)
            self.last_csv_start_position = self.csv_file.tell()
            self.csv_correction = ((1 + len(reductions)) * 6) * ['']
        else:
            self.output_file, self.csv_out = None, None
        
    def insert_bar(self, ochl_bar, bar_volume=None):
        red_bars = {}
        red_new_bars = {}
        last_extreme = {}
        curr_bar, new_base_bar = self.base_ochl.insert(*ochl_bar)
        for name, reduction in self.reduction.items():
            k, l = reduction['bars'].insert(*ochl_bar)
            red_bars[name], red_new_bars[name] = k, l
            if l and reduction['bars'].last_finished_bar():
                last_bar = reduction['bars'].last_finished_bar()
                m = reduction['triads'].insert(last_bar)
                if m:
                    reduction['triads'].swing_analyser.insert_triad(m)
                    print(m)
                    last_extreme[name] = (m.extreme_bar.time, m.extreme_top)
                else:
                    last_extreme[name] = None
            else:
                last_extreme[name] = None
                
        if self.output_file:
            if self.last_csv_start_position == 0:                
                self.csv_out.writerow([curr_bar.time-timedelta(self.base_bar_size)] +self.csv_correction[1:])
                self.last_csv_start_position = self.csv_file.tell()            
            data = list(curr_bar) + [-1]
            for reduction in self.reduction_order:
                data.extend(list(red_bars[reduction]) + [-1])                
            self.csv_file.seek(self.last_csv_start_position)
            self.csv_file.truncate(self.last_csv_start_position)
            if new_base_bar:
                last_bar = self.base_ochl.last_finished_bar()
                if last_bar:
                    self.csv_out.writerow(
                        list(last_bar) + [-1] +self.csv_correction[6:])
            for i, reduction in enumerate(self.reduction_order):
                if red_new_bars[reduction]:
                    last_bar = self.reduction[reduction]['bars'].last_finished_bar()
                    if last_bar:
                        self.csv_out.writerow(
                              (self.csv_correction[:6+i*6] + list(last_bar) + [-1] +
                              self.csv_correction[6+(i+1)*6:]))
                if last_extreme[reduction]:
                    self.csv_out.writerow(
                          ([last_extreme[reduction][0]] + self.csv_correction[1:] +
                           i * [''] + [last_extreme[reduction][1]]) + 
                           ((len(self.reduction_order)-i) * ['']))
            self.last_csv_start_position = self.csv_file.tell()            
            self.csv_out.writerow(data)
            self.csv_out.writerow(([curr_bar.time+timedelta(seconds=self.reduction_order[-1])]
                                  + 4 * [curr_bar.close] + [-1] +
                                  self.csv_correction[6:]))
            self.csv_file.flush()
            
            
class HistoricalSwingAnaliser():
    
    wave_count_info_tuple = namedtuple('wave_count_into_tuple',
                  'official_move_wave_count '
                  'real_move_wave_count '
                  'cumm_official_move_wave_count '
                  'cumm_real_move_wave_count '
                  'nr_of_swings '
                  'perc_official_swings_with_nr_of_moves '
                  'perc_real_swings_with_nr_of_moves '
                  'perc_official_swings_with_at_least_nr_of_moves '
                  'perc_real_swings_with_at_least_nr_of_moves'
                  )
    
    similar_analysis_tuple = namedtuple('similar_analysis',
                  'max_sigma2 number_of_swings number_of_good_swings '
                  'perc_good_swings mode mode_perc harmonic_mean '
                  'harmonic_mean_perc')
    
    def __init__(self, swing_analysis, level=0,
                 column_width=7, perc_float=0):
        if isinstance(swing_analysis, str):
            with open(swing_analysis, 'rb') as pf:
                self.historical_swing_analysis = pickle.load(pf)
        else:
            self.historical_swing_analysis = swing_analysis
        derivative = self.historical_swing_analysis.derivative
        self.column_width = column_width
        self.perc_float = perc_float
        self.simm_mode_delta = 0.1
        self.swing_list = self.historical_swing_analysis.swing_list
        while True:
            self.add_usefull_info()
            self.swing_list = derivative.swing_list
            derivative = derivative.derivative
            if not derivative:
                break
        self.set_level(level)
        
    def set_level(self, level):
        count_level = 0        
        base = self.historical_swing_analysis
        while count_level < level:
            count_level += 1
            base = base.derivative
        self.swing_list = base.swing_list
        self.level = level
        
    
    def add_usefull_info(self):
        #hsa = self.historical_swing_analysis
        for i in range(len(self.swing_list)-1):
            curr_swing = self.swing_list[i]
            next_swing = self.swing_list[i+1]
            curr_swing.following_triangle = next_swing.triad_list[1]
            curr_swing.following_pivot = next_swing.pivot_list[1]
            if (((curr_swing.type == Swing.UP) and
                 (curr_swing.pivot_list[-2] <= curr_swing.following_pivot))
                or
                ((curr_swing.type == Swing.DOWN) and
                 (curr_swing.pivot_list[-2] >= curr_swing.following_pivot))):
                curr_swing.real_moves = curr_swing.nr_of_moves + 1 
            else:
                curr_swing.real_moves = curr_swing.nr_of_moves
    
    def add_wave_count_info(self):
        if not hasattr(self, 'wave_count_info'):
            self.wave_count_info = {}
        level = self.level
        if level in self.wave_count_info:
            return
        official_move_wave_count = defaultdict(int)
        real_move_wave_count = defaultdict(int)
        for swing in self.swing_list[:-1]:
            official_move_wave_count[swing.nr_of_moves] += 1
            real_move_wave_count[swing.real_moves] += 1
        cumm_official_move_wave_count = official_move_wave_count.copy()
        cumm_real_move_wave_count = real_move_wave_count.copy()
        self.cumm(cumm_official_move_wave_count)
        self.cumm(cumm_real_move_wave_count)
        nr_of_swings = cumm_official_move_wave_count[1]
        perc_official_swings_with_nr_of_moves = {
            key:nr / nr_of_swings
            for key, nr in official_move_wave_count.items()}
        perc_real_swings_with_nr_of_moves = {
            key:nr / nr_of_swings
            for key, nr in real_move_wave_count.items()}
        perc_official_swings_with_at_least_nr_of_moves = {
            key:nr / nr_of_swings 
            for key, nr in cumm_official_move_wave_count.items()}
        perc_real_swings_with_at_least_nr_of_moves = {
            key:nr / nr_of_swings 
            for key, nr in cumm_real_move_wave_count.items()}
        self.wave_count_info[level] = self.wave_count_info_tuple(
                official_move_wave_count, real_move_wave_count,
                cumm_official_move_wave_count, cumm_real_move_wave_count,
                nr_of_swings, perc_official_swings_with_nr_of_moves,
                perc_real_swings_with_nr_of_moves, 
                perc_official_swings_with_at_least_nr_of_moves,
                perc_real_swings_with_at_least_nr_of_moves)
        
        
    def chance_to_advance(self, move_start, move_target):
        self.add_wave_count_info()
        if move_start >= move_target:
            return None
        #nr_of_start_moves = self.perc_real_swings_with_at_least_nr_of_moves[move_start]
        #nr_of_targets = self.perc_real_swings_with_at_least_nr_of_moves[move_target]
        info = self.wave_count_info[self.level]
        nr_of_start_moves = info.cumm_real_move_wave_count[move_start]
        nr_of_targets = info.cumm_real_move_wave_count[move_target]
        return nr_of_targets/nr_of_start_moves
    
    def sort_by_similarity(self, *data, algo='all'):
        self.similar_results = {'length benchmark': len(data)}
        if 'nomimal changes' in algo or 'all' in algo:
            self.similar_results['nominal changes'] = self.similar_nominal_changes(*data)
        print('simi results: ', self.similar_results.keys())
        
    def similar_nominal_changes(self, *data):
        answer = []
        if isinstance(data[0], Swing):
            data_diffs, foo = data[0].pivot_changes()
        else:
            data_diffs = data
        min_length = len(data_diffs)
        swing_type = Swing.DOWN if data_diffs[0] < 0 else Swing.UP
        for i, swing in enumerate(self.swing_list[:-1]):
            if len(swing) < len(data_diffs):
                continue
            elif not swing.type == swing_type:
                continue
            elif len(swing) == len(data_diffs):
                if (len(data_diffs) % 2 == 0 and 
                    not swing.real_moves == swing.nr_of_moves):
                    swing_diffs, foo = swing.pivot_changes(swing.following_pivot)
                else:
                    continue
            else:
                swing_diffs, foo = swing.pivot_changes()    
            diffs = zip(swing_diffs, data_diffs)       
            result = sum([(t[0] - t[1])**2 for t in diffs]) / min_length
            answer.append((result, i))
        answer.sort()
        return answer
    
    def similar_list_analysis(self, algo, partial_list_end=None):
        algo_swing_serie = self.similar_results[algo]
        partial_list_end = partial_list_end if partial_list_end else len(algo_swing_serie)
        length_benchmark = self.similar_results['length benchmark']
        profits = []
        for i, s in algo_swing_serie[0: partial_list_end]:
            swing = self.swing_list[s]
            if len(swing) >  length_benchmark:
                profits.append(swing.points)
        if profits:
            mode = mypy.mode(profits, delta=self.simm_mode_delta, round_method='down')
            test = lambda ell: ell >= mode[0]
            mode_perc = mypy.count_in_list(test, profits) / partial_list_end
            harmonic_mean = mypy.harmonic_mean(profits)
            test = lambda ell: ell >= harmonic_mean
            harmonic_mean_perc = mypy.count_in_list(test, profits) / partial_list_end
        else:
            mode = mode_perc = harmonic_mean = harmonic_mean_perc = 0
        analysis = self.similar_analysis_tuple(
              algo_swing_serie[partial_list_end-1][0], partial_list_end,
              len(profits), len(profits)/partial_list_end, mode,
              mode_perc, harmonic_mean, harmonic_mean_perc)
        #analysis = {'max_sigma2': algo_swing_serie[partial_list_end-1][0],
                    #'number_of_swings': partial_list_end,
                    #'number_of_good_swings': len(profits),
                    #'perc_good_swings': len(profits)/partial_list_end,
                    #'mode': mode,
                    #'mode_perc': mode_perc,
                    #'harmonic_mean': harmonic_mean,
                    #'harmonic_mean_perc': harmonic_mean_perc,
                    #}
        return analysis
           
    def show_official_move_wave_count(self):   
        self.add_wave_count_info()
        info = self.wave_count_info[self.level]
        width = self.column_width
        frac = self.perc_float
        o = mypy.SerialTextCreator(separator='|')
        keys = sorted(info.official_move_wave_count.keys())
        for key in keys:
            o.add_chunk('{:^{width}}'.format(key, width=width))
        o.underline('=')
        for key in keys:
            o.add_chunk('{:^{width}}'.format(info.official_move_wave_count[key],
                                            width=width))
        o.next_line()
        for key in keys:
            o.add_chunk('{:^{width}.{frac}%}'.format(
                info.perc_official_swings_with_nr_of_moves[key], 
                width=width, frac=frac))
        return o.text     
    
    def show_cumm_real_move_wave_count(self):      
        self.add_wave_count_info()
        info = self.wave_count_info[self.level]
        width= self.column_width
        frac = self.perc_float
        o = mypy.SerialTextCreator(separator='|')
        keys = sorted(info.cumm_real_move_wave_count.keys())
        for key in keys:
            o.add_chunk('{:^{width}}'.format(key, width=width))
        o.underline('=')
        for key in keys:
            o.add_chunk('{:^{width}}'.format(info.cumm_real_move_wave_count[key],
                                             width=width))
        o.next_line()
        for key in keys:
            o.add_chunk('{:^{width}.{frac}%}'.format(
                info.perc_real_swings_with_at_least_nr_of_moves[key], 
                width=width, frac=frac))
        return o.text
    
    def show_advance_chances_matrix(self):    
        self.add_wave_count_info()
        info = self.wave_count_info[self.level]        
        width= self.column_width
        frac = self.perc_float
        o = mypy.SerialTextCreator(separator='|')
        keys = sorted(info.cumm_real_move_wave_count.keys())
        for key in ['']+keys[1:]:
            o.add_chunk('{:^{width}}'.format(key, width=width))
        o.underline('=')
        for key in keys:
            o.add_chunk('{:{width}}'.format(key, width=width))
            for key2 in keys[1:]:
                chance = self.chance_to_advance(key, key2)
                if chance:
                    o.add_chunk('{:^{width}.{frac}%}'.format(
                        self.chance_to_advance(key, key2),
                        width=width, frac=frac))
                else:
                    o.add_chunk('{:^{width}}'.format('---', width=width))
            o.next_line()
        return o.text
    
        
    def show_overall_stats(self):
        o = mypy.SerialTextCreator()
        o.add_line('official move wave count')
        o.underline('*')
        o.add_text(self.show_official_move_wave_count())
        o.add_line('cumm real move count')
        o.underline('*')
        o.add_text(self.show_cumm_real_move_wave_count())
        print(o.text)
        #self.show_cumm_real_move_wave_count()
        
    def show_simmularity_results(self, algo='all', 
                                 sigma2_max=0.5, sigma2_step=0.05,intro_steps=5):  
        if not hasattr(self, 'similar_results'):
            return 'No simmular results requested'
        print(self.similar_results.keys())
        if algo == 'all':
            algo = ['nominal changes',]
        o = mypy.SerialTextCreator()
        for sim_algo in algo:
            o.add_line(sim_algo)
            o.underline('=')
            results = self.similar_results[sim_algo]
            sigma2_indexes = {}
            sigma2_labels = list(mypy.f_range(sigma2_step, sigma2_max + sigma2_step,
                                          sigma2_step))
            for i, result in enumerate(results, 1):
                sigma2_labels = [x for x in sigma2_labels if x >= result[0]]
                if not sigma2_labels:
                    break
                sigma2_indexes[sigma2_labels[0]] = i
            o.add_line('*sigma2 serie')
            new_data = self.similar_list_analysis(sim_algo)
            print(new_data)
            print('------------------')
            slices = [sigma2_indexes[x] for x in sorted(sigma2_indexes.keys(), reverse=True)]
            while slices[-1] > 2 * intro_steps -1:
                slices.append(mypy.d_round(slices[-1] - intro_steps,
                                           intro_steps, method='down'))
            slices.reverse()            
            for sigma2_label in slices: #sorted(sigma2_indexes.keys()):
                #o.add_line(self.show_)
                new_data = self.similar_list_analysis(sim_algo, sigma2_label)
                                                #sigma2_indexes[sigma2_label])
                print(new_data)
                
            

    def dump_to_screen(self, derivatives=False):
        level = self.level
        if level == 0:
            print('toplevel dump')
            print('+++++++++++++')
        else:
            print('$$$$$ {} deviation $$$$$$$'.format(level))            
        for swing in self.swing_list[:-1]:
            print(swing.start_time, '|', swing.end_time,
                  '{:4} | {:4} | {:4} | {:5} | {:5} | {:5.2f} | {:4.2f}'.format(
                      swing.type, swing.real_moves, swing.last_pure_directional_move,
                        swing.nr_of_moves, swing.nr_of_bars, swing.points,
                        swing.points_percentage*100))
        print()
        if derivatives:
            dediv = self.historical_swing_analysis.derivative
            while dediv:
                level += 1
                last_time = None
                print('$$$$$ {} deviation $$$$$$$'.format(level))
                for swing in dediv.swing_list:
                    print(swing.start_time, '|', swing.end_time,
                          '{:4} | {:4} | {:5} | {:5} | {:5.2f} | {:4.2f}'.format(
                              swing.first_move, swing.type,
                                swing.nr_of_moves, swing.nr_of_bars, swing.points,
                                swing.points_percentage))  
                if last_time and not last_time == swing.start_time:
                    print('   CHECK ABOVE START & END TIMES')
                last_time = swing.end_time
                print()
                dediv = dediv.derivative
                
    @staticmethod
    def cumm(a_dict):
        keys = sorted(a_dict.keys())
        total = a_dict[keys.pop()]
        while keys:
            key = keys.pop()
            total += a_dict[key]
            a_dict[key] = total
                 
        
if __name__ == '__main__':
    import sql_ib_db
    print('TestMode')
    print('++++++++')
    print()
    import tws
    from tws_realbar_request_gscLib import server_client
    #mtr = MultiTriadReducer(15, 15, 60, 120, 180, 240, 300, 360, 420, 
                            #output_file='triaddo')
    mtr = MultiTriadReducer(15, 630, 
                            output_file='triaddo')
    data_server = server_client()
    live_mode = mypy.get_bool('live mode? (Y, n)', default=True)
    ctr = tws.contract_data('AEX-index')
    if live_mode:        
        data = data_server.client_for_request('real_time_bars', ctr, 
                                              '5 secs', 'TRADES', False)
    else:
        start_date = mypy.get_date('start from (YYYY/MM/DD): ', format_='%Y%m%d',
                                   default='20120322')
        #db = ib_db
        db_h = sql_ib_db.HistoricalDatabase('EOE IND EUR AEX@FTA.db')
        data = db_h.data_stream('TRADES_5_secs', 
                                'datetime', 'open', 'close', 'high', 'low',
                                start=start_date)
    for i, latest in enumerate(data):
        if live_mode:
            curr_ochl = ochlBar(latest.time_, latest.open_, latest.close, 
                                latest.high,latest.low)
            mtr.insert_bar(curr_ochl)
            if i == 500000000:
                data.close()
            print(i)
        else:
            curr_ochl = ochlBar(*latest) 
            mtr.insert_bar(curr_ochl)
    hsa = HistoricalSwingAnaliser(mtr.reduction[630]['triads'].swing_analyser)
    hsa.dump_to_screen(derivatives=True)
    with open(os.path.join(mypy.TMP_LOCATION, 'mtr.mtr'), 'wb') as pf:
        pickle.dump(mtr.reduction[630]['triads'].swing_analyser, pf)