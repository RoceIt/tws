#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)

import os.path
from time import sleep

import mypy
import gnuplot

std_of = 'a_csv'
std_of = mypy.get_string('filename ({}): '.format(std_of), default=std_of)

data_file = os.path.join(mypy.TMP_LOCATION, std_of)

chart = gnuplot.chart('a_csv', automatic_redraw=10)
chart.settings.add_pre_setting('datafile','separator','","')
chart.settings.datafile_seperator(',')
chart.settings.timeseries_on_axis('x')

chart.add_plot()
chart.plotlist[0].add_data_serie('column1', filename=data_file, 
                               fields=[1,2],
                               style='line')
chart.plotlist[0].add_data_serie('column2', filename=data_file, 
                               fields=[1,3],
                               style='line')

chart.plot()
mypy.get_bool('enter tot stop', default=True)
chart.close()   