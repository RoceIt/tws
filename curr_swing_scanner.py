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

from barData import ochlBar, ochl #ochl_extra_modes
from swing_performance_array import SwingPerformanceArray
import trade_simulator_for_perm_data

#ochl = ochl_extra_modes

#this is for historical data: should work with a server like, the the realtimedata
CLIENT_ID = 9   ## terugzetten naar 10!
IP = 'localhost' #'10.1.1.102'
PORT = 10911

DB = 0
LIVE = 1

def main():
    print('swing scanner set fixed to scan eoe index, free choice = TODO')
    #contract = tws.contract_data('AEX-index')
    #contract = tws.contract_data('DAX-30')
    contract, db_filename, dataset_ib, dataset_db = get_contract_info()
    base_filename = mypy.get_string('init filename (out): ', default='out')    
    pickle_filename = os.path.join(mypy.TMP_LOCATION,
                                   '.'.join([base_filename, 'pickle']))
    bar_triad_data_filename = os.path.join(mypy.TMP_LOCATION,
                                           '.'.join([base_filename, 'b_t']))
    if True:  #mypy.get_bool('New analysis (Y/n)', default=True):
        bar_size = mypy.get_int('Bar size in seconds (630): ', default=630)
        #live_mode = mypy.get_bool('live mode (Y/n)', default=False)
        start_date = mypy.get_date('start from (YYYY/MM/DD): ', 
                                   format_='%Y%m%d', default='20120901')
        end_date = mypy.get_date('stop on: ', 
                                   format_='%Y%m%d', empty=True)
        base_bar_list = ochl('s', bar_size)
        open(bar_triad_data_filename, 'w').close()
        triad_list = triads.TriadReducer(bar_size)
        #swing_analyser = triads.SwingAnalyser(bar_size, base_filename)
        swing_analyser = triads.SwingCountingByRules("cr_1.cr")
        #trade_manager = trade_simulator_for_perm_data.TradeSimulationByRules(
                                                                #"wtf_trader.cr",
                                                                #sph=True)
        #trade_manager = trade_simulator_for_perm_data.TradeSimulationByRules(
                                                                #"sist.cr",
                                                                #sph=True)
        trade_manager = trade_simulator_for_perm_data.TradeSimulationByRules(
                                                                "first1hour.cr",
                                                                sph=True)
        #trade_manager = trade_simulator_for_perm_data.TradeSimulationByRules(
                                                                #"simpletrader.cr",
                                                                #sph=True)
        if mypy.get_bool("Exit end of day? (y/N)", default=False):
            while True:
                try:
                    eorth = input('How late do the markets close today (HH:MM:SS)? ')
                    eorth = mypy.py_time(eorth)
                    break
                except ValueError:
                    print('Can not proces date format')
            last_entry = mypy.get_int("last entry (seconds before eod):",
                                      default = -1)
            managed_exit = mypy.get_int("managed exit (sec before eod:",
                                        default = -1)
            forced_exit = mypy.get_int("force exit (sec before eod):",
                                       default = -1)
            trade_manager.use_daytrader_mode(eorth, last_entry, managed_exit,
                                             forced_exit)
    #else:
        #base_bar_list, triad_list, swing_analyser = mypy.import_pickle(
                                                              #pickle_filename)
        #assert isinstance(base_bar_list, ochl)
        #assert isinstance(triad_list, triads.TriadReducer)
        #assert isinstance(swing_analyser, triads.SwingAnalyser)
        #bar_size = triad_list.bar_size
        #live_mode = mypy.get_bool('live mode? (Y, n)', default=True)
        #start_date = base_bar_list.time_of_last_data
    print('live mode and historical mode only works fine with the aex-index: WIA')
    data = {DB: None,
            LIVE: None} 
    #if live_mode:
        #realbar_server = tws_realbar_request_gscLib.server_client()
        #live_data = realbar_server.client_for_request('real_time_bars', contract,
                                                 #'5 secs', 'TRADES', False)
        #latest_live_bar = next(live_data)
        #data[LIVE] = live_data
    if start_date:
        if mypy.get_bool("update db (y/N)", default=False):
            historicaldata_new.historical_data_to_db(contract, 
                                                 barsize='5 secs', show=dataset_ib,
                                                 host_ip=IP, client_port=PORT,
                                                 client_id=CLIENT_ID, 
                                                 verbose=True, update=True)
        db_h = sql_ib_db.HistoricalDatabase(db_filename)
        if end_date:
            hist_data = db_h.data_stream(dataset_db, 
                                     'datetime', 'open', 'close', 'high', 'low',
                                     start=start_date, stop=end_date)
        else:
            hist_data = db_h.data_stream(dataset_db, 
                                     'datetime', 'open', 'close', 'high', 'low',
                                     start=start_date)
        data[DB] = hist_data              
    #for mode in [DB, LIVE]:            
    for mode in [DB]:
        if not data[mode]:
            continue
        while True:
        #for i, latest in enumerate(data[mode]):
            #if mode == LIVE:
                #curr_ochl = ochlBar(latest_live_bar.time_, latest_live_bar.open_,
                                    #latest_live_bar.close, latest_live_bar.high,
                                    #latest_live_bar.low)
            #else:
                #try:
                    #bar = next(data[mode])
                #except StopIteration:
                    #break
                #curr_ochl = ochlBar(*bar)
            try:
                bar = next(data[mode])
            except StopIteration:
                break
            curr_ochl = ochlBar(*bar)
            
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
                        ### Handy for checking
                        #print("sending perms")
                        #for line in perms:
                        #    print(line)
                        #mypy.get_bool("drukken", default=True)
                        trade_manager.register(perms)
            # Checking if eventual stoplosses are not triggered. It has
            # to happen here after the new base bar is entered in the
            # triad reduder becaus the new bar is announced 5 seconds(depends
            # on the feeding data bars) after the last bar of that finished
            # bar is passing through this part of the program. If you check for
            # a stoploss before you insert the finished file in the trade manager,
            # you would mess up the time. As long as you don't change the moment a
            # new bar is announced this is ok. When you do change it!!! 
            # re-think this!!!!
            trade_manager.life_bar_checks_and_actions(curr_ochl)
            #trade_manager.export_stoploss_actions("st.t4")
            ##if live_mode:
            #if mode == LIVE:
                #triad_list.insert(curr_bar, finished_bar=False)
                #try:
                    #latest_live_bar = next(data[mode])
                #except StopIteration:
                    #break                
    if True: #mypy.get_bool('Pickle last state for later use (y/N): '):
        print("Saving pickles & csv files")
        mypy.export_pickle((base_bar_list, triad_list, swing_analyser),
                           pickle_filename)
        filenames = {"bars minimal restart info": '.'.join([base_filename, "p0"]),
                     "full bar history": '.'.join([base_filename, "p1"]),
                     "triads minimal restart info": '.'.join([base_filename, "p2"]),
                     "perm minimal restart info": '.'.join([base_filename, "p3"]),
                     "trade manager minimal restart info": '.'.join([base_filename, "p4"]),
                     "full bar history csv": '.'.join([base_filename, "t0"]),
                     "full triad history csv": '.'.join([base_filename, "t1"]),
                     "full perm history csv": '.'.join([base_filename, "t2"]),
                     "full action log csv": '.'.join([base_filename, "t3"]),
                     "stoploss info": '.'.join([base_filename, "t4"]),
                     }
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
        # p4: trade manager, minimal restart info
        base_bar_list.save_minimal_restart_info(filenames["bars minimal restart info"])
        base_bar_list.save_full_bar_history(filenames["full bar history"])
        triad_list.save_minimal_restart_info(filenames["triads minimal restart info"])
        swing_analyser.save_minimal_restart_info(filenames["perm minimal restart info"])
        trade_manager.save_minimal_restart_info(filenames["trade manager minimal restart info"])
        ################################
        #save_text_files
        # t0: finished bars
        # t1: finished triads
        # t2: perm lines
        # t3: trades
        # t4: stoploss info
        base_bar_list.export_full_bar_history(filenames["full bar history csv"])
        triad_list.export_triad_list(filenames["full triad history csv"])
        swing_analyser.export_full_perm_list(filenames["full perm history csv"])
        trade_manager.export_action_log(filenames["full action log csv"])
        trade_manager.export_positions('.'.join([filenames["full action log csv"],
                                                 "positions"]))
        trade_manager.export_stoploss_actions(filenames["stoploss info"])
        
def get_contract_info():
    menu = mypy.SelectionMenu(auto_number=True)
    menu.add_menu_item('AEX', return_value=(tws.contract_data("AEX-index"),
                                            "EOE IND EUR AEX@FTA.db",
                                            "TRADES", "TRADES_5_secs"))
    menu.add_menu_item("DAX", return_value=(tws.contract_data("DAX-30"),
                                            "DAX IND EUR DAX@DTB.db",
                                            "TRADES", "TRADES_5_secs"))
    menu.add_menu_item("EUR.USD", return_value=(tws.contract_data("euro-dollar"),
                                            "EUR CASH USD EUR.USD@IDEALPRO.db",
                                            "MIDPOINT", "MIDPOINT_5_secs"))
    
    return menu.get_users_choice()
        
if __name__ == '__main__':
    main()