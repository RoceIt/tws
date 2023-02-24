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

# versie 0.0.2
# ============
# made changes for new IBrokers package
#    * changed twsConnection, removed blocking option

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

###
# basic settings
###
tws_connection_name = 'tws'

###
# Helpers
###
def wrap(text):
    '''removes aanhalingstekens from text and ads new one around'''
    text = str(text)
    return '"'+text.strip('\'"')+'"'

###
# twsConnection
###
tws_connection = namedtuple('tws_connection',
                            'clientId host port verbose timeout filename')
std_tws_connection = tws_connection(1, '"localhost"', 7496, 'TRUE', 5, 'NULL')

def set_tws_connection(clientId = std_tws_connection.clientId,
                       host     = std_tws_connection.host,
                       port     = std_tws_connection.port,
                       verbose  = std_tws_connection.verbose,
                       timeout  = std_tws_connection.timeout,
                       filename = std_tws_connection.filename):
    if filename != 'NULL':
        filename = wrap(filename)
    return tws_connection(clientId, wrap(host), port, verbose, timeout, blocking)

###
#twsContract
###
class twsContract():
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
        self.conId           = conId
        self.symbol          = symbol
        self.sectype         = sectype
        self.exch            = exch
        self.primary         = primary
        self.expiry          = expiry
        self.strike          = strike
        self.currency        = currency
        self.right           = right
        self.local           = local
        self.multiplier      = multiplier
        self.combo_legs_desc = combo_legs_desc
        self.comboleg        = comboleg
        self.include_expired = include_expired
    def __str__(self):
        '''Definieer de contractparameters'''
        resp = ('conId = {0.conId} \nsymbol = {0.symbol} \nsectype = {0.sectype} \n' +
                'exch = {0.exch} \nprimary = {0.primary} \nexpiry = {0.expiry} \n' +
                'strike = {0.strike} \ncurrency = {0.currency} \nright = {0.right} \n' +
                'local = {0.local} \nmultiplier = {0.multiplier} \n' +
                'combo_legs_desc = {0.combo_legs_desc} \ncomboleg = {0.comboleg} \n' +
                'include_expired = {0.include_expired}')
        return resp.format(self)
    def to_variable(self, name):
        '''Geeft R commando om variabele 'name' in te stellen als contract'''
        resp = ('{0} <- twsContract({1.conId}, "{1.symbol}", "{1.sectype}", ' +
                '"{1.exch}", "{1.primary}", "{1.expiry}", "{1.strike}", "{1.currency}", ' +
                '"{1.right}", "{1.local}", "{1.multiplier}", {1.combo_legs_desc}, ' +
                '{1.comboleg}, "{1.include_expired}")')
        return resp.format(name, self)
class twsFuture(twsContract):
    def __init__(self,
                 symbol, exch, expiry,
                 primary='',
                 currency        = 'USD',
                 right           = '',
                 local           = '',
                 multiplier      = '',
                 include_expired = '0',
                 conId           = 0):
        super().__init__(conId,
                         symbol, 'FUT', exch, primary,
                         expiry, '0.0', 
                         currency,
                         right,
                         local,
                         multiplier,
                         'NULL', 'NULL',
                         include_expired)

def setContract(IBcontract):
    '''returns a twsR contract from IBContract, eventually asks for xtra info'''
    if IBcontract.secType == 'FUT':
        if not IBcontract.symbol or not IBcontract.primaryExch or not IBcontract.expiry:
            print('Te weinig gegevens om contract te maken, voor een Future:')
            print('symbol, primary exchange, expiry')
            raise(TypeError)
        exch = IBcontract.primaryExch if not IBcontract.exchange else IBcontract.exchange
        strike = wrap(IBcontract.strike)
        return twsFuture(IBcontract.symbol, exch, IBcontract.expiry, IBcontract.primaryExch,
                         IBcontract.currency, IBcontract.right, IBcontract.localSymbol,
                         IBcontract.multiplier, '0' if not IBcontract.includeExpired else '1',
                         IBcontract.conId)
    elif IBcontract.secType == 'IND':
        if not IBcontract.symbol or not IBcontract.primaryExch:
            print('Te weinig gegevens om contract te maken, voor een Future:')
            print('symbol, primary exchange, expiry')
            raise(TypeError)
        exch = IBcontract.primaryExch if not IBcontract.exchange else IBcontract.exchange
        strike = wrap(IBcontract.strike)
        return twsContract(IBcontract.conId, IBcontract.symbol, IBcontract.secType,
                           exch, IBcontract.primaryExch, IBcontract.expiry, IBcontract.strike,
                           IBcontract.currency, IBcontract.right, IBcontract.localSymbol,
                           IBcontract.multiplier, 'NULL', 'NULL',
                            '0' if not IBcontract.includeExpired else '1')
    else:
        print('twsR.py/setContract: secType {0} nog niet geïmplementeerd!'.format(
                IBcontract.secType))
        raise


###
# make requests
###

### Historical Data


def reqHistoricalData(Contract, endDateTime=False, barSize='1 day',
                      duration='1 M', useRTH='1', whatToShow='TRADES',
                      time_format='1', verbose='TRUE',tickerId='1',
                      eventHistoricalData=False, filename=False):
    '''Geeft R commando om historische data aan te vragen voor contract'''
    if endDateTime:
        endDateTime = mypy.date_time2format(endDateTime, '%Y%m%d %H:%M:%S')
    resp = ('reqHistoricalData({0},{1}{2},barSize={3},duration={4}, ' +
            'useRTH={5}, whatToShow={6}, time.format={7}, verbose={8} ,' +
            'tickerId={9}{10}{11})')
    request = resp.format(tws_connection_name,
                          Contract,
                          (', ' + wrap(endDateTime)) if endDateTime else '',
                          wrap(barSize), wrap(duration), wrap(useRTH), wrap(whatToShow),
                          wrap(time_format), verbose, wrap(tickerId),
                          (' , eventHistoricalData=' + wrap(eventHistoricalData)) if eventHistoricalData else '',
                          (' , file=' + wrap(filename)) if filename else '')
    return request

###
# make R program code
###
class program():
    '''Creëert een object dat kan weggeschreven worden als R bestand'''
    def __init__(self, tws_settings=std_tws_connection):
        self.header = ['#!/usr/bin/R',
                       'library(IBrokers)',
                       '{0} <- twsConnect({1.clientId},{1.host},{1.port},{1.verbose},{1.timeout},{1.filename})'.format(tws_connection_name, tws_settings)]
        self.body = []
        self.end = ['twsDisconnect({0})'.format(tws_connection_name)]
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
