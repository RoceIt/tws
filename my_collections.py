#!/usr/bin/env python3
#
#  Copyright (c) 2012, Rolf Camps (rolf.camps@scarlet.be)

import collections

class my_dict(dict):
    
    def __setitem__(self, *vars):
        print('mydi', vars)
        super().__setitem__(*vars)

class DictArray(collections.defaultdict):
    
    def __init__(self):
        super().__init__(my_dict)
        
    def __setitem__(self, *vars):
        print('da', vars)
        super().__setitem__(*vars)
        print('da', vars)
        