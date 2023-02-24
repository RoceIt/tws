#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

class MovingAverage(list):
    def __init__(self, periods):
        super().__init__()
        self.periods = periods
        
    def append(self, value):
        super().append(value)
        if len(self) > self.periods:
            self.pop(0)        
        if len(self) == self.periods:
            return sum(self)/self.periods
        else:
            return None