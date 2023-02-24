#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#
import os.path

import mypy
import tws
import sql_ib_db
import historicaldata_new
import triads
import tws_realbar_request_gscLib

from barData import ochlBar, ochl_extra_modes
from swing_performance_array import SwingPerformanceArray
import trade_simulator_for_perm_data

#this is for historical data: should work with a server like, the the realtimedata
CLIENT_ID = 9   ## terugzetten naar 10!
IP = 'localhost' #'10.1.1.102'
PORT = 10911

DB = 0
LIVE = 1

def main():
    #print('swing scanner set fixed to scan eoe index, free choice = TODO')
    #contract = tws.contract_data('AEX-index')
    base_filename = mypy.get_string('init filename (out): ', default='out') 
    inputfile = os.path.join(mypy.TMP_LOCATION, 
                             '.'.join([base_filename, "settings"]))
    (contract, filenames, bar_size, last_quote_time) = mypy.import_pickle(inputfile,
                                                         "swing settings")
    print(contract)
    print(filenames)
    print(bar_size)
    print(last_quote_time)
    start_date = last_quote_time.date()
    live_mode = mypy.get_bool("Live mode (Y/n): ", default=True) 
    while live_mode:
        try:
            eorth = mypy.get_string('How late do the markets close today (17:30:00)? ',
                                    default="17:30:00")
            eorth = mypy.py_time(eorth)
            break
        except ValueError:
            print('Can not proces date format')            
    #bar_triad_data_filename = os.path.join(mypy.TMP_LOCATION,
                                           #'.'.join([base_filename, 'b_t']))
    #
    #restart base bar list
    base_bar_list = ochl_extra_modes()
    base_bar_list.hot_start(filenames["bars minimal restart info"])
    base_bar_list.text_output(filenames["full bar history csv"],
                              unfinished_bar_file=True)
    if live_mode: base_bar_list.set_last_expected_quote(eorth)
    #restart triad list
    triad_list = triads.TriadReducerEM(None)
    triad_list.hot_start(filenames["triads minimal restart info"])
    triad_list.text_output(filenames["full triad history csv"],
                           unfinished_triad_file=True)
    #restart swing analiser
    swing_analyser = triads.SwingCountingByRulesEM()
    swing_analyser.hot_start(filenames["perm minimal restart info"])
    swing_analyser.text_output(filenames["full perm history csv"],
                                        unfinished_new_perm_file=True)  
    #restart trade manager 
    trade_manager = trade_simulator_for_perm_data.TradeSimulationByRulesEM()
    trade_manager.hot_start(filenames["trade manager minimal restart info"])
    trade_manager.text_output(filenames["full action log csv"],
                              position_file=True, advise_file=True)
    #print('live mode and historical mode only works fine with the aex-index: TODO')
    print(base_bar_list.last_finished_bar())
    print(base_bar_list.curr_bar())
    data = {DB: None,
            LIVE: None} 
    if live_mode:
        realbar_server = tws_realbar_request_gscLib.server_client()
        live_data = realbar_server.client_for_request('real_time_bars', contract,
                                                 '5 secs', 'TRADES', False)
        latest_live_bar = next(live_data)
        data[LIVE] = live_data
    if start_date:
        historicaldata_new.historical_data_to_db(contract, 
                                                 barsize='5 secs', show='TRADES',
                                                 host_ip=IP, client_port=PORT,
                                                 client_id=CLIENT_ID, 
                                                 verbose=True, update=True)
        db_h = sql_ib_db.HistoricalDatabase('EOE IND EUR AEX@FTA.db')
        hist_data = db_h.data_stream('TRADES_5_secs', 
                                     'datetime', 'open', 'close', 'high', 'low',
                                     start=start_date)
        data[DB] = hist_data              
    for mode in [DB, LIVE]:
        if not data[mode]:
            continue
        while True:
        #for i, latest in enumerate(data[mode]):
            if mode == LIVE:
                curr_ochl = ochlBar(latest_live_bar.time_, latest_live_bar.open_,
                                    latest_live_bar.close, latest_live_bar.high,
                                    latest_live_bar.low)
            else:
                try:
                    bar = next(data[mode])
                except StopIteration:
                    break
                curr_ochl = ochlBar(*bar)
            if curr_ochl.time <= base_bar_list.time_of_last_data:
                continue
            curr_bar, new_base_bar = base_bar_list.insert(*curr_ochl)
            lfb = base_bar_list.last_finished_bar()
            new_triad = False
            if new_base_bar and lfb:
                trade_manager.finished_bar_checks_and_actions(lfb)
                new_triad = triad_list.insert(lfb)
                if new_triad:
                    #swing_analyser.insert_triad(new_triad)
                    perms = swing_analyser.register(new_triad)
                    if perms:
                        trade_manager.register(perms)
            trade_manager.life_bar_checks_and_actions(curr_ochl) 
            ###if live_mode:
            #if mode == LIVE:
                #u_triad = triad_list.insert(curr_bar, finished=False)
                #if u_triad:
                    #u_perms = swing_analyser.register(u_triad, finished=False)
                    #if u_perms:
                        #trade_manager.register(u_perms, finished=False)
                    #else:
                        #trade_manager.no_unfinished_perms()
                #else: 
                    #swing_analyser.no_unfinished_triad()
                    #trade_manager.no_unfinished_perms() 
                #trade_manager.export_stoploss_actions(filenames["stoploss info"]) 
                ##triad_list.insert(curr_bar, finished_bar=False)
            try:
                latest_live_bar = next(data[mode])
            except StopIteration:
                break                
    if mypy.get_bool('Pickle last state for later use (y/N): '):
        print("Saving pickles & csv files")  
        ################################
        # save genaral settings
        info = (contract, filenames, bar_size, curr_bar.time)
        outputfile = os.path.join(mypy.TMP_LOCATION, 
                                  '.'.join([base_filename, "settings"]))
        mypy.export_pickle(info, outputfile, id_="swing settings")
        ################################
        # save_perm_pickles
        # p0: bardata, minimal restart info
        # p1: bardata, full_bar_history
        # p2: triaddata, minimal restart info
        # p3: permdata, minimal restart info
        base_bar_list.save_minimal_restart_info(filenames["bars minimal restart info"])
        #base_bar_list.save_full_bar_history(filenames["full bar history"])
        triad_list.save_minimal_restart_info(filenames["triads minimal restart info"])
        swing_analyser.save_minimal_restart_info(filenames["perm minimal restart info"])
        trade_manager.save_minimal_restart_info(filenames["trade manager minimal restart info"])
        ################################
    print(base_bar_list.last_finished_bar())
    print(base_bar_list.curr_bar())
    base_bar_list.clean_exit()
        
       
        
if __name__ == '__main__':
    main()