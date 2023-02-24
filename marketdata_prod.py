#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import datetime
import csv
from collections import namedtuple, Iterable
from os.path import join as full_path, exists

import roc_directories as r_dir
import roc_math as r_math
import roc_input as r_input
import roc_output as r_output
import tws
import sql_ib_db
import historicaldata_new as historicaldata
import validate
#from roc_directories import DB_LOCATION, DATA_LOCATION
import tws_realbar_request_gscLib

### STD SETTINGS FOR CONNECTION WITH TWS SERVER
TWS_SERVER_IP = 'localhost'
TWS_SERVER_PORT = 10911
TWS_CLIENT_ID = 60     # test value to stay away from production aps


### STD SETTINGS FOR CONNECTION WITH LIVE BAR SERVER
LIVE_SERVER_IP = 'localhost' # test value to stay away from production server
LIVE_SERVER_PORT = 14701     # test value to stay away from production server

class Error(Exception):
    """Base class for market_data exceptions."""
    pass

class InitTypeError(Error):
    """Exception raised when init parameter has wrong type."""
    pass

class InitValueError(Error):
    """Exception raised when init parameter has invalid value."""
    pass

class DataConflict(Error):
    """Exception raised with conflicting data situation."""
    pass

DATABAR_ELEMENTS = ['time', 'open_', 'high', 'low', 'close',
                    'volume', 'counts', 'vwap', 'twap',
                    'hasgaps', 'duration']

_DataBar = namedtuple('_DataBar', ' '.join(DATABAR_ELEMENTS)) #'time open_ high low close '
                               #   'volume counts vwap twap hasgaps '
                                #  'duration')
class DataBar(_DataBar):
    """An open, high, low, close databar with extra info attributes.
    
    It is assumed that time is the start time of the bar. Volume, counts,
    hasgaps as named.  vwap and twap are the volume and timed weighted 
    average prices.  Size must be a datetime.timedelta object.
    
    Volume, counts, vwap, twap hasgaps and duration can be omitted, all or some of
    them. If so they will default to None. 
    
    To avoid dubious situations, only naive datetime objects are accepted, if 
    not an InitValueError will be raised.  It's the users responsibility to make
    sure he solves forceeable problems (use utc when there's a risc for double
    or missing times when hours include a daylite saving time jump, or an ofset
    f the opening of one of the markets when comparing bars from different 
    timezones).
    
    BiasedInitData will be raised when: 
      - low is bigger then high, 
      - open and|or close are not in the high|low interval
      - volume(*) is 0 and open, high, low and close are no equal
      - volume(*) is 0 and counts is bigger than 0
      - counts(*) is 0 and volume is bigger then 0
      - wap(*) is not inside the high|low interval
      
    (*) if not None
    
    Attributes:
      time -- the start_time of bar without timezone info, datetime.datetime
      open, high, low, close -- all non negative floats
      volume -- number of traded singletons, non negative int or None
      counts -- number of price changes, non negative int or None
      vwap, twap -- weighted average price, non negative float or None
      hasgaps -- missing data, bool or None
      duration -- time duration of the bar, datetime.timedelta or None
      size -- the diff from bar low to bar high
      close_perc -- relative position of close in bar
      
    Methods:
      end_time -- Returns the end time of the DataBar
      __add__ -- Returns the sum of the terms.
      __contains__ -- for value in bar
      __gt__ -- a > b
      __lt__ -- a < b
      duration_aware -- Returns True if DataBar is duration aware.
      joins -- Returns True if end of first bar is begin of the second.
      replace -- Returns a bar with replaced attributes
      is_zero_bar -- Returns True if bar is a zero bar
    """
    
    def __new__(cls, time, open_, high, low, close,
                volume=None, counts=None, vwap=None, twap=None,
                hasgaps=False, duration=None):
        ###
        ###
        return super().__new__(cls,time, open_, high, low, close,
                               volume, counts, vwap, twap,  hasgaps, duration)
    
    def __init__(self, time, open_, high, low, close,
                 volume=None, counts=None, vwap=None, twap=None,
                 hasgaps=None, duration=None):
        """Initialise a databar.
        
        Time, open, high, low, close are the minimum requirements for a
        bar.
        
        Parameters:
          time, open_, high, low, close, volume, counts, vwap, twap, 
          hasgaps, duration -- see class docs
        """
        
        self._validate_init_parameters(time, open_, high, low, close,
                                       volume, counts, vwap, twap,
                                       hasgaps, duration)
        ###
        ###
        super().__init__()
        
    def end_time(self): 
        """Returns the end time of the bar.
        
        If the DataBar is duration naive, a TypeError is raised.
        
        Parameters:
        """
        
        if not self.duration_aware():
            mss = 'not defined for duration naive instances'
            raise TypeError(mss)
        ###
        end_time = self.time + self.duration
        ###
        return end_time
        
    def __add__(self, other):
        """Returns a new DataBar that is the sum of the terms.
        
        Add keeps the time and open of the first bar.  New high is the
        max of both high's and new min the min of the low's.  Volume and
        counts are the sum of both respective values.  You can not add a
        duration aware and duration naive DataBar, a TypeError will be 
        raised.
        
        The time of the other parameter can not be before the time of
        self.  If the parameters are duration aware the time of other
        must be equal to or bigger then the time of first plus the 
        duration of first.  If not a ValueError will be raised.
        
        Volume and counts will be added if available in both bars, if not
        result is set to None.  If duration aware bars, new duration is
        the timedelta between the time of first bar and the end time of
        the second.
        
        If one or both hasgaps attributes is True, the new value is also
        True.  
        If not so:
          both without duration -- hasgaps is False
          both with duration:
            (end first is time of first + duration of first)
            time second is end first -- hasgaps is False 
            time second is bigger then end first -- hasgaps is True
        
        vwap wil be recalculated with volumes if they are available, 
        twap if durations are available.  If adding DataBars without
        volumes, resulting vwap is set to None.  If adding DataBars 
        without duration, resulting twap is set to None. 
        
        Parameters:
          other -- Databar        
        """
        
        if not isinstance(other, DataBar):
            mss = 'unsupported operand type(s) for +: DataBar and {}'
            mss.format(type(other))
            raise TypeError(mss)
        self._validate_add_parameters(self, other)
        ###
        new_bar = self._add_bars(self, other)
        ###
        return new_bar
    
    def __contains__(self, test_value):
        '''returns True if the test value is between high and 
        
        (high and low included) else returns false
        '''
        
        return self.low <= test_value <= self.high
    
    def __gt__(self, other):
        '''return True if high of self is bigger then high of other
        and low of self is bigger then low of other'''
        ###
        greater_then = (
            self.high > other.high and
            self.low > other.low
        )
        ###
        return greater_then
    
    def __lt__(self, other):
        '''return True if high of self is lower then high of other
        and low of self is lower then low of other'''
        ###
        smaller_then = (
            self.low < other.low and
            self.high < other.high
        )
        ###
        return smaller_then
        
    def duration_aware(self):
        """Return True if duration is not None."""
        ###
        ###
        return not self.duration == None
        
    def joins(self, other):
        """Returns True if time of self is the end time of the other.
        
        The end time of self is the time of self plus the duration of self.
        If self or other are duration naive a TypeError will be raised.
        
        Parameters:
          other -- a duration aware DataBar
        """
        
        if not isinstance(other, DataBar):
            mss = '{}'.format(type(other))
            raise TypeError(mss)
        if not (self.duration_aware() and other.duration_aware()):
            mss = 'Only duration aware DataBars can be tested joinable.'
            raise TypeError(mss)
        ###
        ###
        return self.time == other.end_time()
    
    def replace(self, **kwds):
        """Return a new Databar with kwds replaced.
        
        Parameters:
          keywords must be DataBar attributes
        """
        
        for kwd in kwds:
            if not kwd in DATABAR_ELEMENTS:
                mss = '{} is invalid keyword argument'.format(kwd)
                raise Error(mss)
        ###
        new_bar_args = dict()
        for kwd in DATABAR_ELEMENTS:
            new_bar_args[kwd] = kwds.get(kwd, getattr(self, kwd))
        ###
        return DataBar(**new_bar_args)
    
    def is_zero_bar(self):
        """Returns True if bar is a zero bar.
        
        A bar is a zero bar if the duration is timedelta(0), and the
        counts and volume are also 0.
        
        If the bar is not duration aware it will also return False
        """
        ## TEST OK ###
        ###
        if (self.duration_aware() and
            self.duration == datetime.timedelta(0) and
            self.volume == self.counts == 0):
            zero_bar = True
        else:
            zero_bar = False
        ###
        return zero_bar == True
    
    @property
    def size(self):
        '''Returns diff between high and low'''
        return self.high - self.low
    
    @property
    def close_perc(self):
        '''returns relative position of close in the bar'''
        if self.size == 0:
            answer = 100
        else:
            answer = (self.close - self.low) / self.size
        return answer
        
        
    def _validate_init_parameters(self, *args):
        """Validate the parameters of the __init__ function.
        
        Parameters:
          from calling function
        """
        ###
        ###        
        self._validate_types(*args)
        self._validate_values(*args)
        self._check_for_conflicting_values(*args)
        
    def _validate_types(self, *args):
        """Validate the parameter types of the __init__ function.
        
        Parameters:
          from calling function
        """        
        ###
        (time, open_, high, low, close, 
         volume, counts, vwap, twap, hasgaps, duration) = args
        float_or_int = (float, int)
        ###
        if not isinstance(time, datetime.datetime):
            mss = 'time: {}'.format(type(time))
        elif isinstance(open_, bool) or not isinstance(open_, float_or_int):
            mss = 'open @ {}: {}'.format(time, type(open_))
        elif isinstance(high, bool) or not isinstance(high, float_or_int):
            mss = 'high @ {}: {}'.format(time, type(high))
        elif isinstance(low, bool) or not isinstance(low, float_or_int):
            mss = 'low @ {}: {}'.format(time, type(low))
        elif isinstance(close, bool) or not isinstance(close, float_or_int):
            mss = 'close @ {}: {}'.format(time, type(close))
        elif (isinstance(vwap, bool) 
              or 
              not (vwap is None or isinstance(vwap, float_or_int))):
            mss = 'vwap @ {}: {}'.format(time, type(vwap))
        elif (isinstance(twap, bool) 
              or 
              not (twap is None or isinstance(twap, float_or_int))):
            mss = 'twap @ {}: {}'.format(time, type(twap))
        elif (isinstance(counts, bool)
              or
              not (counts is None or isinstance(counts, int))):
            mss = 'counts @ {}: {}'.format(time, type(counts))
        elif (isinstance(volume, bool)
              or
              not (volume is None or isinstance(volume, int))):
            mss = 'volume @ {}: {}'.format(time, type(volume))
        elif not (hasgaps is None or isinstance(hasgaps, bool)):
            mss = 'hasgaps @ {}: {}'.format(time, type(hasgaps))
        elif not (duration is None or isinstance(duration, datetime.timedelta)):
            mss = 'duration @ {}: {}'.format(time, type(duration))
        else:
            return True
        raise InitTypeError(mss)    
    
    def _validate_values(self, *args):
        """Validate the parameter values of the __init__ function.
        
        Parameters:
          from calling function
        """        
        ###
        (time, open_, high, low, close, 
         volume, counts, vwap, twap, hasgaps, duration) = args
        ###
        if not time.tzinfo is None:
            mss = 'time is not naive @ {}'
        elif open_ < 0:
            mss = 'open @ {} negative'
        elif high < 0:
            mss = 'high @ {} negative'
        elif low < 0:
            mss = 'low @ {} negative'
        elif close < 0:
            mss = 'close @ {} negative'
        elif not (vwap is None or vwap >= 0):
            mss = 'vwap @ {} negative'
        elif not (twap is None or twap >= 0):
            mss = 'twap @ {} negative'
        elif not (volume is None or volume >= 0):
            mss = 'volume @ {} negative'
        elif not (counts is None or counts >= 0):
            mss = 'counts @ {} negative'
        else:
            return True
        mss = mss.format(time)
        raise InitValueError(mss)
    
    def _check_for_conflicting_values(self, *args):        
        """Validate the parameter values of the __init__ function.
        
        Parameters:
          from calling function
        """        
        ###
        (time, open_, high, low, close, 
         volume, counts, vwap, twap, hasgaps, duration) = args
        ###
        if low > high: 
            mss = 'low bigger then high @ {}'
        elif not low <= open_ <= high:
            mss = 'open not in high low range @ {}'
        elif not low <= close <= high:
            mss = 'close not in high low range @ {}'
        elif volume == 0 and high != low:
            mss = 'volume is zero with price changes @ {}'
        elif volume == 0 and not counts in (0, None):
            mss = 'volume is zero with pos number of counts @ {}'
        elif counts == 0 and not volume in (0, None):
            mss = 'counts is zero with pos number for volume @ {}'
        elif not (vwap is None or low <= vwap <= high):
            mss = 'vwap outside high low range @ {}'
        elif not (twap is None or low <= twap <= high):
            mss = 'twap outside high low range @ {}'
        else:
            return True
        mss = mss.format(time)
        raise DataConflict(mss)
            
    @staticmethod
    def  _validate_add_parameters(bar1, bar2):
        """Validate the Databars for the __add__ function.
        
        Make sure bar1 and bar2 are Databar's.
        
        Parameters:
          from calling function
        """
        ###
        ###
        if not bar1.duration_aware() == bar2.duration_aware():
            mss = 'Can not add duration aware and duration naive Databars'
            raise TypeError(mss)
        if not bar1.time < bar2.time:
            mss = 'time of second bar must be later then time of first bar'
            raise ValueError(mss)
        if (bar1.duration_aware() and
            not bar1.end_time() <= bar2.time):
            mss = 'second bar can not start before the first one ends'
            raise ValueError(mss)
        
    @staticmethod
    def _add_bars(bar1, bar2):
        """Returns the sum of the bars."""
        ###
        # basics
        time_ = bar1.time
        open_ = bar1.open_
        high = max(bar1.high, bar2.high)
        low = min(bar1.low, bar2.low)
        close = bar2.close
        # volume & vwaps 
        if not (bar1.volume == None or bar2.volume == None):
            volume = bar1.volume + bar2.volume
            if not (bar1.vwap == None or bar2.vwap == None):
                vwap = r_math.weighted_average([(bar1.volume, bar1.vwap),
                                                  (bar2.volume, bar2.vwap)])
            else:
                vwap = None
        else:
            volume = vwap = None
        # counts
        if not (bar1.counts == None or bar2.counts == None):
            counts = bar1.counts + bar2.counts
        else:
            counts = None
        # duration & twap
        if bar1.duration_aware() and bar2.duration_aware():
            duration = bar2.end_time() - bar1.time
            if not (bar1.twap == None or bar2.twap == None):
                twap = r_math.weighted_average(
                          [(bar1.duration.total_seconds(), bar1.twap),
                           (bar2.duration.total_seconds(), bar2.twap)])
            else:
                twap = None
        else:
            duration = twap = None
        # hasgaps
        if bar1.hasgaps == None or bar2.hasgaps == None:
            hasgaps = None
        elif (bar1.hasgaps == True or bar2.hasgaps == True):
            hasgaps = True
        elif not bar1.duration_aware():
            hasgaps = False
        elif bar2.joins(bar1):
            hasgaps = False
        else:
            hasgaps = True
        ###
        return DataBar(time_, open_, high, low, close,  
                       volume, counts,vwap, twap, hasgaps, duration)
    
    def to_csv(self, csv_out):
        csv_out.writerow(self)
            
        
class DataTick():
    """Some tick data
    
    Not implemented!
    """
    
    def __init__(self, *args, **kwds):
        """Not implemented!"""
        raise NotImplementedError('TODO')
    
    
databar_composer_open_mode = {'STANDARD':('standard', True, False, True),
                              'LOOSE': ('loose', True, True, True),
                              'STRICT': ('strict', True, False, False),
                              'FUTURE':  ('future', False, True, True)}
  #mode tuple are respective values for
  #  (self.__open_mode, self._open_is_close_last, open_from_future,
  #                                               open_from_first_data_in_bar)

class DataBarComposer():
    """Returns DataBars of the choosen duration from input.
    
    The duration of the composed bars is set at initialisation by using
    the datetime.timedelta arguments. If complete databars are available
    the insert method will return True. You can also check it with the
    complete_bars_available predicate. next_complete_bar will give you 
    the oldest unread complete bar, curr_bar the composing bar where 
    duration is the timedelta between start of the bar and the last data
    inserted.
    
    You can advance the composer by inserting a datetime.datime object 
    with move_time.  You have to add a bool to indicate if the passed time 
    had gaps or not.
    
    If data is inserted with a datetime.datetime object sooner then the
    end time of the composing bar a ValueError is raised.  If inserted
    data are bars, they are not allowed to span 2 composed bars, if so
    a ValueError is raised.
    
    The composer is normalised.  All composed databars will start at an
    integer-multiple-from-the-duration offset from january first of 
    that year.  When the duration is a multiple of seven (week bars) the
    time is last mondayś  00:00.  This behaviour can be changed. When you
    set a start_time, the composer will not try to normalise it. When you 
    set normalised to False in the init parameters and do not provide a
    start_time, the time of the first data is the start_time.  If you set
    the start time and it is a normalised start time, the normalised
    attribute is set to True, if not to False.
    
    You can initialise the close of previous bar before the composer is
    started. Once started you can read the value, but it is changed
    automatic.
    
    With the open_mode argument you can choose how the open of a bar is
    set.  You can select a mode from the databar_composer_open_mode.
      STANDARD
        When the data time is the start of the composers time, the value
        of the data will be used.  If not and de data point lies in the 
        composing bar, the value will be used.  If not and the close of
        the privious bar is known that will be used.  If not an error is
        raised.
      LOOSE
        Like standard but when when no privious bar value is found, the
        current value will be used.
      STRICT
        Like standard but the option to use a value from a datapoint in
        the composing bar will not be used.  If known the close of the 
        previous bar is used or else an error is raised.
      FUTURE
        Like loose but it will never use the value from the previous
        bar.
    
    After the first data is inserted, all attempts to change the
    composers attributes will raise an Exception.
    
    Properties:
      start_time --  set ofset base (default is calculated)
      previous_close -- close of previous bar (read only when running)
      composed_bar_duration -- size of the bars (read only, set @ init))
      normalised -- bars start from normalised time
      open_mode -- mode to choose open (read only, set @ init)
      composing_bar -- return composing bar (read only)
    
    Methods:
      insert_bar -- insert DataBar in the composer
      insert_tick -- insert TickData in the composer (not implemented)
      move_time -- move composer time to curr time
      end_time -- the time the composing bar is closed 
      pop_complete_bar -- return oldest unread bar
      reset_composer -- returns unread bars and prepares for new set of data
      
    """
    

    
    def __init__(self, *args, **kwds):
        """Initialise the DataBarComposer.
        
        You must use keyword parameters.  Unnmamed parameters or an empty
        parameter list will raise an InitTypeError.  The keyword dict is 
        passed to the datetime.timedelta init. check timedelta docs for
        accepted parameter names and values.
        
        Parameters:
          see datetime.timedelta documentation
          [normalised -- Bool (True)]
          [open_mode -- from databar_composer-open-mode dict (STANDARD)]
        """
        ##TEST OK ##
        if args or not kwds:
            mss = 'Only named arguments accepted'
            raise InitTypeError(mss)
        validate.as_bool(kwds.get('normalised', True), 'normalised: {}')
        validate.as_member(kwds.get('open_mode', 'STANDARD'),
                           databar_composer_open_mode, 'open-mode: {}')
        ###
        normalised = kwds.pop('normalised', True)
        open_mode = kwds.pop('open_mode','STANDARD')
        try:
            bar_duration = datetime.timedelta(**kwds)
            if bar_duration.total_seconds() == 0:
                raise ValueError('bar duration can not be zero seconds')
        except (TypeError, ValueError) as err:
            bar_duration = err
        ###
        if isinstance(bar_duration, (TypeError, ValueError)):
            raise InitTypeError(bar_duration)
        self._normalised = normalised
        self._set_composed_bar_duration(bar_duration)
        self._set_open_mode_to(open_mode)
        self.__previous_close = None
        self._work_list = []
        
    def __eq__(self, other):
        """Returns True of all attributes of self and other are equal."""
        ## TEST OK ##
        if not isinstance(other, DataBarComposer):
            mss = 'Can not compare DataBarComposer with {}'.format(type(other))
            raise TypeError(mss)
        ###
        a, b = self, other
        equal = True
        if not (a.composed_bar_duration == b.composed_bar_duration and
                a.start_time == b.start_time and
                a.__previous_close == b.__previous_close and
                a.normalised == b.normalised and
                a.open_mode == b.open_mode and
                a._open_is_close_last == b._open_is_close_last and
                a._open_from_future == b._open_from_future and
                a._open_from_first_data_in_bar == b._open_from_first_data_in_bar):
            equal = False
        else:
            for a_wl, b_wl in zip(a._work_list, b._work_list):
                if not a_wl == b_wl:
                    equal = False
                    break
        ###
        return equal
    
    @property
    def start_time(self):
        """Returns the start time.
        
        Not allowed to change attribute when composer is running. If not
        set by the user it will be set automatic when the first data is 
        inserted.
        """
        ## TEST OK ##
        ###
        ###
        return getattr(self,'_start_time', None)
    
    @start_time.setter
    def start_time(self, a_datetime):
        ## TEST OK ##
        validate.as_datetime(a_datetime, 'start_time): {}')
        if self._composer_running():
            raise Error('can not change start_time of running composer')
        ###
        ###
        self._start_time = a_datetime
    
    @property
    def last_known_close(self):
        """Returns the last known close.
        
        You can set it if the composer is not running.  So you have an
        initial value.  Once the composer is running it is the close of
        the last bar inserted, or the last value inserted.
        """
        ## TEST OK for inserting bars, ticks not yet implemented ##
        ###
        if self._composer_running():
            close = self.composing_bar.close
        else:
            close = self.__previous_close
        ###
        return close
    
    @last_known_close.setter
    def last_known_close(self, a_value):
        ## TEST OK for inserting bars, ticks not yet implemented ##
        validate.as_int_or_float(a_value, 'last known close: {}')
        if self._composer_running():
            mss = 'user can\'t change last_known__close of running composer'
            raise Error(mss)
        ###
        ###
        self.__previous_close = a_value
        
    @property
    def composed_bar_duration(self):
        """Returns the initialised bar duration.
        
        Not allowed to change attribute after initialisation.
        """
        ## TEST OK ##
        ###
        ###
        return self._composed_bar_duration
    
    @property
    def open_mode(self):
        """Returns the mode to define the open of the composing bar.
        
        Set at init.
        """
        ## TEST OK ##
        ###
        ###
        return self._open_mode

    
    @property
    def composing_bar(self):
        """Return the composing bar.
        
        If the composer hasn't started yet None is returned
        """
        ## TEST OK ##
        ###
        ###
        return self._work_list[-1] if self._work_list else None
    
    @property
    def normalised(self):
        '''Is True if the start is normalised. False if not.
        
        The value is True by default.  If a start time is set it is
        checked to see if it is a normalised time.  If not normalised
        it is set to False.
        '''
        ## TEST OK ##
        ###
        if not self.start_time:
            normalised = self._normalised
        else:
            normalised = self._time_is_normalised_for_duration(
                          self.start_time, self.composed_bar_duration)
        ###
        return normalised

    def end_time(self):
        """Return the time the composed bar will be closed.
        
        if composer is not running and the start time is known, start
        time is the end_time"""
        ## TEST OK ##
        if not self.start_time:
            raise Error('Can not find a start time.')
        ###
        bars = self._work_list
        start_time = bars[-1].time if bars else self.start_time 
        start_time += self.composed_bar_duration if bars else datetime.timedelta(0)
        ###
        return start_time
    
    def insert_bar(self, bar):
        """Insert new bar in the composer, and return the composing bar.
        
        The bar must be a marketdata.DataBar or an Error is raised.  If
        the time of the bar is earlier then end of last bar, an Error is
        raised.  
        
        If there lies a possible endpoint between time of the bar en end
        time of the bar (not inclusive) a valueError will be raised.
        
        If there lies a possible endpoint between the last known time of
        the bar and the composer and the time of the current bar.
        DataBars without volume and counts are inserted but the hasgpas is
        set to True. To avoid this insert current times at these possible
        endpoint to show you confirm time has past without new data.
        
        Parameters:
          bar -- a marketdata.DataBar
        """
        ## TEST OK ##
        if not isinstance(bar, DataBar):
            mss = 'bar: {}'.format(type(bar))
            raise Error(mss)
        if not bar.duration_aware():
            mss = 'bar must be duration aware'
            raise Error(mss)
        ###
        first_data_insert = not self._composer_running()
        ###
        if first_data_insert:
            self._start_composer(bar.time, bar.open_)
        self._insert_bar_in_running_composer(bar)
        composing_bar = self.composing_bar
        if not composing_bar.duration:
            composing_bar = None
        return composing_bar
        
    def move_time(self, time_, gaps):
        '''Advance the time of the composer.
        
        If the composer is not running, an error is raised.
        
        If the move has gaps, hasgaps is set and vwap nor twap are
        changed.  It's the users responsiblity to decide in these
        situations how to react.
        
        If the move has no gaps, vwap is recalculated, twap stays
        the same.
        
        Parameters:
          time_ -- a datetime.datetime
          gaps -- bool, True if period has gaps
        '''
        ## TEST OK ##
        if not self._composer_running():
            raise Error('Pop request to not running composer')
        ###
        ###
        if gaps:
            self._fill_gaps_until(time_)
        else:
            self._move_time_without_gaps_to(time_)
        
        
    def pop_complete_bar(self):
        """Pop oldest complete bar from composer
        
        If the composer is not running an Error is raised.
        
        If no bar is complete, None is returned.
        """
        if not self._composer_running():
            raise Error('Pop request to not running composer')
        ###
        complete_bar_available = len(self._work_list) > 1
        ###
        bar = self._work_list.pop(0) if complete_bar_available else None
        return bar
    
    def reset_composer(self):
        """Return all bars, including composing one, empty working list.
        """
        ###
        answer = self._work_list
        self._work_list = []
        delattr(self, '_start_time')
        return answer
        
    def _insert_bar_in_running_composer(self, bar):
        """Insert the bar.
        
        The bar's start must be equal to or bigger then the composing
        bar's end time. If not an error is raised.
        
        The bar can not span two composing bars -> Error raised.
        
        If there is a gap between the end of the composing bar and
        the current bar, it will be filled. When necessary extra
        bars will be added. The hasgaps off these bars will be set
        to True
        
        Parameters:
          bar -- a DataBar
        """
        ## TEST OK, asserts tests not implemented ##  
        assert self._composer_running(), 'composer must be running'
        assert isinstance(bar, DataBar), 'bar must be DataBar'
        assert bar.duration_aware(), 'bar must be duration aware'
        if self.composing_bar.end_time() > bar.time:
            mss = 'new bar starts in composing bar: {} < {}'
            mss = mss.format(self._work_list[-1].time, bar.end_time())
            raise Error(mss)
        self._raise_error_if_bar_spans_two_composing_bars(bar)
        ###
        bar_adjacent_to_composing_bar = (bar.joins(self.composing_bar))
        ###        
        if not bar_adjacent_to_composing_bar:
            self._fill_gaps_until(bar.time)
        self._insert_adjacent_bar(bar)
        
    def _insert_adjacent_bar(self, bar):
        """Insert the adjacent bar.
        
        Since it requests to insert an adjacent bar it's evident that the
        composer must be running.
        
        Adds a bar to the composing bar, the new bar must be duration 
        aware, be adjacent to the previous and the resulting bar can 
        not cross a composing bars end.
        
        If the resulting composing bar reaches it's end time, a new
        composing bar is started. 
        
        Parameters:
          bar -- a DataBar
        """        
        ## TEST OK ##
        assert self._composer_running(), 'composer must be running'
        assert isinstance(bar, DataBar), 'bar must be DataBar'
        assert bar.duration_aware(), 'bar must be duration aware'
        assert bar.time == self.composing_bar.end_time(), 'bar must be adjacent'
        assert not bar.time + bar.duration > self.end_time(), (
                    'you can not insert behind the end of the composing bar')
        ###
        if self.composing_bar.is_zero_bar():
            # I think I can safely use the bar, becaus it are adjacent
            # bars.  So if the previous bar has created a zerobar, this
            # bar's time must be the open time of a composing bar.
            composing_bar = bar
        else:
            composing_bar = self.composing_bar + bar
        comp_bar_end_time = composing_bar.end_time()
        bar_complete = comp_bar_end_time == self.end_time()
        ###
        self._work_list.pop() #remove the registered composing bar
        self._work_list.append(composing_bar) # add the updated bar
        if bar_complete:
            self._start_new_composing_bar_with_zero_bar(
                                       comp_bar_end_time, composing_bar.close)
            
    def _start_composer(self, time_, open_value):
        """Make sure composer is ready to receive data.
        
        After these actions changing the composers attributes is no
        longer alowed.  The time_ is the time of the first data point,
        the value is the price at that moment, when it's a bar it's the
        open of the bar.
        
        When a start_time is already set, it wil be kept.  If not and
        normalise if False, the start_time will be set to time_.  if
        normalised is True the normalised start_time will be calculated
        and set.
        
        Parameters:
          time_ -- a datetime.datetime
          open_value -- an interger or a float
        """
        ## TEST OK, asserts tests not implemented ##    
        #get_bool('in start composer', default=True)
        assert isinstance(time_, datetime.datetime), (
                                            'time must be datetime.datetime')
        assert isinstance(open_value, (int, float)), (
                                            'open value must be a number')
        assert not isinstance(open_value, bool), 'open value can not be bool'
        assert not self._composer_running(), (
                       'You can not start a running composer')
        if self.start_time and self.start_time > time_:
            mss = 'Data before start composer {} < {}'
            mss = mss.format(self.start_time, time_)
            raise Error(mss)
        ###
        if self.start_time:
            start_time = self.start_time
        elif self.normalised:
            start_time = self._calculate_normalised_start_time(time_)
        else:
            start_time = time_
        ###        #self.__start_time = start_time
        self.start_time = start_time
        self._start_new_composing_bar_with_zero_bar(
            start_time, self._find_open_to_init_a_composing_bar(time_, 
                                                              open_value))
        
    def _find_open_to_init_a_composing_bar(self, time_, open_value):
        """Return the open value for a new composing bar.
        
        The time is a current time, with the value the opening value
        at that moment.
        
        time_ must be equal to or later then the end time time of the
        current composing bar. If there is no composing bar, it is
        compared with the start_time of the composer.
        
        """
        ## TEST OK, asserts tests not implemented ## 
        assert isinstance(self.start_time, datetime.datetime), (
                                  'time of composing bar must already be set')
        assert isinstance(time_, datetime.datetime), (
                                            'time must be datetime.datetime')
        assert isinstance(open_value, (int, float)), (
                                            'open value must be a number')
        assert not isinstance(open_value, bool), 'open value can not be bool'
        ###
        if self._composer_running():
            start_time_next_bar = self.end_time()
        else:
            start_time_next_bar = self.start_time
        ###
        if time_ < start_time_next_bar:
            raise Error('Can not calculate open for an existing bar')
        open_ = self._find_open_for_bar_starting_at(start_time_next_bar,
                                                    time_, open_value)
        return open_
    
    def _find_open_for_bar_starting_at(self, 
                                       start_time, time_, open_value):
        """Return the open value for a new composing bar starting at start_time.
        
        The time_ is a current time, with open_value value at that 
        moment.
        
        start_time must be a datetime.datime greater or equal then the
        close of the composing bar and be an integer multitude of the 
        composers duration away from the composers start time.  If the
        composer is not running, start_time must be the start time.
        
        time_ must be equal to or later then the start_time.
        
        Parameters:
          start_time -- start time of a new composing bar, 
                        a datetime.datetime
          time_ -- a current time, a datetime.datetime
          open_value -- the value at time_, a float or integer,
        """
        ## TEST OK, asserts tests not implemented ##
        assert isinstance(self.start_time, datetime.datetime), (
                                 'time of composing bar must already be set')
        assert isinstance(start_time, datetime.datetime), (
                                 'start_time must be a datetime.datetime')
        assert isinstance(time_, datetime.datetime), (
                                            'time must be datetime.datetime')
        assert isinstance(open_value, (int, float)), (
                                            'open value must be a number')
        assert not isinstance(open_value, bool), 'open value can not be bool'
        assert start_time >= self.start_time, (
                 'start time must be later then self.start_time')
        assert ((start_time - self.start_time) % self.composed_bar_duration == 
                         datetime.timedelta(0)), 'starttime must be multiple'
        assert start_time <= time_, (
                                 'Can not calculate open for an existing bar')
        ###
        bar_end_time = start_time + self.composed_bar_duration
        open_ = None
        open_ = open_value if self._open_from_future else open_
        if self.last_known_close and self._open_is_close_last:
            open_ = self.last_known_close
        if time_ < bar_end_time and self._open_from_first_data_in_bar:
            open_ = open_value
        open_ = open_value if start_time == time_ else open_
        ###
        if open_ == None:
            mss = 'could not find an open value for composing bar @ {}'
            mss = mss.format(time_)
            raise Error(mss)
        return open_
        
    def _start_new_composing_bar_with_zero_bar(self, time_, open_):
        """Add a zero bar to the _work_list.
        
        The zero bar is a bar with duration 0.  The time of that bar is
        the time for the composing bar, the open, high, low and close
        are the open of the bar. Volume and counts are 0.  Since it is a
        zerotime bar, hasgaps is False.  The vwap and twap are also equal
        to the open of the bar.
        
        If the bar is the first bar, time_ must be the same as the start
        time of the composer.  Trying to add a zero bar that is not 
        adjacent to the previous bar will result in an error. 
        """
        ## TEST OK 
        assert isinstance(time_, datetime.datetime), (
                                            'time must be datetime.datetime')
        assert isinstance(open_, (int, float)), (
                                            'open value must be a number')
        assert not isinstance(open_, bool), 'open value can not be bool'
        assert time_ == self.end_time(), (
          'can not open new bars with a gap{} {}'.
                          format(time_, self.end_time()))
        ###
        ###
        self._work_list.append(DataBar(time_, 
                                       open_, open_, open_, open_,
                                       volume=0, counts=0, 
                                       vwap=open_, twap=open_,
                                       hasgaps=False,
                                       duration=datetime.timedelta(0)))         
                                   
    def _composer_running(self):
        """Returns True if composer received data."""
        ## TEST OK ##
        ###
        ###
        return bool(self._work_list)
    
    def _calculate_normalised_start_time(self, time_):
        """Find the last normalised time before time_."""
        ##TEST OK ##
        assert isinstance(time_, datetime.datetime), (
                                     'time must be a datetime.datetime')
        ###
        bar_duration = self.composed_bar_duration
        time00 = time_.replace(hour=0, minute=0, second=0, microsecond=0)
        one_week = datetime.timedelta(7)
        week_bars = bar_duration % one_week == datetime.timedelta(0)
        nr_of_day = time00.weekday()
        if week_bars:
            offset0 = time00 - datetime.timedelta(nr_of_day)
        else:
            offset0 = time00.replace(month=1, day=1)
        offset = (time_ - offset0) % bar_duration  
        ###
        return time_ - offset
                    
        
    def _raise_error_if_bar_spans_two_composing_bars(self, bar):
        """Return True if the bar spans two composing bars."""
        ##TEST OK##
        assert isinstance(bar, DataBar), "bar must be a DataBar"
        assert self._composer_running(),  'composer not running'
        ###
        test_range = []
        time_to_test = self.composing_bar.time
        while time_to_test < bar.end_time():
            time_to_test += self.composed_bar_duration
            test_range.append(time_to_test)
        ###
        for time_ in test_range:
            if bar.time < time_ < bar.end_time():
                mss = 'bar spans 2 bars. {} in {}'
                mss = mss.format(time_, bar.time)
                raise Error(mss)
        return True
    
    def _fill_gaps_until(self, time_):
        '''Advance time due to missing data.
        
        You can only extend a running composer, the open of the composing
        bar will be kept and used as open for all consecutive bars 
        created. This is a fill gaps function used to fill a gap with 
        MISSING data.
        
        You can not make a bar shorter! time_ must be later than the end
        of the composing bar.
        '''        
        ##TEST OK##
        assert isinstance(time_, datetime.datetime), (
                              'time must be a datetime.datetime')
        assert self._composer_running(), 'composer not running'
        assert time_ > self.composing_bar.end_time(), 'can not make bar shorter'
        ###
        bar_end = self.end_time()
        extend_time = bar_end if time_ > bar_end else time_
        ###
        self._extend_composing_bar_until(extend_time, gaps=True)
        if extend_time == bar_end:
            # start next bar where open is close of the previous bar.
            # This must be the correct value, becaus fill_gaps is used
            # to fill a bar becaus of missing data, no new value can
            # be calculated for the open.
            self._start_new_composing_bar_with_zero_bar(
                       extend_time, self.composing_bar.close)
        if extend_time < time_:
            self._fill_gaps_until(time_)
        
    def _extend_composing_bar_until(self, time_, gaps):
        """Extend the bar until time_.
        
        If gaps is True, the hasgaps of the composing bar is set to True.
        Volume and counts will not change.  If the bar has no gaps the
        twap will be adjusted. It's the users responsibity to know if
        there are gaps and eventualy decide on the actions to take.
        
        Requesting to make the bar longer then a composing bar size is
        not allowed.  Neither is it possible to shorten a bar.
        
        Parameters:
          time_ -- a datetime.datetime
          gaps -- bool
        """
        ##TEST OK##
        assert isinstance(time_, datetime.datetime), (
                              'time must be a datetime.datetinme')
        assert isinstance(gaps, bool), 'gap must be bool'
        assert self._composer_running(), 'composer not running'
        assert time_ > self.composing_bar.end_time(), 'can not make bar shorter'
        assert time_ <= self.end_time(), (
            'you can not extend behind the end of the composing bar')
        ###
        cb = self.composing_bar
        ext_bar = {'duration': time_ - cb.time,}
        if gaps == True:
            ext_bar['hasgaps'] = True
        else:
            gap_to_fill = time_ - cb.end_time()
            twap = r_math.weighted_average(
                          [(cb.duration.total_seconds(), cb.twap),
                           (gap_to_fill.total_seconds(), cb.close)])
            ext_bar['twap'] = twap            
        ###
        comp_bar = self._work_list.pop()
        ext_comp_bar = comp_bar.replace(**ext_bar)
        self._work_list.append(ext_comp_bar)
        
    @staticmethod
    def _time_is_normalised_for_duration(a_time, a_delta):
        '''Return True if a_time is normalised for a_delta.'''
        ## TEST OK ##
        assert isinstance(a_time, datetime.datetime), (
                                     'a_time must be a datetime.datetime')
        assert isinstance(a_delta, datetime.timedelta), (
                                   'a_delta must be a datetime.timedelta')
        ###
        time00 = a_time.replace(hour=0, minute=0, second=0, microsecond=0)
        one_week = datetime.timedelta(7)
        week_bars = a_delta % one_week == datetime.timedelta(0)
        nr_of_day = time00.weekday()
        if week_bars:
            offset0 = time00 - datetime.timedelta(nr_of_day)
        else:
            offset0 = time00.replace(month=1, day=1)
        normalised = (a_time - offset0) % a_delta == datetime.timedelta(0)
        ###
        return normalised    
    
    def _set_open_mode_to(self, mode):
        """Set the open mode.
        
        Set at init.
        """
        ## TEST OK ##
        assert not hasattr(self, '_open_mode'), 'only use it @ init'
        assert mode in databar_composer_open_mode, (
                        'mode must be in the databar_composer_open_mode dict')
        ###
        open_mode = databar_composer_open_mode[mode]
        ###
        self._open_mode = open_mode[0]
        self._open_is_close_last = open_mode[1]
        self._open_from_future = open_mode[2]
        self._open_from_first_data_in_bar = open_mode[3]
        
    def _set_composed_bar_duration(self, duration):
        '''Set the duration of the bars to compose.
        
        Set at init.
        
        Parameters:
          duration -- a datetime.timedelta
        '''
        ## TEST OK ##
        assert not hasattr(self, '_composed_bar_duration'), 'only use it @ init'
        assert isinstance(duration, datetime.timedelta), (
                    'duration must be a datetime.timedelta object:')
        ###
        ###
        self._composed_bar_duration = duration
        
    def _move_time_without_gaps_to(self, time_):
        '''Extend and create new bars without gaps until time_.
        
        You can only move the time of a running composer. The open of the
        composing bar will be kept and used as open for all consecutive 
        bars the are eventually created.
        
        In the composing bar the vwap and duration are adjusted. The other
        values stay the same (also the hasgaps of the composing bar!).  
        
        If new bars have to be created the open, high, low, close, vwap
        and twap of the bars are the close of the current composing bar.
        The counts and volume will be zero.
        
        You can not make a bar shorter! time_ must be later than the end
        of the composing bar.
        
        Parameters:
          time_ -- a datetime.datetime
        '''
        ##TEST OK, if _extend_composing_bar_until is tested ## 
        assert isinstance(time_, datetime.datetime), (
                              'time must be a datetime.datetime')
        assert self._composer_running(), 'composer not running'
        assert time_ > self.composing_bar.end_time(), 'can not make bar shorter'
        ###
        bar_end = self.end_time()
        extend_time = bar_end if time_ > bar_end else time_
        self._extend_composing_bar_until(extend_time, gaps=False)
        if extend_time == bar_end:
            # start next bar where open is close of the previous bar.
            # This must be the correct value, becaus fill_gaps is used
            # to fill a bar becaus of missing data, no new value can
            # be calculated for the open.
            self._start_new_composing_bar_with_zero_bar(
                       extend_time, self.composing_bar.close)
        if extend_time < time_:
            self._move_time_without_gaps_to(time_)
            
class DataBarFeederInfo():
    '''Object with info about a DataFeeder.
    
    If the indexdata is set to True, volume will not be set in, or 
    removed from, the available_data list.
    
    Properties:
      available_data -- The Data available in the DataBars.
      indexdata -- True if data is index data, no volume possible
      
    Methods:
      add_available_data -- Add types in the available_data property.
      remove_available_data -- Remove types from the available_data property.
    '''
    
    def __init__(self, *preset_data):
        ## TEST OK ##
        self.available_data = set()
        self.indexdata = False
        if preset_data:
            self.add_available_data(*preset_data)
        
    def add_available_data(self, *data_types):
        ## TEST OK ##
        ###
        unknown_types = [x for x in data_types if x not in DATABAR_ELEMENTS]
        ###
        if unknown_types:
            raise Error('unknown data_types: {}'.format(str(unknown_types)))
        self.available_data |= set(data_types)
        if self.indexdata:
            self.remove_available_data('volume')
        
    def remove_available_data(self, *data_types):
        ###
        ###
        self.available_data -= set(data_types)
        
    @property    
    def indexdata(self):
        '''True if data is indexdata.
        
        If data is indexdata, there are no trades, so there's no volume.
        The dirived classes can use it to check for output DataBar. The
        volume parameter is automatically removed from the available 
        data.
        '''
        ###
        ###
        return self.__indexdata
    
    @indexdata.setter
    def indexdata(self, is_index_data):
        if not isinstance(is_index_data, bool):
            mss = 'type is_index_data:{}'.format(type(is_index_data))
            raise Error(mss)
        ###
        ###
        if is_index_data:
            self.remove_available_data('volume')
        self.__indexdata = is_index_data
    
class DataBarFeeder():
    '''Provides a generator and info about the data generated.
    
    '''    
    def __init__(self, info, **kwds):
        '''Initiate the feeder with a genarator and some info.
        
        Make sure the genarator returns marketdata.DataBar's and that the
        info is correct.
        
        Parameters:
          generator -- a genarator of DataBars
          info -- a DataBarFeederInfo
        '''
        if not isinstance(info, DataBarFeederInfo):
            raise Error('info must be DataBarFeederInfo instance')
        ###
        is_index = kwds.pop('is_index', False)
        ###
        if kwds:
            raise Error('Unexpected keywords: {}'.format(kwds.keys()))
        self.info = info
        if is_index:
            self.info.indexdata = True
        
       
KNOWN_DATA_FILE_TYPES = {
    'csv_type0','csv_type1'
}

def data_bar_feeder(*location, **kwds):
    '''Start a feeder.
    
    Ńeeds a lot of thinking and work, now it's all assof
    '''
    if isinstance(location[0], list):
        feeder = DBFfromDatabarList(location[0])
    elif location[0] == '__tws_live__':
        feeder = DBFfromTWSLiveFeed(location[1:], **kwds)
    elif full_path(*location).endswith('.db'):
        feeder = DBFfromsql_ib_db_5secs_bars(*location, **kwds)
        #feeder.info.indexdata=True
    else:
        feeder = data_bar_feeder_from_file(*location, **kwds)
    return feeder

def data_bar_feeder_from_file(*filename, **kwds):
    '''Return a DataBarFeeder from the file.
    
    Filename is path to the file.  The function tries to find the type of
    the file, and starts the appropriete DataBarFeeder.
    
    If the type is unknown an Error is raised
    
    Parameters:
      <string>, ... -- the path to the file
    '''
    
    assert filename, 'no filename'
    assert exists(r_dir.full_path(*filename)), (
        'file {} doesn\'t exists'.format(r_dir.full_path(*filename)))
    ###
    with open(full_path(*filename)) as inf:
        first_line = inf.readline().rstrip()
    ###
    for type_, class_ in FILE_TYPE_DATA_FEEDER_CLASS_TRANSLATION_DICT.items():
        print(type_, class_.__name__)
        if (hasattr(class_, 'known_headers') and 
            not first_line in class_.known_headers):
            print(first_line, 'not in', class_.known_headers)
            continue
        try:
            print('Checking format')
            class_.check_file_format(*filename)
        except Exception:
            print('check FAILED')
            continue
        break
    else:
        raise Error('Unknown file format')
    dbf = class_(*filename, **kwds)
    return dbf

def data_bar_feeder_from_db(*db_name, **kwds):
    '''Return a DataBarFeeder from the database.
    '''
    
    assert db_name, 'no filename'
    assert exists(r_dir.full_path(*db_name)), (
        'file {} doesn\'t exists'.format(r_dir.full_path(*filename)))
    ###
    
        
class DBFfromCSV_type0(DataBarFeeder):
    '''create DataBarFeeder from csv textfile.
    
    INPUT: Type0 cvs input, index no volumes
      header: True
      seperator: ,
      format: 19/02/2002,09:07:00,488.83,489.06,488.83,488.96,0
      bar time: end of bar
      bar size: 1 minute
      
    
    OUTPUT: Databar
      time, open_, high, low, close, volume
      
    
    '''
    
    known_headers = {
        '"Date","Time","Open","High","Low","Close","TotalVolume"'
    }
    
    def __init__(self,  *filename, **kwds):
        assert filename, 'no filename'
        assert exists(full_path(*filename)), (
            'file {} doesn\'t exists'.format(full_path(*filename)))
        self.check_file_format(*filename)
        ###
        ###
        info = DataBarFeederInfo('time', 'open_', 'high', 
                                 'low', 'close', 'volume')
        self.__filename = full_path(*filename, **kwds)
        super().__init__(info)
        
    def __iter__(self):
        def index_volume(foo):
            return None
        def non_index_volume(value):
            return int(value)
        ###
        duration = datetime.timedelta(minutes=1)
        indexdata = self.info.indexdata
        correct_volume = non_index_volume if not indexdata else index_volume
        ###
        with open(self.__filename) as inf:
            skip_header = inf.readline()
            for line in inf:
                try:
                    databar = self.line_to_bar(line, correct_volume, duration)
                except indexError:
                    continue
                yield databar
        
    
    @staticmethod
    def line_to_bar(line, volume_correction, duration):
        '''Proces the line and return a Databar.
        
        The volume correction is used to set the volume to None when the
        volume of the data is always 0 (e.g. index data).
        
        Parameters:
          volume_correction -- a tr function on the volume value
          duration -- duration of the bar
        '''
        ###
        x = line.split(',') 
        time = datetime.datetime.strptime(' '.join(x[:2]), 
                                          '%d/%m/%Y %H:%M:%S')
        time -= datetime.timedelta(minutes=1) # adjust end of bar time
        open_, high, low, close, volume = (
            float(x[2]), float(x[3]), float(x[4]), float(x[5]), 
            volume_correction(x[6]))
        return DataBar(time, open_, high, low, close, volume, duration=duration)
    
    @staticmethod                
    def check_file_format(*filename):
        ###
        filename = full_path(*filename)
        line_to_bar = DBFfromCSV_type0.line_to_bar
        with open(filename) as inf:            
            lines = (inf.readline(), inf.readline())
        ###
        try:
            line_to_bar(lines[1], lambda x: None, datetime.timedelta(seconds=1))
        except Exception as e:
            print(lines)
            raise Error('wrong file format, dataline not ok')
        try:            
            line_to_bar(lines[0], lambda x: None, datetime.timedelta(seconds=1))
        except Exception:
            return True
        print(lines)
        raise Error('wrong file format, no header line found')
    
class DBFfromCSV_type1(DataBarFeeder):
    '''create DataBarFeeder from csv textfile.
    
    INPUT: Type0 cvs input, index no volumes
      header: True
      seperator: ,
      format: 19/02/2002,09:07:00,488.83,489.06,488.83,488.96,0
      bar time: start of bar
      bar size: 1 minute
      
    
    OUTPUT: Databar
      time, open_, high, low, close, volume
      
    
    '''
    
    known_headers = {
        '<Date>, <Time>, <Open>, <High>, <Low>, <Close>, <Volume>'
    }
    
    def __init__(self,  *filename, **kwds):
        assert filename, 'no filename'
        assert exists(full_path(*filename)), (
            'file {} doesn\'t exists'.format(full_path(*filename)))
        self.check_file_format(*filename)
        ###
        ###
        info = DataBarFeederInfo('time', 'open_', 'high', 
                                 'low', 'close', 'volume')
        self.__filename = full_path(*filename)
        super().__init__(info, **kwds)
        
    def __iter__(self):
        def index_volume(foo):
            return None
        def non_index_volume(value):
            return int(value)
        ###
        duration = datetime.timedelta(minutes=1)
        indexdata = self.info.indexdata
        correct_volume = non_index_volume if not indexdata else index_volume
        ###
        with open(self.__filename) as inf:
            skip_header = inf.readline()
            for line in inf:
                try:
                    databar = self.line_to_bar(line, correct_volume, duration)
                except (IndexError, Error):
                    continue
                yield databar
        
    
    @staticmethod
    def line_to_bar(line, volume_correction, duration):
        '''Proces the line and return a Databar.
        
        The volume correction is used to set the volume to None when the
        volume of the data is always 0 (e.g. index data).
        
        Parameters:
          volume_correction -- a tr function on the volume value
          duration -- duration of the bar
        '''
        ###
        x = line.split(',')
        if not len(x) == 7: raise Error('wrong line format')
        time = datetime.datetime.strptime(' '.join(x[:2]), 
                                          '%m/%d/%Y %H:%M:%S')
        open_, high, low, close, volume = (
            float(x[2]), float(x[3]), float(x[4]), float(x[5]), 
            volume_correction(x[6]))
        return DataBar(time, open_, high, low, close, volume, duration=duration)
    
    @staticmethod                
    def check_file_format(*filename):
        ###
        filename = full_path(*filename)
        line_to_bar = DBFfromCSV_type1.line_to_bar
        with open(filename) as inf:            
            lines = (inf.readline(), inf.readline())
        ###
        try:
            line_to_bar(lines[1], lambda x: None, datetime.timedelta(seconds=1))
        except Exception:
            print('datalíne', lines)
            print(e)
            raise Error('wrong file format, dataline not ok')
        try:            
            line_to_bar(lines[0], lambda x: None, datetime.timedelta(seconds=1))
        except Exception:
            return True
        print('wrong?? header line')
        print(e)
        raise Error('wrong file format, no header line found')
    
class DBFfromDatabarList(DataBarFeeder):
    '''create DataBarFeeder from in memory DataBar list.
    
    INPUT: Databar
      bar time: start of bar
      bar size: databar
      
    
    OUTPUT: Databar
      format depends on original list   
    
    '''    
    
    def __init__(self, *args, **kwds):
        ###
        databarlist = args[0]
        ###
        info = DataBarFeederInfo('time', 'open_', 'high', 
                                 'low', 'close', 'volume',
                                 'counts', 'hasgaps')
        self.fulldata = databarlist
        super().__init__(info)    
        
    def __iter__(self):
        ###
        ###
        for databar in self.fulldata:
            yield databar
    
    
class DBFfromsql_ib_db_5secs_bars(DataBarFeeder):
    '''create DataBarFeeder from sql_ib_db.
    
    INPUT: sql_ib_db
      bar time: start of bar
      bar size: 5 minute
      
    
    OUTPUT: Databar
      time, open_, high, low, close, volume, counts, hasgaps      
    
    '''
    
    def __init__(self, *args, **kwds):
        ###
        db_name = r_dir.full_path(*args)
        start = kwds.pop('start', False)
        stop = kwds.pop('stop', False)
        update = kwds.pop('update', False)
        contract = kwds.pop('contract', None)
        verbose_updating = kwds.pop('verbose_update', True)
        if update and not contract:
            raise Error('Update mode needs a contract')
        info = DataBarFeederInfo(
                'time', 'open_', 'high', 'low', 'close', 
                'volume', 'counts', 'hasgaps',
        )
        ###
        if not exists(db_name):
            raise Error('db {} doesn\'t exists'.format(db_name))
        super().__init__(info, **kwds)
        self.__db_name = full_path(db_name)
        self.start, self.stop = start, stop
        self.update_db = update
        self.contract = contract
        self.verbose_updating = verbose_updating
        
    def __iter__(self):
        def index_volume(foo):
            return None
        def non_index_volume(value):
            return int(value)
        ###
        duration = datetime.timedelta(seconds=5)
        indexdata = self.info.indexdata
        correct_volume = non_index_volume if not indexdata else index_volume
        ###
        if self.update_db:
            historicaldata.historical_data_to_db(
                contract=self.contract, 
                barsize='5 secs', 
                show='TRADES', 
                host_ip=TWS_SERVER_IP, 
                client_port=TWS_SERVER_PORT, 
                client_id=TWS_CLIENT_ID, 
                verbose=self.verbose_updating, 
                update=True)
        db_h = sql_ib_db.HistoricalDatabase(self.__db_name, db_dir=None)
        inf = db_h.data_stream(
                'TRADES_5_secs',
                'datetime', 'open', 'close', 'high', 'low',
                'volume', 'counts', 'hasgaps',
                start=self.start,
                stop=self.stop,
        )
        while inf:
            databar = self.answer_to_bar(
                        answer=next(inf), 
                        volume_correction=correct_volume, 
                        duration=duration)
            yield databar

    
    @staticmethod
    def answer_to_bar(answer, volume_correction, duration):
        '''Proces the line and return a Databar.
        
        The volume correction is used to set the volume to None when the
        volume of the data is always 0 (e.g. index data).
        
        Parameters:
          volume_correction -- a tr function on the volume value
          duration -- duration of the bar
        '''
        ###
        
        return DataBar(
                 answer.datetime, 
                 answer.open, answer.high, answer.low, answer.close,
                 volume=volume_correction(answer.volume), 
                 counts=answer.counts,                     
                 hasgaps=not bool(answer.hasgaps),
                 duration=duration,                 
        )
    
class DBFfromTWSLiveFeed(DataBarFeeder):
    '''create DataBarFeeder from a tws live feed.
    
    '''
    
    def __init__(self, *args, **kwds):
        ###
        tws_contract = kwds.pop('contract')
        barsize = kwds.pop('barsize')
        show = kwds.pop('show')
        rth = kwds.pop('rth', False)
        live_server_ip = kwds.pop('server_ip', LIVE_SERVER_IP)
        live_server_port = kwds.pop('server_port', LIVE_SERVER_PORT)
        info = DataBarFeederInfo(
            'time', 'open_', 'high', 'low', 'close', 
            'volume', 'vwap', 'counts', 'hasgaps',
        )
        ###
        super().__init__(info, **kwds)
        self.contract = tws_contract
        self.barsize = barsize
        self.show = show
        self.rth = rth
        self.server_ip = live_server_ip
        self.server_port = live_server_port
        
    def __iter__(self):
        def index_volume(foo):
            return None
        def non_index_volume(value):
            return int(value)
        ###
        duration = tws.rhd_bar_sizes_2_timedelta[self.barsize]        
        indexdata = self.info.indexdata
        correct_volume = non_index_volume if not indexdata else index_volume
        ###
        realbar_server = tws_realbar_request_gscLib.server_client(
                            server_ip=self.server_ip,
                            server_port=self.server_port,
        )        
        live_data = realbar_server.client_for_request(
            'real_time_bars', 
            self.contract, self.barsize, self.show, self.rth)
        while live_data:
            databar = self.answer_to_bar(
                        answer=next(live_data),
                        volume_correction=correct_volume, 
                        duration=duration)
            yield databar
    
    @staticmethod
    def answer_to_bar(answer, volume_correction, duration):
        '''Proces the line and return a DataBar.'''
        ###
        
        return DataBar(
                time=answer.time_,
                open_=answer.open_,
                high=answer.high,
                low=answer.low,
                close=answer.close,
                volume=volume_correction(answer.volume),
                counts=answer.count,
                duration=duration,
                )
    
FILE_TYPE_DATA_FEEDER_CLASS_TRANSLATION_DICT = {
   'csv_type0': DBFfromCSV_type0,
   'csv_type1': DBFfromCSV_type1,
}

class DBFContinuedWithLiveDBF(r_output.AddExportSystem):
    '''Feed data from DBF and continue with the live DBF.'''
    
    def __init__(self, feeder, livefeeder):
        self.feeder = feeder
        self.live_feeder = livefeeder
        super().__init__()
        
    def __iter__(self):
        feeder = self.feeder
        live_feeder = self.live_feeder
        self.live_mode = False
        previous_end_time = None
        for live_bar in live_feeder:
            if isinstance(feeder, list):
                feeder.append(live_bar)
            for bar in feeder:
                start_time = bar.time
                end_time = bar.end_time()
                if previous_end_time and start_time < previous_end_time:
                    continue
                previous_end_time = end_time
                yield bar
            else:
                if isinstance(feeder, list):
                    feeder = []
                else:
                    print('first live bar received started @ {}'.
                          format(live_bar.time))
                    feeder = [live_bar]
                    self.export_switch_to_live_mode()                    
                    self.live_mode=True
        self.export_flush() #clear export list

class ComposingDatabarFeeder(r_output.AddExportSystem):
    
    '''Compose and feed new databars from feeder.
      
      When timer is live, the announced time is the live time, with bars
      it is the end time of composed bar plus the bar_timer_adjustment. The
      default is bars with a correction of 1 second.
      
      When export finished bars is false, memory usage and speed will be more
      optimal. Live exports the bars when they are announced, only use it in
      live mode it's very slow (lots of IO). With size you choose to save every
      n bars and request saves all until you request a save. The last one is as
      fast as the False mode, but can use lots of mem. False is default
    
    Attributes:
      feeder -- data feeder, a DataBarFeeder
      composer -- The composer to compose new bars, a DataBarComparer
      timer -- 'live'or 'bars'
      export -- False, 'live', size, 'request'
         
    Methods:
      bar_timer_adjustment -- set bar timer adjustment, a timedelta
      
    '''
    
    def __init__(self, *args, **kwds):
        '''Initiate the feederfromfeeder.
        
        Arguments:
          feeder -- the bars feeding feeder
          timer -- 'live' or 'bars'
          export -- choose base export setting
          other args and kwds are send to composer, see DataBarComposer for
          more info
          
        '''
        
        self.feeder = kwds.pop('feeder')
        #self.timer = kwds.pop('timer', 'bars')
        self.bar_timer_adjustment = datetime.timedelta(seconds=1)
        self.live_feeder = kwds.pop('live_feeder', [None])
        self.composer = DataBarComposer(*args, **kwds)
        self.live_mode = False
        super().__init__()
        
    def __iter__(self):
        ###
        feeder = self.feeder
        live_feeder = self.live_feeder
        composer = self.composer
        old_start_time = None
        unread_data = []
        ###
        for live_bar in live_feeder:
            if isinstance(feeder, list):
                feeder.append(live_bar)
            for bar in feeder:
                start_time = bar.time
                if old_start_time and start_time - old_start_time < bar.duration:
                    # skip bars that come to soon, there must be something wrong
                    # with them.
                    print('!!! skipping this bar !!! duration problem {} - {} < {}'.
                          format(start_time, old_start_time, bar.duration))
                    continue
                if (not old_start_time 
                    or 
                    (not start_time.date() == old_start_time.date() and
                     start_time - old_start_time > bar.duration)):
                    # reset the composer, adding some sort of time setting so you
                    # can activate this at other breakes in data (like euro/dollar
                    # at CET between 23:15 and 23:30). Think about it!
                    if not composer.start_time is None:
                        unread_data = composer.reset_composer()
                composing_bar = composer.insert_bar(bar)
                while 1:
                    new_bar = composer.pop_complete_bar()
                    unread_data.append(new_bar)
                    if not new_bar: break
                if len(unread_data) > 1: unread_data.pop() 
                    #dont return the time if new data available
                if self.live_mode:
                    announced = datetime.datetime.now()
                else:
                    announced = bar.end_time() + self.bar_timer_adjustment
                while unread_data:
                    d = unread_data.pop(0)
                    if d is not None:
                        self.export_object(d)
                    yield announced, bar, composing_bar, d
                old_start_time = start_time
            else:
                if live_bar is None:
                    break # out for live_feeder loop
                elif isinstance(feeder, list):
                    feeder = []
                else:
                    print('first live bar received started @ {}'.
                          format(live_bar.time))
                    feeder = [live_bar]
                    self.export_switch_to_live_mode()
                    self.live_mode=True
        self.export_flush() #clear export list

#def compose_new_bars_from_feeder(*args, **kwds):
    #'''Create feeder with new bar length from existing bars.
    
    #Needs the feeder keyword with the feeder, other kwds args will be
    #send to the composer.
    #'''
    #old_start_time = None
    #unread_data = []
    #feeder = kwds.pop('feeder')
    #new_data_bars = DataBarComposer(*args, **kwds)
    #for bar in feeder:
        #start_time = bar.time
        #if old_start_time and start_time - old_start_time < bar.duration:
            ## skip bars that come to short, there must be something wrong
            ## with them.
            #print('!!! skipping this bar !!! duration problem {} - {} < {}'.
                  #format(start_time, old_start_time, bar.duration))
            #continue
        #if (not old_start_time 
            #or 
            #(not start_time.date() == old_start_time.date() and
             #start_time - old_start_time > bar.duration)):
            ## reset the composer, adding some sort of time setting so you
            ## can actrvate this at other breakes in data (like euro/dollar)
            ## at CET between 23:15 and 23:30. Think about it!
            #if not new_data_bars.start_time is None:
                #unread_data = new_data_bars.reset_composer()
        #new_data_bars.insert_bar(bar)
        #new_bar = new_data_bars.pop_complete_bar()
        #if not new_bar is None:
            #unread_data.append(new_bar)
        #while unread_data:
            #d = unread_data.pop(0)
            #yield bar, d
        #else:
            #yield bar, None
        #old_start_time = start_time
                