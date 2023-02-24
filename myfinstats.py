#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import math

import mypy

def continues_comp_rate(start_value=None, end_value=None, list_of_values=None):
    '''calcutates the continues compounded rate (ccr)
    
    if start and end value are given, the ccr for this movement
    if a list is of n ell is given, a list of n-1 ell is returned with the
    ccr's between the ell(n-1) and ell(n)
    '''
    
    mess = 'Start and end value or a list of values, not both!'
    assert (((start_value and end_value) and not list_of_values )
            or
            (not start_value and not end_value and list_of_values)), mess
    ccr = lambda a,b: math.log(b / a)
    if start_value and end_value:
        return ccr(start_value, end_value)
    elif list_of_values:
        rate_list = []
        start_quote = list_of_values[0]
        for end_quote in list_of_values[1:]:
            rate_list.append(ccr(start_quote, end_quote))
            start_quote = end_quote
        return rate_list
            

def hist_variance_of_stock_market_returns(quotes=None, returns=None):
    
    mess = 'You can only give quotes or returns! Not both'
    assert not (quotes and returns), mess
    if quotes:
        returns = continues_comp_rate(list_of_values=quotes)
    aar = mypy.mean(returns) #arithmatic_average_returns
    qsum = math.fsum([(r - aar) ** 2 for r in returns])
    hist_var = qsum / (len(returns) -1)
    return hist_var
        