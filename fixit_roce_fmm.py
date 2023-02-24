#!/usr/bin/env python3
#
#  Copyright (c) 2012, 2013 Rolf Camps (rolf.camps@scarlet.be)
#

# fmm: full modular mode

from datetime import datetime, timedelta, time
import pickle

import roc_input as r_in
import roc_classes as r_cls
import tws
import historicaldata_new as historicaldata
import marketdata
import virtualmarkets
import triads2
import volume_wap_testing
import trader
import market
from permtradingsystem import PermBasicTestTrader
from fixittradingsystem import FixitTestTrader, FastSwingTestTrader, MultiIntervalTestTrader, FVITAOriginalTestTrader
#from theotrader import TheoreticalSinglePositionTrader as TheoTrader

from lifeguard import Lifeguard

CLIENT_ID = 48
IP = 'localhost' #'10.1.1.102'
PORT = 10911

def main():
    
    ##quick selection for testing, menufy it
    ##
    lock_set = False
    print('algo contract: ', end='')
    contract, db_name, dataset_ib, dataset_db, min_tick = get_contract_info()
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
        default='13/10/07',
    ).date()
    end = r_in.get_datetime(
        message='end date ({default}): ',
        time_format='%y/%m/%d',
        default='13/10/11',
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
        lifeguard = Lifeguard('ssr', timedelta(seconds=7))  
        
    #_b_feeder = marketdata.data_bar_feeder(
                #'/home/rolcam/roce/Data/daxfut_2013.txt', 
                #is_index='False', 
                ##start=start, 
                ##stop=end,
                ##update=update_db, #False,
                ##contract=contract_t, #only usefull for update True
    #) 
        
    _b_feeder = marketdata.data_bar_feeder(
                '/home/rolcam/roce/Data/daxfut_2013.txt', 
                is_index='False', 
                #start=start, 
                #stop=end,
                #update=update_db, #False,
                #contract=contract_t, #only usefull for update True
    )
    input('_b_feeder is {}'.format(_b_feeder.__class__))
    feeder = marketdata.ComposingDatabarFeeder(
        feeder=_b_feeder,
        only_finished_bars=True,
        seconds=1
    )
        
    #feeder = marketdata.data_bar_feeder(
                #db_name, 
                #is_index=is_index, 
                #start=start, 
                #stop=end,
                #update=update_db,
                #contract=contract, #only usefull for update True
    #)       
    live_feeder = marketdata.data_bar_feeder(
                    '__tws_live__',
                    contract=contract,
                    barsize='5 secs',
                    show='TRADES',
                    is_index=True,                
    )
    new_bars_kwds_dic = {
        'feeder':feeder,
        'seconds':60,
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
    #triad_list = triads2.TriadReducer(60)
    #triad_list.export_settings(
        #destintriad_listation='csv',
        #filename='/tmp/exp.t1',
    #)
    #new_bars.export_add_action_linked_export_system(triad_list)
    #swing_analyser = triads2.SwingCountingByArgs()
    #swing_analyser.export_settings(
        #destination='csv',
        #filename='/tmp/exp.t2',
    #)
    #new_bars.export_add_action_linked_export_system(swing_analyser)
    #volwap_indicator = volume_wap_testing.VolWapIndicator1(
        #volwap_moderator=1,
        #normaliser=500,
    #)
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
    #p_trader = FixitTestTrader('long', min_tick=min_tick)
    #p_trader = FixitTestTrader('short', min_tick=min_tick)
    #p_trader = FastSwingTestTrader(3, min_tick=min_tick)
    #p_trader = MultiIntervalTestTrader(
        #('bars', 60), ('bars', 120), 
        #min_tick=None,
        #momentum_indicator_osc=(5, 10),
        #rate_of_change_osc=(5, 10),
        #relative_strength_indicator_osc=((3, 20), (9, 20), (14, 80)),
        #stochastic_osc=((9, 3, 20),),
        #simple_moving_average_ti=(14,),
        #linearly_weighted_moving_average_ti=(14,),
        #exponantialy_smooted_moving_average_ti=(14,),
        #macd_ti = ((14, 26, 9),),
    #)
    p_trader = FVITAOriginalTestTrader(
        ('bars', 60, time(8)), 
        ('bars', 120, time(8)), 
        ('bars', 240, time(8)), 
        ('bars', 480, time(8)), 
        ('bars', 960, time(8)), 
        ('bars', 1920, time(8)), 
        ('bars', 3840, time(8)), 
        ('bars', 7680, time(8)), 
        ('bars', 15360, time(8)), 
        ('bars', 30720, time(8)), 
        ('bars', 61440, time(8)),
        min_tick=None,
    )
    p_trader.fvita.export_file_base = "/tmp/fvita_test"
    p_trader.fvita.reset_export_files()
    p_trader.fixed_contract = db_name 
    _t_feeder = marketdata.data_bar_feeder(
                '/home/rolcam/roce/Data/daxfut_2013.txt', 
                is_index='False', 
                #start=start, 
                #stop=end,
                #update=update_db, #False,
                #contract=contract_t, #only usefull for update True
    )
    t_feeder = marketdata.ComposingDatabarFeeder(
        feeder=_t_feeder,
        only_finished_bars=True,
        seconds=5
    )  
    #t_feeder = marketdata.data_bar_feeder(
                #db_name, 
                #is_index=is_index, 
                #start=start, 
                #stop=end,
                #update=False,
                #contract=contract, #only usefull for update True
    #)
    t_market = virtualmarkets.VirtualSingleContractIndexMarketFromDataBarStream(
         t_feeder, db_name)
    p_trader.add_market(t_market)
    p_trader.set_daytrade_mode(
        end_of_day=eorth,
        last_in=last_entry,
        managed_out=managed_exit,
        last_out=forced_exit,
    )
    fvita = p_trader.fvita
    fvita.export_intervalnames()
    for announced, curr_base_bar, composing_bar, new_bar in new_bars:
        if not lock_set:
            fvita.set_export_lock()
            lock_set = True
        ##perm_trading_system.live_bar_checks_and_actions(curr_base_bar)
        #perm_trading_system.event(
            #event_name='new_market_data_for_theoretical_trader',
            #event_time=announced,
            #bar_or_tick=curr_base_bar,
        #)
        #if announced.date() < start:
        #print(announced)
        #print(curr_base_bar)
        #print(composing_bar)
        #print(new_bar)
        if (announced.date() < start
            or
            (composing_bar                                            and
             composing_bar.time.date() < start)
            or
            (new_bar                                                  and
             new_bar.time.date() < start)
        ):
            continue
        try:
            p_trader.check_active_requests(announced)
        except market.Error as err:
            print('scanner stopped: ', err)
            break
        if new_bar: # and new_bar.duration:
            if new_bar.time.date() > end:
                break
            p_trader.new_fixitbar(
                    new_bar,
                    at_time=announced)
            #fvita.export_end_of_bar_status()
            #fvita.export_barstart()
            #fvita.export_basic_moves()
            #fvita.export_low()
            #fvita.export_low_index()
            #fvita.export_high()
            #fvita.ex
            #port_high_index()
            #fvita.export_barvalue('open_')
            #fvita.export_barvalue('close')
            #fvita.export_r_levels()
            #fvita.export_barvalue('close')
            #fvita.export_s_levels()
            #fvita.export_balanced_market(field=6)
            #fvita.export_last_stoch_move()
            #fvita.export_last_move_stoch_result()
            fvita.export_market_status()
            fvita.export_market_status_reason()
            #fvita.export_waves_down_index()
            #fvita.export_waves_up_index()
            #fvita.export_waves_down_extremes()
            #fvita.export_waves_up_extremes()
            print("<<< --- >>>>")
        if new_bars.live_mode:
            advises = []
            use_lifeguard and lifeguard.alife()
            if composing_bar: # for production add check for live running
                new_triad = triad_list.virtual_insert(composing_bar)
                if new_triad:
                    perms = swing_analyser.virtual_register(new_triad)
                    if perms:
                        #advises = perm_trading_system.event(
                            #event_name='register_virtual_perm_lines',
                            #event_time=announced,
                            #perm_lines=perms,
                            #)
                        #for advise in advises:
                            #print(advise)
                        print('\n++++++++++++++++++++++++++')
                        print(perms)
    #for line in p_trader.finished_request_report():
        #print(line)
    #for request in sorted(p_trader.finished_requests):
        #print(p_trader.finished_requests[request])
    print('trader summeries')
    print('================')
    print('balanced market:')
    print(fvita.stats_balanced_market_triggers)
    print('balanced market reasons:')
    print(fvita.stats_balanced_market_triggers_reasons)
    print('confirmed bears:')
    print(fvita.stats_confirmed_bear)
    print('confirmed bulls:')
    print(fvita.stats_confirmed_bull)
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
            "EUR CASH USD EUR.USD@IDEALPRO.db",
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
    
    return menu.get_users_choice()

if __name__ == '__main__':
    main()