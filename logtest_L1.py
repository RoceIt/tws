#!/usr/bin/env python3
#
#  Copyright (c) 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)import logging
import os.path
import sys
import logging

from mypy import LOG_LOCATION as log_dir

_LOG_LEVEL_NAME = 'test2'
add_local_log_level = lambda parent: '.'.join([parent, _LOG_LEVEL_NAME])

def _logger(parent_name, log_to):
    log_name = '.'.join([parent_name, _LOG_LEVEL_NAME]).lstrip('.')
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)
    if log_to == 'STDERR':
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
    elif log_to == 'FILE':
        log_file = os.path.join(log_dir, log_name)
        print('logfile: ', log_file)
        handler = logging.FileHandler(log_file, mode='w')
        handler.setLevel(logging.DEBUG)
    else:
        logger.propagate = False
        handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger

def do_iet(parent_name, log_to):
    lo = _logger(parent_name, log_to)
    
    lo.debug('test2 debug')
    lo.error('test2 error')
    
