#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)


"""
This is "mypy" module

This module provides my own set of variables, functions and classes
"""

import sys
import urllib
import csv
import sqlite3
import tempfile
import os
import pickle
from math import *
from time import mktime, sleep
from datetime import datetime, date, time, timedelta
from collections import namedtuple, deque, defaultdict
from subprocess import Popen
from operator import itemgetter, attrgetter
from functools import wraps

###
# mypy exceptions
class InvalidParameter(Exception): pass

###
# Some global definitions
ABCCorrection = namedtuple('ABCCorrection',
                           'id a a_time b b_time c c_time '
                           'max max_time min min_time')

# Get OS
BASE_OS = os.uname()[0]

# Read settings from .roce directory
settings_path  = os.path.join(os.getenv('HOME'), '.roce')
with open(os.path.join(settings_path, 'mydir')) as ipf:
    mydir = ipf.readline()

# Set standard values
DB_LOCATION = os.path.join(mydir, 'Data/db/')
TMP_LOCATION = os.path.join(mydir, 'tmp/')
VAR_LOCATION = os.path.join(mydir, 'var/')
LOG_LOCATION = os.path.join(mydir, 'log')
SOUND_LIB = os.path.join(mydir, 'settings', 'sounds')
octavelocation = os.path.join(mydir, 'bin/octave/')
DATE_STR = '%Y/%m/%d'
DATE_STR_iso = '%Y-%m-%d'
stdDateStr = DATE_STR
TIME_STR = '%H:%M:%S'
stdTimeStr = TIME_STR
ISO8601TIMESTR = '%Y%m%d %H:%M:%S %Z'
iso8601TimeStr = '%Y-%m-%d %H:%M:%S'
DATE_TIME_STR = ' '.join((DATE_STR, TIME_STR))
stdDateTimeStr = DATE_TIME_STR
octaveDateStr  = '%Y%m%d'

KNOWN_DATE_TIME_FORMATS = [DATE_STR, TIME_STR, ISO8601TIMESTR, iso8601TimeStr,
                           DATE_TIME_STR]

# System tuples
Advice       = namedtuple('Advice', 'time action item reason')
TimeAndValue = namedtuple('TimeAndValue', 'time value')
ABCCorrection = namedtuple('ABCCorrection',
                           'id a a_time b b_time c c_time '
                           'max max_time min min_time')
CodeAndMessage = namedtuple('CodeAndMessage', 'code, message')

class ColumnName:
    def __init__(self, provider='Yahoo'):
        if provider == 'Yahoo':
            self.date=0
            self.open=1
            self.high=2
            self.low=3
            self.close=4
            self.volume=5
            self.adjclose=6
        elif provider == 'Intraday_db':
            self.date='date'
            self.time='time'
            self.symbol='symbol'
            self.volume='volume'
            self.price='price'
        elif provider == 'IBdata':
            self.time=3
            self.open=4
            self.high=5
            self.low=6
            self.close=7
            self.volume=8
            self.wap=9
            self.count=10
        elif provider == 'IB_db':
            self.datetime='datetime'
            self.date='date(datetime)'
            self.time='time(datetime)'
            self.open='open'
            self.high='high'
            self.low='low'
            self.close='close'
            self.volume='volume'
            self.wap='wap'
            self.hasgaps='hasgaps'
            self.counts='counts'
        else:
            print('Oops in class Comumnname')



def url2str(url, code='utf8'):
    """
    Read a url, decode as 'code', return string
    """
    urlp=urllib.request.urlopen(url)
    byteread=urlp.read()
    urlp.close()
    return byteread.decode(code)

def octaveDate(date):
    """
    Returns octave date string from std date string
    """
    myDate=datetime.strptime(date, DATE_STR)
    return myDate.strftime(octaveDateStr)

def table2csv(table, columns, filename):
    """
    Writes columns(a list) from table to filename
    """
#    spamWriter = csv.writer(open('eggs.csv', 'w'), delimiter=' ',
#                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
#    spamWriter.writerow(['Spam'] * 5 + ['Baked Beans'])
#    spamWriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])
    csvh=csv.writer(open(filename, 'w'), dialect='excel')
    for line in table:
        csvh.writerow([line[col] for col in columns])

###
# Input
###

class SelectionMenu():
    
    def __init__(self, menu_items=None, interface='TXT_LINE', message=None,
                 auto_number=False, auto_return_value=True):
        self.menu_items = []
        for menu_item in self.menu_items:
            self.add_menu_item(*menu_item)
        self.interface = interface
        self.message = message
        assert isinstance(auto_number, bool), 'auto_number must be bool'
        self.auto_number = auto_number
        self.auto_return_value = auto_return_value
        self.text_separator = '  |  '
        
    @property
    def interface(self):
        return self.__interface
    
    @interface.setter
    def interface(self, interface):
        txt_table_choice = self._txt_table_choice
        if interface == 'TXT_LINE':
            self.__interface = txt_table_choice            
            self.items_per_row = 0
        elif interface == 'TXT_ROW':
            self.__interface = txt_table_choice
            self.items_per_row = 1
    @property
    def auto_return_value(self):
        '''returns True, False or 'NR' '''
        return self.__auto_return_value
    
    @auto_return_value.setter
    def auto_return_value(self, value):
        if value in {True, False}:
            self.__auto_return_value = value
        elif value == 'NR':
            self.__auto_return_value = value
        else:
            mess = 'auto_return_value must be True, False or \'NR\''
            raise InvalidParameter(mess)
    @property
    def existing_text_values(self):
        return [x[0] for x in self.menu_items]
    @property
    def existing_selector_values(self):
        return [x[1] for x in self.menu_items]
        
    def add_menu_item(self, text, selector=None, return_value=None):
        auto_number = self.auto_number
        auto_return_value = self.auto_return_value
        menu_items = self.menu_items
        existing_text_values = self.existing_text_values
        existing_selector_values = self.existing_selector_values
        if selector == None:
            if auto_number:
                selector = str(len(menu_items))
            else:
                selector = str(text)
        else:
            mess = 'auto_number is on, you can\'t choose a selector'
            assert auto_number == False, mess
            mess = 'selector must be string or int'
            assert isinstance(selector, (int, str)), mess
            selector = str(selector)                            
        if return_value == None:
            mess = 'auto_return_value is False, return value expected'
            assert not auto_return_value == False, mess
            if auto_return_value == True:
                return_value = text
            else:
                return_value = len(menu_items)
        if existing_text_values and text in existing_text_values:
            mess = 'text value already in menu'
            raise InvalidParameter(mess)
        if existing_selector_values and selector in existing_selector_values:
            mess = 'selector {} already used for menu'.format(selector)
            raise InvalidParameter(mess)
        menu_items.append((str(text), selector, return_value))
        
    def get_users_choice(self):
        return self.interface()
        
    def _txt_table_choice(self):
        #make text menu
        menu_items = self.menu_items
        items_per_row  = self.items_per_row
        separator = self.text_separator
        message = self.message
        existing_text_values = self.existing_text_values
        existing_selector_values = self.existing_selector_values
        text_menu = []
        for item_nr, menu_item in enumerate(menu_items):
            text = menu_item[0]
            selector = menu_item[1]
            return_value = menu_item[2]
            if not selector == text:
                selector_text = '({}) '.format(selector)
            else:
                selector_text = ''
            if item_nr == len(menu_items) - 1:
                end = ''
            elif items_per_row > 0 and (item_nr + 1) % items_per_row == 0 :
                end = '\n'
            else:
                end = separator
            text_menu.append(''.join([selector_text, text, end]))
        text_menu = ''.join(text_menu)
        if message == None:
            message = 'Choice: '
        while True:
            print(text_menu)
            print()
            answer = get_string(message)
            if answer in existing_selector_values:
                answer = menu_items[existing_selector_values.index(answer)][2]
                return answer
            print('Invalid choice')
            print()
            
    
def get_int(msg, 
            minimum = None,
            maximum = None,
            default = None,
            empty = False):
    if minimum and maximum and minimum > maximum:
        raise
    while True:
        try:
            line = input(msg)
            if not line and default is not None:
                return default
            if not line and empty:
                return None
            f = int(line)
            if minimum and (f < minimum):
                print('number must be >=', minimum)
            elif maximum and (f > maximum):
                print('number must be <=', maximum)
            else:
                return f
        except ValueError as err:
            print(err)

def get_float(msg, 
              minimum = sys.float_info.min,
              maximum = sys.float_info.max,
              default=None,
              empty = False):
    if minimum > maximum:
        raise
    while True:
        try:
            line = input(msg)
            if not line and default is not None:
                return default
            if not line and empty:
                return None
            f = float(line)
            if (f < minimum):
                print('number must be >=', minimum)
            elif (f > maximum):
                print('number must be <=', maximum)
            else:
                return f
        except ValueError as err:
            print(err)

def get_string(msg,
               max_length = None,
               default = None,
               empty = False):
    while True:
        line = input(msg)
        if line:
            if not max_length or len(line) <= max_length:
                return line
            else:
                continue
        if default is not None:
            return default
        if empty:
            return ''
        print('no empty sting allowed!')

def get_bool(msg,
             default = None):
    while True:
        line = input(msg)
        if line == '' and not default is None:
            return default
        if line in ['N', 'No', 'NO', 'n', 'nee']:
            return False
        if line in ['Y', 'Yes', 'YES', 'y', 'j', 'ja']:
            return True
        print('Y or N? ')
        

def get_date(text, empty=False, format_=None, default=None):
    '''Read a date/time/datetime from stdin, check the format for
    known or given format and return datetime, now will return the
    current time'''
    formats = [format_] if format_ else KNOWN_DATE_TIME_FORMATS
    while 1:
        a_datetime = input(text)
        if a_datetime == '' and default:
            a_datetime = datetime.strptime(default, format_)
        elif a_datetime == '' and empty:
            a_datetime = None
        elif a_datetime == 'now':
            a_datetime = now()
        else:
            for test_format in formats:
                try:
                    t = datetime.strptime(a_datetime, test_format)
                    a_datetime = t
                    break
                except ValueError as err:
                    pass
            else:
                print('unknown format use \'now\' for current time')
                continue
        break        
    return a_datetime

def get_from_list(choices, mess='choose from: ', empty=False):
    '''Presents a list with numbers and return the chosen value'''
    if isinstance(choices, set):
        choices = list(choices)
    print(mess)
    for number, choice in enumerate(choices):
        print('{:2}__{}'.format(number, choice))
    print()
    choice = get_int('choice: ', minimum=0, maximum=len(choices)-1, 
                     empty=empty)
    return choices[choice] if not choice == None else choice
        
def get_line_from_file(ifh, wait=1):
    '''read a line from a file, if no line is available,
    try again after wait seconds'''
    while True:
        line = ifh.readline()
        if not line:
            sleep(wait)
            continue
        break
    return line

            

###
# Output
###

class SerialLineCreator(list):
    
    def __init__(self, separator=' '):
        self.separator = separator
        self.curr_chunk = []
    
    def add_text(self, data):
        assert isinstance(data, str), 'add_text data must be a str value'
        self.curr_chunk.append(data)
        
    def add_chunk(self, data):
        assert isinstance(data, str), 'add_chunk data must be a str value'
        if not len(self.curr_chunk) == 0:
            chunk = ''.join(self.curr_chunk)
            self.curr_chunk = []
            self.add_chunk(chunk)
        self.append(data)
        
    @property
    def is_empty(self):
        return len(self) + len(self.curr_chunk) == 0
    
    @property
    def clear(self):
        while True:
            try:
                self.pop()
            except IndexError:
                break
        self.curr_chunk = []
    
    @property   
    def text(self):        
        output_items = self[:] if len(self) > 0 else []
        if not len(self.curr_chunk) == 0:
            output_items.append(''.join(self.curr_chunk))
        return self.separator.join(output_items)

class SerialTextCreator(list):
    
    def __init__(self, separator=' ', eol='\n', eof=True):
        self.curr_line = SerialLineCreator(separator)
        self.eol = eol
        self.eof = eof
        
    def add_text(self, data):
        self.curr_line.add_text(data)
        
    def add_chunk(self, data):
        self.curr_line.add_chunk(data)

    def add_line(self, line):
        if not self.curr_line.is_empty:
            self.append(self.curr_line.text)
            self.curr_line.clear
        self.append(line)
    
    def next_line(self):
        self.append(self.curr_line.text)
        self.curr_line.clear
    
    def underline(self, symbol='-'):
        length_curr_line = len(self.curr_line.text)
        if length_curr_line == 0:
            length_curr_line = len(self[-1])
        else:
            self.next_line()
        self.append(length_curr_line * symbol)
    
    @property
    def text(self):
        output_items = self[:] if len(self) > 0 else []
        if not self.curr_line.is_empty:
            output_items.append(self.curr_line.text)
        if self.eof:
            output_items.append('')
        return self.eol.join(output_items)
        

def beep(sound, volume=10):

    cliLine = 'paplay --volume {} '.format(int(65536 * 10 / volume)) + sound
    Popen(cliLine, shell=True)
    #Popen('paplay --volume 50000 ../Sources/buy.wav', shell=True)


def play_sound(sound):

    command_line = dict(Linux = 'paplay --volume 65000 {}',
                        Darwin = 'afplay {}')
    Popen(command_line[BASE_OS].format(sound), shell=True)
    
    
def c_print(*content, file_=None):
    '''conditional printing, uses the standard print if 
    output_file is one else puts the file=of argument in the function'''
    if file_:
        print(*content, file=file_)
    else:
        print(*content)
        


def print_list(list_, name=None, file_=None):
    '''Prints a list in a nicer format, if file is None if prints to
    standard output'''
    if name:
        c_print(name, file_=file_)
        c_print('-'*len(name), file_=file_)
        c_print(file_=file_)

    for item in list_:
        c_print(item, file_=file_)
    c_print(file_=file_)


def print_dict(dict_, name=None, file_=None):
    '''Prints a dictionary in a nicer format, if file is None if prints to
    standard output'''
    if name:
        c_print(name, file_=file_)
        c_print('-'*len(name), file_=file_)
        c_print(file_=file_)
    for k, v in dict_.items():
        c_print(k, '|', v, file_=file_)
    c_print(file_=file_)

###
# lists
###

def data_with_common_field_value(*iterable, field, function=None):
    '''returns a tuple with a value of every list where field has the same value
    
    the iterables will be changed'''
    if not function:
        if isinstance(iterable[0], list):
            read_item = lambda l: l.pop(0)
    else:
        read_item = function
    if isinstance(field, int):
        common_field = itemgetter(field)
    else:
        common_field = attrgetter(field)
    nr_of_iterables = len(iterable)
    iterables_nrs = deque(range(nr_of_iterables))
    v = list()
    for i_nr in iterables_nrs:
        if not len(iterable[i_nr]):
            return None
    for i_nr in iterables_nrs:
        v.append(read_item(iterable[i_nr]))
        #print(v[i_nr])
    while True:
        iter_1_nr = iterables_nrs[0]
        iter_2_nr = iterables_nrs[1]
        f1 = common_field(v[iter_1_nr])
        f2 = common_field(v[iter_2_nr])
        if f1 < f2:
            if len(iterable[iter_1_nr]) == 0:
                break
            v[iter_1_nr] = read_item(iterable[iter_1_nr])
        elif f1 > f2:
            if len(iterable[iter_2_nr]) == 0:
                break
            v[iter_2_nr] = read_item(iterable[iter_2_nr])
        else:
            test_value = common_field(v[0])
            for item in v:
                if not common_field(item) == test_value:
                    break
            else:
                return v
        iterables_nrs.rotate(-1)
    for i_nr in iterables_nrs:
        iterable[i_nr].append(v[i_nr])    
    return None

def count_in_list(test, alist):
    count = 0
    for x in alist:
        if test(x):
            count += 1
    return count

###
# Statistical
###

def mean(numbers):
    return fsum(numbers)/len(numbers)

def harmonic_mean(numbers):
    return fsum([1/x for x in numbers]) ** -1 * len(numbers)

def sumQuad(numbers):
    return fsum(ell**2 for ell in numbers)

def quadSum(numbers):
    return fsum(numbers)**2

def sumProd(numbers1, numbers2):
    return fsum([numbers1[i]*numbers2[i] for i in range(0,len(numbers1))])

def s_x_x(numbers):
    return sumQuad(numbers)-quadSum(numbers)/len(numbers)

def s_x_y(numbers1, numbers2):
    sum_prod = sumProd(numbers1, numbers2)
    return sum_prod-fsum(numbers1)*fsum(numbers2)/len(numbers1)
    
def variance(numbers):
    return s_x_x(numbers)/(len(numbers)-1)

def correlation(numbers1, numbers2):
    return s_x_y(numbers1, numbers2)/sqrt(s_x_x(numbers1)*s_x_x(numbers2))

def correlation_I(numbers2):
    return correlation(range(1,len(numbers2)+1), numbers2)

def lsLine(numbers1, numbers2):
    sxy = s_x_y(numbers1, numbers2)
    sxx = s_x_x(numbers1) or 1.0e-16
    syy = s_x_x(numbers2) or 1.0e-16
    rc = sxy/sxx
    q  = (fsum(numbers2)-rc*fsum(numbers1))/len(numbers1)
    r_sq = sxy**2/(sxx*syy)
    return rc, q, r_sq

def lsLine_I(numbers2):
    return lsLine(range(1,len(numbers2)+1), numbers2)

def sma(alist, lookback):
    return mean(alist[-lookback:])

def normsdist (x, mean=0, standard_dev=1):
    result = 0
    x = (x -mean) / standard_dev
    
    if x == 0:
        res = 0.5
    else:
        pi_con = 1 /(sqrt(2 * pi))
        rr = 1 / (1 + 0.2316419 * abs(x))
        rr = (rr * pi_con * exp(-0.5 * x * x) * 
              (0.31938153 + rr * 
               (-0.356563782 + rr * 
                (1.781477937 + rr * 
                 (-1.821255978 + rr * 1.330274429)))))
        if x >= 0:
            res = 1 - rr
        else:
            res = rr
    return res

def mode(alist, delta=1, round_method='round'):
    '''give the mode of the list
    
    The delta gives the distance between the possible modes,
    the round_method, wich alters the number in the list
    before testing, can be 'round' or 'down'.
    
    '''
    modes_dict = defaultdict(int)
    for ell in alist:
        modes_dict[d_round(ell, delta, round_method)] += 1
    mode = []
    maximum = 0
    for key in modes_dict.keys():
        nr_of_ell = modes_dict[key]
        if nr_of_ell > maximum:
            mode = [key]
            maximum = nr_of_ell
        elif nr_of_ell == maximum:
            mode.append(key)
    mode.sort()
    return mode



###
# Math
###

def d_round(number, r, method='round'): #, t, as_string='False'):
    '''round to nearest multiple of r'''
    round_function = {'round': round,
                      'down': int}
    foo = number / r
    foo = round_function[method](foo)
    foo = foo * r
    return foo

def delta(number1, number2):
    return abs(number1 - number2)

###
# generator
###

def f_range(start, stop, step=None):
    
    def dn(number):
        dec = '{:.15f}'.format(number).rstrip('0').split('.')[1]
        return 10**len(dec)
    
    denominator = max(dn(start), dn(stop))
    if step:
        denominator = max(denominator, dn(step))
    start *= denominator
    stop *= denominator
    if step == None:
        step = 1
    else:
        step *= denominator
    start, stop, step = int(start), int(stop), int(step)
    for t in range(start, stop, step):
        yield t/denominator
        
###
# Time
###
   
def py_time(a_time, time_format=TIME_STR):
    '''Geeft datetime object voor string a_time volgens format'''
    #return datetime.strptime(a_time, time_format).time()
    return datetime.strptime(a_time, time_format).time()

def py_date_time(a_date_time, date_time_format=DATE_TIME_STR, days=0):
    '''Geeft datetime object voor string a_date_time volgens format'''
    if date_time_format == TIME_STR:
        d = now().date()+timedelta(days=days)
        t = py_time(a_date_time)
        dt = datetime.combine(d, t)
    else:
        dt = datetime.strptime(a_date_time, date_time_format)
    return dt
def py_date(a_date, date_format=DATE_STR):
    '''Geeft datetime object voor string a_date volgens format'''
    return datetime.strptime(a_date, date_format)
def date_time2epoch(date_time):
    '''Geeft unix time (GMT) voor date_time
    unix time is seconds sinds epoch (1/1/1970)'''
    return int(mktime(date_time.timetuple()))
def epoch2date_time(seconds_from_epoch):
    '''Returns datetime object that represents epoch'''
    return datetime.fromtimestamp(seconds_from_epoch)
def date_time2format(date_time, format):
    '''Geeft date_time terug in format'''
    return date_time.strftime(format)
def time2format(time_, format=TIME_STR):
    '''Geeft time in format'''
    return time_.strftime(format)
datetime2format = date_time2format   # hackje
def py_timedelta(seconds):
    return timedelta(seconds=seconds)
def input_date(text, format=DATE_STR):
    '''Lees een tijd van stdin in in formaat format'''
    while 1:
        time = input(text)
        try:
            datetime.strptime(time, format)
            break
        except ValueError as err:
            print('De data heeft een verkeerd formaat! ', err)
    return time
def now():
    '''returns the datetime object with the current system date and time'''
    return datetime.now()
def timegap_to_year_ratio(date1, date2):
    '''returns a float that represents the timegap in years
    
    uses fixed number of 365 days for the year, mayby some room for
    improvement to take leap years into account'''
    gap = date_time2epoch(date2) - date_time2epoch(date1)
    seconds_per_year = 365 * 24 * 60 * 60
    return gap / seconds_per_year
def seconds_since_start_of_day(datetime_):
    '''Returns the number of seconds passed since 00:00 hours'''
    zero_datetime = datetime.combine(datetime_.date(), time(0))
    return (datetime_ - zero_datetime).seconds
def time_diff(time1, time2):
    '''returns the number of seconds between two times'''
    if time1 < time2:
        time1, time2 = time2, time1
    diff = 0
    diff += (time1.hour - time2.hour) * 3600
    diff += (time1.minute - time2.minute) * 60
    diff += (time1.second - time2.second)
    return diff
    
    

###
# error
###
def raise_not_implemented(raise_, message):
    if raise_:
        raise NotImplementedError(message)
    else:
        print(mess)

###
# for Simulators
###
def qualify_diff(first, second):
    '''returns movement between first and second
    first > second: 'up'
    second > first: 'down'
    second = first: 'eq'
    '''
    qualification = ''
    if first < second:
        qualification = 'up'
    elif first > second:
        qualification = 'down'
    else:
        qualification = 'eq'
    return qualification

def rendement_perc(start, stop, trade):
    if (trade == 'long') or (trade == 'U'):
        rend = ((stop/start)-1)
    elif (trade == 'short') or (trade == 'D'):
        rend = (1-(stop/start))
    return rend

def rendement_BS(advices, quotes, verbose=False):
    '''Berkent het rendement van een strategie die koopt en verkoopt,
    steeds in deze volgorde, anders foutmelding en waarde 1 komt terug'''

    #rend       = 1
    rend       = 0
    buyed      = False
    buy_price  = 0
    sell_price = 1
    for advice in advices:
        if ((buyed and (advice.action == 'buy')) or (not(buyed) and (advice.action == 'sell')) or
            (buyed and (advice.action == 'trade_in')) or (not(buyed) and (advice.action == 'trade_out'))):
            print('De simulator geeft verkeerde signalen!! Check simulator!!')
            return 0
        if advice.action == 'buy':
            buy_price = quotes[advice.time]
            buyed = advice.item
        if advice.action == 'trade_in':
            buy_price = quotes[advice.time]
            buyed = 'long' if advice.item[:3]=='buy' else 'short'
        if advice.action == 'sell' or advice.action == 'trade_out':
            sell_price = quotes[advice.time]
            last_rend = rendement_perc(buy_price, sell_price, buyed)
            if verbose:
                print('Rend: {0:.3p}'.format(last_rend * 100))
            buyed = False
            rend += last_rend
    if buyed:
        print('De simulator heeft een positie gehouden op het einde van de trade!!')
    return rend * 100

###
# pickle
###

def import_pickle(filename, id_ = "std"):
    with open(filename, 'rb') as ifh:
        pickle_id, newObject = pickle.load(ifh)
    if not pickle_id == id_:
        raise Exception("wrong pickle id: {}".format(pickle_id))
    return newObject

def export_pickle(object_, filename, id_="std"):
    with open(filename, 'wb') as ofh:
        pickle.dump((id_, object_), ofh)
    

###
# sqlite3
###

######  DON PLACE SQLITE STUFF HERE         ######
######  PLACE SQLITE STUFF IN mysqlite3.py  ######  

#tableDef_IBHist = ('(datetime text UNIQUE ON CONFLICT IGNORE, open real, high real, low real, '+
#                   'close real, volume integer, wap real, hasgaps integer, counts integer)')

def createDB(location, tableName=None, tableFormat=None):
    mydb=sqlite3.connect(location)
    dbh=mydb.cursor()
    if tableName:
        exstr = 'create table '+tableName+' '+tableFormat
        dbh.execute(exstr)
    mydb.commit()
    dbh.close()
    mydb.close()

###
# temporary files
###

# zou gegeven bestandsnamen moeten onthouden in testen of ze nog in dienst zijn,
# en bij rmTempFile of het wel een tempfile is.
def temp_file_name(directory=TMP_LOCATION):
    fd, filename = tempfile.mkstemp(dir=directory)
    os.close(fd)
    return filename

def rmTempFile(name):
    os.remove(name)
    
