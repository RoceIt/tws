#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''A Python3 interface to the IB TWS api'''

#from copy import copy, deepcopy

import os.path
import logging
import socket
import datetime
from multiprocessing import Queue, Manager, Process
from time import sleep
from queue import Empty

import mypy
import tws
import TWSClientListener as Listener
import TWSClientErrors as E
import TWSClientSendCodes as M

from TWSClientServerMessages import dispatch, ExecDetails
from TWSClientBackdoor import create_info_backdoor

class Error(Exception): pass

class ConnectingError(Error): pass
class NoConnection(Error): pass
class TWSClientWarning(Error): pass

class InvalidID(Error): pass

class RequestError(Error): pass
class RequestArgumentError(RequestError):pass
class ReceivingData(RequestError): pass
class RequestSended(RequestError): pass
class PacingViolation(RequestError): pass
class ExceededMaxLookback(RequestError): pass
class QueryReturnedNoData(RequestError): pass
class TimeOut(RequestError): pass
class RequestStopped(RequestError): pass

LOG_FILENAME = os.path.join(mypy.LOG_LOCATION, 'IBPy.log')
LOG_LEVEL = logging.DEBUG
STD_TIMEOUT = 5

logging.basicConfig(filename=LOG_FILENAME,
                    level=LOG_LEVEL,
                    filemode='w')

#HOST_IP = '127.1.1.1'
HOST_IP = '10.1.1.4'
HOST_PORT = 7496
SOCKET_EOL = '\0'.encode()
ADRESS = (HOST_IP, HOST_PORT)
CLIENT_VERSION = 47
SERVER_VERSION = 38
BAG_SEC_TYPE = 'BAG'

class TWSconnection(socket.socket):

    eol = SOCKET_EOL
    
    def __init__(self, host=HOST_IP, port=HOST_PORT, client_id=0):
        adress = (host, port)
        self.client_version = CLIENT_VERSION
        self.client_id = client_id
        self.name = ''.join([str(self.client_id), '@', 
                             host, '#', str(port)])
        self.request_id = 0 # counter for request id
        self.logger = logging.getLogger('client {} @{}'.format(client_id,
                                                               host))
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        version, time_ = self._make_connection_with_server(adress)
        self.connected = True
        self.server_version = version
        self.connection_time = time_
        self.logger.info('Connected, server version {}; @ {}'.
                         format(self.server_version, self.connection_time))
        self.send(client_id)
        self.server_data = Queue()
        self.hist_data_request_manager = tws.HistoricRequestLimitationsManager()
        # Managed items
        self.manager = Manager()
        self.std_mess_list = self.manager.list()
        self.err_list = self.manager.list()
        self.open_orders = self.manager.dict()
        self.open_orders_completed = self.manager.Event()
        self._current_time = self.manager.Queue()
        self._next_order_id = self.manager.Queue()
        self.order_status = self.manager.dict()
        self.executed_orders = self.manager.dict()
        self.requested_info = self.manager.dict()
        self.accounts = self.manager.dict()
        self.portfolio = self.manager.dict()
        self.tick_data = self.manager.dict()
        self.req_data = self.manager.dict()
        self.req_info = self.manager.dict()
        self.outputfiles = self.manager.Queue()
        self.i_lock = self.manager.Lock() # lock for changing req info
        self.d_lock = self.manager.Lock() # lock for changing req data
        self.l_lock = self.manager.Lock() # lock for logger writing
        # Handlers
        self.server_listener = Process(target=Listener.listen,
                                       args=(self,
                                             self.server_data,
                                             self.logger))
        self.server_listener.daemon = True
        self.server_listener.start()
        self.message_dispatcher = Process(target=dispatch,
                                          args=(self.server_data,
                                                self.std_mess_list,
                                                self.err_list,
                                                self._current_time,
                                                self._next_order_id,
                                                self.open_orders_completed,
                                                self.open_orders,
                                                self.order_status,
                                                self.executed_orders,
                                                self.requested_info,
                                                self.accounts,
                                                self.portfolio,
                                                self.tick_data,
                                                self.req_data,
                                                self.req_info,
                                                ###
                                                self.i_lock,
                                                self.d_lock,
                                                self.outputfiles,
                                                self.logger))
        self.message_dispatcher.daemon = True
        self.message_dispatcher.start()
        self.bd_info = None
        sleep(2)
        if not self.is_alive():
            print('not alive')
            mess = 'Can not connect probably a problem with the client id'
            self.disconnect(silent=True)
            raise ConnectingEror(mess)
        
        
    def disconnect(self, silent=False):

        try:
            self.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self.close()
        self.connected = False
        if not silent:
            mypy.print_list(self.std_mess_list, 'STANDARD LIST')
            mypy.print_list(self.err_list, 'ERROR LIST')
        try:
            while not self.server_data.empty():
                self.logger.warning('data in QUEUE: {}'.
                                    format(self.server_data.get()))
        except AttributeError:
            pass
        self.server_listener.terminate()
        self.message_dispatcher.terminate()
        self.logger.info('Connection closed')
        
    def is_alive(self):

        try:
            self.req_current_time()
        except TimeOut:
            return False
        return True
        
        
    def open_info_backdoor(self, file_name):
        '''Attaches an interface thrue the file (file_name) to read
        information out of the twsClient'''
        self.bd_info = Process(target=create_info_backdoor,
                               args=(file_name,
                                     self.std_mess_list,
                                     self.err_list,
                                     self._current_time,
                                     self._next_order_id,
                                     self.open_orders_completed,
                                     self.open_orders,
                                     self.order_status,
                                     self.executed_orders,
                                     self.requested_info,
                                     self.accounts,
                                     self.portfolio,
                                     self.tick_data,
                                     self.req_data))
        
        self.bd_info.daemon = True
        self.bd_info.start()


    #####
    # Requests
    #####


    def req_current_time(self, wait=STD_TIMEOUT, version=1):

        # Removing messegas that came to late
        # or as uncought side effect
        if not self.connected:
            raise NoConnection()
        while not self._current_time.empty():
            self._current_time.get()
        self.send(M.REQ_CURRENT_TIME)
        self.send(version)
        try:
            time_ = self._current_time.get(timeout=wait)
        except Empty:
            mess = 'current time request was not answered in time!'
            raise TimeOut(mess)
        return time_


    def req_contract_details(self, contract, version=6):
   
        if not self.connected:
            raise NoConnection()
        req_id = self.get_request_id('contract details')
        with self.i_lock:
            info = self.req_info[req_id]
            info.status = 'SENDED'
            self.req_info[req_id] = info
        with self.d_lock:
            self.req_data[req_id] = []
        self.send(M.REQ_CONTRACT_DATA)
        self.send(version)
        self.send(req_id)
        self.send(contract.conId)
        self.send(contract.symbol)
        self.send(contract.secType)
        self.send(contract.expiry)
        self.send(contract.strike)
        self.send(contract.right)
        self.send(contract.multiplier)
        self.send(contract.exchange)
        self.send(contract.currency)
        self.send(contract.localSymbol)
        self.send(contract.includeExpired)
        self.send(contract.secIdType)
        self.send(contract.secId)
        return req_id


    def request_ids(self, version=1):

        if not self.connected:
            raise NoConnection()
        self.send(M.REQ_IDS)
        self.send(version)
        self.send(1)

        
    def request_executions(self, filter_, version=3):

        if not self.connected:
            raise NoConnection()
        req_id = self.get_request_id()
        self.send(M.REQ_EXECUTIONS)
        self.send(version)
        self.send(req_id)
        self.send(filter_.clientId)
        self.send(filter_.acctCode)
        self.send(filter_.time_)
        self.send(filter_.symbol)
        self.send(filter_.secType)
        self.send(filter_.exchange)
        self.send(filter_.side)
        return req_id


    def req_market_data(self, contract, ticklist='', snapshot=False, version=9):

        if not self.connected:
            raise NoConnection()
        req_id = self.get_request_id()
        self.send(M.REQ_MKT_DATA)
        self.send(version)
        self.send(req_id)
        self.send(contract.conId)
        self.send(contract.symbol)
        self.send(contract.secType)
        self.send(contract.expiry)
        self.send(contract.strike)
        self.send(contract.right)
        self.send(contract.multiplier)
        self.send(contract.exchange)
        self.send(contract.primaryExch)
        self.send(contract.currency)
        self.send(contract.localSymbol)
        if contract.secType.upper() == BAG_SEC_TYPE:
            if not contract.comboLegs:
                send(0)
            else:
                raise Error('Not implemented')
        if not contract.underComp:
            self.send(False)
        else:
            raise Error('Not implemented')
        self.send(ticklist)
        self.send(snapshot)
        self.tick_data[req_id] = []
        return req_id


    def stop_market_data(self, req_id, version=1):

        if not self.connected:
            raise NoConnection()
        self.send(M.CANCEL_MKT_DATA)
        self.send(version)
        self.send(req_id)


    def req_real_time_bars(self, contract, barsize='5 secs', 
                           what_to_show='TRADES', use_rth=False,
                           version=1):
        """Send a request for real time bars to tws server.
        
        Data can be read with the real_bar_from method or send to
        a file with the set_outputfile_for_id method.
        
        arguments:
        
        contract -- tws.contract
        check IB API reference guide for other arguments
                
        """
        if not self.connected:
            raise NoConnection()
        if not isinstance(contract, tws.contract):
            raise RequestArgumentError('contract must be tws.contract')
        if not barsize in tws.rtb_bar_sizes:
            raise RequestArgumentError('barsize must be in {}'.
                                        format(tws.rtb_bar_sizes))
        if not what_to_show in tws.rtb_what_to_show:
            raise RequestArgumentError('what_to_show must be in {}'.
                                        format(tws.rtb_what_to_show))
        elif not isinstance(use_rth, bool):
            raise RequestArgumentError('use_rth must be boolean')
        ##### HACK ??####
        # tws api says the only valid value for barsize is 5 seconds
        # but the server does not except '5 secs' as valid input. I
        # change the parameter here to the integer 5 to make it work. Keep
        # checking in future versions if the api behavior or api manual 
        # changes.
        barsize = 5
        #################
        req_id = self.get_request_id('real time bars')
        with self.i_lock:
            info = self.req_info[req_id]
            info.status = 'SENDED'
            self.req_info[req_id] = info
        with self.d_lock:
            self.req_data[req_id] = []
        self.send(M.REQ_REAL_TIME_BARS)
        self.send(version)
        self.send(req_id)
        self.send(contract.symbol)
        self.send(contract.secType)
        self.send(contract.expiry)
        self.send(contract.strike)
        self.send(contract.right)
        self.send(contract.multiplier)
        if contract.exchange == 'SMART':
            self.send(contract.primaryExch)
        else:
            self.send(contract.exchange)
        self.send(contract.primaryExch)
        self.send(contract.currency)
        self.send(contract.localSymbol)
        self.send(barsize)
        self.send(what_to_show)
        self.send(use_rth)
        return req_id


    def stop_real_time_bars(self, req_id, version=1):
        
        def handle_error():
            raise RequestError(self.req_info[req_id].error)
        if not self.connected:
            raise NoConnection()         
        if req_id not in self.req_info:
            raise InvalidID('Unknown request ID')
        if not self.req_info[req_id].type_ == 'real time bars':
            mess = ('trying to stop real time bars but request is \'{}\' id'.
                    format(self.req_info[req_id].type_))
            raise InvalidID(mess)
        if self.req_info[req_id].status == 'ERROR':
            handle_error()
        self.send(M.CANCEL_REAL_TIME_BARS)
        self.send(version)
        self.send(req_id)
        with self.i_lock:
            info = self.req_info[req_id]
            info.status = 'FINISHED'
            self.req_info[req_id] = info
        
    
    def req_historical_data(self, contract, end_date_time, duration,
                            bar_size_setting, what_to_show='TRADES', 
                            use_rth=False,
                            version=4):
                
        if not self.connected:
            raise NoConnection()  
        req_id = self.get_request_id('historical data')
        with self.i_lock:
            info = self.req_info[req_id]
            info.status = 'SENDED'
            info.info = {'bar_size': bar_size_setting}
            self.req_info[req_id] = info
        with self.d_lock:
            self.req_data[req_id] = []
        self.send(M.REQ_HISTORICAL_DATA)
        self.send(version)
        self.send(req_id)
        self.send(contract.symbol)
        self.send(contract.secType)
        self.send(contract.expiry)
        self.send(contract.strike)
        self.send(contract.right)
        self.send(contract.multiplier)
        if (contract.exchange == 'SMART'
            or
            contract.exchange == ''):
            self.send(contract.primaryExch)
        else:
            self.send(contract.exchange)
        self.send(contract.primaryExch)
        self.send(contract.currency)
        self.send(contract.localSymbol)
        self.send(contract.includeExpired)
        self.send(mypy.datetime2format(end_date_time,
                                       tws.DATE_TIME_FORMAT_F))
        self.send(bar_size_setting)
        self.send(duration)
        self.send(use_rth)
        self.send(what_to_show)
        self.send(2)   # ask for epoch data format, 1 is text format
        self.hist_data_request_manager.request_sended()
        return req_id
        

    #####
    # Request readers
    #####

    def read_contract_details(self, req_id, wait=STD_TIMEOUT, remove=True):

        if req_id not in self.req_info:
            return [(False, 'Unknown request')]
        if not self.req_info[req_id].type_ == 'contract details':
            return [(False, 'wrong request type')]
        if self.req_info[req_id].status == 'ERROR':
            return [(False, self.req_info[req_id].error)]
        if self.req_info[req_id].status == 'DATA REMOVED':
            return [(False, self.req_info[req_id].status)]
        end_time = mypy.now() + datetime.timedelta(seconds=wait)
        while not self.req_info[req_id].status == 'FINISHED':
            if mypy.now() > end_time:                
                return [(False, self.req_info[req_id].status)]
            sleep(1)
        data = self.req_data[req_id]
        if remove:
            self.req_data[req_id] = []
            #print(self.req_info[req_id].status)
            with self.i_lock:
                info = self.req_info[req_id]
                info.status = 'DATA REMOVED'
                self.req_info[req_id] = info
        return data


    def read_executions_details(self, req_id=-1):

        if req_id == -1:
            details = self.executed_orders
        else:
            try:
                details = self.requested_info[req_id]
            except KeyError:
                self.logger.error('request id {} doesn\'t exist'.format(req_id))
                raise
        return details


    def dump_ticks(self, req_id=None):
        
        try:
            if req_id == -1 or req_id is None:
                data = {k: v for k, v in self.tick_data.items()
                        if type(k) == int}
            else:
                data = self.tick_data[req_id]
        except KeyError:
            with self.l_lock:
                self.logger.warning('wrong request for tick data {}'.
                                    format((req_id, name)))
            data = None
        return data

    def dump_real_time_bars(self, req_id=None):
        raise NotImplementedError()
        #'''Don't use it, er first give it some good thought!!!
        #check  real_bar_from and the calculators'''
        #try:
            #if req_id == -1 or req_id is None:
                #data = self.req_data
            #else:
                #data = self.req_data[req_id]
        #except KeyError:
            #with self.l_lock:
                #self.logger.warning('wrong request for tick data {}'.
                                    #format((req_id, name)))
            #data = None
        #return data


    def real_bar_from(self, req_id, wait=STD_TIMEOUT):
         
        def handle_error():
            raise RequestError(error)
        
        if req_id not in self.req_info:
            raise InvalidID('Unknown request ID')
        if not self.req_info[req_id].type_ == 'real time bars':
            mess = ('trying to read real time bars from a \'{}\' id'.
                    format(self.req_info[req_id].type_))
            raise InvalidID(mess)
        if self.req_info[req_id].status == 'ERROR':
            handle_error()
        end_time = mypy.now() + datetime.timedelta(seconds=wait)
        real_bar = None
        while mypy.now() <= end_time:
            if self.req_info[req_id].status == 'DATA AVAILABLE':
                with self.d_lock:
                    work_list = self.req_data[req_id]
                    real_bar = work_list.pop(0)
                    self.req_data[req_id] = work_list
                if len(self.req_data[req_id]) == 0:
                    with self.i_lock:
                        info = self.req_info[req_id]
                        info.status = 'NO DATA AVAILABLE'
                        self.req_info[req_id] = info
            elif self.req_info[req_id].status == 'FINISHED':
                if not len(self.req_data[req_id]) == 0:
                    with self.d_lock:
                        work_list = self.req_data[req_id]
                        real_bar = work_list.pop(0)
                        self.req_data[req_id] = work_list
            else:
                sleep(0.5)
                continue
            break
        if real_bar == None:
            status = self.req_info[req_id].status
            if status == 'FINISHED':
                raise RequestStopped('No more data available')
            elif status == 'SENDED':                
                raise RequestSended()
            elif status == 'NO DATA AVAILABLE':
                raise TimeOut('no data available')
            elif status == 'DATA AVAILABLE':
                with self.d_lock:
                    work_list = self.req_data[req_id]
                    real_bar = work_list.pop(0)
                    self.req_data[req_id] = work_list
                if len(self.req_data[req_id]) == 0:
                    with self.i_lock:
                        info = self.req_info[req_id]
                        info.status = 'NO DATA AVAILABLE'
                        self.req_info[req_id] = info
            elif status == 'ERROR':
                handle_error()
            else:
                mess = 'unexpected request status: {}'.format(status)
                raise RequestError(mess)
        return real_bar
            
    def get_historical_request_data(self, req_id, wait=STD_TIMEOUT, remove=True):
        
        def handle_error():
            error = self.req_info[req_id].error
            error_test = 'requesting any data earlier than'
            if error.code == 321 and error_test in error.message:
                raise ExceededMaxLookback()
            error_test = 'HMDS query returned no data'
            if error.code == 162 and error_test in error.message:
                raise QueryReturnedNoData()
            error_test = 'pacing violation'
            if error.code == 162 and error_test in error.message:
                raise PacingViolation()
            else:
                raise RequestError(error)
            
        if req_id not in self.req_info:
            raise InvalidID('Unknown request ID')
        if not self.req_info[req_id].type_ == 'historical data':
            mess = ('trying to read historical data from a \'{}\' id'.
                    format(self.req_info[req_id].type_))
            raise InvalidID(mess)
        if self.req_info[req_id].status == 'ERROR':
            handle_error()
        if self.req_info[req_id].status == 'DATA REMOVED':
            raise RequestError('data removed')      
        end_time = mypy.now() + datetime.timedelta(seconds=wait)
        while not self.req_info[req_id].status == 'FINISHED':
            if mypy.now() > end_time:
                status = self.req_info[req_id].status
                if status == 'RECEIVING DATA':
                    raise ReceivingData()
                elif status == 'SENDED':
                    raise RequestSended()
                elif status == 'FINISHED':
                    break
                elif status == 'ERROR':
                    handle_error()
                    
            sleep(1)
        data = self.req_data[req_id]
        if remove:
            self.req_data[req_id] = []
            #print(self.req_info[req_id].status)
            with self.i_lock:
                info = self.req_info[req_id]
                info.status = 'DATA REMOVED'
                self.req_info[req_id] = info
        return data
        

    #####
    # Account info
    #####

    def account_info(self, action, account='', version=2):

        action_={'START': 1, 'STOP': 2}
        if not action in action_:
            self.logger.error('wrong action for account info')
            return False
        if not self.connected:
            raise NoConnection() 
        self.send(M.REQ_ACCOUNT_DATA)
        self.send(version)
        self.send(action_[action])
        self.send(account)
        return True
        
    
    def dump_account_info(self, account=None):

        if account is None:             
            dump = self.accounts
        else:
            dump = {k: v for k, v in self.accounts.items()
                    if k[0] == account}
        return dump


    def get_account_info(self, name, currency='BASE', account=None):

        account = account if account else list(self.accounts.keys())[0][0]
        try:
            info = self.accounts[(account,name,currency)]
        except KeyError:
            self.logger.error('wrong account info request \n'
                              '\taccount: {} currency: {} value: {}'.
                              format(account, currency, name))
            info = None
        return info


    def dump_portfolio(self, account=None):

        if account is None:
            dump = self.portfolio
        else:
            dump = {k: v for k, v in self.portfolio.items()
                    if k[0] == account}
        return dump


    def get_portfolio_info(self, name, currency='BASE', account=None):

        self.logger.warning('get_portfolio_info not implemented')
        return False


    def set_outputfile_for_id(self, id_, filename, reset=True):

        self.outputfiles.put(id_)
        self.outputfiles.put((filename, reset))


    def remove_outputfile_for_id(self, id_):
        
        self.outputfiles.put(id_)
        

    def get_last_account_update(self):

        return self.accounts['last_update']


    #####
    # Orders
    #####

    def place_order(self, contract, order_settings, version=30):
        """Place order with order_settings for contract
        
        The contract must be a tws.contract.  The order_settings can be
        a tws.order or a dictionary with settings.
        The function returns the tws id of the order.
        
        """
        if not self.connected:
            raise NoConnection()
        #if not type(order_settings) is tws.order:
            #order_id = self.get_order_id()
            #order_settings['orderId'] = order_id
            #if not 'clientId' in order_settings:
                #order_settings['clientId'] = self.client_id
            #order = tws.def_order(**order_settings)
        #else:
            #order = order_settings
            #order_id = order.orderId
        if isinstance(order_settings, tws.order):
            order = order_settings
            order_id = order.orderId
        else:
            order_id = self.get_order_id()
            order_settings['orderId'] = order_id
            if not 'clientId' in order_settings:
                order_settings['clientId'] = self.client_id
            order = tws.def_order(**order_settings)
        self.send(M.PLACE_ORDER)
        self.send(version)
        self.send(order_id)
        # send contract data
        self.send(contract.conId)
        self.send(contract.symbol)
        self.send(contract.secType)
        self.send(contract.expiry)
        self.send(contract.strike)
        self.send(contract.right)
        self.send(contract.multiplier)
        self.send(contract.exchange)
        self.send(contract.primaryExch)
        self.send(contract.currency)
        self.send(contract.localSymbol)
        self.send(contract.secIdType)
        self.send(contract.secId)
        self.send(order.action)
        self.send(order.totalQuantity)
        self.send(order.orderType)
        self.send(order.lmtPrice)
        self.send(order.auxPrice)
        self.send(order.tif)
        self.send(order.ocaGroup)
        self.send(order.account)
        self.send(order.openClose)
        self.send(order.origin)
        self.send(order.orderRef)
        self.send(order.transmit)
        self.send(order.parentId)
        self.send(order.blockOrder)
        self.send(order.sweepToFill)
        self.send(order.displaySize)
        self.send(order.triggerMethod)
        self.send(order.outsideRth)
        self.send(order.hidden)
        if contract.secType.upper() == BAG_SEC_TYPE:
            if not contract.comboLegs:
                send(0)
            else:
                raise Error('Not implemented')
        self.send('')
        self.send(order.discretionaryAmt)
        self.send(order.goodAfterTime)
        self.send(order.goodTillDate)
        self.send(order.faGroup)
        self.send(order.faMethod)
        self.send(order.faPercentage)
        self.send(order.faProfile)
        self.send(order.shortSaleSlot)
        self.send(order.designatedLocation)
        self.send(order.ocaType)
        self.send(order.rule80A)
        self.send(order.settlingFirm)
        self.send(order.allOrNone)
        self.send(order.minQty)
        self.send(order.percentOffset)
        self.send(order.eTradeOnly)
        self.send(order.firmQuoteOnly)
        self.send(order.nbboPriceCap)
        self.send(order.auctionStrategy)
        self.send(order.startingPrice)
        self.send(order.stockRefPrice)
        self.send(order.delta)
        self.send(order.stockRangeLower)
        self.send(order.stockRangeUpper)
        self.send(order.overridePercentageConstraints)
        self.send(order.volatility)
        self.send(order.volatilityType)
        self.send(order.deltaNeutralOrderType)
        self.send(order.deltaNeutralAuxPrice)
        self.send(order.continuousUpdate)
        self.send(order.referencePriceType)
        self.send(order.trailStopPrice)
        self.send(order.scaleInitLevelSize)
        self.send(order.scaleSubsLevelSize)
        self.send(order.scalePriceIncrement)
        self.send(order.clearingAccount)
        self.send(order.clearingIntent)
        self.send(order.notHeld)
        if not contract.underComp:
            self.send(False)
        else:
            raise Error('Not implemented')
        self.send(order.algoStrategy)
        if order.algoStrategy:
            raise Error('Not implemented')
        self.send(order.whatIf)
        return order_id


    def place_bracket_order(self, contract, bracket):

        ENTER_TRADE = {'BULL': 'BUY', 'BEAR': 'SELL'}
        EXIT_TRADE = {'BULL': 'SELL', 'BEAR': 'BUY'}
        br = bracket

        entry_order = dict(action=ENTER_TRADE[br.direction],
                           totalQuantity=br.number_of_contracts,
                           orderType=br.enter_type,
                           lmtPrice=br.enter_limit,
                           auxPrice=br.enter_aux,
                           transmit=False)
        if br.enter_trade_before:
            entry_order['tif']='GTD'
            entry_order['goodTillDate'] = mypy.date_time2format(
                                                   br.enter_trade_before,
                                                   tws.DATE_TIME_FORMAT_F)
        parent_id = self.place_order(contract, entry_order)
        profit_taker = dict(action=EXIT_TRADE[br.direction],
                            totalQuantity=br.number_of_contracts,
                            orderType=br.profit_type,
                            lmtPrice=br.profit_limit,
                            auxPrice=br.profit_aux,
                            parentId=parent_id,
                            transmit=False)
        stop_loss = dict(action=EXIT_TRADE[br.direction],
                         totalQuantity=br.number_of_contracts,
                         orderType=br.stop_type,
                         lmtPrice=br.stop_limit,
                         auxPrice=br.stop_aux,
                         parentId=parent_id,
                         transmit=True if not br.EOD_sell else False)
        if type(br.EOD_sell) == datetime.datetime:
            profit_taker['tif'] = stop_loss['tif'] = 'GTD'
            end_time = mypy.date_time2format(br.EOD_sell,
                                             tws.DATE_TIME_FORMAT_F)
            profit_taker['goodTillDate'] = stop_loss['goodTillDate'] = end_time
        else:
            profit_taker['tif'] = stop_loss['tif'] = 'GTC'
        profit_id = self.place_order(contract, profit_taker)
        stop_id = self.place_order(contract, stop_loss)
        if br.EOD_sell == 'EOD':
            moc = dict(action=EXIT_TRADE[br.direction],
                       totalQuantity=br.number_of_contracts,
                       orderType='MOC',
                       parentId=parent_id,
                       transmit=True )
            moc_id = self.place_order(contract, moc)
        elif type(br.EOD_sell) == datetime.datetime:
            five_secs = datetime.timedelta(seconds=5)
            start_sell = mypy.date_time2format(br.EOD_sell+five_secs,
                                               tws.DATE_TIME_FORMAT_F)
            eod_sell = dict(action=EXIT_TRADE[br.direction],
                            totalQuantity=br.number_of_contracts,
                            orderType='MKT',
                            goodAfterTime=start_sell,
                            parentId=parent_id,
                            transmit=True)
            moc_id = self.place_order(contract, eod_sell)       
        else:
            moc_id = None       
        return parent_id, profit_id, stop_id, moc_id


    def cancel_order(self, id_, version=1):

        if not self.connected:
            raise NoConnection()
        self.send(M.CANCEL_ORDER)
        self.send(version)
        self.send(id_)


    def change_order(self, id_, limit=None, aux=None, quantity=None):

        if id_ in self.open_orders:
            open_order = self.open_orders[id_]
        else:
            raise TWSClientWarning('id not in open orders')
        contract = open_order.contract
        order = open_order.order
        new_values = {}
        if limit:
            new_values['lmtPrice'] = limit
        if aux:
            new_values['auxPrice'] = aux
        if quantity:
            new_values['totalQuantity'] = quantity
        new_order = tws.change_order(order, **new_values)
        self.place_order(contract, new_order)
        


    #####
    # calculators
    #####

    def average_difference(self, rb1, rb2, number_of_bars=50):

        nob = min(len(self.req_data[rb1]), len(self.req_data[rb2]), 
                  number_of_bars)
        l1 = {v.time_: v.wap for v in self.req_data[rb1][-nob:]}
        l2 = {v.time_: v.wap for v in self.req_data[rb2][-nob:]}
        counter = total = 0
        for k in l1.keys():
            try:
                diff = l2[k] - l1[k]
            except KeyError:
                continue
            total += diff
            counter += 1
        avg = total / counter if counter > 0 else None
        return avg, counter

    #####
    # error handling
    #####        

    def error_message_for_req_id(self, req_id):
        
        for i, error in enumerate(self.err_list):
            if error.id_ == req_id:
                break
        else:
            return None
        return self.err_list.pop(i)

    #####
    # Helpers
    #####

    def _make_connection_with_server(self, adress):

        try:
            self.settimeout(30)
            self.connect(adress)  
            self.send(self.client_version)
            server_version = self.read_int()
            self.settimeout(None)
            server_time = self.read_date()
            if server_version < SERVER_VERSION:
                self.logger.error(E.UPDATE_TWS.message)
                raise ConnectingError(E.UPDATE_TWS.message)
        except socket.timeout as err:
            self.close()
            self.logger.error(E.CONNECT_FAIL.message)
            raise ConnectingError(E.CONNECT_FAIL.message)
        except socket.error as err:
            self.close()
            mess = E.CONNECT_FAIL.message
            self.logger.error(mess)
            raise ConnectingError(mess)
        except ValueError as err:
            self.close()
            mess = E_UNEXPECTED_ANSWER.format(err)
            self.logger.error(mess)
            raise ConnectingError(mess)
        return server_version, server_time


    def send(self, message):

        mess = str(message)
        if message is False:
            mess = '0'
        if message is True:
            mess = '1'
        if message is None:
            mess = ''
        if not len(mess) == 0:
            super().send(str(mess).encode())
        super().send(self.eol)


    def _read_line(self):

        answer = ''.encode()
        while True:
            b = self.recv(1)
            if b == self.eol:
                break
            answer += b
        return answer.decode()


    def read_int(self):

        answer = self._read_line()
        return int(answer) if answer else None


    def read_float(self):

        answer = self._read_line()
        return float(answer) if answer else None


    def read_str(self):

        return self._read_line()


    def read_bool(self):

        answer = not self.read_int() == 0
        return answer

      
    def read_date(self, format='ISO8601'):

        date_ = self._read_line()
        if format == 'ISO8601':
            date_ = mypy.py_date_time(date_, mypy.ISO8601TIMESTR)
        elif format == 'EPOCH':
            date_ = mypy.epoch2date_time(int(date_))
        return date_


    def get_request_id(self, type_='unknown'):

        self.request_id += 1
        self.req_info[self.request_id] = RequestStatus(type_)
        return self.request_id


    def get_order_id(self, timeout=STD_TIMEOUT):

        if self._next_order_id.empty():
            self.request_ids()
        try:
            id_ = self._next_order_id.get(timeout=timeout)
        except Empty:
            raise TWSClientWarning('No order id available?')
        return id_

    
class RequestStatus():
    
    valid_status = {'SENDED', 
                    'DATA AVAILABLE', 'RECEIVING DATA',
                    'NO DATA AVAILABLE', 'FINISHED', 
                    'DATA REMOVED', 'ERROR'}
    
    def __init__(self, type_):
        self.type_ = type_
        self.__status = None
        self.action_time = []
        self.__info = None
        
    @property
    def status(self):
        return self.__status
    
    @status.setter
    def status(self, new_status):
        
        #print('orig status: ', self.status)
        if self.__status == new_status:
            return
        elif new_status == 'SENDED':
            if not self.__status is None:
                raise ValueError('request already sended')
            self.action_time = [mypy.now()]
            self.__status = 'SENDED'
        elif new_status == 'DATA AVAILABLE':
            if not self.__status in {'SENDED', 'DATA AVAILABLE',
                                     'NO DATA AVAILABLE', 'FINISHED'}:
                raise ValueError('request is in an invalid state!?')
            if self.__status == 'FINISHED':
                raise RequestError('request was reported as finished?')
            self.action_time = [mypy.now()]
            self.__status = 'DATA AVAILABLE'
        elif new_status == 'NO DATA AVAILABLE':
            if not self.__status in {'DATA AVAILABLE', 'NO DATA AVAILABLE',
                                     'FINISHED'}:
                raise ValueError('request is in an invalid state!?')
            if self.__status == 'FINISHED':
                raise RequestError('request was reported as finished?')
            self.action_time = [mypy.now()]
            self.__status = 'NO DATA AVAILABLE'
        elif new_status == 'RECEIVING DATA':
            if not self.__status =='SENDED':
                raise ValueError('request not yet sended or already finished')
            self.__status = 'RECEIVING DATA'
            self.action_time.append(mypy.now())
        elif new_status == 'FINISHED':
            if not self.__status in {'SENDED', 'RECEIVING DATA',
                                     'DATA AVAILABLE', 'NO DATA AVAILABLE'}:
                raise ValueError('request not yet sended or already finished')
            self.action_time.append(mypy.now())
            self.__status = 'FINISHED'
        elif new_status == 'DATA REMOVED':
            if not self.__status == 'FINISHED':
                raise ValueError('can not remove unfinished data')
            self.__status = 'DATA REMOVED'
        elif new_status == 'ERROR':
            raise('use \'error\' to set error')
        else:
            raise ValueError('Unknown status')
        
        
    @property
    def info(self):
        return self.__info
    
    
    @info.setter
    def info(self, info):
        
        self.__info = info

        
    @property
    def error(self):
        
        return self.__info if self.status == 'ERROR' else False
    
    
    @error.setter
    def error(self, message):
    
        self.__status = 'ERROR'
        self.action_time.append(mypy.now())
        self.__info = message 
        
Connection = TWSconnection  #should be shanged everywhere so this can be removed