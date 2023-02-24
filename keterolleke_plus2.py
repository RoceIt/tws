#!/usr/bin/env python3
#
#  Copyright (c) 2011, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

import pickle

from datetime import datetime, timedelta

import roc_input as r_in
import tws
import market
import historicaldata_new as historicaldata
#import marketdata_prod as data
import marketdata_prod as data
import triads2
import trade_simulator_for_perm_data2
import marketdata
import virtualmarkets

from lifeguard import Lifeguard
from permtradingsystem import KatiesOlTrader

CLIENT_ID = 44   ## terugzetten naar 10!
IP = 'localhost' #'10.1.1.102'
PORT = 10911

def main():
    
    ##quick selection for testing, menufy it
    ##
    contract, db_name, dataset_ib, dataset_db = get_contract_info()
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
    is_index = r_in.get_bool(
                message='index data {}: ', 
                default=True,
    )
    start = r_in.get_datetime(
                message='start date ({default}): ',
                time_format='%y/%m/%d',
                default='13/1/5',
    ).date()
    end = r_in.get_datetime(
                message='end date ({default}): ',
                time_format='%y/%m/%d',
                #default='13/01/10',
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
        last_entry = r_in.get_timedelta("last entry (4500):",
                                  default = '4500 s')
        managed_exit = r_in.get_timedelta("managed exit (sec before eod:",
                                    empty=True)
        forced_exit = r_in.get_timedelta("force exit (1800):",
                                   default = '1800 s')
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
        lifeguard = Lifeguard('keterolleke', timedelta(seconds=7)) 
        
    #_feeder = marketdata.data_bar_feeder(
                #'/home/rolcam/roce/Data/daxfut_2006.txt', 
                #is_index='False', 
    #)
    #feeder = marketdata.ComposingDatabarFeeder(
        #feeder=_feeder,
        #only_finished_bars=True,
        #seconds=5
    #)
                
    feeder = data.data_bar_feeder(
                db_name, 
                is_index=is_index, 
                start=start, 
                stop=end,
                update=update_db,
                contract=contract, #only usefull for update True
    )       
    live_feeder = data.data_bar_feeder(
                    '__tws_live__',
                    contract=contract,
                    barsize='5 secs',
                    show='TRADES',
                    is_index=True,                
    )
    new_bars_kwds_dic = {
        'feeder':feeder,
        'minutes':5,
    }
    if continue_with_live_data:
        new_bars_kwds_dic['live_feeder'] = live_feeder
    new_bars = data.ComposingDatabarFeeder(**new_bars_kwds_dic)
    #
    #
    #new_bars.export_settings(destination='terminal')
    # or
    new_bars.export_settings(
        destination='csv',
        filename='/tmp/nnplus.t0',
    )
    #
    #    
    triad_list = triads2.TriadReducer(60)
    triad_list.export_settings(
        destination='csv',
        filename='/tmp/nnplus.t1',
    )
    new_bars.export_add_action_linked_export_system(triad_list)
    swing_analyser = triads2.SwingCountingByArgs()
    swing_analyser.export_settings(
        destination='csv',
        filename='/tmp/nnplus.t2',
    )
    new_bars.export_add_action_linked_export_system(swing_analyser)
    trade_manager = trade_simulator_for_perm_data2.TradeSimulationByArgs(
            contract_name='DAX index',
            #wavecount_in=2,
            wavecount_in=[2,4,6,8,10,12,14,16,18],
            #wavecount_in=5,
            trailing_exit="entry+percent", start_trailing_at=0.2,
            #fix_exit="percent", fix_at=0.2,
            #min_gap_to_curr="entry+fix", min_gap=0.07,
            #max_gap_to_curr="entry+fix", max_gap=2,
            cap_stop='entry+%', cap=0.29,
            sph=True, 
            reverse=True)
    trade_manager.use_daytrader_mode(
            std_end_time=eorth,
            last_in=last_entry.seconds,
            managed_out=managed_exit.seconds if managed_exit else managed_exit,
            last_out=forced_exit.seconds
    )
    trade_manager.export_settings(
        destination='csv',
        filename='/tmp/nnplus.t3',
    )
    report_destinations = []
    if sound_warning_report:
        report_destinations.append('sound')
    if terminal_report:
        report_destinations.append('terminal')
    new_bars.export_add_action_linked_export_system(trade_manager)
   #############################
   #
   # adding a future trader simulator: ft
   #
    ft = KatiesOlTrader(min_tick='0.5')  
    ft.fixed_contract = 'daxfut'           
    #_b_feeder = marketdata.data_bar_feeder(
                #'/home/rolcam/roce/Data/daxfut_2006.txt', 
                #is_index='False', 
    #)
    #b_feeder = marketdata.ComposingDatabarFeeder(
        #feeder=_b_feeder,
        #only_finished_bars=True,
        #seconds=1
    #)       
    b_feeder = marketdata.data_bar_feeder(
                db_name, 
                is_index='False', 
                #start=start, 
                #stop=end,
                update=False,
                contract=contract, #only usefull for update True
    )
    if continue_with_live_data:
        l_feeder = marketdata.data_bar_feeder(
            '__tws_live__',
            contract=contract,
            barsize='5 secs',
            show='TRADES',
            is_index=False,                
        )
        t_feeder = marketdata.DBFContinuedWithLiveDBF(
            b_feeder, l_feeder)
    else:
        t_feeder = b_feeder
    
    t_market = virtualmarkets.VirtualSingleContractIndexMarketFromDataBarStream(
         t_feeder, 'daxfut')
    ft.add_market(t_market)
    ft.set_daytrade_mode(
        end_of_day=eorth,
        last_in=last_entry,
        managed_out=managed_exit,
        last_out=forced_exit,
    )
   #
   #
   #
   ###############################################################
    for announced, curr_base_bar, composing_bar, new_bar in new_bars:
        if end and announced.date() > end:
            break
        #try:
            #ft.check_active_requests(announced)
        #except market.Error as err:
            #print('scanner stopped: ', err)
            #break
        act = trade_manager.live_bar_checks_and_actions(curr_base_bar)
        if act:
            for a in act:
                print('WWWWW:', a, type(a))
                ft.keterol_traded(a[0], announced)
        try:
            ft.check_active_requests(announced)
        except market.Error as err:
            print('scanner stopped: ', err)
            break
                #print('live_bars checks & act:', a)
        if new_bar:
            act = trade_manager.finished_bar_checks_and_actions(new_bar)
            if act:
                for a in act:
                    ft.keterol_altered_trade(a, announced)
                    try:
                        ft.check_active_requests(announced)
                    except market.Error as err:
                        print('scanner stopped: ', err)
                        break
                    #print('finished_bars checks & act:', a)
            new_triad = triad_list.insert(new_bar)
            if new_triad:
                perms = swing_analyser.register(new_triad)
                if perms:
                    act = trade_manager.register(perms)
                    for a in act:
                        ft.keterol_traded(a, announced)
                        try:
                            ft.check_active_requests(announced)
                        except market.Error as err:
                            print('scanner stopped: ', err)
                            break
            ft.a_new_bar_event_occurred(trade_manager.positions, announced)
                        #print('new_perm:', a)
        #if new_bars.live_mode:
        if True:
        #if False:
            advises = []
            use_lifeguard and lifeguard.alife()
            if composing_bar: # for production add check for live running
                new_triad = triad_list.virtual_insert(composing_bar)
                if new_triad:
                    perms = swing_analyser.virtual_register(new_triad)
                    if perms:
                        advises = trade_manager.virtual_register(perms)
                        if advises:
                            for adv in advises:
                                ft.keterol_is_making_plans(adv, announced)
                                try:
                                    ft.check_active_requests(announced)
                                except market.Error as err:
                                    print('scanner stopped: ', err)
                                    break
                                #print('@',composing_bar.time, '| adv:', adv)
            #trade_manager.report(
                #current_time=datetime.now(),
                #destinations=report_destinations,
                #enter_advise=advises,
            #)
        elif False: #only for testing, is madness
            trade_manager.report(announced, 'terminal')
    with open('/tmp/finreq.pck', 'wb') as pickle_file:
        #for request in sorted(p_trader.finished_requests):
            #pickle.dump(p_trader.finished_requests[request], pickle_file)
        pickle.dump(ft.finished_request_report(), pickle_file)
            
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
        "DAX FUTURE maart 2014", 
        return_value=(
            tws.contract_data("DAX-30_FUT1403"),
            "/home/rolcam/roce/Data/db/DAX FUT X25 20140321 EUR FDAX MAR 14@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
            #"0.5",
        ),
    )
    menu.add_menu_item(
        "DAX bd", 
        return_value=(
            tws.contract_data("DAX-30"),
            '/home/rolcam/roce/Data/daxfut_2013.txt',
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
    
    return menu.get_users_choice()

if __name__ == '__main__':
    main()