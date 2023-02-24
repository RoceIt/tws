#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

import pickle
from collections import namedtuple
from queue import Empty

import mypy
from barData import ochlBar

# routerRule = namedtuple('routerRule',
#                        'test_message_type test_id destination')

MAX_REAL_TIME_BAR_LIST = 100
 
#messages for queue
Error = namedtuple('Error', 'id_ code message')
NextValidId = namedtuple('NextValidId', 'order_id')
OpenOrderEnd = namedtuple('OpenOrderEnd', '')
CurrentTime = namedtuple('CurrentTime', 'time_')
TickPrice = namedtuple('TickPrice', 'id_ type_ price can_auto_execute')
TickSize = namedtuple('TickSize', 'id_ type_ size')
TickOptionComputation = namedtuple('TickOptionComputation',
                                   'id_ type_ implied_volume delta opt_price '
                                   'pv_dividend gamma vega theta und_price')
TickGeneric = namedtuple('TickGeneric', 'id_ type_ value')
TickString = namedtuple('TickString', 'id_ type_ value')
TickEFP = namedtuple('TickEFP', 
                     'id_ type_ basis_points formatted_basis_points '
                     'implied_futures_price hold_days future_expiry '
                     'dividend_impact dividends_to_expiry')
OrderStatus = namedtuple('OrderStatus', 
                         'id_ status filled remaining '
                         'avg_fill_price perm_id parent_id last_fill_price '
                         'client_id why_held')
UpdateAccountValue = namedtuple('UpdateAccountValue', 
                                'key value currency account_name')
PortfolioValue = namedtuple('PortfolioValue', 
                            'contract position market_price '
                            'market_value average_cost unrealised_PNL '
                            'realised_PNL account_name')
UpdateAccountTime = namedtuple('UpdateAccountTime', 'time_')
OpenOrder = namedtuple('OpenOrder', 'id_ contract order order_state')
ScannerData = namedtuple('ScannerData', 
                         'id_ rank contract distance benchmark projection'
                         'legs_str')
ScannerDataEnd = namedtuple('ScannerDataEnd', 'id_')
ContractDetails = namedtuple('ContractDetails', 'id_ contract')
BondContractData = namedtuple('BondContractData', 'id_ contract')
ExecDetails = namedtuple('ExecDetails', 'id_ contract execution')
UpdateMktDepth = namedtuple('UpdateMktDepth', 
                            'id_ position operation side price size')
UpdateMktDepthL2 = namedtuple('UpdateMktDepthL2', 
                              'id_ position marketmaker operation side '
                              'price size')
UpdateNewsBulletin = namedtuple('UpdateNewsBulletin', 
                                'id_ type_ message origin')
ManagedAccounts = namedtuple('ManagedAccounts', 'list_')
ReceiveFA = namedtuple('ReceiveFA', 'type_ xml')
HistoricalData = namedtuple('HistoricalData', 
                            'id_ date_ open high low close volume bar_count '
                            'wap has_gaps')
ScannerParameters = namedtuple('ScannerParameters', 'xml')
RealTimeBars = namedtuple('RealTimeBars', 
                          'id_ time_ open_ high low close volume wap count')
FundamentalData = namedtuple('FundamentalData', 'id_ data')
ContractDetailsEnd = namedtuple('ContractDetailsEnd', 'id_')
AccountDownloadEnd = namedtuple('AccountDownloadEnd', 'account')
ExecutionDetailsEnd = namedtuple('ExecutionDetailsEnd', 'id_')
DeltaNeutralValidation = namedtuple('DeltaNeutralValidation', 'id_ under_comp')
TickSnapshotEnd = namedtuple('TickSnapshotEnd', 'id_')


#incomming messages from server
TICK_PRICE = 1       
TICK_SIZE = 2 
ORDER_STATUS = 3 
ERR_MSG = 4 
OPEN_ORDER = 5 
ACCT_VALUE = 6 
PORTFOLIO_VALUE = 7 
ACCT_UPDATE_TIME = 8 
NEXT_VALID_ID = 9 
CONTRACT_DATA = 10 
EXECUTION_DATA = 11 
MARKET_DEPTH = 12 
MARKET_DEPTH_L2 = 13 
NEWS_BULLETINS = 14 
MANAGED_ACCTS = 15 
RECEIVE_FA = 16 
HISTORICAL_DATA = 17 
BOND_CONTRACT_DATA = 18 
SCANNER_PARAMETERS = 19 
SCANNER_DATA = 20 
TICK_OPTION_COMPUTATION = 21 
TICK_GENERIC = 45 
TICK_STRING = 46 
TICK_EFP = 47 
CURRENT_TIME = 49 
REAL_TIME_BARS = 50 
FUNDAMENTAL_DATA = 51 
CONTRACT_DATA_END = 52 
OPEN_ORDER_END = 53 
ACCT_DOWNLOAD_END = 54 
EXECUTION_DATA_END = 55 
DELTA_NEUTRAL_VALIDATION = 56 
TICK_SNAPSHOT_END = 57 

# tick size

tick_type = {0: "bidSize", 
             1: "bidPrice",
             2: "askPrice",
             3: "askSize",
             4: "lastPrice",
             5: "lastSize",
             6: "high",
             7: "low",
             8: "volume",
             9: "close",
             10: "bidOptComp",
             11: "askOptComp",
             12: "lastOptComp",
             13: "modelOptComp",
             14: "open",
             15: "13WeekLow",
             16: "13WeekHigh",
             17: "26WeekLow",
             18: "26WeekHigh",
             19: "52WeekLow",
             20: "52WeekHigh",
             21: "AvgVolume",
             22: "OpenInterest",
             23: "OptionHistoricalVolatility",
             24: "OptionImpliedVolatility",
             25: "OptionBidExchStr",
             26: "OptionAskExchStr",
             27: "OptionCallOpenInterest",
             28: "OptionPutOpenInterest",
             29: "OptionCallVolume",
             30: "OptionPutVolume",
             31: "IndexFuturePremium",
             32: "bidExch",
             33: "askExch",
             34: "auctionVolume",
             35: "auctionPrice",
             36: "auctionImbalance",
             37: "markPrice",
             38: "bidEFP",
             39: "askEFP",
             40: "lastEFP",
             41: "openEFP",
             42: "highEFP",
             43: "lowEFP",
             44: "closeEFP",
             45: "lastTimestamp",
             46: "shortable",
             47: "fundamentals",
             48: "RTVolume",
             49: "halted",
             50: "bidYield",
             51: "askYield",
             52: "lastYield",
             53: "custOptComp"}


def dispatch(server_messages, std_list, err_list,
             current_time, next_valid_id,
             open_orders_completed, open_orders,
             order_status, executed_orders,
             requested_info,accounts, portfolio,
             tick_data, req_data, req_info,i_lock, d_lock, 
             outputfiles, log):

    
    def handle_error():
        
        if server_mess.id_ > 0:
            with i_lock:              
                info = req_info[server_mess.id_]
                info.error = server_mess
                req_info[server_mess.id_] = info
        else:
            err_list.append(server_mess)
        log.error(str(server_mess))   


    def handle_current_time():

        current_time.put(server_mess.time_)
        log.info(server_mess.time_)


    def handle_contract_details():
        
        id_ = server_mess.id_
        if not id_ in contract_data:
            contract_data[id_] = []
            with i_lock:
                info = req_info[id_]
                info.status = 'RECEIVING DATA'
                req_info[id_] = info
        #with d_lock:
            #data = req_data[id_]
            #data.append(server_mess.contract)
            #req_data[id_] = data
        #log.info('received contract info {} {}'.
                 #format(server_mess.contract.summary.symbol,
                        #server_mess.contract.summary.secType))
        contract_data[id_].append(server_mess.contract)

    def handle_contract_details_end():
         
        id_ = server_mess.id_       
        with d_lock:
            req_data[id_] = contract_data[id_]
        with i_lock:
            info = req_info[server_mess.id_]
            info.status = 'FINISHED'
            req_info[server_mess.id_] = info
        contract_data[id_]= 'FINISHED'


    def handle_next_valid_id():

        while not next_valid_id.empty():
            self.next_valid_id.get()
        next_valid_id.put(server_mess.order_id)
        log.info('received new order id {}'.format(server_mess.order_id))


    def handle_open_order_end():

        open_orders_completed.set()


    def handle_open_order():

        open_orders_completed.clear()
        open_orders[server_mess.id_] = server_mess
        log.info('received open order {} '.format(server_mess.id_))


    def handle_order_status():

        order_status[server_mess.id_] = server_mess
        if server_mess.status == 'Cancelled':
            open_orders.pop(server_mess.id_)
            log.info('order {} cancelled'.format(server_mess.id_))
        elif server_mess.status == 'Filled':
            open_orders.pop(server_mess.id_)
            log.info('order {} filled'.format(server_mess.id_))                
        elif server_mess.status in ['Submitted', 'PreSubmitted']:
            pass
        else:
            log.warning('unhandeled OrderStatus: \n{}\n'.format(server_mess))
            log.info('order {} has (new) status'.format(server_mess.id_))
            std_list.append(server_mess)


    def handle_exec_details():

        order_id = server_mess.execution.orderId
        if server_mess.id_ == -1:
            executed_orders[order_id] = server_mess
            log.info('order {} (partially) executed'.format(order_id))
        else:
            if not server_mess.id_ in requested_info:
                requested_info[server_mess.id_] = {'complete': False}
            requested_info[server_mess.id_][order_id] = server_mess
            log.info('received execdetails for request {} order {}'.
                     format(server_mess.id_, order_id))
        

    def handle_executions_details_end():
        
        if not server_mess.id_ in requested_info:
            requested_info[server_mess.id_] = {}
        requested_info[server_mess.id_]['complete'] = True


    def handle_update_account_value():

        account = server_mess.account_name
        name = server_mess.key
        value = server_mess.value
        currency = server_mess.currency
        value_id = (account, name, currency)
        accounts[value_id] = value
        accounts[account, 'complete'] = False


    def handle_account_download_end():
        
        account = server_mess.account
        accounts[account, 'complete'] = True


    def handle_update_account_time():

        time_ = server_mess.time_
        accounts['last_update'] = time_


    def handle_portfolio_value():
        
        account = server_mess.account_name
        contract = server_mess.contract
        portfolio[(account, contract)] = server_mess


    def handle_tick_price():
        
        id_ = server_mess.id_
        tick_type = server_mess.type_
        price = server_mess.price
        auto_exec = server_mess.can_auto_execute
        tick_id = (id_, tick_type)
        data = (price, auto_exec)
        add_tick(tick_id, data)


    def handle_tick_size():
        
        id_ = server_mess.id_
        tick_type = server_mess.type_
        data = server_mess.size
        tick_id = (id_, tick_type)
        add_tick(tick_id, data)


    def handle_tick_string():

        id_ = server_mess.id_
        tick_type = server_mess.type_
        data = server_mess.value
        tick_id = (id_, tick_type)
        add_tick(tick_id, data)


    def handle_tick_generic():

        id_ = server_mess.id_
        tick_type = server_mess.type_
        data = server_mess.value
        tick_id = (id_, tick_type)
        add_tick(tick_id, data)


    def add_tick(id_, data):
 
        tick_data[id_] = data
        if id_[1] == 'lastTimestamp':
            tick_data[id_] = mypy.epoch2date_time(int(data))
            ticks = {k[1]: v for k, v in tick_data.items()
                     if (type(k) is tuple and
                         k[0] == id_[0])}
            with d_lock:
                work_list = tick_data[id_[0]]
                work_list.append(ticks)
                tick_data[id_[0]] = work_list


    def handle_real_time_bars():
        
        id_ = server_mess.id_
        if id_ in output_files:
            pickle.dump(server_mess, output_files[id_])
            output_files[id_].flush()
        else:
            with d_lock:
                work_list = req_data[id_]
                work_list.append(server_mess)
                req_data[id_] = work_list
        if not req_info[id_].status == 'DATA AVAILABLE':
            with i_lock:
                info = req_info[id_]
                info.status = 'DATA AVAILABLE'
                req_info[id_] = info
        
        
    def handle_historical_data():
        
        id_ = server_mess.id_
        #translate_date = not req_info[id_].info['bar_size'].endswith('day')
        if not id_ in hist_data:
            translate_date = not req_info[id_].info['bar_size'].endswith('day')
            hist_data[id_] = {'data':[], 'translate date':translate_date}
            with i_lock:
                info = req_info[id_]
                info.status = 'RECEIVING DATA'
                req_info[id_] = info
        if server_mess.date_ == 'READY':
            with d_lock:  
                req_data[id_] = hist_data[id_]['data']
            with i_lock:
                info = req_info[id_]
                info.status = 'FINISHED'
                req_info[id_] = info
            hist_data[id_]= 'READY'
            return
        if hist_data[id_]['translate date']: #translate_date: # and server_mess.date_.isnumeric():
            date_ = mypy.epoch2date_time(int(server_mess.date_))
        else:
            try:
                date_ = mypy.py_date(server_mess.date_, '%Y%m%d')
            except ValueError:
                date_ = server_mess.date_
        message = HistoricalData(server_mess.id_, date_, server_mess.open, 
                                 server_mess.high, server_mess.low, 
                                 server_mess.close, server_mess.volume,
                                 server_mess.bar_count, server_mess.wap, 
                                 server_mess.has_gaps)
        hist_data[id_]['data'].append(message)
        #if message.date_ == 'READY':
            #with d_lock:  
                #req_data[id_] = hist_data[id_]['data']
            #with i_lock:
                #info = req_info[id_]
                #info.status = 'FINISHED'
                #req_info[id_] = info
            #hist_data[id_]= 'READY'
        #else:
            #hist_data[id_]['data'].append(message)

    
    def change_output_settings():

        id_ = outputfiles.get()
        if id_ in output_files:
            output_files[id_].close()
            del output_files[id_]
        else:
            filename, reset = outputfiles.get()
            mode = 'wb' if reset else 'ab'
            output_files[id_] = open(filename, mode)
        
        
                   

    handle = {Error: handle_error,
              CurrentTime: handle_current_time,
              ContractDetails: handle_contract_details,
              ContractDetailsEnd: handle_contract_details_end,
              NextValidId: handle_next_valid_id,
              OpenOrderEnd: handle_open_order_end,
              OpenOrder: handle_open_order,
              OrderStatus: handle_order_status,
              ExecDetails: handle_exec_details,
              ExecutionDetailsEnd: handle_executions_details_end,
              UpdateAccountValue: handle_update_account_value,
              AccountDownloadEnd: handle_account_download_end,
              UpdateAccountTime: handle_update_account_time,
              PortfolioValue: handle_portfolio_value,
              TickPrice: handle_tick_price,
              TickSize: handle_tick_size,
              TickString: handle_tick_string,
              TickGeneric: handle_tick_generic,
              RealTimeBars: handle_real_time_bars,              
              HistoricalData: handle_historical_data}
    
    max_real_time_bars = MAX_REAL_TIME_BAR_LIST
    output_files = {}
    hist_data = {}
    contract_data = {}

    while True:
        server_mess = server_messages.get()
        while not outputfiles.empty():
            change_output_settings()
        try:
            handle[type(server_mess)]()
        except KeyError:
            std_list.append(server_mess)
            log.warning('unhandeled server message \n{}\n'.format(server_mess))

    
    
