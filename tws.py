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
import os
from collections import namedtuple
from datetime import datetime, timedelta
from time import sleep

import mypy


class Error(Exception):pass
class ContractNotInDB(Error):pass

### Standards
DATE_TIME_FORMAT_F='%Y%m%d %H:%M:%S %Z'


### Contract info
secTypes = set(['STK', 'OPT', 'FUT', 'IND', 'FOP', 'CASH', 'BAG'])
rights   = set(['P', 'PUT', 'C', 'CALL'])

contract = namedtuple('contract',
                      'symbol secType expiry strike right multiplier '+
                      'exchange currency localSymbol primaryExch '+
                      'includeExpired comboLegsDescrip comboLegs conId '+
                      'secIdType secId underComp')

 
### rhd = request historical data info
rhd_MAX_LOOKBACK = timedelta(days=365)
rhd_bar_sizes_2_timedelta = {
   '1 secs': timedelta(seconds=1),
   '5 secs': timedelta(seconds=5),
}
rhd_intraday_bar_sizes = set(['1 secs', '5 secs', '15 secs', '30 secs', '1 min', 
                              '2 mins', '3 mins', '5 mins', '15 mins', '30 mins',
                              '1 hour'])
rhd_interval_bar_sizes = set(['1 hour', '1 day', '1 week', '1 month', '3 months', 
                              '1 year'])
rhd_bar_sizes = rhd_intraday_bar_sizes | rhd_interval_bar_sizes
rhd_what_to_show = set(['TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK', 
                        'HISTORICAL_VOLATILITY', 'OPTION_IMPLIED_VOLATILITY',
                        'OPTION_VOLUME', 'OPTION_OPEN_INTEREST'])

### rtb = real time bars
rtb_bar_sizes = {'5 secs'}
rtb_what_to_show = set(['TRADES', 'MIDPOINT', 'BID', 'ASK'])

# dictionary with barvalue as key and the following values in a list
#    0: max time period to make request to tws historical with this barvalue
#    1: the python timedelta this barvalue is spanning
rhd_max_req_period = {'1 secs'  : ['1800 S', timedelta(seconds=1)],
                      '5 secs'  : ['9000 S', timedelta(seconds=5)],
                      '15 secs' : ['27000 S', timedelta(seconds=15)],
                      '30 secs' : ['54000 S', timedelta(seconds=30)],
                      '1 min'   : ['1 D', timedelta(minutes=1)],
                      '2 mins'  : ['2 D', timedelta(minutes=2)],
                      '3 mins'  : ['4 D', timedelta(minutes=3)],
                      '5 mins'  : ['6 D', timedelta(minutes=5)],
                      '15 mins' : ['2 W', timedelta(minutes=15)],
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
# 

contract = namedtuple('contract',
                      'symbol secType expiry strike right multiplier '+
                      'exchange currency localSymbol primaryExch '+
                      'includeExpired comboLegsDescrip comboLegs conId '+
                      'secIdType secId underComp')
contract_details = namedtuple('contract_details',
                              'summary marketName tradingClass minTick '
                              'priceMagnifier orderTypes validExchanges '
                              'underConId longName contractMonth industry '
                              'category subcategory timeZoneId tradingHours '
                              'liquidHours '
                              #BOND values
                              'cusip ratings descAppend bondType couponType '
                              'callable_ putable coupon convertible maturity '
                              'issueDate nextOptionDate nextOptionType '
                              'nextOptionPartial notes')
under_comp = namedtuple('under_comp',
                        'conId delta price')

 
def contract_data(contract_name):

    '''Returns the required data for the product with name <contractname>'''
    try:
        return IBcontracts[contract_name]
    except KeyError:
        raise ContractNotInDB(contract_name)

        
def def_contract(symbol='', secType='STK', expiry='', strike=0.0, right='',
                 multiplier='', exchange='', currency='USD', localSymbol='',
                 primaryExch='', includeExpired=False, comboLegsDescrip='',
                 comboLegs=0, conId=0, secIdType='', secId='', underComp=None):

    return contract(symbol, secType, expiry, strike, right, multiplier, exchange,
                    currency, localSymbol, primaryExch, includeExpired,
                    comboLegsDescrip, comboLegs, conId, secIdType, secId,
                    underComp)


def def_details(summary=def_contract(), marketName=None, tradingClass=None, 
                minTick=0, priceMagnifier=None, orderTypes=None, 
                validExchanges=None, underConId=0, longName=None, 
                contractMonth=None, industry=None, category=None,
                subcategory=None, timeZoneId=None, tradingHours=None,
                liquidHours=None, cusip=None, ratings=None, descAppend=None,
                bondType=None, couponType=None, callable_=False, putable=False,
                coupon=0, convertible=False, maturity=None, issueDate=None,
                nextOptionDate=None, nextOptionType=None, 
                nextOptionPartial=False, notes=None):

    return contract_details(summary, marketName, tradingClass, minTick,
                            priceMagnifier, orderTypes, validExchanges,
                            underConId, longName, contractMonth, industry,
                            category, subcategory, timeZoneId, tradingHours,
                            liquidHours, cusip, ratings, descAppend, bondType,
                            couponType, callable_, putable, coupon, convertible,
                            maturity, issueDate, nextOptionDate, nextOptionType,
                            nextOptionPartial, notes)


def def_under_comp(conId=0, delta=0, price=0):

    return under_comp(conId, delta, price)


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
                                                exchange    = 'FTA',
                                                primaryExch = 'FTA',
                                                localSymbol = 'AEX',
                                                currency    = 'EUR'),
               'AEX_FUT1311'     : def_contract(symbol      = 'EOE',
                                                secType     = 'FUT',
                                                multiplier  = 200,
                                                expiry      = '20131115',
                                                exchange    = 'FTA',
                                                localSymbol = 'FTIX3',
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
                                                currency    = 'KRW'),
               'euro-dollar'     : def_contract(symbol      = 'EUR',
                                                secType     = 'CASH',
                                                exchange    = 'IDEALPRO', #'SMART',
                                                primaryExch = 'IDEALPRO',
                                                localSymbol = 'EUR.USD',
                                                currency    = 'USD'),
               'DAX-30'          : def_contract(symbol      = 'DAX',
                                                secType     = 'IND',
                                                exchange    = 'DTB',
                                                primaryExch = 'DTB',
                                                localSymbol = 'DAX',
                                                currency    = 'EUR'),
               'DAX-30_FUT1312'  : def_contract(symbol      = 'DAX',
                                                secType     = 'FUT',
                                                multiplier  = 25,
                                                expiry      = '20131220',
                                                exchange    = 'DTB',
                                                #primaryExch = 'DTB',
                                                localSymbol = 'FDAX DEC 13',
                                                currency    = 'EUR'),
               'DAX-30_FUT1403'  : def_contract(symbol      = 'DAX',
                                                secType     = 'FUT',
                                                multiplier  = 25,
                                                expiry      = '20140321',
                                                exchange    = 'DTB',
                                                #primaryExch = 'DTB',
                                                localSymbol = 'FDAX MAR 14',
                                                currency    = 'EUR'),
               'DAX-30_FUT1406'  : def_contract(symbol      = 'DAX',
                                                secType     = 'FUT',
                                                multiplier  = 25,
                                                expiry      = '20140620',
                                                exchange    = 'DTB',
                                                #primaryExch = 'DTB',
                                                localSymbol = 'FDAX JUN 14',
                                                currency    = 'EUR'),
               'DAX-30_FUT1409'  : def_contract(symbol      = 'DAX',
                                                secType     = 'FUT',
                                                multiplier  = 25,
                                                expiry      = '20140919',
                                                exchange    = 'DTB',
                                                #primaryExch = 'DTB',
                                                localSymbol = 'FDAX SEP 14',
                                                currency    = 'EUR'),
               'DAX-30_FUT1412'  : def_contract(symbol      = 'DAX',
                                                secType     = 'FUT',
                                                multiplier  = 25,
                                                expiry      = '20141219',
                                                exchange    = 'DTB',
                                                #primaryExch = 'DTB',
                                                localSymbol = 'FDAX DEC 14',
                                                currency    = 'EUR'),
               'Apple'           : def_contract(symbol      = 'AAPL',
                                                exchange    = 'SMART',
                                                primaryExch = 'NASDAQ'),
               'DJ_Eurostoxx50'  : def_contract(symbol      = 'ESTX50',
                                                secType     = 'IND',
                                                exchange    = 'DTB',
                                                primaryExch = 'DTB',
                                                localSymbol = 'ESTX50',
                                                currency    = 'EUR'),
               'ESTX-50_FUT'     : def_contract(symbol      = 'ESTX50',
                                                secType     = 'FUT',
                                                expiry      = '201203',
                                                exchange    = 'SMART',
                                                primaryExch = 'DTB',
                                                currency    = 'EUR'),
               'Deutsche_bank'   : def_contract(symbol      = 'DBK',
                                                #secType     = 'STK',
                                                exchange    = 'SMART',
                                                primaryExch = 'IBIS',
                                                currency    = 'EUR'),
               'FTSE-100'        : def_contract(symbol      = 'Z',
                                                secType     = 'IND',
                                                exchange    = 'LIFFE',
                                                localSymbol = 'Z',
                                                currency    = 'GBP'),
               'FTSE_FUT1312'    : def_contract(symbol      = 'Z',
                                                secType     = 'FUT',
                                                multiplier  = 1000,
                                                expiry      = '20131220',
                                                exchange    = 'LIFFE',
                                                #primaryExch = 'DTB',
                                                localSymbol = 'ZZ3',
                                                currency    = 'GBP'),
               }

###
# Orders
###

order_settings = {'COSTUMER': 0,        
                  'FIRM': 1,         
                  'OPT_UNKNOWN': '?',       
                  'OPT_BROKER_DEALER': 'b', 
                  'OPT_CUSTOMER':'c',     
                  'OPT_FIRM': 'f',          
                  'OPT_ISEMM': 'm',         
                  'OPT_FARMM': 'n',         
                  'OPT_SPECIALIST': 'y',    
                  'AUCTION_MATCH': 1,     
                  'AUCTION_IMPROVEMENT': 2,
                  'AUCTION_TRANSPARENT': 3,
                  'EMPTY_STR': ""} 

order_attributes = ('orderId clientId permId action totalQuantity orderType '
                    'lmtPrice auxPrice tif ocaGroup ocaType orderRef transmit '
                    'parentId blockOrder sweepToFill displaySize triggerMethod '
                    'outsideRth hidden goodAfterTime goodTillDate '
                    'overridePercentageConstraints rule80A allOrNone minQty '
                    'percentOffset trailStopPrice faGroup faProfile faMethod '
                    'faPercentage openClose origin shortSaleSlot '
                    'designatedLocation discretionaryAmt eTradeOnly '
                    'firmQuoteOnly nbboPriceCap auctionStrategy startingPrice '
                    'stockRefPrice delta stockRangeLower stockRangeUpper '
                    'volatility volatilityType continuousUpdate '
                    'referencePriceType deltaNeutralOrderType '
                    'deltaNeutralAuxPrice basisPoints basisPointsType '
                    'scaleInitLevelSize scaleSubsLevelSize scalePriceIncrement '
                    'account settlingFirm clearingAccount clearingIntent '
                    'algoStrategy algoParams whatIf notHeld')
order = namedtuple('order',
                   order_attributes)
                   #'orderId clientId permId action totalQuantity orderType '
                   #'lmtPrice auxPrice tif ocaGroup ocaType orderRef transmit '
                   #'parentId blockOrder sweepToFill displaySize triggerMethod '
                   #'outsideRth hidden goodAfterTime goodTillDate '
                   #'overridePercentageConstraints rule80A allOrNone minQty '
                   #'percentOffset trailStopPrice faGroup faProfile faMethod '
                   #'faPercentage openClose origin shortSaleSlot '
                   #'designatedLocation discretionaryAmt eTradeOnly '
                   #'firmQuoteOnly nbboPriceCap auctionStrategy startingPrice '
                   #'stockRefPrice delta stockRangeLower stockRangeUpper '
                   #'volatility volatilityType continuousUpdate '
                   #'referencePriceType deltaNeutralOrderType '
                   #'deltaNeutralAuxPrice basisPoints basisPointsType '
                   #'scaleInitLevelSize scaleSubsLevelSize scalePriceIncrement '
                   #'account settlingFirm clearingAccount clearingIntent '
                   #'algoStrategy algoParams whatIf notHeld')

tagValue = namedtuple('tagValue', 'tag value')

orderState = namedtuple('orderState',
                        'status initMargin maintMargin equityWithLoan '
                        'commission minCommission maxCommission '
                        'commissionCurrency warningText')

execution = namedtuple('execution',
                       'orderId clientId execId time acctNumber exchange side '
                       'shares price permId liquidation cumQty avgPrice')

execution_filter = namedtuple('execution_filter',
                              'clientId acctCode time_ symbol secType exchange '
                              'side')


def def_order(orderId='', clientId='', permId='', action='BUY', totalQuantity=10,
              orderType='LMT', lmtPrice=0, auxPrice=0, tif='DAY', ocaGroup='',
              ocaType=0, orderRef='', transmit=True, parentId=0, blockOrder=0,
              sweepToFill=0, displaySize=0, triggerMethod=0, outsideRth=0,
              hidden=0, goodAfterTime='',  goodTillDate='', 
              overridePercentageConstraints=0, rule80A='', allOrNone=0,
              minQty='', percentOffset='', trailStopPrice='', faGroup='',
              faProfile='', faMethod='', faPercentage='', openClose='O',
              origin=order_settings['COSTUMER'], shortSaleSlot=0, 
              designatedLocation=order_settings['EMPTY_STR'], discretionaryAmt=0,
              eTradeOnly=0, firmQuoteOnly=0, nbboPriceCap='', auctionStrategy=0,
              startingPrice ='', stockRefPrice='', delta='', stockRangeLower='',
              stockRangeUpper='', volatility='', volatilityType='', 
              continuousUpdate =0, referencePriceType='',
              deltaNeutralOrderType ='', deltaNeutralAuxPrice='',
              basisPoints='', basisPointsType='', scaleInitLevelSize='',
              scaleSubsLevelSize='', scalePriceIncrement='', account='', 
              settlingFirm='', clearingAccount='', clearingIntent='',
              algoStrategy='', algoParams=None, whatIf=False, notHeld=False):

    return order(orderId, clientId, permId, action, totalQuantity, orderType, 
                 lmtPrice, auxPrice, tif, ocaGroup, ocaType, orderRef, transmit,
                 parentId, blockOrder, sweepToFill, displaySize, triggerMethod, 
                 outsideRth, hidden, goodAfterTime, goodTillDate, 
                 overridePercentageConstraints, rule80A, allOrNone, minQty, 
                 percentOffset, trailStopPrice, faGroup, faProfile, faMethod, 
                 faPercentage, openClose, origin, shortSaleSlot, 
                 designatedLocation, discretionaryAmt, eTradeOnly, 
                 firmQuoteOnly, nbboPriceCap, auctionStrategy, startingPrice, 
                 stockRefPrice, delta, stockRangeLower, stockRangeUpper, 
                 volatility, volatilityType, continuousUpdate, 
                 referencePriceType, deltaNeutralOrderType, 
                 deltaNeutralAuxPrice, basisPoints, basisPointsType, 
                 scaleInitLevelSize, scaleSubsLevelSize, scalePriceIncrement, 
                 account, settlingFirm, clearingAccount, clearingIntent, 
                 algoStrategy, algoParams, whatIf, notHeld)


def def_execution(orderId=0, clientId=0, execId=None, time_=None, 
                  acctNumber=None, exchange=None, side=None, shares=0, price=0,
                  permId=0, liquidation=0, cumQty=0, avgPrice=0):

    return execution(orderId, clientId, execId, time_, acctNumber, exchange, 
                     side, shares, price, permId, liquidation, cumQty, avgPrice)


def def_execution_filter(clientId=0, acctCode='', time_='', symbol='',
                         secType='', exchange='', side=''):

    return execution_filter(clientId, acctCode, time_, symbol, secType, 
                            exchange, side)


###
# Ristrictions
###

# Zou via een deamon moeten kunnen, send req to deamon en get answer
# als verschillende programma's er nu gebruik van maken komt men zeker
# in de problemen

def get_req_hist_slot(contract, end, barsize, max_period, whatToShow):

    reqHistoryFile =  os.path.join(mypy.VAR_LOCATION, 'tws', 'historylist.pickled')
    curr_time = datetime.now()
    discription_parameters = [str(contract),str(barsize),str(end),str(max_period),str(whatToShow)]
    req_discription = ''.join(discription_parameters)
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

class HistoricRequestLimitationsManager():
    '''Manager to handle the data limitations of the tws server
    
    Simple implementations that just waits for 2 seconds between 2
    consecutive requests and checks if there are no more than 60
    requests in 10 minutes. A much  more specific system would be
    possible if you use the contract, exchange, .. info send with the
    defined methods.
    
    
    '''
    def __init__(self):
        self.sended_requests = []
        
    def request_allowed(self, *parameters):
        print('checking request allowed')
        print(len(self.sended_requests),self.sended_requests)
        self.remove_outdated_data()
        if len(self.sended_requests) == 59:
            print('over 60 requests in 10 minutes')
            first_expired_request = self.sended_requests[0]['time']
            wait = timedelta(seconds=600)-(
                         mypy.now() - self.sended_requests[0]['time'])
            wait = wait.seconds + wait.microseconds/1000000
            wait = wait if wait > 0 else 0
            print('sleep (10 min rule) wait for {} seconds'.format(wait))
            return wait
        if len(self.sended_requests) > 0:
            sleep_for = timedelta(seconds=2)-(
                         mypy.now() - self.sended_requests[-1]['time'])
            sleep_for = sleep_for.seconds + sleep_for.microseconds/1000000
            sleep_for = sleep_for if sleep_for < 2 else 0
            print('going to sleep for {}'.format(sleep_for))
            sleep(sleep_for)
        return True
    
    def request_sended(self, *parameters):
        self.sended_requests.append(
            {'time': mypy.now()})
        
    def remove_outdated_data(self):
        while len(self.sended_requests):
            gap = mypy.now() - self.sended_requests[0]['time']
            if gap > timedelta(seconds=600):
                self.sended_requests.pop(0)
                print('removing outdated request')
            else:
                break
                
        

###############################################################################
#
# SELF CREATED THINGS: NOT DIRECTLY IMPLEMENTED IN API
#
###############################################################################

bracket_order = namedtuple('bracket_order',
                            'number_of_contracts direction '
                            'enter_type enter_limit enter_aux '
                            'profit_type profit_limit profit_aux '
                            'stop_type stop_limit stop_aux '
                            'enter_trade_before EOD_sell')

def def_bracket_order(number_of_contracts=0, direction='BULL',
                      enter_type='MKT', enter_limit=0, enter_aux=0,
                      profit_type='LMT', profit_limit=0, profit_aux=0,
                      stop_type='STP', stop_limit=0, stop_aux=0,
                      enter_trade_before=None, 
                      EOD_sell=False):
    
    return bracket_order(number_of_contracts, direction,
                         enter_type, enter_limit, enter_aux,
                         profit_type, profit_limit, profit_aux,
                         stop_type, stop_limit, stop_aux,
                         enter_trade_before,
                         EOD_sell)

def change_order(orig_order, **changes):

    atrr_list = order_attributes.split(' ')
    order_values = list(orig_order)
    for attr, new_value in changes.items():
        attr_index = atrr_list.index(attr)
        order_values[attr_index] = new_value
    return order(*order_values)

################################################################################
#
# USEFULL IN OTHER PROGRAMMES
#
################################################################################

def get_contract_name(message=None, empty=False):
    '''reads a name and checks if it is a valid contract name'''
    if not message:
        message = 'contract name: '
    while 1:
        name = mypy.get_string(message, empty=empty)
        if (name in IBcontracts.keys()
            or
            (name == '' and empty)):
            break
        print('unknown contract name')
    return name
    