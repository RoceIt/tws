#!/usr/bin/env python3
import sys
import os.path
from time import sleep
import logging
from mypy import LOG_LOCATION as log_dir

_LOG_LEVEL_NAME = 't_log'
    
def _logger(parent_name, log_to):
    log_name = '.'.join([parent_name, _LOG_LEVEL_NAME]).lstrip('.')
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    if log_to == 'STDERR':
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
    elif log_to == 'FILE':
        log_file = os.path.join(log_dir, log_name)
        handler = logging.FileHandler(log_file, mode='w')
        handler.setLevel(logging.DEBUG)
    else:
        logger.propagate = False
        handler = logging.NullHandler()
    logger.addHandler(handler)
    return logger

#ml = logging.getLogger('een')
#ml.setLevel(logging.DEBUG)
#lw = logging.FileHandler('t_log.log', mode='a')
#lw.setLevel(logging.ERROR)
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#lw.setFormatter(formatter)
#ml.addHandler(lw)

def log_something(parent_name, log_to):
    ml = _logger(parent_name, log_to)    
    ml.debug('mess 1')
    ml.error('err mess 1')
    


if __name__ == '__main__':
    p_name = sys.argv[1]
    log_to = sys.argv[2]
    ml = _logger(p_name, log_to)
    ml.debug('mess')
    ml.error('err mess')



