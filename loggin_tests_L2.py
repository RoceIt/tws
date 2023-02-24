#!/usr/bin/env python3
import sys
import os.path
from time import sleep
import logging
import loggin_tests
from mypy import LOG_LOCATION as log_dir

_LOG_LEVEL_NAME = 'abase'
curr_log_name = lambda x: '.'.join([x, _LOG_LEVEL_NAME])

#ml = logging.getLogger('een.twee.drie')
#ml.setLevel(logging.CRITICAL)
#lw = logging.FileHandler('t_l2.log')
#lw.setLevel(logging.NOTSET)
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#lw.setFormatter(formatter)
#ml.addHandler(lw)

#ml.debug('mess')
#ml.error('err mess')

def _logger(parent_name, log_to):
    log_name = '.'.join([parent_name, _LOG_LEVEL_NAME]).lstrip('.')
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    if log_to == 'STDERR':
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
    elif log_to == 'FILE':
        log_file = os.path.join(log_dir, log_name)
        handler = logging.FileHandler(log_file, mode='w')
        handler.setLevel(logging.INFO)
    else:
        logger.propagate = False
        handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger

if __name__ == '__main__':
    p_name = sys.argv[1]
    log_to = sys.argv[2]
    
    ml = _logger(p_name, log_to)
    loggin_tests.log_something(curr_log_name(p_name), log_to)
    
    ml.debug('mess 2')
    ml.error('err mess 2')