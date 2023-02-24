#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from datetime import date, datetime

import roc_input as r_in
import marketdata

def main():
    filename = r_in.get_string(
            'filename: ',
            default=('/home/rolcam/roce/Data/bigdata/'
                     'FDAX TICK Full Historical YYYY-MM-DD.txt'),
    )
    base_file_name = '/home/rolcam/roce/Data/dax_fut_{}.txt'
    #curr_date = None
    #with open(filename, 'r') as if_h:
        #foo = if_h.readline() # skip header line
        #print(foo)
        #for x in range(500000):
            #date_, time_, value, size  = if_h.readline().rstrip().split(',')
            #curr_datetime = datetime.strptime(
                    #' '.join([date_, time_]),
                    #'%Y-%m-%d %H:%M:%S'
            #)
            #tick = marketdata.DataTick(curr_datetime, value, size)
            #if not curr_datetime.date() == curr_date:
                #print(tick)
                #curr_date = curr_datetime.date()
    feeder = marketdata.data_bar_feeder_from_file(filename)
    fl = []
    curr_year = None
    for b in feeder:
        if (curr_year                                                   and
            (len(fl) > 100000 
             or 
             not curr_year == b.time.year)
            ):
                print(b.time)
                with open(base_file_name.format(curr_year), 'a') as of_h:
                    for x in fl:
                        print(*x, file=of_h)
                fl = []
        #r_in.get_bool('cont {}: ', default=True)
        fl.append(b)
        curr_year = b.time.year
            
if __name__ == '__main__':
    main()