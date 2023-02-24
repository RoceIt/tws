#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)

import os.path
from time import sleep

import mypy
import gnuplot

bars_to_print = 1
reductions_to_print = [0] #[0,7]

std_of = 'triaddo'
std_of = mypy.get_string('filename ({}): '.format(std_of), default=std_of)

data_file = os.path.join(mypy.TMP_LOCATION, std_of)
xtra_data_file1 = os.path.join(mypy.TMP_LOCATION,'out____.plot_data' )

chart = gnuplot.chart('triaddo')#, automatic_redraw=14)
chart.settings.add_pre_setting('datafile','separator','","')
chart.settings.datafile_seperator(',')
chart.settings.timeseries_on_axis('x')

chart.add_plot()
number_of_triads = mypy.get_int('Number of triads: ')
serie = bars_to_print
chart.plotlist[0].add_data_serie('base_bars', filename=data_file, 
                               fields=[1+(serie*6),2+(serie*6),5+(serie*6),4+(serie*6),3+(serie*6)],
                               style='financebars')
for triad in reductions_to_print: #range(number_of_triads):
    data_location = 6 + 6 * number_of_triads + triad +1
    chart.plotlist[0].add_data_serie(str(triad), filename=data_file, 
                                     fields=[1,data_location],
                                     style='line')
    
chart.plotlist[0].add_data_serie('upswing', filename=xtra_data_file1,
                                 fields=[1,2], style='points',
                                 color='green')    
chart.plotlist[0].add_data_serie('downswing', filename=xtra_data_file1,
                                 fields=[1,3], style='points',
                                 color='red')    
chart.plotlist[0].add_data_serie('upswing', filename=xtra_data_file1,
                                 fields=[1,4], style='points',
                                 color='green')    
chart.plotlist[0].add_data_serie('downswing', filename=xtra_data_file1,
                                 fields=[1,5], style='points',
                                 color='red')
#chart.plotlist[0].add_data_serie('???', filename=xtra_data_file1,
                                 #fields=[1,6], style='points',
                                 #color='gray')
#chart.plotlist[0].add_data_serie('??? start', filename=xtra_data_file1,
                                 #fields=[1,7], style='points',
                                 #color='black')
chart.plotlist[0].add_data_serie('??? start', filename=xtra_data_file1,
                                 fields=[1,8], style='points',
                                 color='blue')

chart.plot()
mypy.get_bool('enter tot stop', default=True)
chart.close()   