#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#
import os
import sys
from time import sleep
from collections import namedtuple

import mypy
from barData import ochlBar
from position_manager import Action, Position
import triads

BarData = namedtuple("BarData", 'ochlbar seconds_to_go endtime')
Perm = namedtuple("Perm", 'swing_direction swing_count extreme_time '
                          'extreme_value end_time end_value')

def enerve(level):
    for i in range(level):
        print('\a', end='')
        sys.stdout.flush()
        sleep(0.15)

def main():
    base_filename = mypy.get_string('init filename (out): ', default='out')
    mode = mypy.get_int("mode: ", default=0)
    filenames = load_filenames(base_filename)
    bar_data_file = os.path.join(mypy.TMP_LOCATION, 
            '.'.join([filenames["full bar history csv"], 'unfinished']))
    triad_data_file = os.path.join(mypy.TMP_LOCATION, 
            '.'.join([filenames["full triad history csv"], 'unfinished.p']))
    perm_data_file = os.path.join(mypy.TMP_LOCATION, 
            '.'.join([filenames["full perm history csv"], 'unfinished']))
    action_data_file = os.path.join(mypy.TMP_LOCATION, 
            '.'.join([filenames["full action log csv"], 'unfinished']))
    stoploss_info_file = os.path.join(mypy.TMP_LOCATION, 
            filenames["stoploss info"])
    bar_data_time = 0
    old_position = False
    while 1:
        seconds_without_info = 0
        last_bar_data_time = bar_data_time
        while bar_data_time == last_bar_data_time:
            seconds_without_info +=1
            if seconds_without_info > 6:
                enerve(1)
            sleep(1)
            bar_data_time = os.path.getmtime(bar_data_file)
        sleep(0.2)
        bar_data = read_bar_data(bar_data_file)
        triad_data = read_triad_data(triad_data_file)
        perm_data = read_perm_data(perm_data_file)
        action_data = read_action_data(action_data_file)
        position, pos_if_stopped = read_position_data(stoploss_info_file)
        #print("current bar")
        #print("===========")
        #print(bar_data)
        #print(triad_data if triad_data else "No triad devell.")
        #print(perm_data if perm_data else "No perms devell.")
        #print(action_data if action_data else "No actions planned")
        #print("current position")
        #print("----------------")
        #print(position if position else "No positions")
        #print("after stop")
        #print(pos_if_stopped if pos_if_stopped else "No position")
        #print("\n----------------------------------\n")
        if mode == 0:
            print('=====================================================\n')
            print("Bar ends @ {}, {} seconds to go".format(
                bar_data.endtime, bar_data.seconds_to_go))
            print(action_data if action_data else "No actions planned")
            if action_data:
                enerve(2)
            print("")
            print("current position")
            print("----------------")
            print(position if position else "No positions")
            if ((position and not old_position)
                or
                (not position and old_position)):
                enerve(4)
                old_position = not(old_position)            
            print("after stop")
            print(pos_if_stopped if pos_if_stopped else "No position")
            print('\n\n\n')
            
def load_filenames(base_filename, location=mypy.TMP_LOCATION):
    inputfile = os.path.join(mypy.TMP_LOCATION, 
                             '.'.join([base_filename, "settings"]))
    (foo, filenames, foo, foo) = mypy.import_pickle(inputfile,
                                                         "swing settings")
    return filenames

def read_bar_data(path):
    with open(path, 'r') as ifh:
        data = ifh.readlines()
    bar = textline_2_ochlBar(data[0])
    seconds_to_go, endtime = data[1].split(',')
    return BarData(bar, seconds_to_go, endtime)

def read_triad_data(path):
    if os.path.getsize(path) == 0:
        return None
    triad = mypy.import_pickle(path, "triad")
    return triad

def read_perm_data(path):
    if os.path.getsize(path) == 0:
        return None
    with open(path, 'r') as ifh:
        data = ifh.readlines()
    perm_data = []
    for line in data:
        t, m, t1, v1, t2, v2 = line.split(',')
        t1 = mypy.py_date_time(t1, mypy.iso8601TimeStr)
        t2 = mypy.py_date_time(t2, mypy.iso8601TimeStr)
        perm_data.append(Perm(t, m, t1, v1, t2, v2))
    return perm_data

def read_action_data(path):
    if os.path.getsize(path) == 0:
        return None
    with open(path, 'r') as ifh:
        data = ifh.readlines()
    action_data = []
    for line in data:
        print("line to split: ", line)
        i, u, d, s, t, v, *r = line.split(',')
        t = mypy.py_date_time(t, mypy.iso8601TimeStr)
        action_data.append(Action(i, u, d, s, t, v, r))
    return action_data

def read_position_data(path):
    with open(path, 'r') as ifh:
        data = ifh.readlines()
    data.pop(0)
    if not data :
        return None, None
    positions = []
    while not data[0].startswith("position "):
        positions.append(data.pop(0))
    data.pop(0)
    after_stop = []
    if data[0] == "no positions":
        return positions, None
    while data:
        after_stop.append(data.pop(0))
    return positions, after_stop    

def textline_2_ochlBar(textline):
    t, o, c, h, l = textline.split(',')    
    t = mypy.py_date_time(t, mypy.iso8601TimeStr)
    return ochlBar(t, o, c, h, l)
    
        
if __name__ == '__main__':
    main()