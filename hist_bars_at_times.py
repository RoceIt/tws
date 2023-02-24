#!/usr/bin/env python3

#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import csv
import os
from datetime import timedelta

import mypy
import tws as broker
import TWSClient
import twsclientapps as clientapps
from historicaldata_new import historical_data_from_db

CLIENT_ID = 31


def run_simulation(action_bars, hist_data, action_at_time):
    position = 0
    total_result = 0
    contracts_traded = 0
    max_result = 0
    biggest_drawdown = 0
    longest_drawdown = 0
    current_dd_period = 0
    last_fix_entry = None
    reentered = 0
    last_date = mypy.now().date()
    data = []        
    print(action_bars)
    for bar in hist_data:
        curr_time = bar.datetime.time()
        #if not bar.datetime.date() == last_date:
            #last_date = bar.datetime.date()
            #print(last_date)
        if curr_time in action_bars:
            reentered = 0
            action = action_at_time[curr_time]
            if ((action == 'long' and position > 0 )
                or
                (action == 'short' and position < 0)):
                csv_data = list(bar) + [position, 0, total_result, contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
                #continue
            elif action == 'long' and position == 0:
                position = bar.open
                contracts_traded += 1
                last_fix_entry = bar.open
                reentered = 0
                csv_data = list(bar) + [position, 0, total_result, contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
            elif action == 'short' and position == 0:
                position = -bar.open
                contracts_traded += 1
                last_fix_entry = bar.open
                reentered = 0
                csv_data = list(bar) + [position, 0, total_result, contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
            elif action == 'long':
                trade_result = -1 * (bar.open + position)
                total_result += trade_result
                position = bar.open
                contracts_traded += 2
                last_fix_entry = bar.open
                reentered = 0
                max_result = max([max_result, total_result])
                biggest_drawdown = max([biggest_drawdown, max_result-total_result])
                if total_result < max_result:
                    current_dd_period +=1
                else:
                    current_dd_period = 0
                if current_dd_period > longest_drawdown:
                    longest_drawdown = current_dd_period
                csv_data = list(bar) + [position, trade_result, total_result, 
                                        contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
            elif action == 'short':
                trade_result = bar.open - position
                total_result += trade_result
                position = -bar.open
                contracts_traded += 2
                last_fix_entry = bar.open
                reentered = 0
                max_result = max([max_result, total_result])
                biggest_drawdown = max([biggest_drawdown, max_result-total_result])
                if total_result < max_result:
                    current_dd_period +=1
                else:
                    current_dd_period = 0
                if current_dd_period > longest_drawdown:
                    longest_drawdown = current_dd_period
                csv_data = list(bar) + [position, trade_result, total_result, 
                                        contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
            elif action == 'neutral' and position > 0:
                trade_result = bar.open - position
                total_result += trade_result
                position = 0
                contracts_traded += 1
                max_result = max([max_result, total_result])
                biggest_drawdown = max([biggest_drawdown, max_result-total_result])
                if total_result < max_result:
                    current_dd_period +=1
                else:
                    current_dd_period = 0
                if current_dd_period > longest_drawdown:
                    longest_drawdown = current_dd_period
                csv_data = list(bar) + [position, trade_result, total_result, 
                                        contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
            elif action == 'neutral' and position < 0:
                trade_result = -bar.open - position
                total_result += trade_result
                position = 0
                contracts_traded += 1
                max_result = max([max_result, total_result])
                biggest_drawdown = max([biggest_drawdown, max_result-total_result])
                if total_result < max_result:
                    current_dd_period +=1
                else:
                    current_dd_period = 0
                if current_dd_period > longest_drawdown:
                    longest_drawdown = current_dd_period
                csv_data = list(bar) + [position, trade_result, total_result, 
                                        contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
            elif action == 'neutral' and position == 0:
                csv_data = list(bar) + [position, 0, total_result, contracts_traded,
                                        max_result, biggest_drawdown, 
                                        longest_drawdown]
                
            else:
                raise            
            data.append(csv_data)
        elif not position == 0:
            if not max_loss == None:
                if position > 0:
                    virt_result = bar.low - position
                else:
                    virt_result = -bar.high - position
                if virt_result <= max_loss:                    
                    total_result += max_loss
                    position = 0
                    contracts_traded += 1
                    biggest_drawdown = max([biggest_drawdown, 
                                            max_result-total_result]) 
                    csv_data = list(bar) + [position, max_loss, 
                                            total_result, contracts_traded,
                                            max_result, biggest_drawdown, 
                                            longest_drawdown]
                    data.append(csv_data)
                    continue
            if not reentered == 'DONE':
                for start_zone, end_zone, min_profit in profit_zones:
                    if ((start_zone < end_zone and
                         start_zone < curr_time <= end_zone)
                        or
                        (start_zone > end_zone and
                         not end_zone < curr_time <= start_zone)):
                        if position > 0:
                            virt_result = bar.high - position
                        else:
                            virt_result = -bar.low - position
                        if virt_result > min_profit:
                            total_result += min_profit
                            position = 0
                            contracts_traded += 1
                            max_result = max([max_result, total_result])
                            biggest_drawdown = max([biggest_drawdown, 
                                                    max_result-total_result]) 
                            csv_data = list(bar) + [position, min_profit, 
                                                    total_result, contracts_traded,
                                                    max_result, biggest_drawdown, 
                                                    longest_drawdown]
                            data.append(csv_data)
                        break
        elif position == 0 and not reentered == 'DONE' and last_fix_entry:              
            for start_zone, end_zone, re_enter, action in reenter_zones:
                if ((start_zone < end_zone and
                     start_zone < curr_time <= end_zone)
                    or
                    (start_zone > end_zone and
                     not end_zone < curr_time <= start_zone)):
                    if action == 'long' and bar.low < last_fix_entry:
                        position = last_fix_entry
                        contracts_traded += 1
                        csv_data = list(bar) + [position, 0, total_result, contracts_traded,
                                                max_result, biggest_drawdown, 
                                                longest_drawdown]
                        data.append(csv_data)
                    if action == 'short' and bar.high > last_fix_entry:
                        position = -last_fix_entry
                        contracts_traded += 1
                        csv_data = list(bar) + [position, 0, total_result, contracts_traded,
                                                max_result, biggest_drawdown, 
                                                longest_drawdown]
                        data.append(csv_data)
                    if not position == 0:
                        reentered += 1
                    if reentered == re_enter:
                        reentered = 'DONE'                       
                        
                
    return data

def write_simulator_data_to_csv(std_of, data):
    output_file = os.path.join(mypy.TMP_LOCATION, std_of)
    csv_out = csv.writer(open(output_file, 'w', buffering=1))
    csv_out.writerow(['time', 'open', 'high', 'low', 'close', 'volume',
                      'counts', 'wap', 'hasgaps', 'position', 
                      'result_trade', 'total_result', 'nr_of_trades',
                      'max_result', 'biggest_drawdown', 'longest_drawdown'])
    for bar in data:
        csv_out.writerow(list(bar))

def write_multi_sim_data_to_csv(std_of, action_1, action_2, data):
    output_file = os.path.join(mypy.TMP_LOCATION, std_of)
    csv_out = csv.writer(open(output_file, 'w', buffering=1))
    csv_out.writerow([action_1, action_2, 'result', 'max_result', 'biggest_DD',
                      'longest_DD', '#trades'])
    for bar in data:
        csv_out.writerow(list(bar))


client = clientapps.set_up_tws_connection(client_id=CLIENT_ID,
                                              confirm=['client_id'],
                                              interactive = True)
mess = 'select contract'
contract = clientapps.select_contract(client, message=mess).summary
wts = mypy.get_from_list(list(broker.rhd_what_to_show), mess='show: ')
barsize = mypy.get_from_list(list(broker.rhd_bar_sizes), mess='bar: ')
lookback = mypy.get_int('lookback in days (364): ', default=364)
lookback = timedelta(days=lookback)
std_of = 'timed_bars'
std_of = mypy.get_string('write output to {}'.format(std_of), default=std_of)
output_file = os.path.join(mypy.TMP_LOCATION, std_of)
interactive_db_lookup = mypy.get_bool('interactive db lookup? (y/N) ',
                                      default = False)
max_loss = mypy.get_float('max loss (0): ', default=0)
max_loss = -max_loss if not max_loss == 0 else None
action_bars = []
action_at_time = dict()
profit_zones = []
reenter_zones = []

if mypy.get_bool('Single run (Y): ', default=True):
    print('select bartimes to export')
    while True:
        show_time = mypy.get_date('bartime (hh.mm): ', empty=True, format_='%H.%M')
        if not show_time:
            break
        action = mypy.get_from_list(['long', 'short', 'neutral'], 'buy?')
        if not action == 'neutral':
            profit_taker = mypy.get_float('points to take profit (0 = don\'t = default)',
                                        default=0)
            if not profit_taker == 0:            
                profit_time = mypy.get_date('until (hh.mm): ', format_='%H.%M')
                profit_zones.append((show_time.time(), profit_time.time(),
                                     profit_taker))
                re_enter_trade = mypy.get_int('number of re_enters (): ', default=0)
                if not re_enter_trade == 0:         
                    reenter_time = mypy.get_date('until (hh.mm): ', format_='%H.%M')
                    reenter_zones.append((show_time.time(), reenter_time.time(),
                                         re_enter_trade, action))
        action_bars.append(show_time.time())
        action_at_time[show_time.time()] = action
    lookback_period = mypy.now() - lookback
    hist_data = historical_data_from_db(
            contract=contract, start_time=lookback_period, barsize=barsize,
            show=wts, twss=client, verbose=interactive_db_lookup)
    data = run_simulation(action_bars, hist_data, action_at_time)        
    write_simulator_data_to_csv(std_of, data)
else:
    action_1 = mypy.get_from_list(['long', 'short', 'neutral'], 'buy?')
    action_1_start = mypy.get_date('long start (hh.mm): ', format_='%H.%M')
    action_1_stop = mypy.get_date('long stop (hh.mm): ', format_='%H.%M')
    action_2 = mypy.get_from_list(['long', 'short', 'neutral'], 'buy?')
    action_2_start = mypy.get_date('short start (hh.mm): ', format_='%H.%M')
    action_2_stop = mypy.get_date('short stop (hh.mm): ', format_='%H.%M')
    step_minutes = mypy.get_int('stepsize in minutes (30)', default=30)
    action_1_times = []
    new_time = action_1_start
    while not new_time > action_1_stop:
        action_1_times.append(new_time)
        new_time += timedelta(minutes=step_minutes)
    action_2_times = []
    new_time = action_2_start
    while not new_time > action_2_stop:
        action_2_times.append(new_time)
        new_time += timedelta(minutes=step_minutes) 
    lookback_period = mypy.now() - lookback
    hist_data = historical_data_from_db(
        contract=contract, start_time=lookback_period, barsize=barsize,
        show=wts, twss=client, verbose=interactive_db_lookup)
    data = []
    for action_1_time in action_1_times:
        for action_2_time in action_2_times:
            action_bars = [action_1_time.time(), action_2_time.time()]
            print('running simulation {}:{}  {}:{}'.format(
                  action_1, mypy.datetime2format(action_1_time, '%H:%M'),
                  action_2, mypy.datetime2format(action_2_time, '%H:%M')))
            action_at_time.clear()
            action_at_time[action_1_time.time()] = action_1
            action_at_time[action_2_time.time()] = action_2           
            sim_data = run_simulation(action_bars, hist_data, action_at_time)
            print('    Summary: {}'.format(sim_data[-1]))
            try:
                sim_summary = [mypy.datetime2format(action_1_time, '%H:%M'),
                               mypy.datetime2format(action_2_time, '%H:%M'),
                               sim_data[-1][11], sim_data[-1][13],
                               sim_data[-1][14], sim_data[-1][15],
                               sim_data[-1][12]]
                data.append(sim_summary)
            except IndexError:
                print('no data available')
        write_multi_sim_data_to_csv(std_of, action_1, action_2, data)

