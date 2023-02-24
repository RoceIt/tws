#!/usr/bin/env python3
#
#  Copyright (c) 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)import logging
import os.path
import sys
import logging
from logtest_L1 import do_iet

from mypy import LOG_LOCATION as log_dir

_LOG_LEVEL_NAME = 'test'

def _logger(parent_name, log_to):
    print('making logger for {}|{}'.format(parent_name, log_to))
    log_name = '.'.join([parent_name, _LOG_LEVEL_NAME]).lstrip('.')
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    if log_to == 'STDERR':
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
    elif log_to == 'FILE':
        log_file = os.path.join(log_dir, log_name)
        print('logfile: ', log_file)
        handler = logging.FileHandler(log_file+'.debug', mode='w')
        handler.setLevel(logging.DEBUG)
        handler2 = logging.FileHandler(log_file, mode='w')
        handler2.setLevel(logging.INFO)
        logger.addHandler(handler2)
    else:
        logger.propagate = False
        handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger

if __name__ == '__main__':
    parent_name = sys.argv[1]
    log_to = sys.argv[2]
    my_log_name = '.'.join([parent_name, _LOG_LEVEL_NAME]).lstrip('.')
    lo = _logger(parent_name, log_to)
    do_iet(my_log_name, log_to)
    
    lo.debug('test1 debug')
    lo.error('test1 error')
    
    