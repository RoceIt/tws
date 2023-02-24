#!/usr/bin/env python3
#
#  Copyright (c) 2014, Rolf Camps (rolf.camps@scarlet.be)

import os.path
import sys
from multiprocessing import Pipe, Process
from datetime import datetime, timedelta
from subprocess import Popen

import mypy
import oneplot as plot
import roc_datetime as r_dt
import roc_cli as r_cli
import roc_classes as r_cls
from triads import Swing

### MESSAGES ###
REDRAW = 1
ZOOM_TO_WAVES = 2
ZOOM_OUT = 3
START_UP_WAVE = 4
DRAW_VLINE = 5
SHOW_LIVE_GP_CODE = 6
SHOW_SENDED_GP_CODE = 7
START_DOWN_WAVE = 8
REMOVE_PAUSES = 9
SHOW_PAUSES = 10
ZOOM_TO_LAST_N_DAYS = 11
REMOVE_BAR_COUNTS = 12
SHOW_BAR_COUNTS = 13
SHOW_MARKET_STATUS = 14
REMOVE_MARKET_STATUS = 15
HIDE_SMA = 16
SHOW_SMA = 17
SHOW_SUPPORT = 18
REMOVE_SUPPORT = 19
MAX_SUPPORT_LINES = 20
SHOW_RESISTANCE = 21
REMOVE_RESISTANCE = 22
MAX_RESISTANCE_LINES = 23
SHOW_BOLL_BARS = 24
HIDE_BOLL_BARS = 25
ZOOM_TO_LAST_N_HOURS = 26
SET_CHART_IN_LOOKBACK_MODE = 27
X_AXIS_BACK = 28
X_AXIS_FORWARD = 29
ZOOM_X = 30

i_s = [
    "bars_60",
    "bars_120",
    "bars_240",
    "bars_480",
    "bars_960",
    "bars_1920",
    "bars_3840",
    "bars_7680",
    "bars_15360",
    "bars_30720",
    "bars_61440",
]

ii_s = [
    "info_60",
    "info_120",
    "info_240",
    "info_480",
    "info_960",
    "info_1920",
    "info_3840",
    "info_7680",
    "info_15360",
    "info_30720",
    "info_61440",
]
    
show_i_s = [0,]
    
show_ii_s = []
#show_i_s = [x for x in range(len(i_s))]

verbose = False
chart_list = []
mif_base = ''
total_mess = 0

default_end_space = 5   # in percent of total number of data shown
minum_bars_shown = 20
active_lookback_chart = None

def main():
    global chart_list
    global mif_base
    global auto_renew
    global total_mess
    for i in range(len(i_s)):
        chart_list.append(None)
    mif_base = sys.argv[1]
    auto_renew = float(sys.argv[2]) if len(sys.argv) == 3 else 60
    for chart_id in show_i_s:
        add_chart(chart_id, chart_list, mif_base, auto_renew)
    print('cl', chart_list, [x[2] for x in chart_list if x])
    total_in, total_out = Pipe()
    total_draw = Process(target=total_view,
                   args=([x[2] for x in chart_list if x],
                         #'/home/rolcam/scan/total_view.png',
                         '/home/rolcam/scan/total_test.png',
                         total_in,
    ))
    total_mess = total_out
    total_draw.daemon = True
    total_draw.start()    
    cli_settings = {
        "cli_start_mss": True,
        "prompt": "mip> ",
    }
    cli_commands = {
        "quit": quit,
        "info": info_cli,
        "redraw": redraw_charts,
        "intervals": intervals_cli,
        "chart": charts_cli,
        "lookback": lookback_cli,
    }
    r_cli.CommandLineInterface(cli_settings, cli_commands).start()
    remove_charts("all")
    total_draw.terminate()

def quit(parameters):
    return r_cli.CommandLineInterface.STOP, "fin"
####
quit.def_t = (
    ("exit", "q"),
    "stop program",
    (quit,),
    #(quit, roc_cli.CommandLineInterface.stop),
)

    
def unset_active_lookback_chart(line):
    active_lookback_chart = None
    print('unset active lookback chart')

def lookback_cli(line):
    global active_lookback_chart
    use = 'use: l <chart number>'
    if (not line
        or
        len(line.split()) > 1
    ):
        print(use)
        return        
    else:
        chart_number = int(line)
    settings = {
        "prompt": "mip/lookback> ",
    }
    print('chart number: {}'.format(chart_number))
    if chart_list[chart_number] is None:
        print('chart {} not active'.format(chart_number))
        return
    chart_list[chart_number][1].send([SET_CHART_IN_LOOKBACK_MODE,])
    active_lookback_chart = chart_number
    commands = {
        "up": r_cli.up,
        "back": move_x_back,
        "forward": move_x_forward,
        "zoom": zoom_x,
        #"active_intervals": list_intervals,
        #"show_gnuplot_code": show_gp_code,
        #"show_sended_code": show_sended_gp_code,
        #"hide_gnuplot_code": hide_gp_code,
    }
    return r_cli.CommandLineInterface(settings, commands).start()
lookback_cli.def_t = (
    ("l",),
    "Start lookback",
    (lookback_cli, unset_active_lookback_chart),
)

def move_x_back(parameters):
    global chart_list
    chart_list[active_lookback_chart][1].send([X_AXIS_BACK,])
move_x_back.def_t = (
    ('b',),
    "move time back",
    (move_x_back,),
)
    
def move_x_forward(parameters):
    global char_list
    chart_list[active_lookback_chart][1].send([X_AXIS_FORWARD,])
move_x_forward.def_t = (
    ('f',),
    "move time forward",
    (move_x_forward,),
)

def zoom_x(parameters):
    use = 'zoom [in|+|out|-] [left|center|right|l|c|r]'
    mss = None
    global char_list
    parameters = parameters.split() if parameters else []
    nr_of_parameters = len(parameters)
    if nr_of_parameters == 0:
        mss = ['in', 'center'] 
    elif nr_of_parameters == 1:
        parameter = parameters[0]
        if parameter in ['in', '+']:
            mss = ['in', 'center']
        elif parameter in ['out', '-']:
            mss = ['out', 'center']
        elif parameter in ['left', 'l']:
            mss = ['in', 'left']
        elif parameter in ['center', 'c']:
            mss = ['in', 'center']
        elif parameter in ['right', 'r']:
            mss = ['in', 'right']
    elif nr_of_parameters == 2:
        io = {'+': 'in', 'in': 'in', '-':'out', 'out':'out'}
        para1 = parameters[0]
        if para1 in io:
            para2 = parameters[1]
            if para2 in ['left', 'l']:
                mss = [io[para1], 'left']
            elif para2 in ['center', 'c']:
                mss = [io[para1], 'center']
            elif para2 in ['right', 'r']:
                mss = [io[para1], 'right']
    if mss:
        mss = [ZOOM_X,] + [mss]
        chart_list[active_lookback_chart][1].send(mss)
    else:
        print(use)
zoom_x.def_t = (
    ('z',),
    "zoom chart",
    (zoom_x,),
)

def info_cli(line):
    settings = {
        "prompt": "mip/info> ",
    }
    commands = {
        "up": r_cli.up,
        "active_intervals": list_intervals,
        "show_gnuplot_code": show_gp_code,
        "show_sended_code": show_sended_gp_code,
        #"hide_gnuplot_code": hide_gp_code,
    }
    return r_cli.CommandLineInterface(settings, commands).start(line)
info_cli.def_t = (
    ("?",),
    "Get info",
    (info_cli,),
)
            
def list_intervals(parameters):
    global chart_list
    for n, v in enumerate(chart_list):
        print("{} | {} ({})".format(
            n, i_s[n], '-' if v is None else '*'))
    return '\n'
list_intervals.def_t = (
    ("li",),
    "List shown intervals",
    (list_intervals,),
)
            
def show_gp_code(parameters):
    global chart_list
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: gpc {<id0> <id1> ... <idn>}|{all}'
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send([SHOW_LIVE_GP_CODE,])
show_gp_code.def_t = (
    ("gpc",),
    "show gnuplot code",
    (show_gp_code,),
)

def show_sended_gp_code(parameters):
    global chart_list
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: show_sended_gp_code {<id0> {<id1> {... {<idn>}}}}|{all}'
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send([SHOW_SENDED_GP_CODE,])
show_sended_gp_code.def_t = (
    ("s",),
    "show sended gnuplot code",
    (show_sended_gp_code,),
)
    

def redraw_charts(line):
    global chart_list
    mss = [REDRAW,]
    for chart_def in chart_list:
        if chart_def is None:
            continue
        chart_def[1].send(mss)
    return "done"
redraw_charts.def_t = (
    ('r',),
    "Redraw all charts",
    (redraw_charts,),
)

def intervals_cli(line):
    settings = {
        "prompt": "mip/intervals> ",
    }
    commands = {
        "up": r_cli.up,
        "add_interval": add_charts,
        "remove_interval": remove_charts,
        "list intervals": list_intervals,
    }
    return r_cli.CommandLineInterface(settings, commands).start(line)
intervals_cli.def_t = (
    ("i",),
    "Intervals subdir",
    (intervals_cli,),
)
            
            
def add_charts(parameters):
    global chart_list
    global mif_base
    global auto_renew
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: add {<id0> <id1> ... <idn>}|{all}'
    for chart_id in intervals:
        add_chart(chart_id, chart_list, mif_base, auto_renew)
add_charts.def_t = (
    ('add', '+'),
    'add charts for intervals',
    (add_charts,),
)
        
def add_chart(chart_id, chart_list, name_base, auto_renew):
    if chart_list[chart_id] is not None:
        return
    mess_in, mess_out = Pipe()
    name = '_'.join([name_base, i_s[chart_id]])
    proc = Process(target=mif,
                   args=(i_s[chart_id],
                         name,
                         mess_in,
                         auto_renew,
                         verbose,
    ))
    proc.daemon = True
    proc.start()
    chart_list[chart_id] = (proc, mess_out, name)
    if total_mess:
        total_mess.send(['update_files', [x[2] for x in chart_list if x]])
    
def remove_charts(parameters):
    global chart_list
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: remove {<id0> <id1> ... <idn>}|{all}'
    for chart_id in intervals:
        remove_chart(chart_id, chart_list)
remove_charts.def_t = (
    ('remove', '-'),
    'remove charts from intervals',
    (remove_charts,),
)        
    
def remove_chart(chart_id, chart_list):
    chart_proces = chart_list[chart_id]
    if chart_proces is not None:
        process, mess_pipe_out, name = chart_proces
        process.terminate()
        mess_pipe_out.close()
        chart_list[chart_id] = None
        print("removed", chart_id)
    if total_mess:
        total_mess.send(['update_files',[x[2] for x in chart_list if x]])

def charts_cli(line):
    settings = {
        "prompt": "mip/chart> ",
    }
    commands = {
        "up": r_cli.up,
        "zoom": zoom_charts_cli,
        "add_info": add_remove_info_to_charts_cli,
    }
    return r_cli.CommandLineInterface(settings, commands).start(line)
charts_cli.def_t = (
    ("c",),
    "Customize charts",
    (charts_cli,),
)
        
def zoom_charts_cli(line):
    settings = {
        "prompt": "mip/chart/zoom> ",
    }
    commands = {
        "up": r_cli.up,
        "swings": zoom_charts_to_swings,
        "days": zoom_charts_to_days,
        "hours": zoom_charts_to_hours,
        "out": zoom_charts_out,
    }
    return r_cli.CommandLineInterface(settings, commands).start(line)
zoom_charts_cli.def_t = (
    ("z",),
    "zoom charts",
    (zoom_charts_cli,),
)
    
def zoom_charts_to_swings(parameters):
    global chart_list
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: swings {<id0> <id1> ... <idn>}|{all}'
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send([ZOOM_TO_WAVES,])
zoom_charts_to_swings.def_t = (
    ("s",),
    "zoom charts to swings",
    (zoom_charts_to_swings,),
)

def zoom_charts_to_days(parameters):
    global chart_list
    print('parameters', parameters)
    try:
        days, parameters = parameters.strip().split(' ',1)
    except ValueError:
        return 'use: days <nr_of_days> {<id0> <id1> ... <idn>}|{all}'        
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: days <nr_of_days> {<id0> <id1> ... <idn>}|{all}'
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send([ZOOM_TO_LAST_N_DAYS, days])
zoom_charts_to_days.def_t = (
    ("d"),
    "zoom charts to days",
    (zoom_charts_to_days,),
)

def zoom_charts_to_hours(parameters):
    global chart_list
    print('parameters', parameters)
    try:
        hours, parameters = parameters.strip().split(' ',1)
    except ValueError:
        return 'use: hours <nr_of_hours> {<id0> <id1> ... <idn>}|{all}'        
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: hours <nr_of_hours> {<id0> <id1> ... <idn>}|{all}'
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send([ZOOM_TO_LAST_N_HOURS, hours])
zoom_charts_to_hours.def_t = (
    ("h"),
    "zoom charts hours",
    (zoom_charts_to_hours,),
)
    
        
def zoom_charts_out(parameters):
    global chart_list
    mss = [ZOOM_OUT,]
    try:
        intervals = intervals_from(parameters, chart_list)
    except ValueError:
        return 'use: out {<id0> <id1> ... <idn>}|{all}'
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send(mss)
zoom_charts_out.def_t = (
    ("-", "o"),
    "zoom charts out",
    (zoom_charts_out,),
)

def add_remove_info_to_charts_cli(line):
    settings = {
        "prompt": "mip/chart/add_info> ",
    }
    commands = {
        "up": r_cli.up,
        "upswing_start": add_upswing_start,
        "downswing_start": add_downswing_start,
        "last_barcounts": add_last_bar_counts,
        "market_status": add_market_status,
        "pauses": add_pauses,
        "moving_average": add_moving_average,
        "bollinger_bands": add_bollinger_bands,
        "support_levels": add_support_levels,
        "max_support_levels": set_max_support_levels,
        "resistance_levels": add_resistance_levels,
        "max_resistance_levels": set_max_resistance_levels,
    }
    return r_cli.CommandLineInterface(settings, commands).start(line)
add_remove_info_to_charts_cli.def_t = (
    ("i",),
    "add/remove info to/from chart",
    (add_remove_info_to_charts_cli,),
)
        
def add_upswing_start(parameters):
    command = 'upswing_start'
    request = [START_UP_WAVE, 1]
    namebase = 'uss_{}'
    add_swing_start(command, request, namebase, parameters)
add_upswing_start.def_t = (
    ('uss',),
    "Show vertical line @ upswing start",
    (add_upswing_start,),
)

def add_downswing_start(parameters):    
    command = 'downswing_start'
    request = [START_DOWN_WAVE, 1]
    namebase = 'dss_{}'
    add_swing_start(command, request, namebase, parameters)
add_downswing_start.def_t = (
    ('dss',),
    "Show vertical line @ downswing start",
    (add_downswing_start,),
)
    
def add_swing_start(command, request, namebase, parameters):   
    global chart_list   
    usage = ('{}  {{remove}} {{<id0> <id1> ... <idn>}}|{{all}} '
             '{{[to|from] {{<id0> <id1> ... <idn>}}|{{all}}').format(command)
    remove = False
    if 'remove' in parameters:
        foo, parameters = parameters.split('remove')
        remove = True
    if 'to' in parameters:
        parameters, export_list = parameters.split('to')
        try:
            export_list = intervals_from(export_list, chart_list)
        except ValueError:
            return usage
    else:
        export_list = None
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send(request)
        a_datetime = chart_list[chart_nr][1].recv()
        export_to = export_list if export_list else [chart_nr]
        name = namebase.format(chart_nr)
        for chart_nr2 in export_to:
            if remove:
                chart_list[chart_nr2][1].send(
                    [DRAW_VLINE, name, None])
            else:
                chart_list[chart_nr2][1].send(
                    [DRAW_VLINE, name, a_datetime])
                
def add_pauses(parameters): 
    global chart_list   
    usage = 'add_pauses  {{remove}} {{<id0> <id1> ... <idn>}}|{{all}}'
    remove = False
    if 'remove' in parameters:
        foo, parameters = parameters.split('remove')
        remove = True
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        if remove:
            chart_list[chart_nr][1].send(
                [REMOVE_PAUSES,])
        else:
            chart_list[chart_nr][1].send(
                [SHOW_PAUSES,])
add_pauses.def_t = (
    ('p',),
    "Show pauses",
    (add_pauses,),
)

def add_last_bar_counts(parameters):
    global chart_list
    usage = 'add_last_bar_counts {remove}'
    remove = True if parameters.endswith('remove') else False
    intervals = intervals_from('all', chart_list)    
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        if remove:
            chart_list[chart_nr][1].send(
                [REMOVE_BAR_COUNTS,])
        else:
            chart_list[chart_nr][1].send(
                [SHOW_BAR_COUNTS,])
add_last_bar_counts.def_t = (
    ('bc',),
    "Show bar counts",
    (add_last_bar_counts,),
)

def add_market_status(parameters):
    global chart_list
    usage = 'add_market_status {remove}'
    remove = True if parameters.endswith('remove') else False
    intervals = intervals_from('all', chart_list)    
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        if remove:
            chart_list[chart_nr][1].send(
                [REMOVE_MARKET_STATUS,])
        else:
            chart_list[chart_nr][1].send(
                [SHOW_MARKET_STATUS,])
add_market_status.def_t = (
    ('ms',),
    "Show market status",
    (add_market_status,),
)

def add_moving_average(parameters):
    global chart_list
    usage = 'add_moving_average {{remove}} {{<id0> <id1> ... <idn>}}|{{all}}'
    remove = False
    if 'remove' in parameters:
        foo, parameters = parameters.split('remove')
        remove = True
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        if remove:
            chart_list[chart_nr][1].send(
                [HIDE_SMA,])
        else:
            chart_list[chart_nr][1].send(
                [SHOW_SMA,])
add_moving_average.def_t = (
    ('sma',),
    "Show simple moving average",
    (add_moving_average,),
)

def add_bollinger_bands(parameters):
    global chart_list
    usage = 'add_bolinger_bands {{remove}} {{<id0> <id1> ... <idn>}}|{{all}}'
    remove = False
    if 'remove' in parameters:
        foo, parameters = parameters.split('remove')
        remove = True
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        if remove:
            chart_list[chart_nr][1].send(
                [HIDE_BOLL_BARS,])
        else:
            chart_list[chart_nr][1].send(
                [SHOW_BOLL_BARS,])
add_bollinger_bands.def_t = (
    ('bol',),
    "Show bolinger bands",
    (add_bollinger_bands,),
)

def add_support_levels(parameters):
    global chart_list
    usage = 'add_support_levels {{remove}} {{<id0> <id1> ... <idn>}}|{{all}}'
    remove = False
    if 'remove' in parameters:
        foo, parameters = parameters.split('remove')
        remove = True
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        if remove:
            chart_list[chart_nr][1].send(
                [REMOVE_SUPPORT,])
        else:
            chart_list[chart_nr][1].send(
                [SHOW_SUPPORT,])
add_support_levels.def_t = (
    ('sup',),
    "Show support levels",
    (add_support_levels,),
)

def add_resistance_levels(parameters):
    global chart_list
    usage = 'add_resistance_levels {{remove}} {{<id0> <id1> ... <idn>}}|{{all}}'
    remove = False
    if 'remove' in parameters:
        foo, parameters = parameters.split('remove')
        remove = True
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        if remove:
            chart_list[chart_nr][1].send(
                [REMOVE_RESISTANCE,])
        else:
            chart_list[chart_nr][1].send(
                [SHOW_RESISTANCE,])
add_resistance_levels.def_t = (
    ('res',),
    "Show resistance levels",
    (add_resistance_levels,),
)

def set_max_support_levels(parameters):
    global chart_list
    usage = 'set_max_support_levels {{max_nr}|+|-} {{<id0> <id1> ... <idn>}}|{{all}}'
    try:
        new_max, parameters = parameters[0], parameters[1:]
    except IndexError:
        return usage
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send([MAX_SUPPORT_LINES, new_max])
set_max_support_levels.def_t = (
    ('maxsup',),
    "Max support levels",
    (set_max_support_levels,),
)

def set_max_resistance_levels(parameters):
    global chart_list
    usage = 'set_max_resistance_levels {{max_nr}|+|-} {{<id0> <id1> ... <idn>}}|{{all}}'
    new_max, parameters = parameters[0], parameters[1:]
    try:
        intervals = intervals_from(parameters, chart_list)    
    except ValueError:
        return usage
    for chart_nr in intervals:
        if chart_list[chart_nr] is None:
            continue
        chart_list[chart_nr][1].send([MAX_RESISTANCE_LINES, new_max])
set_max_resistance_levels.def_t = (
    ('maxres',),
    "Max resistance levels",
    (set_max_resistance_levels,),
)
    
def intervals_from(parameters, chart_list):
    if parameters.strip() == 'all':
        intervals = range(len(chart_list))
    elif parameters:
        intervals = [int(x) for x in parameters.strip().split(' ')]
    else:
        raise ValueError()
    return intervals
    
def mif(name, base_data_filename, mess, auto_renew, verbose):
        
    def default_time_axis_start():
        return 0
    
    def default_time_axis_end():
        shown_bars = days['last_bar_nr'] - time_axis_start_end[0]() + 1
        surplus = int(shown_bars * default_end_space / 100 + 0.5)
        return days['last_bar_nr'] + surplus + 1
    
    def fixed_time_axis_value(number):
        def dd():
            return number
        return dd
    
    ### get info ###
    std_if = base_data_filename
    unfinished_base_data = base_data_filename + '_u'
    std_extra = base_data_filename + '_events'
    unfinished_extra = std_if + '_event_u'
    ii_base_data = base_data_filename + '_ii'
    ii_unfinished_base_data = base_data_filename + '_ii_u'
    analyse_std_if = std_if.split('_')
    bar_type = analyse_std_if[-2]
    bar_duration = int(analyse_std_if[-1])  #int for seconds
    upwave_file = "_".join([std_if, "upwave"])
    downwave_file = "_".join([std_if, "downwave"])
    pauses = [0]
    days = {'fp':0, 'last':None, 'last_bar_nr':0} # days and start of day
    chart_mode = {'live'}
    time_axis_start_end = [default_time_axis_start, default_time_axis_end]
    bar_counts = [0]
    market_status = [0]
    resistance, support = [0], [0]
    charted_resistance, charted_support = [], []
    max_nr_of_supp, max_nr_of_ress = [3], [3]
    updating_chart_elements = set()
    lock=r_cls.DirLock(base_data_filename)
    
    ### plot functions
    def show_base_bars(chart):
        chart.add_data_serie(title='base_bars', 
            filename=std_if, 
            fields=[1,3,4,5,6],
            style='financebars', 
            linestyle='basebars',
        )
        chart.add_data_serie(
            name='unfinished_base_bar', 
            filename=unfinished_base_data, 
            fields=[1,3,4,5,6],
            style='financebars', 
            linestyle='u_basebars')
        chart.add_data_serie(
            name='xtra', 
            filename=std_extra, 
            fields=[1,2,3,4],
            style='labels',
            diy='tc rgbcolor variable'
            #linestyle='basebars'
        )
        chart.add_data_serie(
            name='unf_xtra', 
            filename=unfinished_extra, 
            fields=[1,2,3,4],
            style='labels',
            diy='tc rgbcolor variable'
            #linestyle='basebars'
        )
                            
    def show_upwave(chart):
        chart.add_data_serie(title="up_wave", 
            filename=upwave_file,
            fields=[2,3],
            style='lines',
            linestyle='upwave',
        )
                            
    def show_downwave(chart):
        chart.add_data_serie(title="down_wave", 
            filename=downwave_file,
            fields=[2,3],
            style='lines', 
            linestyle='downwave',
        )
        
    def show_moving_average(chart):
        chart.add_data_serie(title='moving_avg',
            filename=std_if,
            fields=[1,10],
            style='lines',
            linestyle='moving_avg')
        
    def show_upper_band(chart):
        chart.add_data_serie(title='upper_band',
            filename=std_if,
            fields=[1,14],
            style='lines',
            linestyle='bolbolbol')
        
    def show_lower_band(chart):
        chart.add_data_serie(title='lower_band',
            filename=std_if,
            fields=[1,13],
            style='lines',
            linestyle='bolbolbol')
        
    def show_stoch(chart):
        chart.add_data_serie(title='stoch',
            filename=std_if,
            fields=[1,11],
            style='lines',
            linestyle='stoch')
        
    def show_macd(chart):
        chart.add_data_serie(name='macdd',
            filename=std_if,
            fields=[1,18],
            style='lines',
            linestyle='delta')
        chart.add_data_serie(name='macdd',
            filename=std_if,
            fields=[1,17],
            style='boxes',
            linestyle='basebars')
        chart.add_data_serie(name='macdf',
            filename=std_if,
            fields=[1,15],
            style='lines',
            linestyle='macd_f')
        chart.add_data_serie(name='macds',
            filename=std_if,
            fields=[1,16],
            style='lines',
            linestyle='macd_s')
        
    def show_support_level(chart, name, value):
        print('adding support level', name)
        chart.add_data_serie(name=name,
            function = str(value),
            linestyle='support',
        )
        
    def show_resistance_level(chart, name, value):
        print('adding resistance level', name)
        chart.add_data_serie(name=name,
            function = str(value),
            linestyle='resistance',
        )
        
    ### instructions ###
    def redraw(new_instruction):
        if verbose: print(name, "| redraw")
    
    def update_days():
        position = days['fp']
        with lock:
            with open(std_if, 'r') as if_h:
                if_h.seek(position)
                last_known_date = days['last']
                barnr = days['last_bar_nr']
                line = if_h.readline()
                while line:
                    line = line.strip().split(',')
                    barnr = int(line[0])
                    date = datetime.strptime(
                        line[1], r_dt.ISO_8601_DATETIME_FORMAT).date()
                    if last_known_date is None:
                        days['first'] = date
                        days[date] = (barnr, position)
                        days['last'] = date
                    elif date > last_known_date:
                        days[date] = (barnr, position)
                        days['last'] = date
                    last_known_date = date
                    position = if_h.tell()
                    line = if_h.readline()
                days['fp'] = if_h.tell()
                days['last_bar_nr'] = barnr
            
    def update_bar_counts():
        position = bar_counts[0]
        with lock:
            #with open(ii_base_data, 'r') as if_h:
            with open(std_if, 'r') as if_h:
                if_h.seek(position)
                for line in if_h:
                    line = line.strip().split(',')
                    #bar_nr, down, up = line[0], line[2], line[3]
                    bar_nr, down, up = line[0], line[7], line[8]
                    bar_counts.append((int(bar_nr), int(down), int(up)))
                    if len(bar_counts) > 2: bar_counts.pop(-2)
                bar_counts[0]=if_h.tell()  
            
    def update_market_status():
        position = market_status[0]
        with lock:
            with open(ii_base_data, 'r') as if_h:
                if_h.seek(position)
                for line in if_h:
                    line = line.strip().split(',')
                    bar_nr, status = line[0], line[1]
                    market_status.append((int(bar_nr), status))
                    if len(market_status) > 2: market_status.pop(-2)
                market_status[0]=if_h.tell()  
                #print(market_status)
            
    def update_support():
        position = support[0]
        with lock:
            with open(ii_base_data, 'r') as if_h:
                if_h.seek(position)
                for line in if_h:
                    line = line.strip().split(',')
                    bar_nr, support_info = line[0], line[4]
                    if support_info == 'set()':
                        supports = []
                    else:
                        supports = [
                            float(x) 
                            for x in support_info.strip('{}').split('-> ')
                        ]
                    support.append((int(bar_nr), supports))
                    if len(support) > 2: support.pop(-2)
                support[0]=if_h.tell()  
                print(support)
            
    def update_resistance():
        position = resistance[0]
        with lock:
            with open(ii_base_data, 'r') as if_h:
                if_h.seek(position)
                for line in if_h:
                    line = line.strip().split(',')
                    bar_nr, resistance_info = line[0], line[5]
                    if resistance_info == 'set()':
                        resistances = []
                    else:
                        resistances = [
                            float(x) 
                            for x in resistance_info.strip('{}').split('-> ')
                        ]
                    resistance.append((int(bar_nr), resistances))
                    if len(resistance) > 2: resistance.pop(-2)
                resistance[0]=if_h.tell()  
                print(resistance)        
    
    def active_swing_zone_start():
        downwave_start = read_from_wave_file(downwave_file, 'start_time', 1, lock)
        upwave_start = read_from_wave_file(upwave_file, 'start_time', 1, lock)
        if not (upwave_start or downwave_start):
            if verbose: 
                print(name, "| no waves found")
            return False
        waves_start = ((upwave_start and downwave_start and 
            min([upwave_start, downwave_start]))
            or
            upwave_start
            or 
            downwave_start
        )
        return waves_start
    
    def zoom_time_axis(start, end):
        args = dict()
        if end < minum_bars_shown:
            start = 0
        elif end - start < minum_bars_shown:
            start = end - minum_bars_shown
        start -= 0 if start == 0 else 0.5
        args['x_begin'] = start
        args['x_end'] = end
        i_canvas.zoom(**args)
        macd_canvas.zoom(**args)
        stoch_canvas.zoom(**args)        
    
    def zoom_to_waves(new_instruction):
        enable_live_mode(True)
        time_axis_start_end[0] = last_waves
        time_axis_start_end[1] = default_time_axis_end
        
    def last_waves():
        waves_start = active_swing_zone_start()
        if not waves_start:
            return
        if bar_type == "bars":
            if bar_duration < 300:
                lookback = 10 #timedelta(seconds=60*bar_duration)
            elif bar_duration < 800:
                lookback = 5 #timedelta(seconds=120*bar_duration)
            elif bar_duration < 3600:
                lookback = 5 #timedelta(1)
            elif bar_duration < 12000:
                lookback = 5 #timedelta(5)
            else:
                lookback = 5 #timedelta(10)
            zoom_start = waves_start - lookback
        if verbose: print(name, "| zoom to waves {} {}".format(
            waves_start, zoom_start))
        return zoom_start
    
    def zoom_to_last_n_days(new_instruction):
        enable_live_mode(True)
        lookback_days = min(int(new_instruction[1]), len(days) - 1)
        time_axis_start_end[0] = last_days(lookback_days)
        time_axis_start_end[1] = default_time_axis_end
        
    def last_days(lookback):
        def dd():
            last_day = days['last']
            start = last_day - timedelta(lookback - 1)
            while start not in days:
                start -= timedelta(1)
                if start < days[0]:
                    return 0
            t_start = days[start][0]           
            return t_start
        return dd
    
    def zoom_to_last_n_hours(new_instruction):
        enable_live_mode(True)
        lookback_hours = int(new_instruction[1])
        bars_to_show = int(3600 * lookback_hours / bar_duration + 0.5)
        time_axis_start_end[0] = last_bars(bars_to_show)
        time_axis_start_end[1] = default_time_axis_end
        
    def last_bars(bars_to_show):
        def dd():
            last_bar_nr = days['last_bar_nr']
            if last_bar_nr < bars_to_show:
                return 0
            t_start = last_bar_nr - bars_to_show
            return t_start
        return dd
    
    def zoom_out(new_instruction):
        enable_live_mode(True)
        time_axis_start_end[0] = default_time_axis_start
        time_axis_start_end[1] = default_time_axis_end
    
    def send_start_upwave(new_instruction):
        filename = upwave_file
        return send_start_wave(filename, new_instruction)
    
    def send_start_downwave(new_instruction):
        filename = downwave_file
        return send_start_wave(filename, new_instruction)
    
    def send_start_wave(filename, new_instruction):
        wave = new_instruction[-1]
        wave_start = read_from_wave_file(filename, 'start_time', wave, lock)
        mess.send(wave_start)
    
    def draw_vline(new_instruction):
        #redraw = False
        name, x = new_instruction[1:]
        if name.startswith('uss'):
            linestyle = 'upwave'
        elif name.startswith('dss'):
            linestyle = 'downwave'
        else:
            linestyle = None
        i_canvas.add_vertical_line(name, x, linestyle)
    
    def show_gp_code(new_instruction):
        i_canvas.show_code = True
    
    def show_sended_gp_code(new_instruction):
        #redraw = False
        print("i_code")
        print(i_canvas.sended_code)
        print("macd_code")
        print(macd_canvas.sended_code)
        print("stoch_code")
        print(stoch_canvas.sended_code)
    
    def show_bar_counts(new_instructions):
        updating_chart_elements.add(SHOW_BAR_COUNTS)
        update_bar_counts()
        with lock:
            #with open(ii_unfinished_base_data, 'r') as if_h:
            with open(unfinished_base_data, 'r') as if_h:
                line = if_h.readline()
                if line:
                    line = line.strip().split(',')
                    #down, up = line[2], line[3]
                    down, up = line[7], line[8]
                else:
                    foo, down, up = bar_counts[1]
        t = 'd: {} | u: {}'.format(down, up)
        i_canvas.add_label('bar_counts', t, 
                        plot.Position('graph', 0.05, 'graph', 0.95),
                        labelstyle='redlabel',
                       )
        
    def remove_bar_counts(new_intstructions):
        updating_chart_elements.discard(SHOW_BAR_COUNTS)
        i_canvas.add_label('bar_counts', None)
    
    def show_market_status(new_instructions):
        updating_chart_elements.add(SHOW_MARKET_STATUS)
        t = {
            'unknown': '???',
            'balanced fall': 'v v v v ---   >>>>>>>',
            'balanced rise': '^ ^ ^ ^ ---   >>>>>>>',
            'bull confirmed': '^ ^ ^ ^ ^ ^ ^ ^ ^',
            'bear confirmed': 'v v v v v v v v v ',
        }
        
        update_market_status()
        with lock:
            with open(ii_unfinished_base_data, 'r') as if_h:
                line = if_h.readline()
                if line:
                    line = line.strip().split(',')
                    status = line[1]
                else:
                    foo, status = market_status[1]
        i_canvas.add_label('market_status', t[status], 
                        plot.Position('graph', 0.5, 'graph', 0.1),
                        labelstyle='redlabel',
                       )
        
    def remove_market_status(new_intstructions):
        updating_chart_elements.discard(SHOW_MARKET_STATUS)
        i_canvas.add_label('market_status', None)
    
    def show_sma(new_instructions):  
        show_moving_average(i_canvas)
        
    def hide_sma(new_instructions):
        i_canvas.remove_data_serie('moving_avg')
    
    def show_bolba(new_instructions):  
        show_lower_band(i_canvas)   
        show_upper_band(i_canvas)
        
    def hide_bolba(new_instructions):
        i_canvas.remove_data_serie('upper_band')
        i_canvas.remove_data_serie('lower_band')
    
    def show_support(new_instructions):
        remove_support(None)
        updating_chart_elements.add(SHOW_SUPPORT)
        if len(support) > 1:
            foo, old_supports = support[-1]
        else:
            old_supports = None
        update_support()
        foo, supports = support[-1]
        for n, supp in enumerate(sorted(supports, reverse=True)):
            if n == max_nr_of_supp[0]:
                break
            name = 'support_{}'.format(n)
            charted_support.append(name)
            show_support_level(i_canvas, name, supp)
        print(i_canvas.plotdata)
        
    def remove_support(new_instructions):
        updating_chart_elements.discard(SHOW_SUPPORT)
        for name in charted_support:
            i_canvas.remove_data_serie(name)
        charted_support.clear()
    
    def set_max_support_lines(new_instructions):
        new_max = new_instructions[1]
        if new_max == '+':
            max_nr_of_supp[0] += 1
        elif new_max == '-':
            max_nr_of_supp[0] -= 1
        else:
            max_nr_of_supp[0] = int(new_max)
        print('max support lines', max_nr_of_supp[0])
        show_support(True)
    
    def show_resistance(new_instructions):
        remove_resistance(None)
        updating_chart_elements.add(SHOW_RESISTANCE)
        if len(resistance) > 1:
            foo, old_resistances = resistance[-1]
        else:
            old_resistances = None
        update_resistance()
        foo, resistances = resistance[-1]
        for n, supp in enumerate(sorted(resistances)):
            if n == max_nr_of_ress[0]:
                break
            name = 'resistance_{}'.format(n)
            charted_resistance.append(name)
            show_resistance_level(i_canvas, name, supp)
        print(i_canvas.plotdata)
        
    def remove_resistance(new_instructions):
        updating_chart_elements.discard(SHOW_RESISTANCE)
        for name in charted_resistance:
            i_canvas.remove_data_serie(name)
        charted_resistance.clear()
    
    def set_max_resistance_lines(new_instructions):
        new_max = new_instructions[1]
        if new_max == '+':
            max_nr_of_ress[0] += 1
        elif new_max == '-':
            max_nr_of_ress[0] -= 1
        else:
            max_nr_of_ress[0] = int(new_max)
        print('max resistance lines', max_nr_of_ress[0])
        show_resistance(True)
        
    def enable_lookback_mode(new_instructions):
        if 'lookback' not in chart_mode:
            chart_mode.discard('live')
            chart_mode.add('lookback')
            time_axis_start_end[0] = fixed_time_axis_value(
                                               time_axis_start_end[0]())
            time_axis_start_end[1] = fixed_time_axis_value(
                                               time_axis_start_end[1]())
            i_canvas.title = '!! LOOKBACK {} LOOKBACK!!'.format(name)
    
    def enable_live_mode(new_instructions):
        # Don't forget to set the right time axis start end in the calling 
        # function
        if 'live' not in chart_mode:
            chart_mode.discard('lookback')
            chart_mode.add('live')
            i_canvas.title = name
            
    def move_x_axis_back(new_instruction):
        start = time_axis_start_end[0]()
        end = min(time_axis_start_end[1](), days['last_bar_nr'])
        zoom_level = end - start
        new_start = int(max(start - (zoom_level /2), 0))
        new_end = new_start + zoom_level
        time_axis_start_end[0] = fixed_time_axis_value(new_start)
        time_axis_start_end[1] = fixed_time_axis_value(new_end)
            
    def move_x_axis_forward(new_instruction):
        start = time_axis_start_end[0]()
        end = min(time_axis_start_end[1](), days['last_bar_nr'])
        zoom_level = end - start
        new_end = int(min(end + (zoom_level /2) + 0.5, days['last_bar_nr']))
        new_start = new_end - zoom_level
        time_axis_start_end[0] = fixed_time_axis_value(new_start)
        time_axis_start_end[1] = fixed_time_axis_value(new_end)
        
    def zoom_x_axis(new_instructions):
        new_instructions = new_instructions[1]
        io, lcr = new_instructions
        print("ZZZZZZZZZZZZZZZ  zooming {} {}".format(io, lcr))
        start = time_axis_start_end[0]()
        end = min(time_axis_start_end[1](), days['last_bar_nr'])
        zoom_level = end - start
        if io == 'in':
            zoom_level /= 2
        else:
            zoom_level *= 2
        if lcr == 'left':
            end = start + zoom_level
        elif lcr == 'right':
            start = end - zoom_level
        else:
            mid = (start + end) / 2
            start = int(mid - zoom_level / 2)
            end = int(mid + zoom_level / 2 + 0.5)
        if start < 0:
            start = 0
        if end > days['last_bar_nr']:
            end = days['last_bar_nr']
        time_axis_start_end[0] = fixed_time_axis_value(start)
        time_axis_start_end[1] = fixed_time_axis_value(end)
            
        
    def update_added_elements():
        if SHOW_BAR_COUNTS in updating_chart_elements:
            show_bar_counts(None)
        if SHOW_MARKET_STATUS in updating_chart_elements:
            show_market_status(None)
        if SHOW_PAUSES in updating_chart_elements:
            show_pauses(None)
        if SHOW_SUPPORT in updating_chart_elements:
            show_support(None)
        if SHOW_RESISTANCE in updating_chart_elements:
            show_resistance(None)
    
    action_for = {
        REDRAW: redraw,
        ZOOM_TO_WAVES: zoom_to_waves,
        ZOOM_TO_LAST_N_DAYS: zoom_to_last_n_days,
        ZOOM_TO_LAST_N_HOURS: zoom_to_last_n_hours,
        ZOOM_OUT: zoom_out,
        START_UP_WAVE: send_start_upwave,
        START_DOWN_WAVE: send_start_downwave,
        DRAW_VLINE: draw_vline,
        SHOW_LIVE_GP_CODE: show_gp_code,
        SHOW_SENDED_GP_CODE: show_sended_gp_code,
        SHOW_BAR_COUNTS: show_bar_counts,
        REMOVE_BAR_COUNTS: remove_bar_counts,
        SHOW_MARKET_STATUS: show_market_status,
        REMOVE_MARKET_STATUS: remove_market_status,
        SHOW_SMA: show_sma,
        HIDE_SMA: hide_sma,
        SHOW_SUPPORT: show_support,
        REMOVE_SUPPORT: remove_support,
        MAX_SUPPORT_LINES: set_max_support_lines,
        SHOW_RESISTANCE: show_resistance,
        REMOVE_RESISTANCE: remove_resistance,
        MAX_RESISTANCE_LINES: set_max_resistance_lines,
        SHOW_BOLL_BARS: show_bolba,
        HIDE_BOLL_BARS: hide_bolba,
        SET_CHART_IN_LOOKBACK_MODE: enable_lookback_mode,
        X_AXIS_BACK: move_x_axis_back,
        X_AXIS_FORWARD: move_x_axis_forward,
        ZOOM_X: zoom_x_axis,
    }
    
    #i_canvas = plot.Canvas(title=name, terminal='x11', 
                        #lock=r_cls.DirLock(base_data_filename))    
    #x_canvas = plot.Canvas(title=name, terminal='x11', 
                        #lock=r_cls.DirLock(base_data_filename))
    
    i_canvas = plot.Canvas(title=name, terminal='png', 
                        lock=r_cls.DirLock(base_data_filename),
                        filename='{}_i'.format(base_data_filename),
                        size=(640,640),
                        )       
    macd_canvas = plot.Canvas(terminal='png', 
                        lock=r_cls.DirLock(base_data_filename),
                        filename='{}_m'.format(base_data_filename),
                        size=(640,150),)
    stoch_canvas = plot.Canvas(terminal='png', 
                        lock=r_cls.DirLock(base_data_filename),
                        filename='{}_x'.format(base_data_filename),
                        size=(640,150),)
    #x(time) axis management
    update_days()
    # I_CANVAS
    i_canvas.show_code = verbose
    i_canvas.linestyle('basebars', plot.LineColor('by_name', 'black'))
    i_canvas.linestyle('u_basebars', plot.LineColor('by_name', 'gray60'))
    i_canvas.linestyle('upwave', plot.LineColor('by_name', 'green'))
    i_canvas.linestyle('downwave', plot.LineColor('by_name', 'red'))
    i_canvas.linestyle('moving_avg', plot.LineColor('by_name', "blue"))
    i_canvas.labelstyle('downpause', plot.TextColor('by_name', "red"))
    i_canvas.labelstyle('uppause', plot.TextColor('by_name', "green"))
    i_canvas.labelstyle('redlabel', plot.TextColor('by_name', 'red'))
    i_canvas.linestyle('support', plot.LineColor('by_name', 'dark-green'))
    i_canvas.linestyle('resistance', plot.LineColor('by_name', 'dark-red'))
    i_canvas.linestyle('bolbolbol', plot.LineColor('by_name', 'gray60'))
    i_canvas.settings.datafile_seperator(',')
    #i_canvas.settings.timeseries_on_axis('x')
    i_canvas.settings.margin('left', 8)
    i_canvas.settings.mouse(False)
    i_canvas.settings.tics('x', label=False)
    i_canvas.settings.margin('bottom', 0)
    i_canvas.settings.grid()
    show_base_bars(i_canvas)
    show_upwave(i_canvas)
    show_downwave(i_canvas)
    i_canvas.draw()
    # MACD_CANVAS
    macd_canvas.linestyle('macd_f', plot.LineColor('by_name', 'blue'))
    macd_canvas.linestyle('macd_s', plot.LineColor('by_name', 'red'))
    macd_canvas.linestyle('basebars', plot.LineColor('by_name', 'black'))
    macd_canvas.linestyle('delta', plot.LineColor('by_name', 'green'))
    macd_canvas.show_code = True
    macd_canvas.settings.datafile_seperator(',')
    #macd_canvas.settings.timeseries_on_axis('x')
    macd_canvas.settings.margin('left', 8)
    macd_canvas.settings.mouse(False)
    macd_canvas.settings.tics('x', label=False)
    macd_canvas.settings.margin('top', 0)
    macd_canvas.settings.margin('bottom', 0)
    macd_canvas.settings.boxwidth(1)
    macd_canvas.settings.zeroaxis('x')
    macd_canvas.settings.grid()
    show_macd(macd_canvas)
    macd_canvas.draw()
    # STOCH_CANVAS
    stoch_canvas.linestyle('stoch', plot.LineColor('by_name', 'black'))
    stoch_canvas.show_code = True
    stoch_canvas.settings.datafile_seperator(',')
    #stoch_canvas.settings.timeseries_on_axis('x')
    stoch_canvas.settings.margin('left', 8)
    stoch_canvas.settings.mouse(False)
    stoch_canvas.settings.margin('top', 0)
    stoch_canvas.settings.tics('y', hide_value=0)
    stoch_canvas.settings.tics('y', hide_value=100)
    stoch_canvas.settings.grid()
    show_stoch(stoch_canvas)
    stoch_canvas.draw()
    zoom_time_axis(time_axis_start_end[0](), time_axis_start_end[1]())
    while 1:
        replot = True
        if mess.poll(auto_renew):
            new_instruction = mess.recv()
            action_for[new_instruction[0]](new_instruction)
        update_days()
        print(bar_duration, ':', days)
        update_added_elements()
        zoom_time_axis(time_axis_start_end[0](), time_axis_start_end[1]())
        i_canvas.draw()
        macd_canvas.draw()
        stoch_canvas.draw()
    mess.close()
    i_canvas.close()
    
def total_view(interval_names, name, mess):
    
    result_name = name
    last_update = 0
    i_file_names = x_file_names = m_file_names = None
    
    def create_file_names():
        i_names, x_names, m_names = [], [], []
        for name in interval_names:
            i_names.append('{}_i.png'.format(name))
            x_names.append('{}_x.png'.format(name))
            m_names.append('{}_m.png'.format(name))
        return i_names, x_names, m_names
            
    def find_newer_date():
        t = 0
        for base in (i_file_names, x_file_names, m_file_names):
            for name in base:
                t = max(t, os.stat(name).st_mtime)
        return t if t > last_update else None
    
    def create_total_view():
        #print('in total view')
        #for base in (i_file_names, x_file_names):
            #for name in base:
                #print(name)
        popen_args = ['montage']
        popen_args.extend(i_file_names)
        popen_args.extend(m_file_names)
        popen_args.extend(x_file_names)
        popen_args.extend(['-mode', 'Concatenate', '-tile', 'x3'])
        popen_args.append(result_name)
        print(popen_args)
        Popen(popen_args)
        
    i_file_names, x_file_names, m_file_names = create_file_names()
    print(i_file_names, x_file_names, m_file_names)
    while 1:
        if mess.poll(1):
            new_instruction = mess.recv()
            if new_instruction[0] == 'update_files':
                interval_names = new_instruction[1]
                i_file_names, x_file_names, m_file_names = create_file_names()
        new_updates = find_newer_date()
        if new_updates:
            print(new_updates)
            last_update = new_updates
            create_total_view()
    
def read_from_wave_file(filename, info, wave_nr, lock):
    if info == 'start_time':
        field = 1
        line = wave_nr
    else:
        raise ValueError("unknown info type: {}".format(info))
    with lock:
        with open(filename, 'r') as if_h:
            lines = if_h.readlines(line)
    try:
        line = lines[line-1]
    except KeyError:
        return None
    info = line.split(',')[field] if line else None
    info = None if info == "None" else int(info)
    #info = None if info == "None" else datetime.strptime(
                                           #info, r_dt.ISO_8601_DATETIME_FORMAT)
    return info
        
    

if __name__ == '__main__':
    main()