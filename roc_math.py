#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import math
import itertools

from roc_settings import Error
import validate

def weighted_average(collection_of_weight_value_tuples):
    """Returns the weighted average of the (weight, value) tuples in iterable.
    
    All weights and values must be numbers.
    
    A ValueError wil be raised when:
      - iterable is empty
      - all weights are zero
      - there are negative weigths
    
    Arguments:
      collection_of_weight_value_tuples -- as named
    """
    
    validate.as_Sized_Iterable(collection_of_weight_value_tuples)
    if len(collection_of_weight_value_tuples) == 0:
        raise ValueError('tuple collection can not be empty.')
    for foo in filter(lambda w: w[0] < 0, collection_of_weight_value_tuples):
        raise ValueError('negative weights not allowed.')
    for foo in filter(lambda w: w[0] > 0, collection_of_weight_value_tuples):
        break
    else:
        raise ValueError('Not all weights can be zero')
    ###
    weightproduct = itertools.starmap(lambda a, b: a * b,
                                      collection_of_weight_value_tuples)
    p_sum = math.fsum(weightproduct)
    weights = itertools.starmap(lambda a, b: a,
                                collection_of_weight_value_tuples)
    w_sum = math.fsum(weights)
    average = p_sum / w_sum
    ###
    return average
