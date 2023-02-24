#!/usr/bin/env python3

#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)

import csv
import os
from datetime import timedelta

import mypy
import tws as broker
import TWSClient
import twsclientapps as clientapps
from historicaldata_new import historical_data_from_db
from tws_realbar_request_gscLib import server_client


client = clientapps.set_up_tws_connection(client_id=22,
                                              confirm=['client_id'],
                                              interactive = True)
mess = 'select curr straddle'
curr_str_c = clientapps.select_contract(client, message=mess, secType='FOP',
                                   symbol='GC',right='C').summary
curr_str_p = clientapps.select_contract(client, message=mess, secType='FOP',
                                   symbol='GC',right='P', 
                                   strike=curr_str_c.strike,
                                   expiry=curr_str_c.expiry,
                                   multiplier=curr_str_c.multiplier).summary
mess = 'select next straddle'
next_str_c = clientapps.select_contract(client, message=mess, secType='FOP',
                                   symbol='GC',right='C').summary
next_str_p = clientapps.select_contract(client, message=mess, secType='FOP',
                                   symbol='GC',right='P', 
                                   strike=next_str_c.strike,
                                   expiry=next_str_c.expiry,
                                   multiplier=next_str_c.multiplier).summary
client.disconnect(silent=False)
methods = ['bid/ask', 'midpoint']
method = mypy.get_from_list(methods, 'method: ')
if method == 'midpoint':
    curr_wts = next_wts = 'MIDPOINT'
else:
    curr_wts = 'BID'
    next_wts = 'ASK'
port = mypy.get_int('realbar server port (empty for default): ', default=14701)
data_server = server_client(server_port=port)
curr_c_data = data_server.client_for_request('real_time_bars', curr_str_c, 
                                          '5 secs', curr_wts, False)
curr_p_data = data_server.client_for_request('real_time_bars', curr_str_p, 
                                          '5 secs', curr_wts, False)
next_c_data = data_server.client_for_request('real_time_bars', next_str_c, 
                                          '5 secs', curr_wts, False)
next_p_data = data_server.client_for_request('real_time_bars', next_str_p, 
                                          '5 secs', curr_wts, False)
curr_c_data_list = []
curr_p_data_list = []
next_c_data_list = []
next_p_data_list = []
dataset = [curr_c_data_list, curr_p_data_list, next_c_data_list, next_p_data_list]
multiplier = int(curr_str_c.multiplier)

while 1:
    curr_c_data_list.append(next(curr_c_data))
    curr_p_data_list.append(next(curr_p_data))
    next_c_data_list.append(next(next_c_data))
    next_p_data_list.append(next(next_p_data))
    data = mypy.data_with_common_field_value(*dataset, field='time_')
    if data:
        curr_price = data[0].close + data[1].close
        next_price = data[2].close + data[3].close
        diff_price = curr_price - next_price
        print(data[0].time_, ': ', int(diff_price * multiplier))