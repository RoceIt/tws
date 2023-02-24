#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)
#
#  license: GNU GPLv3
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.

import pickle
import mypy
import os
from collections import namedtuple
from datetime import datetime, timedelta
from time import sleep


###
# definitions
###

### Contract
secTypes = set(['STK', 'OPT', 'FUT', 'IND', 'FOP', 'CASH', 'BAG'])
rights   = set(['P', 'PUT', 'C', 'CALL'])

contract = namedtuple('contract',
                      'symbol secType expiry strike right multiplier '+
                      'exchange currency localSymbol primaryExch '+
                      'includeExpired comboLegsDescrip comboLegs conId')


### reqHistoricalData

rhd_intraday_bar_sizes = set(['1 secs', '5 secs', '15 secs', '30 secs', '1 min', 
                              '2 mins', '3 mins', '5 mins', '15 mins', '30 mins',
                              '1 hour'])
rhd_interval_bar_sizes = set(['1 hour', '1 day', '1 week', '1 month', '3 months', 
                              '1 year'])
rhd_bar_sizes = rhd_intraday_bar_sizes | rhd_interval_bar_sizes
rhd_what_to_show = set(['TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK', 
                        'HISTORICAL_VOLATILITY', 'OPTION_IMPLIED_VOLATILITY',
                        'OPTION_VOLUME'])

rhd_max_req_period = {'1 secs'  : ['1800 S', timedelta(seconds=1)],
                      '5 secs'  : ['9000 S', timedelta(seconds=5)],
                      '15 secs' : ['27000 S', timedelta(seconds=15)],
                      '30 secs' : ['54000 S', timedelta(seconds=30)],
                      '1 min'   : ['1 D', timedelta(minutes=1)],
                      '2 mins'  : ['2 D', timedelta(minutes=2)],
                      '3 mins'  : ['4 D', timedelta(minutes=3)],
                      '5 mins'  : ['6 D', timedelta(minutes=5)],
                      '15 mins' : ['20D', timedelta(minutes=15)],
                      '30 mins' : ['4 W', timedelta(minutes=30)],
                      '1 hour'  : ['4 W', timedelta(minutes=60)],
                      '1 day'   : ['1 Y', timedelta(days=1)], 
                      '1 week'  : ['1 Y', timedelta(days=7)],
                      '1 month' : ['1 Y', timedelta(days=28)],
                      '3 months': ['1 Y', timedelta(days=89)],
                      '1 year'  : ['1 Y', timedelta(days=365)]}

###
# Contracts
###

# Zou automatisch via db of zo moeten kunnen en dan met functies contracten toevoegen
# en verwijderen van db.

def def_contract(symbol='', secType='STK', expiry='', strike=0.0, right='',
                 multiplier='', exchange='', currency='USD', localSymbol='',
                 primaryExch='', includeExpired=False, comboLegsDescrip='',
                 comboLegs=0, conId=0):
    return contract(symbol, secType, expiry, strike, right, multiplier, exchange,
                    currency, localSymbol, primaryExch, includeExpired,
                    comboLegsDescrip, comboLegs, conId)


IBcontracts = {'GC_FUT_JUNE_2010': def_contract(symbol      = 'GC', 
                                                secType     = 'FUT',
                                                primaryExch = 'NYMEX',
                                                expiry      = '201006',
                                                currency    = 'USD'),
               'GC_FUT_AUG_2010' : def_contract(symbol      = 'GC', 
                                                secType     = 'FUT',
                                                primaryExch = 'NYMEX',
                                                expiry      = '201008',
                                                currency    = 'USD'),
               'AEX-index'       : def_contract(symbol      = 'EOE',
                                                secType     = 'IND',
                                                primaryExch = 'FTA',
                                                currency    = 'EUR'),
               'DJ_Industrial'   : def_contract(symbol      = 'INDU',
                                                secType     = 'IND',
                                                primaryExch = 'NYSE'),
               'Nasdaq_100'      : def_contract(symbol      = 'NDX',
                                                secType     = 'IND',
                                                primaryExch = 'NASDAQ'),
               'S&P_500'         : def_contract(symbol      = 'SPX',
                                                secType     = 'IND',
                                                primaryExch = 'CBOE'),
               'S&P_ASX_200'     : def_contract(symbol      = 'SPI',
                                                secType     = 'IND',
                                                primaryExch = 'SNFE',
                                                currency    = 'AUD'),
               'KOSPI_200'       : def_contract(symbol      = 'K200',
                                                secType     = 'IND',
                                                primaryExch = 'KSE',
                                                currency    = 'KRW')}


###
# Ristrictions
###

# Zou via een deamon moeten kunnen, send req to deamon en get answer
# als verschillende programma's er nu gebruik van maken komt men zeker
# in de problemen

def get_req_hist_slot(contract, end, barsize, max_period, whatToShow):
    reqHistoryFile =  mypy.varlocation+'tws/historylist.pickled'
    curr_time = datetime.now()
    req_discription = str(contract)+str(barsize)+str(end)+str(max_period)+str(whatToShow)
    if not os.path.exists(reqHistoryFile):
        historyList = []
    else:
        fh = open(reqHistoryFile, 'rb')
        historyList = pickle.load(fh)
        fh.close()
    historyList = [x for x in historyList if x[0] + timedelta(minutes=10) > curr_time]
    messageSend = False
    while len(historyList) > 60:
        historyList = [x for x in historyList if x[0] + timedelta(minutes=10) > curr_time]
        if message:
            print('Meer dan 60 verzoeken de laatste 10 minuten, wacht op slot')
            messageSent = True
        sleep(1)
    for a_time, a_discr in historyList:
        if (a_discr == req_discription) and (curr_time - a_time < timedelta(seconds = 15)):
            print('zelfde verzoek binnen 15 seconden, even wachten')
            sleep(15)
        try:
            a_discr.index(str(contract)+str(barsize))
            sleep(0.4)
        except ValueError:
            pass
    historyList.append((curr_time, req_discription))
    fh = open(reqHistoryFile, 'wb')
    pickle.dump(historyList, fh)
    fh.close()

    return 1  # zou eventueel een id kunnen meegeven om verschillende simultane req te behandelen
