#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from datetime import datetime, date, time, timedelta, timezone

ISO_8601_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

def timetodatetime(a_time, fix_date=date.today()):
    '''make a datetime object from a timeobject.
    
    It changes the time to the time today,  you make it change
    to time someday by setting fix_date to someday.
    
    Parameters:
      a_time -- a datetime.time
      fix_date -- a datetime.time (default is today)
    '''
    ###
    ###
    return datetime.combine(fix_date, a_time)

def time_operation_timedelta(a_time, operator, a_timedelta):
    '''Return the resulting time.'''
    t = timetodatetime(a_time)
    if operator == '+':
        t += a_timedelta
    if operator == '-':
        t -= a_timedelta
    return t.time()

def round_down(a_datetime, a_timedelta):
    '''Round down to nearest multiple of the timedelta.'''
    if a_timedelta.days:
        raise AttributeError('timedelta must be smaller then 1 day')
    ts = int(a_datetime.timestamp())
    rts = ts // a_timedelta.seconds *a_timedelta.seconds    
    return datetime.fromtimestamp(rts)

def now():
    return datetime.now()
