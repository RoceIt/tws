#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)


import os.path

import mypy
import EvalTAW

def main():
    name = mypy.get_string('Basename of batch? ')
    time_frame_unit = mypy.get_string('Timeframe unit(s): ',
                                      max_length=1, default='s')
    number_of_units_start = mypy.get_int('Number of units start (600) : ',
                                         minimum=1,
                                         default=600)
    number_of_units_stop = mypy.get_int('Number of units stop (600): ',
                                        minimum=number_of_units_start,
                                        default = 600)
    number_of_units_stop += 1
    number_of_units_step = mypy.get_int('Number of units stepsize (1): ', 
                                        default=1)
    strategy_name = mypy.get_string('Strategie name (tbes)', default = 'tbes')

    lbp_start = mypy.get_int('Limit B to percentage start (0 is off): ',
                             minimum=0, maximum=100,
                             default=0)
    if not lbp_start == 0:
        lbp_stop = mypy.get_int('Limit B to percentage stop: ',
                                minimum=lbp_start, maximum=100,
                                default=100)
        lbp_step = mypy.get_int('Limit B to percentage step (1): ',
                                minimum=1, maximum=100, default=1)
    else:
        lbp_stop = lbp_step = '*'

    ms_start = mypy.get_int('Nominal maximal stop start (0 is off): ',
                            default=0)
    if not ms_start == 0:
        mess = 'Nominal maximal stop stop ({}): '.format(ms_start)
        ms_stop = mypy.get_int(mess, minimum=ms_start, default=ms_start)
        info = mypy.get_bool('Is stepsize smaller then 1 (N)', default = False)
        if info == True:
            ms_step_num = mypy.get_int('numinator maximal stop step (1): ',
                                      minimum=1, default=1)
            ms_step_nom = mypy.get_int('nominator maximal stop step (1): ',
                                      minimum=1, default=1)
        else:
            ms_step_num = ms_step_nom = 1
    else:
        ms_stop = ms_step_num = ms_step_nom = '*'

    eod_regime = mypy.get_string('End of day regime (capda): ', default='capda')
    eval_batch_2_csv(name, time_frame_unit, number_of_units_start,
                     number_of_units_stop,  number_of_units_step, strategy_name,
                     lbp_start, lbp_stop, lbp_step, ms_start, ms_stop,
                     ms_step_num, ms_step_nom, eod_regime)


def eval_batch_2_csv(name, time_frame_unit, 
                     number_of_units_start, number_of_units_stop,
                     number_of_units_step, 
                     strategy_name,
                     lbp_start, lbp_stop, lbp_step, 
                     ms_start, ms_stop, ms_step_num, ms_step_nom,
                     eod_regime,
                     outputfile=None):

    def search_for_existing_filenames():
        timeframes = range(number_of_units_start,
                           number_of_units_stop,
                           number_of_units_step)
        lbp_range = range(lbp_start, lbp_stop, lbp_step)
        
        for number_of_timeframes in
    
    filenames = search_existing_filenames()
    for filename in filenames:
        print(filename)

    pass

if __name__ == '__main__':
    main()
