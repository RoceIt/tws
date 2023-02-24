#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.

import os.path
import pickle
import mypy
import barData
import corse
from time import sleep, localtime, strftime


def main():
    corse_watcher_pickle_base_name = 'AEX-index_TRADES_5_secs_1800s'
    corse_watcher_pickle_full_name = corse_watcher_pickle_base_name+'.corse'
    corse_watcher_pickle_bull_corse_name = corse_watcher_pickle_base_name + '.bull'
    corse_watcher_pickle_bear_corse_name = corse_watcher_pickle_base_name + '.bear'

    if os.path.isfile(corse_watcher_pickle_full_name):
        print('loading corse_watcher instance')
        with open(corse_watcher_pickle_full_name,'rb') as ifh:
            cwh = pickle.load(ifh)
    else:
        cwh = corse_watcher('s', 1800)
    base_file  = mypy.tmplocation+'indu5s.data'
    column     = mypy.ColumnName('IBdata')
    ioh = open(base_file, 'r')
    try:
        while 1:
            latest = ioh.readline().split()
            if not latest:
                sleep(0.5)
                continue
        #print(strftime(mypy.stdTimeStr, localtime(int(latest[column.time]))), 
        #       float(latest[column.wap]))
            try:
                theTime = mypy.epoch2date_time(float(latest[column.time]))
                #quote   = float(latest[column.wap])
                bar_open = float(latest[column.open])
                bar_low = float(latest[column.low])
                bar_high = float(latest[column.high])
                bar_close = float(latest[column.close])
            except (ValueError, IndexError) as err:
                continue
            if cwh.insert(theTime, bar_open, bar_close, bar_high, bar_low,
                          verbose=True):
                cwh.exportCorses(corse_watcher_pickle_bull_corse_name,
                                 corse_watcher_pickle_bear_corse_name)
                ###
                # Uncomment the following lines to pause this program for testing
                #print('If you can read this, call the programmer he/she should qoute out the next line')
                #sleep(10)
    except KeyboardInterrupt:
        print('clean exit, writing corse_watcher to file')
        cwh.write_to_file(corse_watcher_pickle_full_name)
        if cwh.insert_curr_bar():
            print('corses for tomorrow already available')
            cwh.exportCorses(corse_watcher_pickle_bull_corse_name,
                             corse_watcher_pickle_bear_corse_name)
                      

class corse_watcher():
    '''This class manages the required steps to convert (time, quote) data
    to corse signals.
    If first sends it data to a ochl (open, close, high, low) class. Next comes
    the redecur and finally the corse gets the reducer output.
    '''
    def __init__(self, ochl_unit, ochl_number_of_units):
        self.bar_list = barData.ochl(ochl_unit, ochl_number_of_units)
        self.reducer = barData.reducer()
        self.corse = corse.corse()
    def insert(self, curr_time, curr_open, curr_close, curr_high, curr_low, verbose=False):
        '''Here the data gets processed. This function returns True if the corse
        was changed, else False'''
        corse_changed = False
        if self.bar_list.insert(curr_time, curr_open, curr_close, curr_high, curr_low)[1]:
            if self.bar_list.last_finished_bar():
                if verbose:
                    print('new bar started. Last bar:', self.bar_list.last_finished_bar())
                if self.reducer.insert(self.bar_list.last_finished_bar()):
                    print(self.reducer.last_extreme())
                    self.corse.insert(self.reducer.last_extreme())
                    corse_changed = True
        return corse_changed

    def insert_curr_bar(self):
        '''This function inserts the last bar in the the ochl list, 
        use at own risk, may corrupt the corse_watcher'''
        corse_changed = False
        if self.reducer.insert(self.bar_list.curr_bar()):
            #print(self.reducer.last_extreme())
            self.corse.insert(self.reducer.last_extreme())
            corse_changed = True
        return corse_changed

    def info(self, search_for):
        '''Function will return the info you ask for'''
        if search_for == 'datetime_curr_bar':
            answer = self.bar_list.curr_bar().time
        else:
            print('corse_watcher.corse_watcher.info: unknown value for search_for')
            answer = None
        return answer

    def exportCorses(self, bullName, bearName):
        self.corse.pickle_corses(bullName,bearName)

    def write_to_file(self, corse_watcher_name):
        with open(corse_watcher_name, 'wb') as ofh:
            pickle.dump(self, ofh)
                    
if __name__ == '__main__':
    main()
            
        
