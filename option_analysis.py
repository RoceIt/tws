#!/usr/bin/env python3

#  FILENAME: option_analysis.py

#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import sys
import os.path
import csv
from datetime import timedelta
from collections import namedtuple
from pickle import load, dump
from time import sleep

import mypy
import tws as broker
import TWSClient
import twsclientapps as clientapps
import gnuplot
from historicaldata_new import historical_data_from_db
import options
from mysolvers import solve_to_min_1u as find_min

CLIENT_ID = 8
LOOKBACK = timedelta(days=45)  #set to 10 for testing purposes

###
# the constants
###

# 
PUT = 'PUT'
CALL = 'CALL'
INDEX = 'INDEX'
PRODUCT_TYPES = {PUT, CALL, INDEX}

TRADES = 'TRADES'
ASK = 'ASK'
BID = 'BID'
MIDPOINT = 'MIDPOINT'
UNKNOWN = 'UNKNOWN'
INFO_TYPES = {TRADES, ASK, BID, MIDPOINT, UNKNOWN}

OPEN = 'OPEN'
CLOSE = 'CLOSE'
HIGH = 'HIGH'
LOW = 'LOW'
VOLUME = 'VOLUME'

BarAnalyzerInfo = namedtuple('AnalyzerInfo', 
                             'date_ open_ high low close volume')
OHLC = namedtuple('OHLC', ' '.join([OPEN, HIGH, LOW, CLOSE]))

def main():
    if len(sys.argv) == 1:
        interactive()
    elif sys.argv[1] == 'terminal': 
        name = mypy.get_string('basefile: ', default='multi_upc_out')
        multi_upc_terminal(name)
    else:
        mess = 'version with these parameters not yet(?) available'
        raise NotImplementedError(mess)
    
def interactive():
    if mypy.get_bool('multi mode (y/N): ', default=False):
        choice = 2
    else:
        choice = 1
    if choice == 1:
        i_underlying_put_call()
    elif choice == 2:
        i_multi_upc()
    else:
        mess = 'choice not yet implemented'
        raise NotImplementedError(mess)
    
#######################################################################
#
# UNDERLYING PUT CALL
#

class UnderlyingPutCall():
    
    def __init__(self, underlying, put, call,
                 inv_put=None, inv_call=None):
        self.underlying = underlying
        self.put = put
        self.call = call
        self.inv_put = inv_put
        self.inv_call = inv_call
        self.underlying_data = []
        self.put_data = []
        self.call_data = []
        self.inv_put_data = []
        self.inv_call_data = []
        self.dataset=[self.underlying_data, self.put_data, self.call_data]
        if not (self.inv_put == None or self.inv_call == None):
            self.modes = {'set_sig', 'auto_sig'}
            self.dataset += [self.inv_put_data, self.inv_call_data]
        else:
            self.modes = {'auto_sig'}
        
    def data_for(self, ctr, data):
        assert isinstance(data, BarAnalyzerInfo)
        if ctr == self.underlying:
            self.underlying_data.append(data)
            set_data = 'underlying'
        elif ctr == self.put:
            self.put_data.append(data)
            set_data = 'put'
        elif ctr == self.call:
            self.call_data.append(data)
            set_data = 'call'
        elif ctr == self.inv_put:
            self.inv_put_data.append(data)
            set_data = 'inv_put'
        elif ctr == self.inv_call:
            self.inv_call_data.append(data)
            set_data = 'inv_call'
        else:
            set_data = None
        return set_data
    
    def analysis(self):
        data = mypy.data_with_common_field_value(*self.dataset, field='date_')
        result = None
        if data:
            try:
                result = upc_analyzer(data, self.put, self.call,
                                      self.modes, self.inv_put, self.inv_call)
            except options.NoSolution:
                pass
        return result
    
    @property
    def has_empty_datalist(self):
        '''Returns True of one or more of the  datalists are empty'''
        for data in self.dataset:
            if data == []:
                print('empty datalist')
                return True
        return False
    
    @property
    def has_inverse_options(self):
        '''Returns True if inverse options for put and call are defined'''
        if self.inv_call == None or self.inv_put == None:
            return False
        else:
            return True
        
    def clear_data_lists(self):
            self.put_data = []
            self.underlying = []
            self.call_data = []
            self.inv_call_data = []
            self.inv_put_data = []
            
def i_underlying_put_call():
    modes = {'set_sig', 'auto_sig'}
    #modes = {'auto_sig'}
    std_of = 'upc_out.csv'
    print('mode for comparing a put/call combination and its underlying')
    client = clientapps.set_up_tws_connection(client_id=CLIENT_ID,
                                              confirm=['client_id'],
                                              interactive = True)
    mess = 'select underlying'
    underlying = clientapps.select_contract(client, message=mess).summary
    #print('underlying: ', underlying)
    und_wts = mypy.get_from_list(list(broker.rtb_what_to_show), mess='show: ')
    mess = 'select call option'
    call_option = clientapps.select_contract(client, message=mess,
                                             symbol=underlying.symbol,
                                             secType='OPT', #'OPT',
                                             right='C').summary
    if 'set_sig' in modes:
        call_option_inverse = clientapps.inverse_option(
                                 client, call_option).summary
        if call_option_inverse == None:
            print('no reverse option found, disabled set sigma mode')
            modes.remove('set_sig')
            put_option_inverse == None        
    #print('call: ', call_option)
    mess = 'select put option'
    put_option = clientapps.select_contract(client, message=mess,
                                            symbol=underlying.symbol,
                                            secType='OPT', #'OPT',
                                            right='P').summary
    if 'set_sig' in modes:
        put_option_inverse = clientapps.inverse_option(
                                client, put_option).summary
        if put_option_inverse == None:
            print('no reverse option found, disabled set sigma mode')    
            modes.remove('set_sig')  
    else:
        put_option_inverse = call_option_inverse = None
    #print('put: ', put_option)
    opt_wts = mypy.get_from_list(list(broker.rtb_what_to_show), mess='show: ')
    std_of = mypy.get_string('write output to {}'.format(std_of), default=std_of)
    output_file = os.path.join(mypy.TMP_LOCATION, std_of)
    csv_out = csv.writer(open(output_file, 'w', buffering=1))
    csv_out.writerow(upc_csv_header)
    to_file = lambda x: upc_csv(x, csv_out)
    underlying_put_call(client, 
                        underlying, put_option, call_option,
                        und_wts, opt_wts, 
                        #modes=modes,
                        inv_put=put_option_inverse, 
                        inv_call=call_option_inverse,
                        output=to_file) #std_upc_result_handler)
    client.close()

      
def underlying_put_call(client,
                        underlying, put, call,
                        und_wts='TRADES', opt_wts='TRADES',
                        lookback=LOOKBACK, hist_barsize='5 mins',
                        inv_put=None, inv_call=None,
                        output=None):
    
    upc = UnderlyingPutCall(underlying, put, call, inv_put, inv_call)
    
    #setting up live feeds and live feed dictionary
    print('starting live feeds')
    underlying_id = client.req_real_time_bars(underlying,
                                              what_to_show=und_wts)
    call_id = client.req_real_time_bars(call, what_to_show=opt_wts)
    put_id = client.req_real_time_bars(put, what_to_show=opt_wts)
    real_bar_dictionary = clientapps.RealBarDictionary(client)
    real_bar_dictionary.add_id('underlying id', underlying, underlying_id)
    real_bar_dictionary.add_id('call', call, call_id)
    real_bar_dictionary.add_id('put', put, put_id)    
    if 'set_sig' in upc.modes:
        inv_call_id = client.req_real_time_bars(inv_call,
                                                what_to_show=opt_wts)
        inv_put_id = client.req_real_time_bars(inv_put, 
                                               what_to_show=opt_wts)
        real_bar_dictionary.add_id('inv_call', inv_call, inv_call_id)
        real_bar_dictionary.add_id('inv_put', inv_put, inv_put_id)
    #requesting historical data from db
    print('requesting historical data')
    interactive_db_lookup = mypy.get_bool('interactive db lookup? (y/N) ',
                                          default = False)
    lookback_period = mypy.now() - lookback
    request = lambda ctr, show: historical_data_from_db(
        contract=ctr, start_time=lookback_period, barsize=hist_barsize,
        show=show, twss=client, verbose=interactive_db_lookup)
    print('* underlying data')
    underlying_hist = request(underlying, und_wts)
    print('* call data')
    call_hist = request(call, opt_wts)
    print('* put data')
    put_hist = request(put, opt_wts)    
    if 'set_sig' in upc.modes:
        print('* inverse call data')
        inv_call_hist = request(inv_call, opt_wts)
        print('* inverse put data')
        inv_put_hist = request(inv_put, opt_wts)
    else:
        inv_call_hist = inv_put_hist = None
    #Analyze historical data
    for data in underlying_hist:
        upc.data_for(underlying, _hist_db_record_2_bar_analyzer_info(data))
    for data in put_hist:
        upc.data_for(put, _hist_db_record_2_bar_analyzer_info(data))
    for data in call_hist:
        upc.data_for(call, _hist_db_record_2_bar_analyzer_info(data))   
    if 'set_sig' in upc.modes:
        for data in inv_put_hist:
            upc.data_for(inv_put, _hist_db_record_2_bar_analyzer_info(data))
        for data in inv_call_hist:
            upc.data_for(inv_call, _hist_db_record_2_bar_analyzer_info(data))
    while not upc.has_empty_datalist:
        analysis = upc.analysis()
        if analysis:
            output(analysis)
    #Analyze live data
    print('live bars')
    while True:
        real_bar_data = real_bar_dictionary.collect_available_data()
        for contract, data in real_bar_data:
            upc.data_for(contract, _tws_real_time_bar_2_bar_analyzer_info(data))
        analysis = upc.analysis()
        if analysis:
            output(analysis)
            
    client.stop_real_time_bars(underlying_id)
    client.stop_real_time_bars(call_id)    
    client.stop_real_time_bars(put_id)
    
def i_multi_upc():    
    modes = {'set_sig', 'auto_sig'}
    #modes = {'auto_sig'}
    std_of = 'multi_upc_out'
    std_settings_file_name = 'imupc_saved_settings'
    print('mode for comparing a put/call combinations and its underlying')
    client = clientapps.set_up_tws_connection(client_id=CLIENT_ID,
                                              confirm=['client_id'],
                                              interactive = True)
    if mypy.get_bool('Use saved request (y/N): ', default=False):
        mess = 'file_name ({}): '.format(std_settings_file_name)
        file_name = mypy.get_string(mess, default=std_settings_file_name)
        (underlying, put_options, call_options, und_wts, opt_wts, 
         put_options_inverses, call_options_inverses,
         list_of_upc, std_of) = mypy.import_pickle(file_name)
    else:
        mess = 'select underlying'
        underlying = clientapps.select_contract(client, message=mess).summary
        und_wts = mypy.get_from_list(list(broker.rtb_what_to_show), mess='show: ')
        mess = 'select call options'
        call_options = clientapps.select_list_of_contracts(
                                                client, message=mess,
                                                symbol=underlying.symbol,
                                                secType='OPT', right='C',
                                                confirm=['expiry'],
                                                reuse=['expiry'])
        mess = 'select put options'
        put_options = clientapps.select_list_of_contracts(
                                                client, message=mess,
                                                symbol=underlying.symbol,
                                                secType='OPT', right='P',
                                                confirm=['expiry'],
                                                reuse=['expiry'])
        opt_wts = mypy.get_from_list(list(broker.rtb_what_to_show), mess='show: ')
        call_options_inverses, put_options_inverses = [], []
        if 'set_sig' in modes:
            print('select reverse options')
            for option in call_options:
                call_options_inverses.append(clientapps.inverse_option(
                                                           client, option).summary)
            for option in put_options:
                put_options_inverses.append(clientapps.inverse_option(
                                                           client, option).summary)
        list_of_upc = []
        for put_i, put in enumerate(put_options):
            for call_i, call in enumerate(call_options):
                if put.strike < call.strike:
                    list_of_upc.append(
                        UnderlyingPutCall(underlying,
                                          put, call,
                                          put_options_inverses[put_i],
                                          call_options_inverses[call_i]))
        std_of = mypy.get_string('write output to {}'.format(std_of), default=std_of)
        if mypy.get_bool('Save selection (y/N)', default=False):
            mess = 'file_name ({}): '.format(std_settings_file_name)
            file_name = mypy.get_string(mess, default=std_settings_file_name)
            mypy.export_pickle((underlying, put_options, call_options, und_wts, 
                                opt_wts, put_options_inverses, 
                                call_options_inverses, list_of_upc, std_of),
                               file_name)
    multi_upc(client, underlying,
              put_options, call_options,
              und_wts, opt_wts,
              put_options_inverses, call_options_inverses,
              list_of_upc, output_file_name=std_of)
    
def multi_upc(client, underlying, put_list, call_list, und_wts, opt_wts,
              inv_put_list, inv_call_list, upc_list,
              lookback=LOOKBACK, hist_barsize='5 mins',
              output_file_name = 'multi_upc_out'):
    
    def set_up_real_bar_dictionary():
        rbd = clientapps.RealBarDictionary(client)
        for put_i, put in enumerate(put_list):
            id_ = client.req_real_time_bars(put, what_to_show=opt_wts)
            name = 'put'+str(put_i)
            rbd.add_id(name, put, id_)
            inv_put = inv_put_list[put_i]
            sleep(1)
            if not inv_put == None:
                id_ = client.req_real_time_bars(inv_put, what_to_show=opt_wts)
                name = 'inv_put'+str(put_i)
                rbd.add_id(name, inv_put, id_)
                sleep(1)
        for call_i, call in enumerate(call_list):
            id_ = client.req_real_time_bars(call, what_to_show=opt_wts)
            name = 'call'+str(call_i)
            rbd.add_id(name, call, id_)
            inv_call = inv_call_list[call_i]
            sleep(1)
            if not inv_call == None:
                id_ = client.req_real_time_bars(inv_call, what_to_show=opt_wts)
                name = 'inv_call'+str(call_i)
                rbd.add_id(name, inv_call, id_)
                sleep(1)
        return rbd
    
    def fill_upc_list_with_historical_data():
        print('Collecting historical option data: ')
        for option_list in put_list, call_list, inv_put_list, inv_call_list:
            if option_list == None:
                continue
            for option in option_list:
                if option == None:
                    continue
                print('.', end='')
                for data in request(option, opt_wts):
                    bar = _hist_db_record_2_bar_analyzer_info(data)
                    for upc in upc_list:
                        upc.data_for(option, bar)
            print()
        
    def open_output_for_each_upc():
        csv_out_list = []
        for upc_i, upc in enumerate(upc_list):
            output_file = os.path.join(
                                mypy.TMP_LOCATION, output_file_name+str(upc_i))
            csv_out = csv.writer(open(output_file, 'w', buffering=1))
            csv_out.writerow(upc_csv_header)
            csv_out_list.append(csv_out)
            #to_file = lambda x, y: upc_csv(x, csv_out_list[upc_i])
        return csv_out_list
    
    #create info file for upc_investigator
    info_file_name = os.path.join(
                        mypy.TMP_LOCATION, '.'.join([output_file_name, 'info']))
    mypy.export_pickle(upc_list, info_file_name)
    #setting up live feeds and live feed dictionary   
    print('starting live feeds')
    real_bar_dictionary = set_up_real_bar_dictionary()
    underlying_id = client.req_real_time_bars(underlying,
                                              what_to_show=und_wts)
    real_bar_dictionary.add_id('underlying', underlying, underlying_id)
    #requesting historical data from db
    print('requesting historical data')
    interactive_db_lookup = mypy.get_bool('interactive db lookup? (y/N) ',
                                          default = False)
    lookback_period = mypy.now() - lookback
    request = lambda ctr, show: historical_data_from_db(
        contract=ctr, start_time=lookback_period, barsize=hist_barsize,
        show=show, twss=client, verbose=interactive_db_lookup)
    print('* underlying data')
    underlying_hist = request(underlying, und_wts)
    fill_upc_list_with_historical_data()
    for data in underlying_hist:
        bar = _hist_db_record_2_bar_analyzer_info(data)        
        for upc_i, upc in enumerate(upc_list):
            print(upc_i, upc.data_for(underlying, bar))
    #analyzing historical data
    print('analyzing historical data: ')
    csv_output_h = open_output_for_each_upc()
    output = lambda data, h_nr: upc_csv(data, csv_output_h[h_nr])
    for upc_i, upc in enumerate(upc_list):
        print('.', end='')
        while not upc.has_empty_datalist:
            #print(upc_i, end='')
            analysis = upc.analysis()
            if analysis:
                output(analysis, upc_i)
                #print('*', end='')
    print()
    #analyzing live data
    for upc in upc_list:
        upc.clear_data_lists()
    print('live bars')
    while True:
        real_bar_data = real_bar_dictionary.collect_available_data()
        for contract, data in real_bar_data:
            bar = _tws_real_time_bar_2_bar_analyzer_info(data)
            for upc in upc_list:
                upc.data_for(contract, bar)
        for upc_i, upc in enumerate(upc_list):
            print(upc_i)
            analysis = upc.analysis()
            if analysis:
                print(upc_i)
                output(analysis, upc_i)
    

def multi_upc_terminal(base_file_name):
    
    menu = mypy.SelectionMenu()
    menu.add_menu_item('List combos', 'c', mupc_list_combos)
    menu.add_menu_item('New chart', 'n', mupc_new_chart)
    menu.add_menu_item('Remove chart', 'r', mupc_remove_chart)
    menu.add_menu_item('Quit', 'q')
    
    info_file_name = os.path.join(
                        mypy.TMP_LOCATION, '.'.join([base_file_name, 'info']))
    upc_list = mypy.import_pickle(info_file_name)
    open_charts = dict()
    
    while True:
        choice = menu.get_users_choice()
        if choice == 'Quit':
            break
        else:
            choice(base_file_name, upc_list, open_charts)
    for type_ in open_charts:
        for plot in open_charts[type_].values():
            plot.close()

def mupc_new_chart(base_file_name, upc_list, open_charts):
    
    menu = mypy.SelectionMenu(auto_number=True, interface='TXT_ROW')
    menu.add_menu_item('strangle price', return_value=mupc_sp)
    menu.add_menu_item('underlying + strangle low', return_value=mupc_usl)
    menu.add_menu_item('underlying + strangle low(i)', return_value=mupc_usli)
    menu.add_menu_item('strangle sigma', return_value=mupc_sigma)
    menu.add_menu_item('Quit')
    
    choice = menu.get_users_choice()
    if choice == 'Quit':
        return
    choice(base_file_name, upc_list, open_charts)
    
def select_list_of_strangles(upc_list):
    selected_list = []
    max_selection_nr = len(upc_list) - 1
    while True:
        mupc_list_combos(None,upc_list, None, exclude=selected_list)
        strangle_nr = mypy.get_int('select strangle (\'enter\' to stop): ',
                                   maximum=max_selection_nr, empty=True)
        if strangle_nr == None:
            break
        if strangle_nr in selected_list:
            continue
        selected_list.append(strangle_nr)
        if len(upc_list) == len(selected_list):
            break #stop if all combo's are selected
    return selected_list        
        
def mupc_usl(base_file_name, upc_list, open_charts):
    '''draw underlying strangle low'''
    strangle_list = select_list_of_strangles(upc_list)
    if 'strangle low' in open_charts:
        if str(strangle_list) in open_charts['strangle low']:
            print('plot exists!')
    else:
        open_charts['strangle low'] = dict()
    if strangle_list:
        new_plot = mupc_draw(base_file_name, 
                             upc_list, strangle_list, 'strangle low')
        open_charts['strangle low'][str(strangle_list)] = new_plot
        
def mupc_usli(base_file_name, upc_list, open_charts):
    '''draw underlying strangle low set'''
    strangle_list = select_list_of_strangles(upc_list)
    if 'strangle low set' in open_charts:
        if str(strangle_list) in open_charts['strangle low set']:
            print('plot exists!')
    else:
        open_charts['strangle low set'] = dict()
    if strangle_list:
        new_plot = mupc_draw(base_file_name,
                             upc_list, strangle_list, 'strangle low set')
        open_charts['strangle low set'][str(strangle_list)] = new_plot
        
def mupc_sp(base_file_name, upc_list, open_charts):
    '''draw strangle price'''
    strangle_list = select_list_of_strangles(upc_list)
    if 'strangle price' in open_charts:
        if str(strangle_list) in open_charts['strangle price']:
            print('plot exists!')
    else:
        open_charts['strangle price'] = dict()
    if strangle_list:
        new_plot = mupc_draw(base_file_name,
                             upc_list, strangle_list, 'strangle price')
        open_charts['strangle price'][str(strangle_list)] = new_plot 
         
def mupc_sigma(base_file_name, upc_list, open_charts):
    '''draw strangle sigma'''
    strangle_list = select_list_of_strangles(upc_list)
    if 'strangle sigma' in open_charts:
        if str(strangle_list) in open_charts['strangle sigma']:
            print('plot exists!')
    else:
        open_charts['strangle sigma'] = dict()
    if strangle_list:
        new_plot = mupc_draw(base_file_name,
                             upc_list, strangle_list, 'strangle sigma')
        open_charts['strangle sigma'][str(strangle_list)] = new_plot
        
def mupc_remove_chart(base_file_name, upc_list, open_charts):
    #select chart
    open_types = list(open_charts.keys())
    number_of_open_types = len(open_types)
    if number_of_open_types == 0:
        print('No open charts.')
        return
    if number_of_open_types == 1:
        type_ = open_types.pop()
    else:
        type_ = mypy.get_from_list(open_types, 'type of chart: ')
    data_sets = list(open_charts[type_].keys())
    number_of_data_sets = len(data_sets)
    assert number_of_data_sets > 0, (        
            'bad clean up in open_charts dict, type without a member')
    if number_of_data_sets == 1:
        data_set = data_sets.pop()
    else:
        data_set = mypy.get_from_list(data_sets, 'data set: ')
    #close chart    
    open_charts[type_][data_set].close()
    #update open_charts
    open_charts[type_].pop(data_set)
    if len(open_charts[type_]) == 0:
        open_charts.pop(type_)
    
def mupc_draw(base_file_name, upc_list, strangle_list, type_):
    draw_underlying_types = {'strangle low', 'strangle low set'}
    x_y_datafile_fields = {'underlying': [1,2],
                           'strangle low': [1, 11],
                           'strangle low set': [1,14],
                           'strangle price': [1,9],
                           'strangle sigma': [1,12]}
    data_file_names = []
    data_strangle_names = []
    for strangle_nr in strangle_list:
            data_file_names.append(os.path.join(
                mypy.TMP_LOCATION, base_file_name+str(strangle_nr)))
            data_strangle_names.append(
                str(upc_list[strangle_nr].put.strike) + '/' +
                str(upc_list[strangle_nr].call.strike))
    chart = gnuplot.chart(type_, automatic_redraw=5)
    chart.settings.datafile_seperator(',')
    chart.settings.timeseries_on_axis('x')
    for file_i, filename in enumerate(data_file_names):
        chart.add_data_serie(title=data_strangle_names[file_i],
                             filename=filename, 
                             fields=x_y_datafile_fields[type_],
                             style='line')
    if type_ in draw_underlying_types:
        chart.add_data_serie(title='underlying', filename=data_file_names[0], 
                             fields=x_y_datafile_fields['underlying'],
                             style='line')
    chart.plot()
    return chart
        
        
            
    
def mupc_list_combos(foo, upc_list, bar, exclude=[]):
    print('COMBO\'S')
    print('=======')
    print('NR |    PUT     |   CALL     |  INVERSE')
    print('-----------------------------------------')
    format_line = '{:2} | {:10} | {:10} | {}'
    for upc_i, upc in enumerate(upc_list):
        if upc_i in exclude:
            # don't show combo's in exclude list
            continue
        print(format_line.format(upc_i, upc.put.strike, upc.call.strike, 
                               upc.has_inverse_options))
    print()
                 
    
def upc_proces_history(underlying, put, call, 
                       underlying_hist, put_hist, call_hist,
                       und_wts, opt_wts,
                       modes, 
                       put_inv, call_inv, 
                       inv_put_hist, inv_call_hist,
                       output):
    if 'auto_sig' in modes:
        dataset = [underlying_hist, put_hist, call_hist]
    if 'set_sig' in modes:
        dataset = [underlying_hist, put_hist, call_hist,
                   inv_put_hist, inv_call_hist]
    while True:
        data = mypy.data_with_common_field_value(*dataset,
                                                 field='datetime')
        if not data:
            break
        else:
            for ell_nr in range(len(data)):
                row = data[ell_nr]
                data[ell_nr] = BarAnalyzerInfo(
                    row.datetime, 
                    row.open, row.high, row.low, row.close,
                    row.volume)
            try:
                result = upc_analyzer(data, put, call, modes, put_inv, call_inv)
            except options.NoSolution:
                continue
            output(result)

    
def upc_analyzer(data, put, call, modes, inv_put, inv_call):
    
    underlying_data = data[0]
    put_data = data[1]
    call_data = data[2]
    result = BarAnalysis(underlying_data.date_)
    result.add_index(underlying_data)
    result.add_put_info(put_data, put)
    result.add_call_info(call_data, call)
    if 'set_sig' in modes:
        inv_put_data = data[3]
        inv_call_data = data[4]
        result.add_call_info(inv_put_data, inv_put, name='inverse put')
        result.add_put_info(inv_call_data, inv_call, name='inverse call')
    result.calc_strangle_info(modes=modes)
    return result

def std_upc_result_handler(result):
    
    print('close', result.close(INDEX))
    print('intrinsic value put', result.intrinsic_value(PUT))
    print('intrinsic value call', result.intrinsic_value(CALL))
    print('time value put', result.time_value(PUT))
    print('time value call', result.time_value(CALL)),
    result.intrinsic_value(PUT)
    

upc_csv_header = ['time', 'underlying',
                  'put',
                  'intrinsic val put', 'time val put',
                  'call',
                  'intrinsic val call', 'time val call',
                  'sum pc', 'sum time val pc',
                  'strangle low', 'strangle deviation',
                  'strangle low val',
                  'set strangle low', 'set strangle low val']
def upc_csv(result, csv_handler):
    
    curr_date = mypy.datetime2format(result.date_, mypy.iso8601TimeStr)
    info = [curr_date, result.close(INDEX), 
            result.close(PUT),
            result.intrinsic_value(PUT), result.time_value(PUT),
            result.close(CALL),
            result.intrinsic_value(CALL), result.time_value(CALL),
            result.close(PUT)+result.close(CALL),
            result.time_value(PUT)+result.time_value(CALL),
            result.strangle_low, result.strangle_accror_deviation,
            result.strangle_low_value]
    if hasattr(result, 'set_low'):
        info += [result.set_low, result.set_low_value]    
    csv_handler.writerow(info)

#######################################################################
#
# BAR ANALYSIS
#

class BarAnalysis():
    
    def __init__(self, date_):
        self.date_ = date_
        self.__basic_info = dict()
        self.__intrinsic_value = dict()
        self.__time_value = dict()
        self.options = dict()
        
    def add_basic_info(self, data, name, product_type=None, info_type=None):
        
        assert isinstance(data, BarAnalyzerInfo)
        full_name = info_name(name, product_type, info_type)
        self.__basic_info[full_name] = data
        
    def basic_info(self, name, product_type, info_type, info):
        tr = {OPEN: 'open_',
              HIGH: 'high',
              LOW: 'low',
              CLOSE: 'close',
              VOLUME: 'volume'}
        full_name = info_name(name, product_type, info_type)
        try:
            return getattr(self.__basic_info[full_name], tr[info])
        except KeyError:
            raise InfoNotSet('{}/{}'.format(name, info))
  
    def open_(self, name=None, product_type=INDEX, info_type=None):
        
        return self.basic_info(name, product_type, info_type, OPEN)
    
    def high(self, name=None, product_type=INDEX, info_type=None):
        
        return self.basic_info(name, product_type, info_type, HIGH)
    
    def low(self, name=None, product_type=INDEX, info_type=None):
        
        return self.basic_info(name, product_type, info_type, LOW)
        
    def close(self, name=None, product_type=INDEX, info_type=None):
        
        return self.basic_info(name, product_type, info_type, CLOSE)
    
    def volume(self, name=None, product_type=INDEX, info_type=None):
        
        return self.basic_info(self, name, product_type, info_type, VOLUME)
        
    def add_index(self, data, name=None, info_type=None):
        
        self.add_basic_info(data, name, INDEX, info_type)
        
    def add_put_info(self, data, put, 
                     und_name=None, und_type=INDEX, und_info=None,
                     name=None, info_type=None):
        
        full_name = info_name(name, PUT, info_type)
        self.options[full_name] = options.option_from_tws_contract(put)
        und_full_name = info_name(und_name, und_type, und_info)        
        self.add_basic_info(data, full_name)
        if not und_full_name in self.__basic_info:
            raise AttributeError('underlying name type info not found')
        self.__intrinsic_value[full_name] = self.intrinsic_value_option(
                                              PUT, put.strike, und_full_name)
        self.__time_value[full_name] = self.time_value_option(full_name)
        
        
    def add_call_info(self, data, call, 
                     und_name = None, und_type=INDEX, und_info=None,
                      name=None, info_type=None):
        
        full_name = info_name(name, CALL, info_type)
        self.options[full_name] = options.option_from_tws_contract(call)
        und_full_name = info_name(und_name, und_type, und_info)
        self.add_basic_info(data, full_name)
        if not und_full_name in self.__basic_info:
            raise AttributeError('underlying name type info not found')
        self.__intrinsic_value[full_name] = self.intrinsic_value_option(
                                              CALL, call.strike, und_full_name)
        self.__time_value[full_name] = self.time_value_option(full_name)
        
    def calc_strangle_info(self, 
                           call_name=None, call_info_type=None,
                           put_name=None, put_info_type=None,
                           und_name=None, und_type=INDEX, und_info=None,
                           modes={'auto_sig'},
                           inv_put_name='inverse put', inv_put_info_type=None,
                           inv_call_name='inverse call', inv_call_info_type=None):
        
        full_call_name = info_name(call_name, CALL, call_info_type)
        full_put_name = info_name(put_name, PUT, put_info_type)
        full_und_name = info_name(und_name, und_type, und_info)
        call = self.options[full_call_name]
        put = self.options[full_put_name]
        st = options.Strangle(call.strike, put.strike, call.expiry)    
        st.autoset_black_and_scholes(self.close(full_und_name),
                                     self.close(full_call_name),
                                     self.close(full_put_name),
                                     self.date_)
        self.strangle_low = st.low
        self.strangle_low_value = st.est_value_for_price(self.strangle_low)
        self.strangle_accror_deviation = st.accror_deviation
        self.strangle_sentiment = st.sentiment
        self.strangle_risk_free_interest_rate = st.risk_free_interest_rate
        if not 'set_sig' in modes:
            return
        full_inv_call_name = info_name(inv_call_name, PUT, inv_call_info_type)
        full_inv_put_name = info_name(inv_put_info_type, CALL, inv_put_info_type)
        call = self.options[full_call_name]
        put = self.options[full_inv_call_name]
        st_ = options.Strangle(call.strike, put.strike, call.expiry)
        st_.autoset_black_and_scholes(self.close(full_und_name),
                                     self.close(full_call_name),
                                     self.close(full_inv_call_name),
                                     self.date_)
        self.c_strangle_accror_deviation = st_.accror_deviation
        self.c_strangle_sentiment = st_.sentiment
        self.c_strangle_risk_free_interest_rate = st_.risk_free_interest_rate
        call = self.options[full_inv_put_name]
        put = self.options[full_put_name]
        st_ = options.Strangle(call.strike, put.strike, call.expiry)
        st_.autoset_black_and_scholes(self.close(full_und_name),
                                     self.close(full_inv_put_name),
                                     self.close(full_put_name),
                                     self.date_)
        self.p_strangle_accror_deviation = st_.accror_deviation
        self.p_strangle_sentiment = st_.sentiment
        self.p_strangle_risk_free_interest_rate = st_.risk_free_interest_rate
        call = self.options[full_call_name]
        put = self.options[full_put_name]
        st_set = options.Strangle(call.strike, put.strike, call.expiry)
        st_set.set_black_and_scholes(
            call_risk_free_interest_rate=self.c_strangle_risk_free_interest_rate,
            put_risk_free_interest_rate=self.p_strangle_risk_free_interest_rate,
            time_delta=self.date_,
            call_accror=self.c_strangle_accror_deviation,
            put_accror=self.p_strangle_accror_deviation,
            call_sentiment=self.c_strangle_sentiment,
            put_sentiment=self.p_strangle_sentiment)           
        self.set_low = st_set.low
        self.set_low_value = st_set.est_value_for_price(self.set_low)
                           
    def intrinsic_value_option(self, right, strike, underlying):
        iv = dict()
        iv[OPEN] = strike - self.open_(underlying)
        iv[CLOSE] = strike - self.close(underlying)
        iv[HIGH] = strike - self.high(underlying)
        iv[LOW] = strike - self.low(underlying)
        if right == CALL:
            iv = {k:-1*v for k,v in iv.items()}
        iv = {k: 0 if v < 0 else v for k, v in iv.items()}
        return OHLC(iv[OPEN], iv[HIGH], iv[LOW], iv[CLOSE])
    
    def intrinsic_value(self, name, product_type=None, info_type=None, 
                        info=CLOSE):
        full_name = info_name(name, product_type, info_type)
        return getattr(self.__intrinsic_value[full_name], info)
    
    def time_value_option(self, option_name):
        
        assert _is_option_name(option_name), 'name is not no option'
        on = option_name
        tv = dict()
        tv[OPEN] = self.open_(on) - self.intrinsic_value(on, info=OPEN)
        tv[CLOSE] = self.close(on) - self.intrinsic_value(on, info=CLOSE)
        tv[HIGH] = self.high(on) - self.intrinsic_value(on, info=HIGH)
        tv[LOW] = self.low(on) - self.intrinsic_value(on, info=LOW)        
        return OHLC(tv[OPEN], tv[HIGH], tv[LOW], tv[CLOSE])
    
    def time_value(self, name, product_type=None, info_type=None, 
                        info=CLOSE):
        full_name = info_name(name, product_type, info_type)
        return getattr(self.__time_value[full_name], info)
            
    
        
        
def info_name(name, product_type, info_type):
    ID_TAG = '4roce'
    #check if name is a info_name, if so return name
    if name and name.endswith(ID_TAG):
        return name
    #check if name is member of product type, if so assume no name is given
    if name in PRODUCT_TYPES:
        if product_type in INFO_TYPES:
            info_type = product_type
        product_type = name
        name = None
    #create name
    name = name if name else UNKNOWN
    info_type = info_type if info_type else UNKNOWN
    #print(name, product_type, info_type)
    return '|'.join([name, product_type, info_type, ID_TAG])

def _is_option_name(name):
    
    if name:
        el = name.split('|')
        answer = el[1] in [PUT, CALL]
    else:
        answer = False
    return answer

def _hist_db_record_2_bar_analyzer_info(record):
    return BarAnalyzerInfo(
                    record.datetime, 
                    record.open, record.high, record.low, record.close,
                    record.volume)

def _tws_real_time_bar_2_bar_analyzer_info(bar):
    return BarAnalyzerInfo(
                    bar.time_, 
                    bar.open_, bar.high, bar.low, bar.close,
                    bar.volume) 

    
if __name__ == '__main__':
    main()