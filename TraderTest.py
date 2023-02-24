#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

import Trader

################################################################################
# test functions
################################################################################
#
# Make sure following names are defined in the dictionary you send to the 
# test functions
#
################################################################################
#
STATUS = '$STATUS_TraderTest'
# is True if trader in trade else False
################################################################################

def test_data(trader):
    # give the trader you want to run the test on
    data = {STATUS: trader.status}
    return data

def in_trade(**vars):
    return True if vars[STATUS]==Trader.IN_TRADE else False 
