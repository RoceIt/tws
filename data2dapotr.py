#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

'''
the triad live runner, is a program to proces live from a data file, search
triads in it and send orders to a tws server
it starts 2 helper programs one to proces the incomming data and one to
manage the trading part they communicate with each other thrue a pipe
'''

import sys
import os.path
import pickle
from time import sleep
from multiprocessing import Queue

import mypy
import TWSClient
from barData import ochlBar
from simple_triad_system import get_settings, Trader, DataProcessor


def main():
    data_file = sys.argv[-1]    
    base_file = os.path.join(mypy.TMP_LOCATION, data_file)
    settings = get_settings()
    if settings:
        s = settings
        quote_data_for_trader = Queue()
        quote_data_for_data_processor = Queue()
        trader = Trader(settings=s,
                        data_feed=quote_data_for_trader)
        data_processor = DataProcessor(settings,
                                       data_feed=quote_data_for_data_processor,
                                       trader=trader)
        ioh = open(base_file, 'rb')        
        while 1:
            try:
                latest = pickle.load(ioh)
                print('latest', latest)
            except EOFError:
                latest = False
            if not latest:
                #if not os.path.isfile(SCS_running):
                #    break           
                sleep(0.2)
                continue
            curr_bar = ochlBar(latest.time_, latest.open_, latest.close, 
                               latest.high,latest.low)
            quote_data_for_data_processor.put(curr_bar)
            quote_data_for_trader.put(curr_bar)

if __name__ == '__main__':
    main()