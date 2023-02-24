#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)
#


"""
This is "myR" module

This module provides standard tools for creating R files
and accessing tws api via R
"""

from collections import namedtuple
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile

import tws
import mypy


_TWS_CONNECTION_NAME = 'tws'
_tws_connection = namedtuple('_tws_connection',
                            'clientId host port verbose timeout filename')

STD_TWS_CONNECTION = _tws_connection(1, '"localhost"', 7496, 'TRUE', 5, 'NULL')


class _TWSContract():
    def __init__(self,
                 conId,
                 symbol, sectype, exch, primary,
                 expiry, strike,
                 currency,
                 right,
                 local,
                 multiplier,
                 combo_legs_desc, comboleg,
                 include_expired):
        self.conId = conId
        self.symbol = symbol
        self.sectype = sectype
        self.exch = exch
        self.primary = primary
        self.expiry = expiry
        self.strike = strike
        self.currency = currency
        self.right = right
        self.local = local
        self.multiplier = multiplier
        self.combo_legs_desc = combo_legs_desc
        self.comboleg = comboleg
        self.include_expired = include_expired
    def __str__(self):
        '''Definieer de contractparameters'''
        resp = ('conId = {0.conId} \nsymbol = {0.symbol} \n'
                'sectype = {0.sectype} \nexch = {0.exch} \n'
                'primary = {0.primary} \nexpiry = {0.expiry} \n'
                'strike = {0.strike} \ncurrency = {0.currency} \n'
                'right = {0.right} \nlocal = {0.local} \n'
                'multiplier = {0.multiplier} \n'
                'combo_legs_desc = {0.combo_legs_desc} \n'
                'comboleg = {0.comboleg} \n'
                'include_expired = {0.include_expired}')
        return resp.format(self)
    def to_variable(self, name):
        '''Geeft R commando om variabele 'name' in te stellen als contract'''
        resp = ('{0} <- twsContract({1.conId}, "{1.symbol}", "{1.sectype}", '
                '"{1.exch}", "{1.primary}", "{1.expiry}", "{1.strike}", '
                '"{1.currency}", "{1.right}", "{1.local}", "{1.multiplier}", '
                '{1.combo_legs_desc}, {1.comboleg}, "{1.include_expired}")')
        return resp.format(name, self)


class _TWSFuture(_TWSContract):
    def __init__(self,
                 symbol, exch, expiry,
                 primary = '',
                 currency = 'USD',
                 right = '',
                 local = '',
                 multiplier = '',
                 include_expired = '0',
                 conId = 0):
        super().__init__(conId,
                         symbol, 'FUT', exch, primary,
                         expiry, '0.0', 
                         currency,
                         right,
                         local,
                         multiplier,
                         'NULL', 'NULL',
                         include_expired)

def _wrap(text):
    '''removes aanhalingstekens from text and ads new one around'''
    text = str(text)
    return '"'+text.strip('\'"')+'"'


def set_tws_connection(clientId = STD_TWS_CONNECTION.clientId,
                       host     = STD_TWS_CONNECTION.host,
                       port     = STD_TWS_CONNECTION.port,
                       verbose  = STD_TWS_CONNECTION.verbose,
                       timeout  = STD_TWS_CONNECTION.timeout,
                       filename = STD_TWS_CONNECTION.filename):
    if filename != 'NULL':
        filename = _wrap(filename)
    return _tws_connection(clientId, _wrap(host), port, verbose, timeout, filename)



def _set_contract(ib_contract):
    '''returns a twsR contract from IBContract, eventually asks for xtra info'''
    if ib_contract.secType == 'FUT':
        if not ib_contract.symbol or not ib_contract.primaryExch or not ib_contract.expiry:
            print('Te weinig gegevens om contract te maken, voor een Future:')
            print('symbol, primary exchange, expiry')
            raise(TypeError)
        exch = ib_contract.primaryExch if not ib_contract.exchange else ib_contract.exchange
        strike = _wrap(ib_contract.strike)
        return _TWSFuture(ib_contract.symbol, exch, ib_contract.expiry, ib_contract.primaryExch,
                         ib_contract.currency, ib_contract.right, ib_contract.localSymbol,
                         ib_contract.multiplier, '0' if not ib_contract.includeExpired else '1',
                         ib_contract.conId)
    elif ib_contract.secType == 'IND' or ib_contract.secType == 'STK':
        if not ib_contract.symbol or not ib_contract.primaryExch:
            print('Te weinig gegevens om contract te maken, voor een Future:')
            print('symbol, primary exchange, expiry')
            raise(TypeError)
        exch = ib_contract.primaryExch if not ib_contract.exchange else ib_contract.exchange
        strike = _wrap(ib_contract.strike)
        return _TWSContract(ib_contract.conId, ib_contract.symbol, ib_contract.secType,
                           exch, ib_contract.primaryExch, ib_contract.expiry, ib_contract.strike,
                           ib_contract.currency, ib_contract.right, ib_contract.localSymbol,
                           ib_contract.multiplier, 'NULL', 'NULL',
                            '0' if not ib_contract.includeExpired else '1')
    elif ib_contract.secType == "CASH":
        if not ib_contract:
            print('Te weinig gegevens om contract te maken, voor een FutureCurrency:')
            print('symbol')
            raise(TypeError)
        primaryExch = ib_contract.primaryExch if ib_contract.primaryExch else 'IDEALPRO'
        exch = ib_contract.primaryExch if not ib_contract.exchange else ib_contract.exchange
        strike = _wrap(ib_contract.strike)
        return _TWSContract(ib_contract.conId, ib_contract.symbol, ib_contract.secType,
                           exch, ib_contract.primaryExch, ib_contract.expiry, ib_contract.strike,
                           ib_contract.currency, ib_contract.right, ib_contract.localSymbol,
                           ib_contract.multiplier, 'NULL', 'NULL',
                            '0' if not ib_contract.includeExpired else '1')
    else:
        print('twsR.py/_set_contract: secType {0} nog niet geïmplementeerd!'.format(
                ib_contract.secType))
        raise

def make_historical_request(ib_contract, end, barsize, max_period, whatToShow, 
                            filename, clientId=10, host='localhost', port=7496):
    contract = _set_contract(ib_contract)
    tws.get_req_hist_slot(contract, end, barsize, max_period, whatToShow)
    tws_conn = set_tws_connection(clientId=clientId, host=host, port=port)
    request = program(tws_conn)
    request.add_instruction(contract.to_variable('contract'))
    request.add_instruction(_reqHistoricalData('contract',
                                              end, barsize,
                                              max_period,
                                              whatToShow=whatToShow,
                                              filename=filename))
    request.run()


###
# make requests
###

### Historical Data


def _reqHistoricalData(Contract, endDateTime=False, barSize='1 day',
                      duration='1 M', useRTH='1', whatToShow='TRADES',
                      time_format='1', verbose='TRUE',tickerId='1',
                      eventHistoricalData=False, filename=False):
    '''Geeft R commando om historische data aan te vragen voor contract'''
    if endDateTime:
        endDateTime = mypy.date_time2format(endDateTime, '%Y%m%d %H:%M:%S')
    resp = ('reqHistoricalData({0},{1}{2},barSize={3},duration={4}, ' +
            'useRTH={5}, whatToShow={6}, timeFormat={7}, verbose={8} ,' +
            'tickerId={9}{10}{11})')
    request = resp.format(_TWS_CONNECTION_NAME,
                          Contract,
                          (', ' + _wrap(endDateTime)) if endDateTime else '',
                          _wrap(barSize), _wrap(duration), _wrap(useRTH), _wrap(whatToShow),
                          _wrap(time_format), verbose, _wrap(tickerId),
                          (' , eventHistoricalData=' + _wrap(eventHistoricalData)) if eventHistoricalData else '',
                          (' , file=' + _wrap(filename)) if filename else '')
    return request

###
# make R program code
###
class program():
    '''Creëert een object dat kan weggeschreven worden als R bestand'''
    def __init__(self, tws_settings=STD_TWS_CONNECTION):
        self.header = ['#!/usr/bin/R',
                       'library(IBrokers)',
                       '{0} <- twsConnect({1.clientId},{1.host},{1.port},{1.verbose},{1.timeout},{1.filename})'.format(_TWS_CONNECTION_NAME, tws_settings)]
        self.body = []
        self.end = ['twsDisconnect({0})'.format(_TWS_CONNECTION_NAME)]
    def __str__(self):
        resp = ''
        for line in self.header+self.body+self.end:
           resp += line+'\n'
        return resp
    def add_instruction(self, instruction):
        '''Adds instruction string to body list '''
        self.body.append(instruction)
    def to_file(self, filename):
        fh = open(filename,'w')
        fh.write(self.__str__())
        fh.close()
    def run(self, blocking=True, filename='R_run'):
        '''Voert programma uit
        standaard met blocking= True en tijdelijke bestandsnaam,
        als blocking = False, kan men een bestandsnaam ingeven of stdnaam gebruiken
        de gebruiker is dan zelf verantwoordelijk om het bestand eventueel op te kuisen!'''
        if blocking:
            R_file= NamedTemporaryFile(mode='w+')
            R_file.write(self.__str__())
            R_file.flush()
            Popen (['R', ' --vanilla', '-f', R_file.name]).wait()
        else:
            self.to_file(filename)
            Popen (['R', ' --vanilla', '-f', filename])
