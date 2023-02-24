#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import unittest
from datetime import datetime

import marketdata

class TestClassInits(unittest.TestCase):
    
    def test_DataBar_creation(self):
        ###
        time_ = datetime.now()
        open_ = 10.0
        high = 11.0
        low = 9.0
        close = 11.0
        volume = 10
        counts = 3
        wap = 10.0
        hasgaps = False
        ###
        # make sure legal input passes
        try:
            marketdata.DataBar(time_, open_, high, low, close, 
                               volume, counts, wap, hasgaps)
            marketdata.DataBar(time_, open_, high, low, close)
        except Exception as e:
            fail('Fails with legal input: {}'.format(e))
            
if __name__ == '__main__':
    unittest.main()