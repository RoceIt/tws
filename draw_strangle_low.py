#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)

import os.path
from time import sleep

import mypy
import gnuplot

std_of = 'upc_out.csv'
std_of = mypy.get_string('filename ({}): '.format(std_of), default=std_of)

data_file = os.path.join(mypy.TMP_LOCATION, std_of)

chart = gnuplot.chart('upc_out')
chart.settings.add_pre_setting('datafile','separator','","')
chart.settings.add_pre_setting('timefmt','"%Y-%m-%d %H:%M:%S"')
chart.settings.add_pre_setting('xdata','time')

chart.add_plot()
chart.plotlist[0].add_data_serie('underlying', filename=data_file, 
                               fields=[1,2],
                               style='line')
chart.plotlist[0].add_data_serie('low', filename=data_file, 
                               fields=[1,11],
                               style='line')

while 1:
    chart.plot()
    sleep(10)
    