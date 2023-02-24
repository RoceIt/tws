#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import decimal as dcm

from roc_settings import Error

Decimal = dcm.Decimal
ROUND_DOWN = dcm.ROUND_DOWN
ROUND_UP = dcm.ROUND_UP

def round_to_nearest(dcm_base, dcm_round_to, rounding):
    round_to = dcm.Decimal(str(dcm_round_to))
    base = dcm_base.quantize(round_to, rounding=rounding)
    if base% round_to == 0:
        return base
    if rounding == dcm.ROUND_DOWN:
        return int(base/round_to) * round_to
    if rounding == dcm.ROUND_UP:
        m = int(base/round_to)
        m = m + (1 if m > 1 else -1)
        return m * round_to
    raise Error('unknown rounding: {}'.format(rounding))

        
    
