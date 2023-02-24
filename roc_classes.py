#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import os
from time import sleep

class Blocked(Exception): pass

class FixedAttributes():
    '''Don't allow adding attributes after __init__.
    
    Call the super init function after the classes own init function
    to avoid creation of other attributes.
    
    I think this can be a good help to avoid programming errors.
    '''
    def __init__(self):
        self.__valid_attr = self.__dir__()
        
    def __setattr__(self, a, v):
        try:
            valid = a in self.__valid_attr
        except AttributeError:
            valid = True
        if valid:
            super().__setattr__(a, v)
        else:
            mss = 'FixedAttributes mode, creation of new attr not allowed:{}'
            mss.format(a)
            raise AttributeError(mss)
        
class DirLock():
    def __init__(self, name='foo', wait=True):
        self.dirname = '/tmp/dirlocks/'+name
        self.wait = wait
        
    def __str__(self):
        return 'DirLock {}'.format(self.dirname)
        
    def __enter__(self):
        while 1:
            try:
                os.makedirs(self.dirname)
                return True
            except OSError as e:
                if not self.wait:
                    raise Blocked()
            sleep(0.05)
    def __exit__(self, type, value, traceback):
        os.rmdir(self.dirname)
        
class NoLock():
    def __enter__(self):
        pass
    def __exit__(self, type, value, traceback):
        pass
