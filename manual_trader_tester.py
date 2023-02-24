#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
import pickle

import roc_input as r_in
from roc_datetime import now

import marketdata
import market
import virtualmarkets
import trader
import strategies

def main():
    test_trader = trader.Trader()
    available_requests = []
    menu = main_menu()
    while True:
        print()
        choice = menu.get_users_choice()
        if callable(choice):
            choice(
                test_trader=test_trader,
                available_requests=available_requests,
            )
        elif choice == 'QUIT': 
            break
        else:
            print(choice, 'not implemented')
        
def add_market(**kw_d):
    test_trader = kw_d['test_trader']
    menu = market_menu()
    name = r_in.get_string(
        message='market name: ',
        empty=True,
    )
    choice = menu.get_users_choice()
    if callable(choice):
        new_market = choice()
    else:
        new_market = choice
    try:
        test_trader.add_market(new_market, name)
    except trader.Error as err:
        print('\n!!!!!!!!!!\n!! err:', err, '\n!!!!!!!!!!\n')
    except AssertionError as err:
        print('\n!!!!!!!!!!\n!! system err:', err, '\n!!!!!!!!!!\n')
    mss = 'added {name} (type: {type}) to test trader'.format(
                name=name,
                type=type(new_market),
    )
    print(mss)
    return name

def market_from_bar_list():    
    #file_name = '/home/rolcam/roce/tmp.aex.db'
    file_name = '/home/rolcam/roce/tmp.dax.db'
    with open(file_name, 'rb') as pf:
        ham, pd = pickle.load(pf)
    feeder = marketdata.data_bar_feeder(pd)
    return virtualmarkets.VirtualSingleContractIndexMarketFromDataBarStream(
                                                        feeder, 'Test', 'dax')

def add_fixed_contract(**kw_d):
    test_trader = kw_d['test_trader']
    name = r_in.get_string(
        message='contract name: ',
    )
    try:
        test_trader.fixed_contract = name
    except trader.Error as err:
        print('\n!!!!!!!!!!\n!! err:', err, '\n!!!!!!!!!!\n')
    except AssertionError as err:
        print('\n!!!!!!!!!!\n!! system err:', err, '\n!!!!!!!!!!\n')
    mss = 'added fixed contract {}'.format(name)    

def define_request(**kw_d):
    available_request = kw_d['available_requests']
    id_ = r_in.get_string(
                message='id: ',
    )
    markets = select_markets(**kw_d)
    contracts = select_contracts(**kw_d)
    direction = r_in.get_string(
                message='direction: ',
                empty=True,
    )
    size = r_in.get_integer(
                message='size: ',
                default=0,
    )
    enter_strategy = select_enter_strategy(**kw_d)
    exit_strategies = []
    while 1:
        exit_strategy = select_exit_strategy(**kw_d)
        exit_strategies.append(exit_strategy)
        if not r_in.get_bool('add more strategies {}', default=False):
            break
    created = r_in.get_datetime(
                message='created (Y/M/D h:m:s): ',
                time_format='%Y/%m/%d %H:%M:%S',
                empty=True,
    )
    virtual = r_in.get_bool(
                message='use virtual mode ({})',
                default=False,
    )
    request = trader.TraderRequest(
        id_=id_,
        markets=markets,
        contracts=contracts,
        direction=direction,
        size=size,
        enter_strategy=enter_strategy,
        exit_strategies=exit_strategies,
        created=created,
    )
    if virtual:
        request.virtual = True
    print('added new request to available requests.')
    available_request.append(request)
    
def select_enter_strategy(**kw_d):
    menu = enter_strategy_menu()
    strategy = menu.get_users_choice()(**kw_d)
    return strategy

def define_single_default(**kw_d):    
    if r_in.get_bool('delayed start {}? ', default=False):
        start = r_in.get_datetime(
            message='start @: ',
            time_format='%Y/%m/%d %H:%M:%S',
        )
    else:
        start = 'now'
    if not r_in.get_bool('good till cancel {}? ', default=True):
        valid_until = r_in.get_datetime(
            message='start @: ',
            time_format='%Y/%m/%d %H:%M:%S',
        )
    else:
        valid_until = 'gtc'
    limit_price = r_in.get_currency_value(
        message='limit price, 0 or empty is no limit',
        default=0,
    )
    strategy = strategies.SingleDefault(
        start, 
        valid_until, 
        limit_price
    )
    return strategy
    
def select_exit_strategy(**kw_d):
    menu = exit_strategy_menu()
    strategy = menu.get_users_choice()(**kw_d)
    return strategy

def define_single_stop_profit_taker(**kw_d):
    strategy_args = dict()
    if r_in.get_bool('Use fixed stop {}', default=False):
        fix_stop = r_in.get_currency_value(
            message='stop @? ',
        )
        strategy_args['fix_stop'] = fix_stop
    else:
        #stop_base = r_in.get_string(
            #message='stop base: '
        #)
        #strategy_args['stop_base'] = stop_base
        strategy_args['stop_base'] = (
                  exit_strategy_base_menu().get_users_choice())        
        stop_ofset = r_in.get_currency_value(
            message='stop ofset: ',
            empty=True,
        )
        if stop_ofset:
            strategy_args['stop_ofset'] = stop_ofset
        else:
            stop_percentage = r_in.get_float(
                message='stop percentage: ',
            )
            strategy_args['stop_percentage'] = stop_percentage
        initial_safety_stop_value = r_in.get_float(
            message='initial safety stop value: ',
            empty=True,
        )
        if initial_safety_stop_value:
            strategy_args['initial_safety_stop_value'] = (
                                           initial_safety_stop_value)
    if r_in.get_bool('Use fixed profit taker {}', default=False):
        fix_profit = r_in.get_currency_value(
            message='profit taker @? ',
        )
        strategy_args['fix_profit'] = fix_profit
    else:
        #profit_base = bar_in.get_string(
            #message='profit base: '
        #)
        #strategy_args['profit_base'] = profit_base
        strategy_args['profit_base'] = (
                  exit_strategy_base_menu().get_users_choice())
        profit_ofset = r_in.get_currency_value(
            message='profit ofset: ',
            empty=True,
        )
        if profit_ofset:
            strategy_args['profit_ofset'] = profit_ofset
        else:
            profit_percentage = r_in.get_float(
                message='profit percentage: ',
            )
            strategy_args['profit_percentage'] = profit_percentage
    return strategies.SingleStopProfitTaker(**strategy_args)
        
def select_markets(**kw_d):
    menu = market_selection_menu()
    markets = menu.get_users_choice()(**kw_d)
    return markets

def request_single_free_market(**kw_d):
    market_name = r_in.get_string(
        message='name of market for trader: ',
        empty=True
    )
    market_name = market_name or None
    return market_name

def request_single_safe_market(**kw_d):
    menu = available_markets_selection_menu(**kw_d)
    market_name = menu.get_users_choice()
    return market_name
    
def request_free_market_dict(**kw_d):
    market_dict = dict()
    while 1:
        name = r_in.get_string(
                message='local market name: ',
        )
        target_name = r_in.get_string(
                message='trader market name: ',
        )
        market_dict[name] = target_name
        if not r_in.get_bool('add more market(s) {}? ', default=True):
            break
    return market_dict

def request_safe_market_dict(**kw_d):
    menu = available_markets_selection_menu(**kw_d)
    market_dict = dict()
    while 1:
        name = r_in.get_string(
                message='local market name: ',
        )
        target_name = menu.get_users_choice()
        market_dict[name] = target_name
        if not r_in.get_bool('add more market(s) {}? ', default=True):
            break
    return market_dict

def select_contracts(**kw_d):
    menu = contracts_selection_menu()
    contracts = menu.get_users_choice()(**kw_d)
    return contracts

def request_single_contract(**kw_d):
    contract = r_in.get_string(
        message='name of contract for trader: ',
        empty=True
    )
    contract = contract or None
    return contract
    
def request_contract_dict(**kw_d):
    contract_dict = dict()
    while 1:
        name = r_in.get_string(
                message='local contract name: ',
        )
        target_name = r_in.get_string(
                message='trader contract name: ',
        )
        contract_dict[name] = target_name
        if not r_in.get_bool('add more contract(s) {}? ', default=True):
            break
    return contract_dict or None
    
def send_request(**kw_d):
    test_trader = kw_d['test_trader']
    available_requests = kw_d['available_requests']
    if not available_requests:
        print('No requests available')
        return
    menu = available_requests_selection_menu(**kw_d)
    request_nr = menu.get_users_choice()
    print('last syncronisation time: ', test_trader.last_sync())
    request_time = r_in.get_datetime(
                message='send @: (Y/M/D h:m:s): ',
                time_format='%Y/%m/%d %H:%M:%S',
                empty=True,
    )
    try:
        test_trader.add_requests([available_requests[request_nr]], request_time)
    except trader.RequestRejectedError as err:
        print('send request failed: {}'.format(err))
        
def guard_requests(**kw_d):
    #print('@@@@@ mtt/guard_requests @@@@@')
    test_trader = kw_d['test_trader']
    test_trader.check_active_requests(now())
    
def trader_info(**kw_d):
    test_trader = kw_d['test_trader']
    menu = trader_info_menu()
    choice = menu.get_users_choice()
    choice(**kw_d)
    
def print_trader_str_representation(**kw_d):
    test_trader = kw_d['test_trader']
    print('\n')
    print(test_trader, '\n')

def print_trader_markets(**kw_d):
    test_trader = kw_d['test_trader']
    print('\nMARKETS\n')
    for name, market in test_trader.markets.items():
        print('{name:15}: {type}'.format(
                    name=name,
                    type=type(market),
        ))
    print('\n----------\n')
    
def show_request_lists(**kw_d):
    menu = show_request_lists_menu()
    list_to_show = menu.get_users_choice()
    list_to_show(**kw_d)
    
def show_rejected_requests(**kw_d):
    test_trader = kw_d['test_trader']
    request_list = test_trader.rejected_requests   
    print('REJECTED REQUESTS')  
    print('===============')    
    for full_request in request_list.values():
        print(full_request['request'])
        print('!! REJECTED: ', full_request['rejected'])
        print()
        
def show_active_requests(**kw_d):
    test_trader = kw_d['test_trader']
    request_list = test_trader.active_requests    
    print('ACTIVE REQUESTS')  
    print('===============')    
    for request in request_list.values():
        print(request.request)
        print('ORDERS: ', request.orders)
        print('MANAGERS: ', request.managers)
        print()
        
def show_unfilled_requests(**kw_d):
    test_trader = kw_d['test_trader']
    request_list = test_trader.unfilled_requests    
    print('UNFILLED REQUESTS')  
    print('===============')    
    for request in request_list.values():
        print(request.request)
        
def show_finished_requests(**kw_d):
    test_trader = kw_d['test_trader']
    request_list = test_trader.finished_requests  
    print('FINISHED REQUESTS')  
    print('===============')    
    for request in request_list.values():
        print(request.request)

def show_erroneous_requests(**kw_d):
    test_trader = kw_d['test_trader']
    request_list = test_trader.erroneous_requests    
    print('ERRONEOUS REQUESTS')  
    print('===============')    
    for request in request_list.values():
        print(request.request)
        print('ORDERS: ', request.orders)
        print('MANAGERS: ', request.managers)
        print()

def market_info(**kw_d):
    menu = market_info_menu()
    choice = menu.get_users_choice()
    choice(**kw_d)
    
def print_market_str_representation(**kw_d):
    test_trader = kw_d['test_trader']
    market = request_single_safe_market(**kw_d)
    print('\n')
    print(test_trader.markets[market], '\n')
    
def show_active_orders(**kw_d):
    test_trader = kw_d['test_trader']
    market = request_single_safe_market(**kw_d)
    for id_, order in test_trader.markets[market].active_orders.items():
        print(id_, order)
        
def show_finished_orders(**kw_d):
    test_trader = kw_d['test_trader']
    market = request_single_safe_market(**kw_d)
    for id_, order in test_trader.markets[market].finished_orders.items():
        print(id_, order)   
    
def request_info(**kw_d):
    menu = request_info_menu()
    choice = menu.get_users_choice()
    choice(**kw_d)
    
def show_all_available_requests(**kw_d):
    available_requests = kw_d['available_requests']
    for i, request in enumerate(available_requests):
        print('tester id: ', i)
        print(request)
        print()
    
# MENU DEFINITIONS   
    
def main_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='choice: ',
                auto_number=True,
    )
    m.add_menu_item('add market', return_value=add_market)
    m.add_menu_item('add_fixed_contract', return_value=add_fixed_contract)
    m.add_menu_item('remove market')
    m.add_menu_item('define request', return_value=define_request)
    m.add_menu_item('change request')
    m.add_menu_item('send request', return_value=send_request)
    m.add_menu_item('check active requests', return_value=guard_requests)
    m.add_menu_item('get trader info', return_value=trader_info)
    m.add_menu_item('get market info', return_value=market_info)
    m.add_menu_item('get request info', return_value=request_info)
    m.add_menu_item('QUIT')
    return m

def market_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='choice: ',
                auto_number=True,
    )
    m.add_menu_item('a not a market (error!!)', return_value='market')
    m.add_menu_item('market.Market', return_value=market.Market)
    m.add_menu_item('barlist', return_value=market_from_bar_list)
    return m
    
def trader_info_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='choice: ',
                auto_number=True,
    )
    m.add_menu_item('string representation', 
                    return_value=print_trader_str_representation)
    m.add_menu_item('available markets', return_value=print_trader_markets)
    m.add_menu_item('request_lists', return_value=show_request_lists)
    return m

def market_info_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='choice: ',
                auto_number=True,
    )
    m.add_menu_item('string representation',
                    return_value=print_market_str_representation)
    m.add_menu_item('active orders', return_value=show_active_orders)
    m.add_menu_item('finished orders', return_value=show_finished_orders)
    return m
    

def request_info_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='choice: ',
                auto_number=True,
    )
    m.add_menu_item('show all available requests', 
                    return_value=show_all_available_requests)
    return m

def show_request_lists_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='choice: ',
                auto_number=True,
    )
    m.add_menu_item('rejected_requests', return_value=show_rejected_requests)
    m.add_menu_item('active_requests', return_value=show_active_requests)
    m.add_menu_item('unfilled_requests', return_value=show_unfilled_requests)
    m.add_menu_item('finished_requests', return_value=show_finished_requests)
    m.add_menu_item('erroneous_requests', return_value=show_erroneous_requests)
    return m

def market_selection_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='market selection mode: ',
                auto_number=True,
    )
    m.add_menu_item('single free', return_value=request_single_free_market)
    m.add_menu_item('single safe', return_value=request_single_safe_market)
    m.add_menu_item('dict free', return_value=request_free_market_dict)
    m.add_menu_item('dict safe', return_value=request_safe_market_dict)
    return m

def contracts_selection_menu():
    m = r_in.SelectionMenu(
                interface='TXT_ROW',
                message='contract selection mode: ',
                auto_number=True,
    )
    m.add_menu_item('single', return_value=request_single_contract)
    m.add_menu_item('dict', return_value=request_contract_dict)
    return m

def enter_strategy_menu():
    m = r_in.SelectionMenu(
        message='select enter strategy: ',
        auto_number=True,
    )
    m.add_menu_item('single_default', return_value=define_single_default)
    return m

def exit_strategy_menu():
    m = r_in.SelectionMenu(
        message='select exit strategy: ',
        auto_number=True,
    )
    m.add_menu_item('single_stop_profit_taker', 
                    return_value=define_single_stop_profit_taker)
    return m

def exit_strategy_base_menu():
    m = r_in.SelectionMenu(
        interface='TXT_LINE', 
        message='base: ',
        auto_number= True,
    )
    m.add_menu_item('avg_parent_in')
    return m

def available_markets_selection_menu(**kw_d):
    test_trader = kw_d['test_trader']
    assert isinstance(test_trader, trader.Trader)
    available_markets = test_trader.markets
    m = r_in.SelectionMenu(
            message='market: ',
            auto_number=True
    )
    m.add_items(available_markets)
    return m

def available_requests_selection_menu(**kw_d):
    ### solve problem so i can use the same id twice!!!!!!!
    available_requests = kw_d['available_requests']
    choices = [x.id_ for x in available_requests]
    m = r_in.SelectionMenu(
            message='request: ',
            auto_number=True,
            auto_return_value='NR',
    )
    m.add_items(choices)
    return m

def get_contract_info():
    menu = r_in.SelectionMenu(auto_number=True)
    menu.add_menu_item(
        'AEX', 
        return_value=(
            tws.contract_data("AEX-index"),
            "/home/rolcam/roce/Data/db/EOE IND EUR AEX@FTA.db",
            "TRADES", 
            "TRADES_5_secs",
        ),
    )
    menu.add_menu_item(
        "DAX", 
        return_value=(
            tws.contract_data("DAX-30"),
            "/home/rolcam/roce/Data/db/DAX IND EUR DAX@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
        ),
    )
    menu.add_menu_item(
        "EUR.USD", 
        return_value=(
            tws.contract_data("euro-dollar"),
            "EUR CASH USD EUR.USD@IDEALPRO.db",
            "MIDPOINT", 
            "MIDPOINT_5_secs",
        ),
    )
    menu.add_menu_item(
        "Eurostoxx", 
        return_value=(
            tws.contract_data("DJ_Eurostoxx50"),
            "ESTX50 IND EUR ESTX50@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
        ),
    )
    
if __name__ == '__main__':
    main()
