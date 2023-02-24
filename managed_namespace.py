#!/usr/bin/env python3
#
#  Copyright (c) 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)


"""Module with classes for thread safe property handling.

These functions give you more control and info over the properties you 
use in threading code.  log_parent, log_to and log_lvl parameters can be 
used  to control the logging.
  
Exceptions
  ManagedNamespaceError --> general exception
  
Classes
  ManagedNamespace --> thread safe namespace with extra features
  DictWithAccessedFlag --> a dict that reports if a key has been accessed
  
"""


import threading
import logging
import os.path

from mypy import LOG_LOCATION as log_dir


__ALL__ = ['ManagedNamespaceError', 'ManagedNamespace', 'DictWithAccessedFlag']


class ManagedNamespaceError(Exception):pass


class ManagedNamespace():
    
    """A class you can use as namespace.
    
    All attributes you create in this namespace are set and removed with
    locks.  There are methods implemented to create, use and remove 
    locks and conditions from the namespace.  If you want to call
    different methods as 1 action use the 'with atomic_action:'
    statement.  __setattr__ and __delattr__ are defined so you can
    create and remove attributes.  log_parent, log_to and log_lvl can be
    set at intialisation.
    
    Methods
      add_condition --> add condition to namespace
      remove_condition --> remove condition from namespace
      has_condition --> test if condition exists in namespace
      condition --> the condition
      add_lock --> add lock to namespace
      remove_lock --> remove lock from namespace
      has_lock --> test if lock exists in namespace
      lock --> the lock
      
    Properies:
      atomic_action --> lock to hijack the namespace      
    
    """
    
    __name_space_lock = threading.Lock()
    __atomic_action = threading.Lock()
    
    def __init__(self, log_parent='', log_to='FILE', log_lvl=logging.DEBUG):
        """Initialise the Namespace.
        
        Check 'ROCE_logging' docs for logging parameters.
        
        """
        self.__reserved_names = dir(self)
        self.__logger = _logger(log_parent, 'namespace', log_to, log_lvl)
        self.__condition = dict()
        self.__lock = dict()
        self.__logger.info('Initialised namespace')
    
    def __setattr__(self, name, value):
        # Creating the self.name attribute.
        if not name == '_ManagedNamespace__reserved_names':
            if name in self.__reserved_names:
                mess = 'trying to assign to reserved keyword {}'.format(name)
                self.__logger.error(mess)
                raise ManagedNamespaceError(mess) 
        with self.__name_space_lock:
            new_attribute = not name in self.__dict__
            self.__dict__[name] = value
        if hasattr(self, '_ManagedNamespace__logger'):
            if new_attribute:
                self.__logger.info('new attribute: {}'.format(name))
            self.__logger.debug('{} <-- {}|{}'.format(name, type(value), value))
           
    def __delatrr__(self, name):
        # Remove the self.name atribute
        with self.__name_space_lock:
            if name in self.__dict__:
                del(self.__dict__[name])
                existing_name = True
            else:
                existing_name = False            
        if not existing_name:
            mess = 'Tried to remove non existing attribute {}'.format(name)
            self.__logger.warning(mess)
        else:
            self.__logger.info('removed attribute: {}'.format(name))
        return existing_name
    
    def add_condition(self, *name):
        """Add condition name to namespace.
        
        The name can be defined by more than one parameter, make sure
        they are all hashable.  This method creates a named 
        threading.condition which you can use in your code by using the
        classes condition method.
        
        """
        with self.__name_space_lock:
            if name in self.__condition:
                mess = '{} already used as condition'.format(name)
                self.__logger.error(mess)
                raise ManagedNamespaceError(mess)
            self.__condition[name] = threading.Condition()
            self.__logger.info('new condition: {}'.format(name))
            
    def remove_condition(self, *name):
        """Remove the condition name from the namespace."""
        with self.__name_space_lock:
            if name in self.__condition:                
                self.__condition.pop(name)
                condition_exists = True
            else:
                condition_exists = False
            if not condition_exists:    
                mess = 'Tried to remove non existing attribute {}'.format(name)
                self.__logger.warning(mess)
            else:
                self.__logger.info('removed condition: {}'.format(name))
            return condition_exists
            
    def has_condition(self, *name):
        """Test if condition name exists in namespace."""
        with self.__name_space_lock:
            return name in self.__condition
            
    def condition(self, *name):
        """The requested condition."""
        with self.__name_space_lock:
            if not name in self.__condition:
                mess = 'unknown condition: {}'.format(name)
                self.__logger.error(mess)
                raise ManagedNamespaceError(
                    '{} unknown condition'.format(name))
            return self.__condition[name]
        
    def add_lock(self, *name):
        """Add lock name to namespace.
        
        The name can be defined by more than one parameter, make sure
        they are all hashable.  This method creates a named 
        threading.lock which you can use in your code by using the
        classes lock method.
        
        """
        with self.__name_space_lock:
            if name in self.__lock:
                mess = '{} already used as lock'.format(name)
                self.__logger.error(mess)
                raise ManagedNamespaceError(mess)
            self.__lock[name] = threading.Lock()
            self.__logger.info('new lock: {}'.format(name))
            
    def remove_lock(self, *name):
        """Remove the lock name from the namespace."""
        with self.__name_space_lock:
            if name in self.__lock:              
                self.__lock.pop(name)
                lock_exists = True
            else:
                lock_exists = False
            if not lock_exists:
                mess = 'Tried to remove non existing lock {}'.format(name)
                self.__logger.warning(mess)
            else:
                self.__logger.info('removed lock: {}'.format(name))
            return lock_exists
            
    def has_lock(self, *name):
        """Test if lock name exists in namespace."""
        with self.__name_space_lock:
            return name in self.__lock
            
    def lock(self, *name):
        """The requested lock."""
        with self.__name_space_lock:
            if not name in self.__lock:
                raise ManagedNamespaceError(
                    '{} unknown lock'.format(name))
            return self.__lock[name]
    
    @property
    def atomic_action(self):
        """Lock to hijack the namespace."""
        return self.__atomic_action
    
    
class DictWithAccessedFlag(dict):  

    def __setitem__(self, k, v):
        flagged_value = (v, False)
        super().__setitem__(k, flagged_value)
        
    def __getitem__(self, k):
        value, flagged = super().__getitem__(k)
        if not flagged:
            flagged_value = (value, True)
            super().__setitem__(k, flagged_value)
        return value
    
    def key_used_for_reading(self, k):        
        value, flagged = super().__getitem__(k)
        return flagged
 
    
def _logger(parent_name, local_log_name, log_to, log_lvl):
    # Check 'ROCE_logging' docs for logging parameters.
    log_name = '.'.join([parent_name, local_log_name]).lstrip('.')
    logger = logging.getLogger(log_name)
    logger.setLevel(log_lvl)
    if parent_name:
        return logger
    formatter = logging.Formatter('%(levelname)s %(name)s: %(message)s')
    handler_list = []
    if log_to == 'STDERR':
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(formatter)
        handler_list.append(handler)
    elif log_to == 'FILE':
        log_file = os.path.join(log_dir, log_name)
        handler = logging.FileHandler(log_file, mode='a')
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)
        handler_list.append(handler)
        if log_lvl == logging.DEBUG:
            log_file = '.'.join([log_file, 'DEBUG'])
            handler = logging.FileHandler(log_file, mode='a')
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            handler_list.append(handler)        
    else:
        logger.propagate = False
        handler = logging.NullHandler()
        handler_list.append(handler)
    for handler in handler_list:
        logger.addHandler(handler)
    return logger