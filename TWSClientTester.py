#!/usr/bin/env python3

from multiprocessing import Queue

import TWSClient
import twsclientapps
import TWSTrader_corseabc
from time import sleep
import mypy
import tws
import TWSClientServerMessages as M

CLIENT_ID = 666
client_id = CLIENT_ID #mypy.get_int('client id ({})'.format(CLIENT_ID),
                         #default=CLIENT_ID)
#IP = '10.1.1.102'
#ip = mypy.get_string('ip ({})'.format(IP),
                         #default=IP)
##twss = TWSClient.TWSconnection('localhost', client_id=client_id)
#try:
    #twss = TWSClient.TWSconnection(ip, 10911, client_id=client_id)
#except TWSClient.ConnectingError:
    #print('Problem')
    #exit()
    
twss = twsclientapps.set_up_tws_connection(client_id=client_id, 
                                           interactive=True)
if not twss:
    exit()
traderlist = {}

last_entry = mypy.now().replace(hour=17, minute=10, second=0)

an_index = tws.contract_data('AEX-index')
a_us_index = tws.contract_data('DJ_Industrial')
a_sec = tws.contract_data('Deutsche_bank')
a_us_sec = tws.contract_data('Apple')
dax = tws.contract_data('DAX-30')
dax_fut = tws.contract_data('DAX-30_FUT')
eurdol = tws.contract_data('euro-dollar')

simple_order_settings = dict(clientId=client_id,
                             lmtPrice=25.00)
market_order_settings = dict(clientId=client_id,
                             orderType='MKT')
abc_bracket_order_settings = dict(number_of_contracts=10,
                                  direction='BULL',
                                  enter_type='STP LMT',
                                  enter_trade_before=last_entry)            
filter_settings = dict(clientId=client_id)


                  
while 1:
    m = mypy.get_int('message code to send: ')
    if m > 0:
        twss.send(m)
    elif m == -1:  # stop
        break
    elif m == -2:  # print std list
        mypy.print_list(twss.std_mess_list, 'STANDARD LIST')
    elif m == -3:  # print err list
        mypy.print_list(twss.err_list, 'ERROR LIST')
    elif m == -4: # list open orders list
        mypy.print_dict(twss.open_orders, 'OPEN ORDERS')
        #for k, v in twss.open_orders.items():
        #    print(k, v)
    elif m == -5:
        mypy.print_dict(twss.order_status, 'ORDER STATUS')
    elif m == -6:
        mypy.print_dict(twss.executed_orders, 'EXECUTED ORDERS')

    elif m == -10:  # print contract details for id
        id_ = mypy.get_int('contract details for id? ')
        mypy.print_list(twss.read_contract_details(id_), 
                        'info for id {}'.format(id_))
    elif m == -11:  # print exec details for id
        id_ = mypy.get_int('exec details for id (empty=current)? ')
        print(twss.read_executions_details(id_))
    elif m == -15:  # print historical data from id
        id_ = mypy.get_int('historical data from id? ')
        print(twss.get_historical_request_data(id_))

    elif m == -20:  # dump account info
        print(twss.dump_account_info())
    elif m == -21:  # read account info
        value = mypy.get_string('value of ')
        curr = mypy.get_string('in currency ', default='BASE')
        print('value: ', twss.get_account_info(value, curr))
    elif m == -22:  # print time of last update
        print('last update ', twss.get_last_account_update())
    elif m == -23:  # dump portfolio info
        print(twss.dump_portfolio())

    elif m == -30:  # dump market ticks
        id_ = mypy.get_int('market id to dump: ')
        name = mypy.get_string('info name (lastPrice): ',
                               empty=True)
        print(twss.dump_ticks(id_, name))

    elif m == -40:  # dump real ticks
        id_ =  mypy.get_int('real bar id to dump: ')
        print(twss.dump_real_time_bars(id_))
    elif m == -41:  # loop over  real req id
        id_ =  mypy.get_int('real bar id to loop: ')
        while True:
            try:
                line = twss.real_bar_from(id_)
                print(line)
            except KeyboardInterrupt:
                break

    elif m == -50: # list trader
        for trader in traderlist.values():
            print('{}: {}'.format(trader.name, trader.status))
            
    elif m == -60: # start a backdoor
        file_name = mypy.get_string('backdoor file name: ')
        open(file_name, 'w').close()
        twss.open_info_backdoor(file_name)

    elif m == -101:  # req & print current time
        t = twss.req_current_time()
        print('It\'s {}'.format(t))
    elif m == -102:  # req execution data
        mypy.get_int('for client id ({})'.format(client_id), 
                     default = client_id)
        filter_ = tws.def_execution_filter(**filter_settings)
        id_ = twss.request_executions(filter_)
        print('Requesting execution details with id {}'.format(id_))

    elif m == -110:  # ask an_index details
        print('Working with : {}'.format(an_index))
        id_ = twss.req_contract_details(an_index)
        print('request id = {}'.format(id_))
    elif m == -111:  # ask a_us_index details        
        print('Working with : {}'.format(a_us_index))
        id_ = twss.req_contract_details(a_us_index)
        print('request id = {}'.format(id_))
    elif m == -112:  # ask a_us_sec details
        print('Working with : {}'.format(a_us_sec))
        id_ = twss.req_contract_details(a_us_sec)
        print('request id = {}'.format(id_))
    elif m == -115: #make a contract and ask details
        ctr = tws.def_contract()
        symbol, secType, expiry, strike, right, multiplier, \
             exchange, currency, localSymbol, woo, includeExpired, \
             foo, bar, conId, secIdType, secId, boo = ctr
        conId = mypy.get_int('conId: ', default=conId)
        symbol = mypy.get_string('symbol: ', default=symbol)
        secType = mypy.get_string('secType: ', default=secType)
        expiry = mypy.get_string('expiry: ', empty=True)
        strike = mypy.get_float('strike: ', default=strike)
        right = mypy.get_string('right: ', empty=True)
        multiplier = mypy.get_string('multiplier: ', empty=True)
        exchange = mypy.get_string('exchange: ', empty=True)
        currency = mypy.get_string('currency: ', empty=True)
        localSymbol = mypy.get_string('localSymbol: ', empty=True)
        includeExpired = mypy.get_string('includeExpired: ', empty=True)
        secIdType = mypy.get_string('secIdType: ', empty=True)
        secId = mypy.get_string('secId: ', empty=True)
        ctr = tws.def_contract(symbol, secType, expiry, strike, right, 
                               multiplier, exchange, currency, localSymbol,
                               woo, includeExpired, foo, bar, conId, secIdType,
                               secId, boo)
        print(ctr)
        id_ = twss.req_contract_details(ctr)
        print('request id = {}'.format(id_))
        
        
        

    elif m == -120:  # start account_info
        print('starting account info')
        succes = twss.account_info('START')
        print('succes: ', succes)
    elif m == -121:  # stop account_info
        print('stopping account info')
        succes = twss.account_info('STOP')
        print('succes: ', succes)

    elif m == -130:  # request an_index market data
        print('starting market data request')
        id_ = twss.req_market_data(an_index)
        print('id: ', id_ )
    elif m == -131:  # request a_us_sec_market data
        print('starting market data request')
        id_ = twss.req_market_data(a_us_sec)
        print('id: ', id_ )
    elif m == -139: # stop market data
        id_ = mypy.get_int('market id to stop: ')
        twss.stop_market_data(id_)

    elif m == -140:  # request an_index real bar data
        print('starting market data request')
        id_ = twss.req_real_time_bars(an_index)
        print('id: ', id_ )
    elif m == -141:  # request a_us_sec_real bar data
        print('starting market data request')
        id_ = twss.req_real_time_bars(a_us_sec)
        print('id: ', id_ )
    elif m == -145:  # request real data for contract
        contract = mypy.get_string('contract name:')
        try:
            contr_data = tws.contract_data(contract)
        except mypy.ContractNotInDB:
            print('Unknown contract')
            continue
        id_ = twss.req_real_time_bars(contr_data)
        print('id: ', id_ )
    elif m == -148:  # set outputfile for bardata
        stream = mypy.get_int('id: ')
        filename = mypy.get_string('filename: ')
        twss.set_outputfile_for_id(stream, filename)
    elif m == -149: # stop market data
        id_ = mypy.get_int('market id to stop: ')
        twss.stop_real_time_bars(id_)
    elif m == -150:  #request historical data
        contract = mypy.get_string('contract name:')
        try:
            contr_data = tws.contract_data(contract)
        except mypy.ContractNotInDB:
            print('Unknown contract')
            continue
        end_date = mypy.get_date('end date: ')
        duration = mypy.get_string('duration (int[SDWMY]): ')
        barsize = mypy.get_string('barsize (1 sec, 5 secs ...): ')
        what = mypy.get_string('what to show: ')
        rth = not(mypy.get_bool('outside reg. trading hours (y/n): '))
        id_ = twss.req_historical_data(contr_data, end_date, duration, barsize,
                                       what, rth)
        print('id: ', id_ )
        

    elif m == -201:  # send a_us_sec limit order
        p = mypy.get_float('price (25,00): ', default=25.00)
        simple_order_settings['lmtPrice'] = p
        id_ = twss.place_order(a_us_sec, simple_order_settings)
        print('order id: ', id_)
    elif m == -202: # send a_sec limit order
        p = mypy.get_float('price (25,00): ', default=25.00)
        simple_order_settings['lmtPrice'] = p
        id_ = twss.place_order(a_sec, simple_order_settings)
        print('order id: ', id_)
    elif m == -203: # send a_us_sec market order
        id_ = twss.place_order(a_us_sec, market_order_settings)
        print('order id: ', id_)
    elif m == -204: # send a_sec
        id_ = twss.place_order(a_sec, market_order_settings)
        print('order id: ', id_)
    elif m == -205:
        market_order_settings['totalQuantity'] = 100000
        id_ = twss.place_order(eurdol, market_order_settings) 
        print('order id: ', id_)
                                  
    elif m == -210: # send a_us_sec bracket_order
        last_entry = mypy.now().replace(hour=17, minute=10, second=0)
        a = mypy.get_float('a (25,00): ', default=25.00)
        b = mypy.get_float('b (30,00): ', default=30.00)
        c = mypy.get_float('c (20,00): ', default=20.00)
        os = abc_bracket_order_settings
        os.update({'enter_limit': a, 
                   'enter_aux': a,
                   'profit_limit': b,
                   'stop_aux': c,
                   'EOD_sell': True})
        br_order = tws.def_bracket_order(**os)
        id_p, id_g, id_s, id_e = twss.place_bracket_order(a_us_sec,
                                                          br_order)
        print('id\'s: {} | {} | {} | {}'.format(id_p, id_g, id_s, id_e))
    elif m == -220:  # change an order
        id_ = mypy.get_int('change order? ')
        li = mypy.get_float('li (0): ', default=0)
        au = mypy.get_float('b (0): ', default=0)
        qu = mypy.get_float('c (0): ', default=0)
        li = li if not li == 0 else None
        au = au if not au == 0 else None
        qu = qu if not qu == 0 else None
        twss.change_order(id_, li, au, qu)
    elif m == -299:  # cancel order
        id_ = mypy.get_int('order id to cancel: ')
        twss.cancel_order(id_)

    elif m == -300:  # print avg diff between 2 contracts
        c1 = mypy.get_int('req id of first contract(1): ', default=1)
        c2 = mypy.get_int('req id of second contract(2): ', default=2)
        print( twss.average_difference(c1, c2)[0])
    elif m == -301:  # loop avg diff
        c1 = mypy.get_int('req id of first contract(1): ', default=1)
        c2 = mypy.get_int('req id of second contract(2): ', default=2)
        while True:
            print( twss.average_difference(c1, c2)[0])
            sleep(5)


    elif m == -500: # add trader
        name = mypy.get_int('tradername(id): ')
        b = mypy.get_float('b (30,00): ', default=30.00)
        c = mypy.get_float('c (20,00): ', default=20.00)
        trader = TWSTrader_corseabc.Trader(name, b, c, twss)
        traderlist[name] = trader
    elif m == -501: # add dax trader
        last_entry = mypy.now().replace(hour=17, minute=10, second=0)
        exit_trade = mypy.now().replace(hour=17, minute=28, second=0) 
        name = mypy.get_int('tradername(id): ')
        b = mypy.get_float('b (30,00): ', default=30.00)
        c = mypy.get_float('c (20,00): ', default=20.00)
        trader = TWSTrader_corseabc.Trader(name, b, c, twss,
                                           max_stop=16,
                                           lb_profit=98,
                                           trading_permitted_until=last_entry,
                                           close_positions_after=exit_trade,
                                           min_price_variation=0.5)
        traderlist[name] = trader
    elif m == -510: # send order to trader
        trader_name = mypy.get_int('tradername(id): ')
        contractname = mypy.get_string('Contract name: ')
        try:
            contract = tws.contract_data(contractname)
        except KeyError:
            print('contract unknown')
            continue
        noc = mypy.get_int('number of contracts: ')
        a = mypy.get_float('a (25,00): ', default=25.00)
        trader = traderlist[trader_name]
        trader.send_order(contract, noc, a)
        print(trader.enter_id, trader.profit_id, trader.stop_id, trader.moc_id)
    elif m == -519: # remove order
        trader_name = mypy.get_int('tradername(id): ')
        trader = traderlist[trader_name]
        trader.remove_order()
    elif m == -520: # change order
        trader_name = mypy.get_int('tradername(id): ')
        trader = traderlist[trader_name]
        a = mypy.get_float('new a: ')
        trader.send_new_a_value(a)

    elif m == -1000:
        mm = input('text to send: ')
        twss.send(mm)
twss.disconnect()
