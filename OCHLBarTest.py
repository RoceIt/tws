#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

################################################################################
# test functions
################################################################################
#
# Make sure following names are defined in the dictionary you send to the 
# test functions
#
################################################################################
#
VALUE = '$VALUE_OCHLBarTest'
# a value
TIME = '$TIME_OCHLBarTest'
# The time of the bar
HIGH = '$HIGH_OCHLBarTest'
# The high of the bar
LOW = '$LOW_OCHLBarTest'
# The low of the bar
OPEN = '$OPEN_OCHLBarTest'
# The open of the bar
CLOSE = '$CLOSE_OCHLBarTest'
# The close of the bar
################################################################################

def test_data(ochl_bar):
    # give the bar you want to run the tests on
    data = {TIME: ochl_bar.time,
            OPEN: ochl_bar.open,
            CLOSE: ochl_bar.close,
            HIGH: ochl_bar.high,
            LOW: ochl_bar.low}
    return data

def high_higher_then(**vars):
    answer = False
    if vars[HIGH] > vars[VALUE]:
        answer = True
    return answer

def low_lower_then(**vars):
    answer = False
    if vars[LOW] < vars[VALUE]:
        answer = True
    return answer

def bar_after(**vars):
    answer = False
    if vars[TIME].time() > vars[VALUE]:
        answer = True
    return answer

def bar_before(**vars):
    answer = False
    if vars[TIME].time() < vars[VALUE]:
        answer = True
    return answer




#def high_higher_then_b(**vars):
#    answer = False
#    if vars[CURR_HIGH] > vars[VALUE]:
#        answer = True
#    return anwser
