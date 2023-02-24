#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

'''Check data soundness and create a data info files.

 
'''

import os.path
import datetime

from functools import wraps
from collections import namedtuple

import mypy
import validate
from roc_input import get_bool, get_time
from roc_output import print_list

class Error(Exception):
    """Base class for data_checker exceptions."""
    pass

class FunctionCallError(Error):
    """Exception raised when function is called with 'wrong' parameters.
    
    Not for the obvious errors like type errors, missing parameters, ...
    but to allert when the parameters make a wrong request.
    
    Attributes:
      err_code -- 
      parameter_dict -- dictionary with all the parameters
      message -- explanation of the problem
    """
    
    def __init__(self, err_code, parameter_dict, message):
        self.err_code = err_code
        self.parameters = parameter_dict
        self.message = message
    
    def __str__(self):
        return self.message
    
class MethodNotAllowedError(Error):
    """Exception raised when method call is not allowed.
    
    An explenation is returned.
    """
    pass



class DailyDataInfo():
    '''General day data info.
    
    The info file has a ddi (daily data info) extension by default, it's
    a pickle with three objects.
    1. the name of the base file
    2. update info, a list with following info
        1. a list with known start hours,
           the first element is the current standard time
        2. a list with known end hours, 
           the first element is the current standard time
        3. a list of registered events
    3. a dictionary with the dates as keys
        and a tuple with following values as value
        1. SRTH (start of regular trading hours)
        2. ERTH (end of regular trading hours)
        3. first tick
        4. last tick
        5. list of gaps
        6. list of events    
    '''
    
    MODE_NEW = 0
    MODE_UPDATE = 1
    MODE_CLIENT = 2
    
    ERR_NEW_MODE_WITH_EXISTING_FILENAME = 0
    ERR_UNKNOWN_INFO_FILE = 1
    ERR_UNKNOWN_MODE = 2
    ERR_OVERLAPPING_TRADE_ZONE = 3
    
    def __init__(self, filename, mode, file_check=True):
        """Initialise DailyDataInfo instance.
        
        The session_info attribute is a dictionary that is not saved.
        You can use it to store info related to the ddi to pass along
        in your program.
        
        Parameters:
          filename -- str with the name of the analysis file
          mode -- DailyDataInfo constant that starts with MODE_xxx
          file_check -- in NEW-mode don't check if file exist when False
        """
        
        self._validate_init_parameters(filename, mode, file_check)
        ###
        ###
        self.filename = filename
        self.mode = mode
        if self.mode in {DailyDataInfo.MODE_UPDATE, DailyDataInfo.MODE_CLIENT}:
            self._load(self.filename)
        else:
            self.basefile = []
            self.rth_start_times = []
            self.rth_end_times = []
            self.ath_start_times = []
            self.ath_end_times = []
            self.known_events = []
            self.analysis_parameters = dict()
            self.data_info = dict()
        self.session_info = dict()
        
    def dump(self, verbose='all'):
        ###
        print('basefile: ', self.basefile)
        print('start times: ',self.rth_start_times)
        print('end times: ',self.rth_end_times)
        print('ath start: ',self.ath_start_times)
        print('ath end: ',self.ath_end_times)
        print('events: ', self.known_events)
        print('parameters :', self.analysis_parameters)
        print('data info: ', len(self.data_info))
        if hasattr(self, 'date_info'):
            print('date info: ', self.date_info)
        print('sessino_info: ', self.session_info)
            
    
    def changes_allowed(f):
        """Decorator to check if changes to the data are allowed."""
        
        @wraps(f)
        def wrapper(self, *args, **kwds):
            if not self.mode in {DailyDataInfo.MODE_NEW, 
                                 DailyDataInfo.MODE_UPDATE}:
                tr = {DailyDataInfo.MODE_CLIENT: 'client'}
                mss = 'DailyDataInfo, {} mode does not allow changes'
                mss = mss.format(tr[self.mode])
                raise MethodNotAllowedError(mss)
            return f(self, *args, **kwds)
        return wrapper
    
    def no_unstored_info(f):
        """Decorator to check if theres no unstored info."""
        
        @wraps(f)
        def wrapper(self, *args, **kwds):
            if (hasattr(self, 'date_info') and
                not self.date_info == None):
                mss = "DailyDataInfo, unstored data present."
                raise MethodNotAllowedError(mss)
            return f(self, *args, **kwds)
        return wrapper
    
    def inserting_data_allowed(f):
        """Decorator to check if data can be inserted."""
        
        @wraps(f)
        def wrapper(self, *args, **kwds):
            if (not hasattr(self, 'date_info')
                or
                self.date_info == None):
                mss = "DailyDataInfo, not ready for inserting data."
                raise MethodNotAllowedError(mss)
            return f(self, *args, **kwds)
        return wrapper
    
    @changes_allowed
    def new_valid_time(self, start_or_end, rth_or_ath, time_, standard=False):
        """Add a valid start/end time to the rth/ath list.
        
        The first element in the list is the standard start time, so when
        there is only one element it's the standard.
        
        Parameters:
          start_or_end -- 'start' or 'end'
          rth_or_ath -- 'rth' or 'ath'
          time_ -- a datetime.time object
          standard -- bool
        """
        
        validate.as_time(time_, 'time_: {}')
        validate.as_bool(standard, 'standard: {}')
        validate.as_member(start_or_end, {'start', 'end'}, 'start_or_end: {}')
        validate.as_member(rth_or_ath, {'rth', 'ath'}, 'rth_or_ath: {}')
        ###
        sel = {'start': {'rth': self.rth_start_times,
                         'ath': self.ath_start_times},
               'end': {'rth': self.rth_end_times,
                       'ath': self.ath_end_times}}
        time_list = sel[start_or_end][rth_or_ath]
        ###
        if not time_ in time_list:
            time_list.append(time_)
        if standard:
            time_list.remove(time_)
            time_list.insert(0, time_)
    
    @changes_allowed
    def new_event(self, event):
        """Add an event to the event list
        
        Parameters:
          event -- an event, no restrictions
        """
        
        ###
        ###
        if not event in self.events:
            self.events.append(event)
            
    
    @changes_allowed
    @no_unstored_info
    def add_new_date(self, date_):
        """Prepare instance to accept data for a new date.
        
        Make sure the date isn't already in the info dict and that
        all previous changes are stored in the dict.
        
        Parameters:
          date_ -- a datetime.date
        """
        
        validate.as_date(date_, 'date_: {}')
        if date_ in self.data_info:
            raise Error('Date already in db, use update')
        ###
        ###
        self.date_info = {'date': date_,
                          'rth': [],
                          'ath': [],
                          'first_data': [],
                          'last_data': [], 
                          'first_rth_data': [],
                          'last_rth_data': [],
                          'gaps': [],
                          'events': []}
        
    @changes_allowed
    @no_unstored_info
    def update(self, date_):
        """Load info for date_ and make accessible for changes.
        
        Make sure the date exist.
        
        Parameters:
          date_ -- a datetime.date
        """    
        
        validate.as_date(date_, 'date_: {}')
        ###
        update_info = self.data_info[date_]
        ###
        self.date_info = update_info 
    
    def store(self, to_file=False):
        """Store the new data in the dict."""
        
        ###
        date_data_available = hasattr(self, 'date_info')
        if date_data_available:
            i = self.date_info
            date = i['date']
        ###
        if date_data_available:
            self.data_info[date] = self.date_info 
            del(self.date_info)
        if to_file:
            self._save_data_info()
        
    @inserting_data_allowed
    def trading_hours(self, rth_or_ath, start, first, last, end):
        """Set regular/all trading hours for active date.
        
        Make sure start and end are in the respective rth/ath time lists.
        first and last are the first and last bars in the zone.
        
        Parameters:
          start -- a datetime.time
          end -- a datime.time 
        """
        
        assert start <= first <= last <= end, (
            'times are out of order {}, {}, {}, {}'.format(
              start, first, last, end))
        validate.as_time(start, 'start: {}')
        validate.as_time(end, 'end: {}')
        validate.as_time(first, 'first: {}')
        validate.as_time(last, 'last: {}')
        validate.as_member(rth_or_ath, {'rth', 'ath'}, 'rth_or_ath: {}')
        if rth_or_ath == 'rth':
            validate.as_member(start, self.rth_start_times, 'start: {}')
            validate.as_member(end, self.rth_end_times, 'end: {}')
        else:
            validate.as_member(start, self.ath_start_times, 'start: {}')
            validate.as_member(end, self.ath_end_times, 'end: {}')
        for start_, end_ in self.date_info[rth_or_ath]:
            if ((start_ <= start < end_) or (start_ < end <= end_) or
                (start <= start_ < end) or (start < end_ <= end)):
                raise Error('Overlapping trading zones')           
        ###
        first_tr = {'ath': 'first_data', 'rth': 'first_rth_data'}
        last_tr = {'ath': 'last_data', 'rth': 'last_rth_data'}
        trading_zone = (start, end)
        ###
        self.date_info[rth_or_ath].append(trading_zone)
        self.date_info[first_tr[rth_or_ath]].append(first)
        self.date_info[last_tr[rth_or_ath]].append(last)

    @inserting_data_allowed
    def time_of(self, special_data_bar, time_):
        """Set the time for the specified special bar.
        
        Parameters:
          special_data_bar -- 'first_data', 'last_data', 
                              'first_rth_data', 'last_rth_data'
          time_ -- a datetime.time
        """
        
        validate.as_time(time_)
        validate.as_member(special_data_bar,
                           {'first_data', 'last_data',
                            'first_rth_data', 'last_rth_data'})
        ###
        ###
        self.date_info[special_data_bar] = time_
        
    @inserting_data_allowed
    def add_gap(self, start, end):
        """Add gap for active date.
        
        Parameters:
          start -- a datetime.time
          end -- a datime.time 
        """

        validate.as_time(start, 'start: {}')
        validate.as_time(end, 'end: {}')
        for start_, end_ in self.date_info['gaps']:
            if ((start_ <= start < end_) or (start_ < end <= end_) or
                (start <= start_ < end) or (start < end_ <= end)):
                raise Error('Overlapping gap zones')                
        ###
        gap_zone = (start, end)
        ###
        self.date_info['gaps'].append(gap_zone)
        
    def add_event(self, *args, **kwds):
        """Not yet defined
        
        api also not defined
        """
        raise NotImplementedError()
    
    @inserting_data_allowed 
    def curr_date(self):
        ###
        curr_date = self.date_info['date']
        ###
        return curr_date
    
    @property
    def standard_ath_start(self):
        ###
        if self.ath_start_times:
            standard_ath_start = self.ath_start_times[0]
        else:
            None
        ###
        return standard_ath_start
    
    @property
    def standard_ath_end(self):
        ###
        if self.ath_end_times:
            standard_ath_end = self.ath_end_times[0]
        else:
            None
        ###
        return standard_ath_end    
    
    def set_up_start_end_times(self):
        '''Initialise the known rth and ath start and end times.
        
        You can only use this setuptool if non of them are already set.        
        '''
        
        assert (not self.rth_start_times and not self.rth_end_times and
                not self.ath_start_times and not self.ath_end_times), (
                'Don\'t use setup tool when values are already inserted.')
        ###
        ###
        print('Insert RTH start times, the first value you enter is the'
              'standard value.  \'enter\' to stop adding times.')
        for t in ('start', 'end'):
            standard_set = False
            while True:
                time = get_time('{} time (hh:mm:ss)'.format(t), 
                                '%H:%M:%S', empty=standard_set,
                                el_message='a standard value must be set',
                                err_message='invalid time')
                if not time: break
                self.new_valid_time(t, 'rth', time)
                standard_set = True
        if get_bool('data outside RTH {}? ', default=False):  
            for t in ('start', 'end'):
                standard_set = False
                while True:
                    time = get_time('{} time (hh:mm:ss)'.format(t), 
                                    '%H:%M:%S',empty=standard_set,
                                    el_message=' a standard value must be set',
                                    err_message='invalid time')
                    if not time: break
                    self.new_valid_time(t, 'ath', time)
                    standard_set = True
        else:
            self.ath_end_times = self.rth_end_times
            self.ath_start_times = self.rth_start_times
        
    #def set_up_
                
    def _save_data_info(self):
        """Store data info in file."""
        
        ###
        info_ = (self.basefile, 
                self.rth_start_times, self.rth_end_times, 
                self.ath_start_times, self.ath_end_times,
                self.known_events, self.analysis_parameters,
                self.data_info)
        ###
        mypy.export_pickle(info_, self.filename, id_='data info')
            
    def _load(self, filename):
        """Load a saved info file.
        
        Parameters:
          filename -- The full path to the file          
        """
        ###
        ###
        (self.basefile, 
         self.rth_start_times, self.rth_end_times, 
         self.ath_start_times, self.ath_end_times,
         self.known_events, self.analysis_parameters,
         self.data_info) = mypy.import_pickle(filename, id_='data info')
        
            
    def _validate_init_parameters(self,filename, mode, file_check):
        """Validate the parameters of the __init__ function.
        
        Parameters:
          filename, mode -- from calling function
        """
        
        ###
        function_call_parameters = locals()
        ###
        if mode == DailyDataInfo.MODE_NEW:
            if file_check and os.path.exists(filename):
                mss = 'New mode but file {} already exists, dubious situation'
                mss.format(filename)
                raise FunctionCallError(
                        DailyDataInfo.ERR_NEW_MODE_WITH_EXISTING_FILENAME, 
                        function_call_parameters, mss)
        elif mode in {DailyDataInfo.MODE_UPDATE, DailyDataInfo.MODE_CLIENT}:
            if not os.path.exists(filename):
                mss = "File {} doesn't exist.".format(filename)
                raise FunctionCallError(
                        DailyDataInfo.ERR_UNKNOWN_INFO_FILE, 
                        function_call_parameters, mss)
        else:
            mss = "mode {} unknown".format(mode)
            raise FunctionCallError(
                    DailyDataInfo.ERR_UNKNOWN_MODE, function_call_parameters, 
                    mss)


