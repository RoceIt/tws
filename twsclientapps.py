#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

import mypy
import tws
import TWSClient

HOST_IP = 'localhost'
PORT = 10911
CLIENT = 666


CONTRACT = 'CONTRACT'
ID = 'ID'
DATA = 'DATA'

class AppFailed(Exception): pass


def set_up_tws_connection(host_ip=None, port_nr=None, client_id=None, 
                          message=None, confirm=[],
                          interactive=False):
    '''prints the message and returns an active TWSConnection 
    
    ask the user for unknown parameters and set up the connection
    confirm is the list of paramaters that will be checked for with the user
    values for confirm are 'host_ip', 'port_nr', 'client_id'
    '''
    
    if message:
        print(message)
    if interactive and host_ip is None or 'host_ip' in confirm:
        interactive = True
        default = host_ip if host_ip else HOST_IP
        ip = mypy.get_string('host ip ({}): '.format(default), default=default)
    else:
        ip = host_ip
    if interactive and port_nr is None or 'port_nr' in confirm:
        interactive = True
        default = port_nr if port_nr else PORT
        port = mypy.get_string('port nr ({}): '.format(default), default=default)
    else:
        port = port_nr
    if interactive and client_id is None or 'client_id' in confirm:
        interactive = True
        default = client_id if client_id else CLIENT
        id_ = mypy.get_int('client id ({}): '.format(default), default=default)
    else:
        id_ = client_id
    try:
        answer = TWSClient.TWSconnection(ip, port, id_)
    except TWSClient.ConnectingError as err:
        if interactive:
            mess = 'Connection failed!\n{}\nRetry (Y|N): '.format(err)
            if mypy.get_bool(mess, default=False):
                answer = set_up_tws_connection(host_ip, port_nr, client_id)
            else:
                raise AppFailed('Could not make a connection')
        else:
            raise AppFailed('Could not make a connection')
    return answer


def active_tws_available(ip=None, port=None, client_id=None, twss=None):
    
    if not twss:
        if not(ip == None
               or
               port == None
               or
               client_id == None):
            try:
                twss = set_up_tws_connection(ip, port, client_id)            
            except AppFailed:
                return False
            twss.disconnect(silent=True)
            return True
        else:
            return False   
    print('checking availability tws ', twss)
    mess = 'twss must be a TWSClient.TWSconnection'
    assert isinstance(twss, TWSClient.TWSconnection), mess
    return twss.is_alive()

def select_contract(twss, symbol=None, secType=None, expiry='', strike=0.0,
                    right='', multiplier='', exchange=None, currency=None,
                    localSymbol=None, primaryExch=None, includeExpired=None,
                    comboLegsDescrip='', comboLegs=0, conId=0, secIdType='',
                    secId='', underComp=None, message=None, confirm=[], 
                    interactive=False):
    
    def select_contract_from_list(contracts):
        selectors = ('symbol', 'secType', 'expiry', 'strike', 'right',
                     'exchange')
        for selector in selectors:
            options = sorted({x.summary.__getattribute__(selector) 
                            for x in contracts})
            if len(options) == 1:
                continue
            mess = 'select {}'.format(selector)
            choice = mypy.get_from_list(options, mess)
            contracts = [x for x in contracts 
                         if x.summary.__getattribute__(selector) == choice]
        if len(contracts) > 1:
            options = sorted([x.summary.localSymbol for x in contracts])
            mess = 'Choose a contract'
            choice = mypy.get_from_list(options, mess)
            contracts = [x for x in contracts 
                         if x.summary.localSymbol == choice]
        print('contract: ', contracts[0].summary.localSymbol)
        input('push enter')
        return contracts
    while True:    
        if message:
            print(message)
        if symbol is None or 'symbol' in confirm:
            interactive = True
            default = symbol if symbol else 'EOE'
            symbol_ = mypy.get_string('symbol ({}): '.format(default), 
                                      default=default).upper()
        else:
            symbol_ = symbol
        if secType is None or 'secType' in confirm:
            interactive = True
            default = secType if secType else 'STK'
            secType_ = mypy.get_string('secType ({}): '.format(default),
                                       default=default).upper()
        else:
            secType_ = secType
        if secType_ in ['OPT', 'FUT', 'FOP']:
            if expiry is '' or'expiry' in confirm:
                interactive = True
                mess = 'expiry ({}): '.format(expiry)
                default = expiry if expiry else None
                expiry_ = mypy.get_string(mess, default=default, empty=True)
            else:
                expiry_ = expiry
            if expiry_ == '' and not includeExpired:
                interactive = True            
                includeExpired_ = mypy.get_bool('Include expired (y/N): ',
                                                default = False)
            else:
                includeExpired_ = True
            if multiplier == '' or 'multiplier' in confirm:
                interactive = True
                default = multiplier if multiplier else 'number'
                multiplier_ = mypy.get_float('multiplier ({}): '.format(default),
                                             default='')
            else:
                multiplier_ = multiplier
        else:
            expiry_ = expiry
            multiplier_ = multiplier
            includeExpired_ = True
        if secType_ in ['OPT', 'FOP']:
            if right == '' or 'right' in confirm:
                interactive = True
                mess = 'right ({}): '.format(right if right else 'C|P')
                default = right if right else None                
                right_ = mypy.get_string(mess, default=default, 
                                         empty=True).upper()
            else:
                right_ = right
            if strike == 0 or 'strike' in confirm:
                interactive = True
                default = strike if not strike == 0 else 'number'            
                strike_ = mypy.get_float('strike ({}): '.format(default),
                                          default=0.0)
            else:
                strike_ = strike
        else:
            right_ = right
            strike_ = strike            
        req_contract = tws.def_contract(symbol_, secType_, expiry_, strike_, right_,
                                        multiplier_, exchange, currency, 
                                        localSymbol, primaryExch, includeExpired_)
        req_id = twss.req_contract_details(req_contract)
        while True:
            data = twss.read_contract_details(req_id)
            if not data[0][0] and data[0][1] == 'RECEIVING DATA':
                continue
            break
        if not data[0][0]:
            if interactive:
                print(twss.read_contract_details(req_id))
                return False
            else:
                raise AppFailed('no contract found')
        if len(data) > 1:
            interactive = True
            data = select_contract_from_list(data)
        if interactive:
            print(data)
            if mypy.get_bool('Contrakt ok? (Y/n)', default=True):
                break
        else:
            break
    return data[0]

def select_list_of_contracts(twss, symbol=None, secType=None, expiry='',
                            strike=0.0, right='', multiplier='', exchange=None,
                            currency=None, localSymbol=None, primaryExch=None, 
                            includeExpired=None, comboLegsDescrip='',
                            comboLegs=0, conId=0, secIdType='', secId='',
                            underComp=None, message=None, confirm=[], reuse=[]):
    contract_list = []
    while True:
        contract = select_contract(twss, symbol, secType, expiry, strike, right,
                                   multiplier, exchange, currency, localSymbol,
                                   primaryExch, includeExpired, comboLegsDescrip,
                                   comboLegs, conId, secIdType, secId, underComp,
                                   message, confirm, interactive=True)
        if contract:
            contract = contract.summary
            contract_list.append(contract)
            print('list:',contract_list)
        else:
            print('No contract found!')
            if mypy.get_bool('Retry (Y/n)?', default=True):
                continue
            else:
                break
        if not mypy.get_bool('Add more contracts(Y/n)? ', default=True):
            break
        if 'symbol' in reuse:
            symbol = contract.symbol
        if 'secType' in reuse:
            secType = contract.secType
        if contract.right and 'right' in reuse:
            right = contract.right
            secType = contract.secType
        if contract.expiry and 'expiry' in reuse:
            expiry = contract.expiry
            secType = contract.secType
    return contract_list
            
        

def inverse_option(twss, option):
    '''returns the put (call) option for the given call(put) option
    
    You can enter a tws.contract or tws.contract_details as input, but it must
    be an option!
    If the inverse option doesn't exist, None is returned
    '''
    
    option = option if isinstance(option, tws.contract) else option.summary
    mess = 'option parameter must be a tws.contract(_details) with secType option'
    assert option.secType, mess
    if option.right[0].upper() == 'P':
        inv_right = 'C'
    elif option.right[0].upper() == 'C':
        inv_right = 'P'
    else:
        raise AppFailed('option has no right set?')
    print ('using inverse right', inv_right)
    try:
        inv_option = select_contract(twss, option.symbol, option.secType,
                                     option.expiry, option.strike, inv_right, 
                                     option.multiplier, 
                                     currency=option.currency,
                                     message='selecting inverse option')
    except AppFailed:
        inv_option = None
    return inv_option
    


class RealBarDictionary(dict):
    ''' dictionary to store contracts and the id's of the requested real bars
    
    it also remembers the client, you can use collect_row_of_data to try to
    collect data from the real bars
    '''
    
    def __init__(self, client):
        assert isinstance(client, TWSClient.Connection)
        super().__init__()
        self.twss = client
        
    def add_id(self, name, tws_contract, tws_id):
        self[name] = {CONTRACT: tws_contract, ID: tws_id}
    
    def collect_available_data(self, verbose=True):
        '''a list of tuples (contract, data)
        
        The real bar dict is a dict of dict:
            {'name1': {'id': id1, 'data': bar, ...},
            {'name2': {'id': id2, 'data': foo, ...},
            ...                                     }
        Every name dict must have an 'id' and 'data' key
        '''
        read_data = []
        twss = self.twss
        for name, feed in self.items():
            try:
                new_data = twss.real_bar_from(feed[ID])
                read_data.append((feed[CONTRACT], new_data))
                if verbose:
                    print('{}: {}'.format(name, new_data))
            except TWSClient.TimeOut:
                if verbose:
                    print('timed out')
            except TWSClient.RequestSended:
                if verbose:
                    print('request sended')
            except TWSClient.RequestStopped:
                if verbose:
                    print('feed was stopped!')
        return read_data          
                    
#def select_value(var, name, default, conf_list, get_function):
    
    #if var is None or name in conf_list:
        #def_value = var if var else default
        #value = get_function('{} ({})'.format(name, def_value),
                             #default=def_value)
    #else:
        #value = var
    #return value
    