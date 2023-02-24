#!/usr/bin/env python3
#
#  Copyright (c) 2012, 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from datetime import datetime, timedelta

import roc_input as r_in
import tws
import historicaldata_new as historicaldata
import marketdata as data
import triads2
import trade_simulator_for_perm_data2

from lifeguard import Lifeguard

CLIENT_ID = 48
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
        default='13/06/28',
    ).date()
    end = r_in.get_datetime(
        message='end date ({default}): ',
        time_format='%y/%m/%d',
        #default='13/06/28',
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
        last_entry = r_in.get_integer("last entry (4500):",
                                  default = 4500)
        managed_exit = r_in.get_integer("managed exit (sec before eod:",
                                    default = -1)
        forced_exit = r_in.get_integer("force exit (1800):",
                                   default = 1800)
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
        'minutes':1,
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
    trade_manager = trade_simulator_for_perm_data2.TradeSimulationByArgs(
            contract_name='DAX index',
            #wavecount_in=2,
            wavecount_in=[2,4,6,8,10,12,14,16,18],
            #wavecount_in=5,
            trailing_exit="entry+percent", start_trailing_at=0.07,
            #fix_exit="percent", fix_at=0.15,
            #min_gap_to_curr="entry+fix", min_gap=0.07,
            #max_gap_to_curr="entry+fix", max_gap=2,
            cap_stop='entry+%', cap=0.07,
            sph=True, 
            reverse=True)
    trade_manager.use_daytrader_mode(
            std_end_time=eorth,
            last_in=last_entry,
            managed_out=managed_exit,
            last_out=forced_exit
    )
    trade_manager.export_settings(
        destination='csv',
        filename='/tmp/exp.t3',
    )
    report_destinations = []
    if sound_warning_report:
        report_destinations.append('sound')
    if terminal_report:
        report_destinations.append('terminal')
    new_bars.export_add_action_linked_export_system(trade_manager)
    for announced, curr_base_bar, composing_bar, new_bar in new_bars:
        trade_manager.live_bar_checks_and_actions(curr_base_bar)
        if new_bar:
            trade_manager.finished_bar_checks_and_actions(new_bar)
            new_triad = triad_list.insert(new_bar)
            if new_triad:
                perms = swing_analyser.register(new_triad)
                if perms:
                    trade_manager.register(perms)
        if new_bars.live_mode:
            advises = []
            use_lifeguard and lifeguard.alife()
            if composing_bar: # for production add check for live running
                new_triad = triad_list.virtual_insert(composing_bar)
                if new_triad:
                    perms = swing_analyser.virtual_register(new_triad)
                    if perms:
                        advises = trade_manager.virtual_register(perms)
            trade_manager.report(
                current_time=datetime.now(),
                destinations=report_destinations,
                enter_advise=advises,
            )
        elif False: #only for testing, is madness
            trade_manager.report(announced, 'terminal')
            
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
    
    return menu.get_users_choice()

if __name__ == '__main__':
    main()