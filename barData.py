#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import csv
import pickle
import os.path
from collections import namedtuple
from datetime import timedelta

import mypy

ochlbar     = namedtuple('ochlbar', 'time open close high low')
reduced_Bar = namedtuple('reduced_Bar', 'curr_time time type value')

TOP    = 'maximum'
BOTTOM = 'minimum'

FIRST_HIGH_HIGHER_THEN = 1
FIRST_LOW_LOWER_THEN = 2
MINIMUM = 3
MAXIMUM = 4

class ochlBar(ochlbar):
    
    def __add__(self, other):
        '''Joins 2 bar, keeps open of first, close of second and
        max and min for hi and low'''
        return ochlBar(self.time,
                       self.open,
                       other.close,
                       max(self.high, other.high),
                       min(self.low, other.low))
    
    def __contains__(self, test_value):
        '''returns True if the test value is between high and low
        (high and low included) else returns false'''
        try:
            return self.low <= test_value <= self.high
        except:
            print("in problem")
            print("test: ",test_value)
            print("bar: ", self)
            raise
    def __gt__(self, other):
        '''return True if high of self is bigger then high of other
        and low of self is bigger then low of other'''
        return (self.high > other.high and
                self.low > other.low)
    
    def __lt__(self, other):
        '''return True if high of self is lower then high of other
        and low of self is lower then low of other'''
        return (self.low < other.low and
                self.high < other.high)
    
    @property
    def size(self):
        '''diff between high and low'''
        return self.high - self.low
    
    @property
    def close_perc(self):
        '''position of close in the bar'''
        if self.size == 0:
            answer = 100
        else:
            answer = (self.close - self.low) / self.size
        return answer
    
    def outside_interval(self, a, b):
        '''Checks if ochlbar has no values in the interval a, b'''
        answer = True
        a, b = sorted((a, b))
        if ((a <= self.low  and b >= self.high)
            or self.low < a < self.high
            or self.low < b < self.high):
            answer = False
        return answer
    
    def inside_interval(self, a, b):
        '''Checks if all values of ochlbar lies in the interval a, b'''
        a, b = sorted((a, b))
        if self.low >= a and self.high <= b:
            answer = True
        else:
            answer = False
        return answer
    
    def to_csv_writer(self, csv_handler):
        csv_handler.writerow(self)
        
def store(bar_list, dest_file):
    try:
        with open(dest_file, 'wb') as ofh:
            pickle.dump(bar_list, ofh)
    except EnvironmentError as err:
        print(err)

def load(location):
    try:
        with open(location, 'rb') as ifh:
            bar_list = pickle.load(ifh)
    except EnvironmentError as err:
        print(err)
    return bar_list

class ochl():
    #het was de bedoeling om met _new_bar_s verschillende functies te kunnen
    # schrijven en dan de juiste fuctie toe te kennen bij de __init__ 
    # dat lukte allemaal goed tot ik moest picklen, je kan in een instance geen naam
    # picklen die naar een functie verwijst :(. Nu voorlopig gehacked door de 
    # toekenning weg te laten rechtstreeks _new_bar_s aan te roepen wat de ochl
    # wat minder flexibel maakt. om deze hack te laten slagen heb ik ook self moeten
    # toevoegen aan de _new_bar_s parameters zou hier beter ook wat meer over leren
    def _new_bar_s(self,start_time_bar, curr_time, seconds_for_bar):
        newbar = False
        if seconds_for_bar >= 86399:
            print('maximale waarde voor aantal seconden is 86399')
            exit()
        bar_duration = curr_time - start_time_bar
        if (bar_duration.days 
            or 
            bar_duration.seconds >= seconds_for_bar
            or
            (self.normalised_bars and 
             not mypy.seconds_since_start_of_day(curr_time) % self.number_of_units)):
            newbar = True
        #elif (self.normalised_bars and 
              #not bar_duration.seconds % self.number_of_units)
        return newbar
        
        
    #def _eop_s(a_time, number_of_seconds):
    #    if number_of_seconds >= 3600:
    #        print('maximale waarde voor aantal seconden is 3599')
    #        exit()
    #    seconds = a_time.minute*60 + a_time.second
    #    return False if seconds % number_of_seconds != 0 else True

    def __init__(self,unit='s', number_of_units=5, time_normalised_bar=True):
        self.ochl_list = []
        self.unit      = unit
        self.normalised_bars = time_normalised_bar
        self.number_of_units = number_of_units
        self.time=self.open = self.high = self.low = None
        self.time_of_last_data = None
                
    def insert(self, curr_time, curr_open, curr_close, curr_high, curr_low):
        '''Returns a tupple (curr_bar, new_bar_started)
        current_bar is the bar that is building
        new_bar_started is a boolean that's true if a new bar is started'''
        bar = None
        new_bar_started = False
        if (not self.time_of_last_data is None and
            curr_time <= self.time_of_last_data):
            return self.ochl_list[-1], False
        self.time_of_last_data = curr_time
        if not self.ochl_list or self._new_bar_s(self.ochl_list[-1].time, 
                                                 curr_time,
                                                 self.number_of_units):
            new_bar_started = True
            self.open  = curr_open
            self.high  = curr_high
            self.low   = curr_low
            self.time  = curr_time
            bar = ochlBar(self.time, self.open, curr_close, self.high, self.low)
            self.ochl_list.append(bar)
        else:
            self.high  = max(self.high, curr_high)
            self.low   = min(self.low, curr_low)
            bar = ochlBar(self.time, self.open, curr_close, self.high, self.low)
            self.ochl_list[-1] = bar
        return bar, new_bar_started
    
    def exclusive_end(self):
        '''the time when this bar will be finished, actually the begintime
        of the next bar
        '''
        return self.time + timedelta(seconds=self.number_of_units)
        
    def save_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        outputfile = os.path.join(location, filename)
        info = (self.unit, self.number_of_units, self.normalised_bars,
                self.time, self.open, self.high, self.low,
                self.time_of_last_data, self.ochl_list[-2:])
        mypy.export_pickle(info, outputfile, id_="ochl: minimal_restart_info")
        
    def load_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        if not self.ochl_list == []:
            raise Exception("trying to load data in a running ochl")
        inputfile = os.path.join(location, filename)
        (self.unit, self.number_of_units, self.normalised_bars,
         self.time, self.open, self.high, self.low,
         self.time_of_last_data, self.ochl_list) = mypy.import_pickle(
                                    inputfile, id_="ochl: minimal_restart_info")
        
    def save_full_bar_history(self, filename, location=mypy.TMP_LOCATION): 
        outputfile = os.path.join(location, filename)
        info = self.ochl_list
        mypy.export_pickle(info, outputfile, id_="full_bar_history")
        
    def load_full_bar_history(self, filename, location=mypy.TMP_LOCATION):
        if not self.ochl_list == []:
            raise Exception("trying to load data in a running ochl")
        inputfile = os.path.join(location, filename)
        self.ochl_list = mypy.import_pickle(inputfile, 
                                            id_="full_bar_history")
        
    def export_full_bar_history(self, filename, location=mypy.TMP_LOCATION):
        outputfile = os.path.join(location, filename)
        with open(outputfile, 'w', newline='') as ofh:
            csv_out = csv.writer(ofh)
            for bar in self.ochl_list[:-1]:
                bar.to_csv_writer(csv_out)

    def last_finished_bar(self):
        '''Returns the last completed bar'''
        return self.ochl_list[-2] if len(self.ochl_list)>1 else None

    def curr_bar(self):
        '''Returns the current bar'''
        return self.ochl_list[-1] if self.ochl_list else None

    def select(self, search_for, value=0, since=None, included=True):
        '''Returns a date, value tupple or None, NOne if it not found'''

        ########################################################################
        # Selectors
        ########################################################################
        #
        def _first_high_higher_then(value, bar_list):
            for bar in bar_list:
                if bar.high > value:
                    return bar.time, bar.high
            else:
                return None, None
        #
        ########################################################################
        #
        def _first_low_lower_then(value, bar_list):
            for bar in bar_list:
                if bar.low < value:
                    return bar.time, bar.low
            else:
                return None, None
        #
        ########################################################################
        #
        def _minimum(bar_list):
            min_time, min_ = bar_list[0].time, bar_list[0].low
            for bar in bar_list:
                if bar.low < min_:
                    min_ = bar.low
                    min_time = bar.time
            return min_time, min_
        #
        ########################################################################
        #
        def _maximum(bar_list):
            max_time, max_ = bar_list[0].time, bar_list[0].high
            for bar in bar_list:
                if bar.high > max_:
                    max_ = bar.low
                    max_time = bar.time
            return max_time, max_
        #
        ########################################################################
    
        if since == None:
            search_list = self.ochl_list
        else:
            for bar_count in reversed(range(0, len(self.ochl_list))):
                if self.ochl_list[bar_count].time <= since:
                    first_bar = bar_count + (0 if included else 1)
                    if first_bar == len(self.ochl_list):
                        return None, None
                    else:
                        search_list = self.ochl_list[first_bar:]
                        break
            else:
                return None, None
        if search_for == FIRST_HIGH_HIGHER_THEN:
            answer = _first_high_higher_then(value, search_list)
            #print('***************fhht', answer, '*****************************')
        elif search_for == FIRST_LOW_LOWER_THEN:
            answer = _first_low_lower_then(value, search_list)
            #print('***************fllt', answer, '*****************************')
        elif search_for == MINIMUM:
            answer = _minimum(search_list)
            #print('***************min', answer, '*****************************')
        elif search_for == MAXIMUM:
            answer = _maximum(search_list)
            #print('***************max', answer, '*****************************')
        return answer

class ochl_extra_modes(ochl):
    
    def insert(self, *parameters):
        bar, new_bar_started = super().insert(*parameters)
        if new_bar_started:
            if hasattr(self, "finished_bars_filename"):
                with open(self.finished_bars_filename, 'a', newline='') as ofh: 
                    writer = csv.writer(ofh)
                    self.last_finished_bar().to_csv_writer(writer)
            if hasattr(self, "easy_restart_filename"):
                self.save_minimal_restart_info(filename)
        if hasattr(self, "unfinished_bar_file"):
            print("writing unfinished bar @ ", mypy.now())
            with open(self.unfinished_bar_file, 'w', newline='') as ofh: 
                writer = csv.writer(ofh)
                self.curr_bar().to_csv_writer(writer)
                curr_time = parameters[0].time()
                writer.writerow([self.time_until_next_bar(curr_time),
                                 self.exclusive_end()])
        return bar, new_bar_started
    
    def hot_start(self, minimal_restart_info, mri_location=mypy.TMP_LOCATION,
                  full_bar_history=None, fbh_location=mypy.TMP_LOCATION):
        self._mri = minimal_restart_info
        self._mri_location = mri_location
        self.load_minimal_restart_info(minimal_restart_info, mri_location)
        if full_bar_history:
            self.full_bar_history_filename = full_bar_history
            self.full_bar_history_location = fbh_location
            self.load_full_bar_history(full_bar_history, fbh_location)
        self._hot_start = True
        
    def clean_exit(self):
        print("bar_extra_modes clean exit")
    
    def text_output(self, 
                    finished_bars_file=None, fb_location=mypy.TMP_LOCATION,
                    unfinished_bar_file=None, ub_location=mypy.TMP_LOCATION):
        if finished_bars_file == None and unfinished_bars_file == None:
            raise Exception("Live data mode started without files to export to")
        if finished_bars_file:
            self.finished_bars_filename = os.path.join(fb_location, 
                                                       finished_bars_file)
            if not hasattr(self, "_hot_start"):
                open(self.finished_bars_filename, 'w').close()
        if unfinished_bar_file == True:
            unfinished_bar_file = '.'.join([finished_bars_file, "unfinished"])
            ub_location = fb_location
        if unfinished_bar_file:
            self.unfinished_bar_file = os.path.join(ub_location,
                                                    unfinished_bar_file)
            
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
            
    def set_last_expected_quote(self, last_quote_time):
        self.last_expected_quote = last_quote_time
        
    def time_until_next_bar(self, curr_time):
        basic_end_time = (self.curr_bar().time + timedelta(
                                       seconds=self.number_of_units)).time()
        if (hasattr(self, "last_expected_quote") and
            self.last_expected_quote < basic_end_time):
            basic_end_time = self.last_expected_quote
        return mypy.time_diff(basic_end_time, curr_time)
        
class reducer():
    INITIALISEER = 'initialiseer'
    BEAR         = 'bear'
    BULL         = 'bull'
    IN_DOUBT     = '?'
    def find_last_max(self):
        answer = reduced_Bar(self.bars[-1].time,
                             self.bars[-1].time,
                             TOP,
                             self.bars[-1].high)
        count = 2
        while 1:
            if count > len(self.bar_qualification):
                return answer
            elif self.bar_qualification[-count] == reducer.BEAR:
                break
            #if ((self.bar_qualification[-count] == reducer.BULL) or
            #    (self.bar_qualification[-count] == reducer.IN_DOUBT)):
            else:
                #
                if self.bars[-count].high > answer.value:
                    answer = reduced_Bar(self.bars[-1].time,
                                         self.bars[-count].time,
                                         TOP,
                                         self.bars[-count].high)
            count += 1
        if len(self.reduced_graph):
            while self.reduced_graph[-1].time <= self.bars[-count].time:
                if self.bars[-count].high > answer.value:
                    answer = reduced_Bar(self.bars[-1].time,
                                         self.bars[-count].time,
                                         TOP,
                                         self.bars[-count].high)
                count += 1
        return answer



    def find_last_min(self):
        answer = reduced_Bar(self.bars[-1].time,
                             self.bars[-1].time,
                             BOTTOM,
                             self.bars[-1].low)
        count = 2
        while 1:
            if count > len(self.bar_qualification):
                return answer
            elif self.bar_qualification[-count] == reducer.BULL:
                break
            #if ((self.bar_qualification[-count] == reducer.BEAR) or
            #    (self.bar_qualification[-count] == reducer.IN_DOUBT)):
            else:
                if self.bars[-count].low < answer.value:
                    answer = reduced_Bar(self.bars[-1].time,
                                         self.bars[-count].time,
                                         BOTTOM,
                                         self.bars[-count].low)
            count += 1
        if len(self.reduced_graph):
            while self.reduced_graph[-1].time <= self.bars[-count].time:
                if self.bars[-count].low < answer.value:
                    answer = reduced_Bar(self.bars[-1].time,
                                         self.bars[-count].time,
                                         BOTTOM,
                                         self.bars[-count].low)
                count += 1
        return answer

    def __init__(self):
        self.bars              = []
        self.bar_qualification = []
        self.reduced_graph     = []
        self.initialiseer      = True

    def insert(self, bar):
        self.bars.append(bar)
        if self.initialiseer:
            self.status = reducer.INITIALISEER
            if len(self.bars) < 3:
                pass
            elif self.bars[-1].high > self.bars[-2].high > self.bars[-3].high:
                self.status = reducer.BULL
                self.initialiseer = False
            elif self.bars[-1].low < self.bars[-2].low < self.bars[-3].low:
                self.status = reducer.BEAR
                self.initialiseer = False
        else:
            if (self.status == reducer.BULL):
                if self.bars[-1].high < self.bars[-3].low:
                    self.status = reducer.BEAR                    
                elif self.bars[-1].high < self.bars[-2].high:
                    self.status = reducer.IN_DOUBT
                else:
                    self.status = reducer.BULL
            elif (self.status == reducer.BEAR):
                if self.bars[-1].low > self.bars[-3].high:
                    self.status = reducer.BULL
                elif self.bars[-1].low > self.bars[-2].low:
                    self.status = reducer.IN_DOUBT
                else:
                    self.status = reducer.BEAR
            elif (self.status == reducer.IN_DOUBT and self.bar_qualification[-2] == self.BULL):
                if self.bars[-1].high <= self.bars[-2].high:
                    self.status = reducer.BEAR
                else:
                    self.status = reducer.BULL
            elif (self.status == reducer.IN_DOUBT and self.bar_qualification[-2] == self.BEAR):
                if self.bars[-1].low >= self.bars[-2].low:
                    self.status = reducer.BULL
                else:
                    self.status = reducer.BEAR

        curr_red_bar = False
        if len(self.bar_qualification) >= 2:
            a = self.bar_qualification[-1]
            b = self.bar_qualification[-2]
            if a != b and a != reducer.IN_DOUBT:
                if b == reducer.BULL:
                    curr_red_bar = self.find_last_max()
                elif b == reducer.BEAR:
                    curr_red_bar = self.find_last_min()
        if len(self.bar_qualification) >= 3:
            c = self.bar_qualification[-3]
            if b == reducer.IN_DOUBT:
                if c == reducer.BULL and a == reducer.BEAR:
                    curr_red_bar = self.find_last_max()
                if c == reducer.BEAR and a == reducer.BULL:
                    curr_red_bar = self.find_last_min()
        if curr_red_bar:
            if ((len(self.reduced_graph)) and 
                 (curr_red_bar.time <= self.reduced_graph[-1].time)):
                self.reduced_graph = self.reduced_graph[:-1]
                curr_red_bar = False
            else:
                self.reduced_graph.append(curr_red_bar)

        self.bar_qualification.append(self.status)
        # print(self.bar_qualification[-3:]) deze print was voor testing
        #return(self.status)
        return curr_red_bar

    def last_extreme(self):
        '''Returns the last max or min'''
        return self.reduced_graph[-1]
    
    
