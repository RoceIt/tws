#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)

'''Functions on iterable instances.'''

import itertools

def abcd_2_ab_bc_cd(iterable):
    '''Make pairs of *every* consecutive combination in the iterable.'''
    ###
    a, b = itertools.tee(iterable)
    next(b, None) # advance second part 1 instance
    ###
    return zip(a, b)

def delta(iterable, absolute=False):
    '''Return an iterable with the deltas between the consecutive elements.
    
    The delta is the quantitve value of the move from the first element
    to the second.  If absolute is True is will returns the absolute  
    value of the delta.
    
    Parameters:
      iterable -- an iterable instance
      absolute -- bool, if true the absolute values of the deltas are 
                  returned
    '''
    ###
    if absolute:
        delta = lambda x, y: abs(y - x)
    else:
        delta = lambda x, y: y - x
    ###
    return itertools.starmap(delta, abcd_2_ab_bc_cd(iterable))
    