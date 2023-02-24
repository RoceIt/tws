#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from trader import *

class virtual_market():
    pass

class TheoreticalTrader(Trader): 
    """work in action"""    
    
    def __init__(self,
            stoploss_handler='kiss',
            profit_handler='kiss',
        ):
        self.stoploss_handler = stoploss_handler
        self.profit_handler = profit_handler
        super().__init__()
        

class TheoreticalSinglePositionTrader(TheoreticalTrader):   
    """work in action"""    
    
    def __init__(self,
            stoploss_handler='kiss',
            profit_handler='kiss',
            trailing_exit=False, start_trailing_at=0,
            fix_exit=False, fix_at=0,
            max_gap_to_curr=False, max_gap=0,
            min_gap_to_curr=False, min_gap=0,
            cap_stop=False, cap=0,
        ):
        self.positions = []