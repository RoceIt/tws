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
ABC_A = '$ABC_A'
# A value if the corse
CURR_HIGH = '$CURR_MAX'
# The max of the current bar
CURR_LOW = '$CURR_MIN'
# The min of the current bar
################################################################################


def high_higher_then_a(**vars):
    answer = False
    if vars[CURR_HIGH] > vars[ABC_A]:
        answer = True
    return answer

def low_lower_then_c(**vars):
    answer = False
    if vars[CURR_LOW] < vars[ABC_C]:
        answer = True
    return answer

def high_higher_then_b(**vars):
    answer = False
    if vars[CURR_HIGH] > vars[ABC_B]:
        answer = True
    return anwser
