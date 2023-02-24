#!/usr/bin/env python3
#
#  Copyright (c) 2012, 2013 Rolf Camps (rolf.camps@scarlet.be)
#

# fmm: full modular mode

from datetime import datetime, timedelta
import pickle

import roc_input as r_in
import tws
import historicaldata_new as historicaldata
import marketdata_prod as marketdata
import virtualmarkets
import triads2
import trader
import market
from permtradingsystem import PermBasicTestTraderDev as PermBasicTestTrader
#from theotrader import TheoreticalSinglePositionTrader as TheoTrader

from lifeguard import Lifeguard

CLIENT_ID = 48
IP = 'localhost' #'10.1.1.102'
PORT = 10911

def main():
    
    ##quick selection for testing, menufy it
    ##
    print('algo contract: ', end='')
    contract, db_name, dataset_ib, dataset_db, foo = get_contract_info()
    print('trader contract: ', end= '')
    contract_t, db_name_t, dataset_ib_t, dataset_db_t, min_tick = get_contract_info()
    continue_with_live_data = r_in.get_bool(
        message='continue with live data {}: ',
        default=False,
    )
    if continue_with_live_data:
        use_lifeguard = r_in.get_bool(
            message='use lifeguard {}',
            default=True
        )
    else:
        use_lifeguard = False
    if not r_in.get_bool("use min_tick {}? ", default=True):
        min_tick=None
    is_index = r_in.get_bool(
        message='index data {}: ', 
        default=True,
    )
    start = r_in.get_datetime(
        message='start date ({default}): ',
        time_format='%y/%m/%d',
        default='13/09/23',
    ).date()
    end = r_in.get_datetime(
        message='end date ({default}): ',
        time_format='%y/%m/%d',
        #default='13/10/14',
        empty=True,
    )
    end = end.date() if end else None
    update_db = r_in.get_bool(
                message='update db {}: ',
                default=False,
    )
    sound_warning_report = terminal_report = True
    if r_in.get_bool("Exit end of day? (Y/n)", default=True):
        while True:
            try:
                eorth = r_in.get_time(
                    'How late do the markets close today ({default})? ',
                    time_format='%H:%M:%S',
                    default="17:30:00"
                )
                #eorth = mypy.py_time(eorth)
                break
            except ValueError:
                print('Can not proces date format')
        last_entry = r_in.get_timedelta("last entry (900 s):",
                                  default = '900 s') #'4500 s')
        managed_exit = r_in.get_timedelta("managed exit (sec before eod:",
                                    empty=True)
        forced_exit = r_in.get_timedelta("force exit (120 s):",
                                   default = '120 s') #'1800 s')
    else:
        eorth = last_entry = managed_exit = forced_exit = None
    print('settings')
    print('========')
    print(db_name, '( index: ', is_index, ')')
    print('start: ', start)
    print('stop: ', end)
    print('terminal report: ', terminal_report)
    print('sound warning: ', sound_warning_report)
    ##
    #########################################
    
    if use_lifeguard:
        lifeguard = Lifeguard('ssr', timedelta(seconds=7))
        
    feeder = marketdata.data_bar_feeder(
                db_name, 
                is_index=is_index, 
                start=start, 
                stop=end,
                update=update_db,
                contract=contract, #only usefull for update True
    )       
    live_feeder = marketdata.data_bar_feeder(
                    '__tws_live__',
                    contract=contract,
                    barsize='5 secs',
                    show='TRADES',
                    is_index=True,                
    )
    new_bars_kwds_dic = {
        'feeder':feeder,
        #'minutes':1,
        'seconds':60,  ###############################################################
    }
    if continue_with_live_data:
        new_bars_kwds_dic['live_feeder'] = live_feeder
    new_bars = marketdata.ComposingDatabarFeeder(**new_bars_kwds_dic)
    #
    #
    #new_bars.export_settings(destination='terminal')
    # or
    new_bars.export_settings(
        destination='csv',
        filename='/tmp/exp.t0',
    )
    #
    #    
    triad_list = triads2.TriadReducer(60)
    triad_list.export_settings(
        destination='csv',
        filename='/tmp/exp.t1',
    )
    new_bars.export_add_action_linked_export_system(triad_list)
    swing_analyser = triads2.SwingCountingByArgs()
    swing_analyser.export_settings(
        destination='csv',
        filename='/tmp/exp.t2',
    )
    new_bars.export_add_action_linked_export_system(swing_analyser)
    #perm_trading_system = PermsTradingSystem_0(
        #unique_request_id = 'PTS0', #this is not unique enough, for testing
        #contract_name='DAX index',
        #wavecount_in=[2,4,6,8,10,12,14,16,18],
        #reverse=True,
    #)
    #perm_trading_system.use_theoretical_trader(TheoTrader(
        #stoploss_handler='kiss', 
        #profit_handler='kiss', 
        #trailing_exit='entry+percent', start_trailing_at=0.07, 
        ##fix_exit=False, fix_at=0, 
        ##max_gap_to_curr=False, max_gap=0, 
        ##min_gap_to_curr=False, min_gap=0, 
        #cap_stop='entry+%', cap=.07,
    #))
    #perm_trading_system.use_daytrader_mode(
            #std_end_time=eorth,
            #last_in=last_entry,
            #managed_out=managed_exit,
            #last_out=forced_exit
    #)
    #perm_trading_system.export_settings(
        #destination='csv',
        #filename='/tmp/exp.t3',
    #)
    report_destinations = []
    if sound_warning_report:
        report_destinations.append('sound')
    if terminal_report:
        report_destinations.append('terminal')
    #new_bars.export_add_action_linked_export_system(perm_trading_system)
    #perm_trading_system.check_setup()
    p_trader = PermBasicTestTrader(min_tick=min_tick)
    p_trader.fixed_contract = db_name_t   
    #t_feeder = [marketdata.data_bar_feeder(
                #db_name_t, 
                #is_index='False', 
                ##start=start, 
                ##stop=end,
                #update=update_db, #False,
                #contract=contract_t, #only usefull for update True
    #)  ]
    #if continue_with_live_data:
        #t_feeder.append(marketdata.data_bar_feeder(
            #'__tws_live__',
            #contract=contract_t,
            #barsize='5 secs',
            #show='TRADES',
            #is_index=False,                
    #))               
    b_feeder = marketdata.data_bar_feeder(
                db_name_t, 
                is_index='False', 
                #start=start, 
                #stop=end,
                update=update_db, #False,
                contract=contract_t, #only usefull for update True
    )
    if continue_with_live_data:
        l_feeder = marketdata.data_bar_feeder(
            '__tws_live__',
            contract=contract_t,
            barsize='5 secs',
            show='TRADES',
            is_index=False,                
        )
        t_feeder = marketdata.DBFContinuedWithLiveDBF(
            b_feeder, l_feeder)
    else:
        t_feeder = b_feeder
    t_market = virtualmarkets.VirtualSingleContractIndexMarketFromDataBarStream(
         t_feeder, db_name_t)
    p_trader.add_market(t_market)
    p_trader.set_daytrade_mode(
        end_of_day=eorth,
        last_in=last_entry,
        managed_out=managed_exit,
        last_out=forced_exit,
    )
    curr_id = None
    for announced, curr_base_bar, composing_bar, new_bar in new_bars:
        ##perm_trading_system.live_bar_checks_and_actions(curr_base_bar)
        #perm_trading_system.event(
            #event_name='new_market_data_for_theoretical_trader',
            #event_time=announced,
            #bar_or_tick=curr_base_bar,
        #)
        try:
            p_trader.check_active_requests(announced)
        except market.Error as err:
            print('scanner stopped: ', err)
            break
        if new_bar:
            #perm_trading_system.finished_bar_checks_and_actions(new_bar)
            #trader should do his own bar keeping
            new_triad = triad_list.insert(new_bar)
            if new_triad:
                perms = swing_analyser.register(new_triad)
                if perms:
                    p_trader.new_perms(perms, announced)
                    #r = p_trader.new_perms(perms, announced)
                    #if not r == 'in trade':
                        #curr_id = r
                    #requests = perm_trading_system.event(
                        #event_name='register_perm_lines',
                        #event_time=announced,
                        #perm_lines=perms,
                    #)
                    #for request in requests:
                        #print(request)
                    #print('\n++++++++++++++++++++++++++')
                    #print(perms)
            #if curr_id:
                #p_trader.current_value_of_request(curr_id, announced)
            continue
        if True: #new_bars.live_mode:
            advises = []
            use_lifeguard and lifeguard.alife()
            if composing_bar: # for production add check for live running
                new_triad = triad_list.virtual_insert(composing_bar)
                if new_triad:
                    perms = swing_analyser.virtual_register(new_triad)
                    if perms:
                        p_trader.virtual_new_perms(perms, announced)
                        #advises = perm_trading_system.event(
                            #event_name='register_virtual_perm_lines',
                            #event_time=announced,
                            #perm_lines=perms,
                            #)
                        #for advise in advises:
                            #print(advise)
                        #print('\n++++++++++++++++++++++++++')
                        #print(perms)
    #for line in p_trader.finished_request_report():
        #print(line)
    #for request in sorted(p_trader.finished_requests):
        #print(p_trader.finished_requests[request])
    with open('/tmp/finreq.pck', 'wb') as pickle_file:
        #for request in sorted(p_trader.finished_requests):
            #pickle.dump(p_trader.finished_requests[request], pickle_file)
        pickle.dump(p_trader.finished_request_report(), pickle_file)
    
            
def get_contract_info():
    menu = r_in.SelectionMenu(auto_number=True)
    menu.add_menu_item(
        'AEX', 
        return_value=(
            tws.contract_data("AEX-index"),
            "/home/rolcam/roce/Data/db/EOE IND EUR AEX@FTA.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.01",
        ),
    )
    menu.add_menu_item(
        'AEX FUTURE november 2013', 
        return_value=(
            tws.contract_data('AEX_FUT1311'),
            "/home/rolcam/roce/Data/db/EOE FUT X200 20131115 EUR FTIX3@FTA.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.05",
        ),
    )
    menu.add_menu_item(
        "DAX", 
        return_value=(
            tws.contract_data("DAX-30"),
            "/home/rolcam/roce/Data/db/DAX IND EUR DAX@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.01",
        ),
    )
    menu.add_menu_item(
        "DAX FUTURE december 2013", 
        return_value=(
            tws.contract_data("DAX-30_FUT1312"),
            "/home/rolcam/roce/Data/db/DAX FUT X25 20131220 EUR FDAX DEC 13@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.5",
        ),
    )
    menu.add_menu_item(
        "EUR.USD", 
        return_value=(
            tws.contract_data("euro-dollar"),
            "/home/rolcam/roce/Data/db/EUR CASH USD EUR.USD@IDEALPRO.db",
            "MIDPOINT", 
            "MIDPOINT_5_secs",
            "0.000001",
        ),
    )
    menu.add_menu_item(
        "Eurostoxx", 
        return_value=(
            tws.contract_data("DJ_Eurostoxx50"),
            "ESTX50 IND EUR ESTX50@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
            "None",
        ),
    )
    menu.add_menu_item(
        'FTSE 100', 
        return_value=(
            tws.contract_data("FTSE-100"),
            "/home/rolcam/roce/Data/db/Z IND GBP Z@LIFFE.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.01",
        ),
    )
    menu.add_menu_item(
        'ZFTSE 100 FUTURE december 2013', 
        return_value=(
            tws.contract_data('FTSE_FUT1312'),
            "/home/rolcam/roce/Data/db/Z FUT X1000 20131220 GBP ZZ3@LIFFE.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.5",
        ),
    )
    
    return menu.get_users_choice()

if __name__ == '__main__':
    main()