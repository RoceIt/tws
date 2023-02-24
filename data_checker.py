#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#
from sys import stdout as output
import datetime

from roc_input import (SelectionMenu, get_bool, get_timedelta,
                       get_existing_file_name, get_new_filename,
                       get_time)
from roc_directories import CSV_DATA_LOCATION, full_path
import roc_itertools
import roc_datetime
from data_info import DailyDataInfo
from marketdata import data_bar_feeder_from_file

def main():
    '''Select data checker sub category.'''
    ###
    menu = SelectionMenu(
        interface='TXT_ROW',
        message='Choice: ',
        auto_number=True
    )
    menu.add_menu_item('Daily data', return_value=daily_data)
    menu.add_menu_item('Quit', return_value='quit')
    ###
    while True:
        print()
        choice = menu.get_users_choice()
        if choice == 'quit':
            break
        choice()
        
def daily_data():
    '''Select daily data checker function.'''
    ###
    menu = SelectionMenu(interface='TXT_ROW',
                         message='Choice: ',
                         auto_number=True)
    menu.add_menu_item('New', return_value=new_daily_data)
    menu.add_menu_item('Update', return_value=update_daily_data)
    menu.add_menu_item('Read', return_value=read_daily_data)
    ###
    menu.get_users_choice()()
    
def new_daily_data():
    '''Create a new daily data analysis file.'''
    ###
    menu = SelectionMenu(interface='TXT_ROW',
                         message='Choice: ',
                         auto_number=True)
    menu.add_menu_item('from file' , return_value=new_daily_data_from_file)
    menu.add_menu_item('from database', return_value=new_daily_data_from_db)
    menu.add_menu_item('Quit', return_value=SelectionMenu.pass_)
    ###
    menu.get_users_choice()()
    
def new_daily_data_from_file():
    '''Create a new daily data analysis file.'''
    ###
    base_file_name = get_existing_file_name('base_filename ({}): ',
                                   default=full_path(CSV_DATA_LOCATION, 'AEX'),
                                   warning_mss='unknown file')
    base_is_index = get_bool('indexdata {}:')
    info_file_name = '.'.join([base_file_name, 'ddi'])
    info_file_name = get_new_filename('Daily Data Info file name ({}): ',
                                      default=info_file_name,
                                      is_ok_mss='overwrite file {}',
                                      warning_mss='file exists!')
    ###
    ddi = DailyDataInfo(
              info_file_name, DailyDataInfo.MODE_NEW, file_check=False)
    all_data = data_bar_feeder_from_file(base_file_name, is_index=base_is_index)
    fill_ddi_file(ddi, all_data)
    
def new_daily_data_from_db():
    print('New daily data from db not implemented')
    
def update_daily_data():
    print('UPDATE not implemented')
    
def read_daily_data():
    print('READ not implemented')
    
def fill_ddi_file(ddi, all_data):
    '''Chop data in daily chunks, and proces these.'''
    assert isinstance(ddi, DailyDataInfo)
    ###
    one_day_of_data = []
    first_run = True
    days_checked = 0
    ###
    ddi.set_up_start_end_times()
    ddi.session_info['max start gap'] = ddi_select_max_start_timegap(ddi)
    ddi.session_info['max end gap'] = ddi_select_max_end_timegap(ddi)
    ddi.session_info['fixed ath rth translation'] = dict()
    ddi.session_info['multiple trading periods'] = ddi_select_multi_mode(ddi)
    for line in all_data:    
        one_day_of_data.append(line)
        if first_run:
            first_run = False
            continue
        if one_day_of_data[-1].time.date() == one_day_of_data[-2].time.date():
            continue
        days_checked += 1
        if days_checked % 20 == 0:
            print('.', end='')
            output.flush()
        analyse_ddi(ddi, one_day_of_data[:-1])
        one_day_of_data = one_day_of_data[-1:]
    ddi.store(to_file=True)
        
def analyse_ddi(ddi, one_day_of_data):
    '''Analyse one day of data.'''
    assert isinstance(ddi, DailyDataInfo)
    ###
    ###
    date = one_day_of_data[0].time.date()
    ddi.add_new_date(date)
    if ddi.session_info['multiple trading periods']:
        ddi_set_multiple_start_end_info(ddi, one_day_of_data)
    else:
        ddi_set_single_start_end_info(ddi, one_day_of_data)
    ddi_search_and_insert_gaps(ddi, one_day_of_data)
    ddi.store()
    
    
def ddi_select_max_start_timegap(ddi, maximum=datetime.timedelta(hours=1/2)):
    '''Ask the maximal exceptable timegap for the auto select start times.
    
    The gap can't be bigger or equeal the the smallest gap between all
    ath and rth start times. If not it would be dubious.
    
    Paremeters:
      ddi -- a DailyDataInfo instance
      maximum -- a datetime.timedelta with the maximum gap
    '''
    assert isinstance(ddi, DailyDataInfo)
    ###
    all_times = set(ddi.ath_start_times) | set(ddi.rth_start_times)
    if len(all_times) == 1:
        gap = maximum
    else:        
        gap = min(roc_itertools.delta(
                    sorted(map(roc_datetime.timetodatetime, all_times))))
        gap = min(gap, maximum)
    ###
    users_choice = get_timedelta(
        'Maximal gap for automatic start time choice (e.g. 5 minutes): ',
        err_message = 'Invalid choice!', 
        maximum=gap, lim_message='max gap is {1}')
    return users_choice
    
def ddi_select_max_end_timegap(ddi, maximum=datetime.timedelta(hours=1/2)):
    '''Ask to maximal exceptable timegap for the auto select end times.
    
    The gap can't be bigger or equeal the the smallest gap between all
    ath and rth start times. If not it would be dubious.
    
    Paremeters:
      ddi -- a DailyDataInfo instance
      maximum -- a datetime.timedelta with the maximum gap
    '''
    assert isinstance(ddi, DailyDataInfo)
    ###
    all_times = set(ddi.ath_end_times) | set(ddi.rth_end_times)
    if len(all_times) == 1:
        gap = maximum
    else:        
        gap = min(roc_itertools.delta(
                    sorted(map(roc_datetime.timetodatetime, all_times))))
        gap = min(gap, maximum)
    ###
    users_choice = get_timedelta(
        'Maximal gap for automatic time choice end of day(e.g. 5 minutes): ',
        err_message = 'Invalid choice!', 
        maximum=gap, lim_message='max gap is {1}')
    return users_choice

def ddi_select_multi_mode(ddi):
    '''Select to search for multiple trading periods'''
    ###
    mss = 'Multiple trading periods {}'
    ###
    return get_bool(mss, default=False)

def ddi_set_multiple_start_end_info(ddi, one_day_of_data):
    '''Select start and ends for data with more then one trading period'''
    mss = 'Multiple trading periods not implemented'
    raise NotImplementedError(mss)

def ddi_set_single_start_end_info(ddi, one_day_of_data):
    '''Select start and end for data with one trading perion'''
    ###
    date_ = one_day_of_data[0].time.date()
    first_time = one_day_of_data[0].time.time()
    last_time = one_day_of_data[-1].time.time()
    starttime, rth_start = ddi_select_start(ddi, date_, first_time)
    end_time, rth_end = ddi_select_end(ddi, date_, last_time)
    first_ath_data = one_day_of_data[0].time.time()
    last_ath_data = one_day_of_data[-1].time.time()
    first_rth_data = ddi_find_first_rth_data(one_day_of_data, rth_start)
    last_rth_data = ddi_find_last_rth_data(one_day_of_data, rth_end)
    ###
    ddi_set_ath_rth_hours (ddi, [starttime], [first_ath_data], 
                                [rth_start], [first_rth_data],
                                [last_rth_data], [rth_end],
                                [last_ath_data], [end_time])

def ddi_set_ath_rth_hours(ddi, ath_start, first_ath,
                               rth_start, first_rth,
                               last_rth, rth_end,
                               last_ath, ath_end):
    '''Set the zones in the ddi.
    
    All the parameters(not ddi) are lists. ath and rth lists must all have.
    '''
    assert isinstance(ddi, DailyDataInfo)
    ###
    ###
    for start, first, last, end in zip(ath_start, first_ath, last_ath, ath_end):
        ddi.trading_hours('ath', start, first, last, end)
    for start, first, last, end in zip(rth_start, first_rth, last_rth, rth_end):
        ddi.trading_hours('rth', start, first, last, end)  

def ddi_search_and_insert_gaps(ddi, one_day_of_data):
    '''Find gaps and insert them in the ddi.'''
    assert isinstance(ddi, DailyDataInfo)
    ###
    known_gaps = ddi.date_info['last_data']
    previous_end = None
    ###
    for bar in one_day_of_data:
        curr_time = bar.time.time()
        if not(previous_end is None
               or
               previous_end == curr_time
               or
               previous_end in known_gaps):
            ddi.add_gap(previous_end, curr_time)
        previous_end = bar.end_time().time()
    

def ddi_select_start(ddi, date_, first_known_time):
    '''Return the first rth/ath time of the day.
    
    First it checks to see if the first_known_time is close to a known
    start time. If so it is returned, if not, it will try to resolve the
    time with the users help.
    
    Parameters:
      ddi -- a DailyDataInfo instance
      first_known_time -- a datetime.datetime object, the first of the day
    '''
    assert isinstance(ddi, DailyDataInfo)
    ###
    start_time = ddi_auto_select_start(ddi, first_known_time)
    ###
    if start_time is None:
        start_time = ddi_manually_select_start(ddi, date_, first_known_time)
    rth_start = ddi_rthforath(ddi, start_time, 'start')    
    return start_time, rth_start

def ddi_auto_select_start(ddi, first_known_time):
    '''Returns the start time if auto_selection is possible.'''
    assert isinstance(ddi, DailyDataInfo)
    ###
    gap = (roc_datetime.timetodatetime(first_known_time) - 
                    roc_datetime.timetodatetime(ddi.standard_ath_start))
    ###
    if datetime.timedelta(0) <= gap <= ddi.session_info['max start gap']:
        return ddi.standard_ath_start
    else:
        return None
    
def ddi_manually_select_start(ddi, date_, first_known_time):
    '''Ask user to change or add a start time.'''
        
    assert isinstance(ddi, DailyDataInfo)
    ###
    mss = 'Can\'t auto select start. First data on {}'
    warning = mss.format(first_known_time)
    menu_mss = 'Select new to add a start time: '
    only_rth = only_rth_p(ddi) 
    choice_menu = SelectionMenu(message=menu_mss, auto_number=True)
    choice_menu.add_items([t for t in ddi.ath_start_times 
                           if t <= first_known_time])
    choice_menu.add_menu_item('new')    
    ###
    print('\n\n', date_)
    print(warning)
    choice = choice_menu.get_users_choice()
    if choice == 'new':
        start = ddi_new_ath('start', ddi, first_known_time)
    elif choice == ddi.standard_ath_start:
        start = choice
    else:
        start = choice
        ddi_set_new_ath_standard('start', ddi, choice)
    return start
    
def ddi_select_end(ddi, date_, last_known_time):
    '''Return the last rth/ath time of the day.
    
    First it checks to see if the last_known_time is close to a known
    end time. If so it is returned, if not, it will try to resolve the
    time with the users help.
    
    Parameters:
      ddi -- a DailyDataInfo instance
      last_known_time -- a datetime.datetime object, the last of the day
    '''
    ###
    end_time = ddi_auto_select_end(ddi, last_known_time)
    ###
    if end_time is None:
        end_time = ddi_manually_select_end(ddi, date_, last_known_time)
    rth_end = ddi_rthforath(ddi, end_time, 'end')    
    return end_time, rth_end

def ddi_auto_select_end(ddi, last_known_time):
    '''Returns the end time if auto_selection is possible.'''
    assert isinstance(ddi, DailyDataInfo)
    ###
    gap = (roc_datetime.timetodatetime(ddi.standard_ath_end) -
                       roc_datetime.timetodatetime(last_known_time))
    ###
    if datetime.timedelta(0) <= gap <= ddi.session_info['max end gap']:
        return ddi.standard_ath_end
    else:
        return None
    
def ddi_manually_select_end(ddi, date_, last_known_time):
    '''Ask user to change or add a end time.'''        
    assert isinstance(ddi, DailyDataInfo)
    ###
    mss = 'Can\'t auto select end. Last data on {}'
    warning = mss.format(last_known_time)
    menu_mss = 'Select new to add an end time: '
    only_rth = only_rth_p(ddi)
    choice_menu = SelectionMenu(message=menu_mss, auto_number=True)
    choice_menu.add_items([t for t in ddi.ath_end_times 
                           if t >= last_known_time])
    choice_menu.add_menu_item('new')    
    ###
    print('\n\n', date_)
    print(warning)
    choice = choice_menu.get_users_choice()
    if choice == 'new':
        end = ddi_new_ath('end', ddi, last_known_time)
    elif choice == ddi.standard_ath_end:
        end = choice
    else:
        end = choice
        ddi_set_new_ath_standard('end', ddi, choice)
    return end

def ddi_new_ath(start_or_end, ddi, ref_time):
    ''' Insert a new ath start/end in the ddi.
    
    If only rth is set to True in the session_info dir, it is also added
    to the rth start list.
    '''
    assert isinstance(ddi, DailyDataInfo)
    ###    
    only_rth = ddi.session_info['only rth']
    lists = {True: ['ath', 'rth'], False: ['ath']}[only_rth]
    get_mss = {True: 'New {} time (hh:mm:ss): '.format(start_or_end),
               False: 'New ath {} time (hh:mm:ss): '.
                                      format(start_or_end)}[only_rth]
    err_mss = 'invalid time'
    if start_or_end == 'start':
        minimum, maximum, lim_mss = None, ref_time, 'max time is {1}'
    else:
        minimum, maximum, lim_mss = ref_time, None, 'min time is {0}'
    ###
    new_time = get_time(get_mss, '%H:%M:%S', err_message=err_mss,
                        maximum=maximum, minimum=minimum, lim_message=lim_mss)
    for list_ in lists:
        ddi.new_valid_time(start_or_end, list_, new_time)
    ddi_set_new_ath_standard(start_or_end, ddi, new_time)
    return new_time

def ddi_set_new_ath_standard(start_or_end, ddi, new_standard):
    '''Set new_standard as new ath standard start/end value.
    
    If rth_only is set, do the same with the rth_list.
    '''
    assert isinstance(ddi, DailyDataInfo)
    ###
    only_rth = ddi.session_info['only rth']
    lists = {True: ['ath', 'rth'], False: ['ath']}[only_rth]
    is_std_mss = 'Set {} as new standard value? {{}}'.format(new_standard)
    ###
    if get_bool(is_std_mss, default=False):
        for list_ in lists:            
            ddi.new_valid_time(start_or_end, list_, new_standard, True)
            
def ddi_rthforath(ddi, ath_time, start_or_end):
    '''Find a rth time for the given ath time.'''
    assert isinstance(ddi, DailyDataInfo)
    ###
    only_rth = only_rth_p(ddi)
    tr = ddi.session_info['fixed ath rth translation']
    rth_time = tr.get(ath_time)
    ###
    if only_rth:
        rth_time = ath_time
    elif rth_time is None:
        mss = 'select rth for ath @ {}: '.format(ath_time)
        choice_menu = SelectionMenu(message=mss, auto_number=True)
        all_times = set(ddi.rth_end_times + ddi.rth_start_times)
        if start_or_end == 'start':
            all_times = [t for t in all_times if t >= ath_time]
        else:
            all_times = [t for t in all_times if t <= ath_time]
        choice_menu.add_items(all_times)
        choice_menu.add_menu_item('new')    
        rth_time = choice_menu.get_users_choice()
        if rth_time == 'new':
            rth_time = ddi_new_rth(start_or_end, ddi, ath_time)
        if get_bool('add as default to sessions ath_rth info? {}',default=True):
            tr[ath_time] = rth_time
    return rth_time
            
        
def only_rth_p(obj):
    '''Check if for ibhect rth art equal to ath'''
    ###
    ###
    if isinstance(obj, DailyDataInfo):
        answer = obj.session_info.get('only rth')
        if answer is None:
            mss = 'All trading hours are regular trading hours? {} '
            obj.session_info['only rth'] = get_bool(mss, default=True)
    else:
        mss = 'only_rth_p not defined for {}'.format(type(obj))
        raise Exception(mss)
    return answer

def ddi_new_rth(start_or_end, ddi, ref_time):
    ''' Insert a new rth start/end in the ddi.'''
    assert isinstance(ddi, DailyDataInfo)
    ###   
    get_mss = 'New rth {} time (hh:mm:ss): '.format(start_or_end)
    err_mss = 'invalid time'
    if start_or_end == 'start':
        minimum, maximum, lim_mss = ref_time, None, 'min time is {0}'
    else:
        minimum, maximum, lim_mss = None, ref_time, 'max time is {1}'
    ###
    new_time = get_time(get_mss, '%H:%M:%S', err_message=err_mss,
                        maximum=maximum, minimum=minimum, lim_message=lim_mss)
    ddi.new_valid_time(start_or_end, 'rth', new_time)
    ddi_set_new_ath_standard(start_or_end, ddi, new_time)
    return new_time

def ddi_set_new_ath_standard(start_or_end, ddi, new_standard):
    '''Set new_standard as new ath standard start/end value.
    
    If rth_only is set, do the same with the rth_list.
    '''
    assert isinstance(ddi, DailyDataInfo)
    ###
    is_std_mss = 'Set {} as new standard value? {{}}'.format(new_standard)
    ###
    if get_bool(is_std_mss, default=False):
            ddi.new_valid_time(start_or_end, 'ath', new_standard, True)
            
def ddi_find_first_rth_data(one_day_of_data, rth_start):
    '''Return the first time equal to or later then rth start'''
    ###
    for d in one_day_of_data:
        first_time = d.time.time()
        if first_time >= rth_start:
            break
    else:
        first_time = None
    ###
    return first_time
            
def ddi_find_last_rth_data(one_day_of_data, rth_end):
    '''Return the last time smaller then rth end'''
    ###
    for d in reversed(one_day_of_data):
        last_time = d.time.time()
        if last_time < rth_end:
            break
    else:
        last_time = None
    ###
    return last_time

if __name__ == '__main__':
    main()