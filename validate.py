#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import datetime
import collections
import os
import decimal


class Error(Exception):
    """Base class for validate exceptions."""
    pass

class TypeError(Error):
    """Raised when a type validation failed."""
    pass
    
class ValueError(Error):
    """Raised when a value validation failed."""
    pass


######
# Standard types
######

def as_bool(obj, mss='{}'):
    """Validate object as bool instance, raise TypeError if not.
    
    The mss will be formatted with the type of the object and send with
    the raised error.
    
    Parameters:
      obj -- an object
      mss -- a str wich may contain one format placeholder
    """
    ## TEST OK ##
    ###
    ###
    if not isinstance(obj, bool):
        mss = mss.format(type(obj))
        raise TypeError(mss)
    return True

######
# datetime types
######

def as_time(obj, mss='{}'):  
    """Validate object as datetime.time instance, raise TypeError if not.
    
    The mss will be formatted with the type of the object and send with
    the raised error.
    
    Parameters:
      obj -- an object
      mss -- a str wich may contain one format placeholder
    """
    ###
    ###
    if not isinstance(obj, datetime.time):
        mss = mss.format(type(obj))
        raise TypeError(mss)
    return True
    
def as_date(obj, mss='{}'):  
    """Validate object as datetime.date instance, raise TypeError if not.
    
    The mss will be formatted with the type of the object and send with
    the raised error.
    
    Parameters:
      obj -- an object
      mss -- a str wich may contain one format placeholder
    """
    
    ###
    ###
    if not isinstance(obj, datetime.date):
        mss = mss.format(type(obj))
        raise TypeError(mss)
    return True
    
def as_datetime(obj, mss='{}'):  
    '''Validate object as datetime.datetime instance, raise TypeError if
    not.
    
    The mss will be formatted with the type of the object and send with
    the raised error.
    
    Parameters:
      obj -- an object
      mss -- a str wic
    '''
    ## TEST OK ##    
    ###
    ###
    if not isinstance(obj, datetime.datetime):
        mss = mss.format(type(obj))
        raise TypeError(mss)
    return True

def as_date_or_datetime(obj, mss={}):  
    '''Validate object as datetime.datetime instance or datetiime.time
    instance, raise TypeError if not.
    
    The mss will be formatted with the type of the object and send with
    the raised error.
    
    Parameters:
      obj -- an object
      mss -- a str wic
    '''
    ## TEST OK ##    
    ###
    ###
    if (not isinstance(obj, datetime.datetime)                        and
        not isinstance(obj, datetime.time)
    ):
        mss = mss.format(type(obj))
        raise TypeError(mss)
    return True


######
# number tests
######

def as_int_or_float(obj, mss='{}'):
    """Validate object as an int or real.
    
    If obj is bool it will not be validated!
    
    The mss will be formatted with the type of the object and send with
    the raised error.
    
    Parameters:
      obj -- an object
      mss -- a str wich may contain one format placeholder
    """
    ## TEST  OK ##
    if (isinstance(obj, bool) 
        or
        not (isinstance(obj, int) or isinstance(obj, float))):
        mss = mss.format(type(obj))
        raise TypeError(mss)
    return True

######
# collection tests
######

def as_member(obj, iterable, mss='{}'):    
    """Validate object as member of iterable, raise ValueError if not.
    
    Raises validate.ValueError. The mss will be formatted with the object
    and send with the raised error.
    
    Parameters:
      obj -- an object
      iterable -- an iterable
      mss -- a str wich may contain one format placeholder
    """
    
    ###
    ###
    if not obj in iterable:
        mss = mss.format(obj)
        raise ValueError(mss)
    return True

def as_Sized_Iterable(obj, mss='{}'):
    """Validate object as iterable with a length.
    
    Raises validate.TypeError. The mss will be formatted with the failed
    requisite.
    
    Parameters:
      obj -- an object
      mss -- a str wich may contain one format placeholder
    """
    ## TEST OK ##
    ###
    ###
    if not isinstance(obj, collections.Iterable):
        mss = mss.format('not iterable')
        raise TypeError(mss)
    if not isinstance(obj, collections.Sized):
        mss = mss.format('no length available')
        raise TypeError(mss)
    return True

def all_Keys_in_List(a_dict, validation_list, mss={}):
    """Raise error if keys in dict are not in validation list."""
    ###
    ###
    for k in a_dict.keys():
        if k not in validation_list:
            raise KeyError('Key not in validation list: {}'.format(k))
    return True

######
# file tests
######
def as_existing_file(file_name, mss='{}'):
    '''Validate abjext as existing file.
    
    Raises validate.ValueError when the file doesn't exist. The mss 
    is formatted with the object.
    
    Parameters:
      file_name -- a string as the full path to the file
      mss -- a str wich may contain one format placeholder
    '''
    ## TEST OK ##
    assert isinstance(file_name, str), 'file_name must be string'
    ###
    ###
    if not os.path.isfile(file_name):
        mss = mss.format(file_name)
        raise ValueError(mss)
    return True 