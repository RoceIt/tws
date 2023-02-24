#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)

import os.path

import mypy
import gnuplot

std_of = 'upc_out.csv'
std_of = mypy.get_string('filename ({}): '.format(std_of), default=std_of)

data_file = os.path.join(mypy.TMP_LOCATION, std_of)

chart = gnuplot.chart('upc_out', automatic_redraw=10)
chart.settings.datafile_seperator(',')
chart.settings.timeseries_on_axis('x')

chart.add_plot()
chart.add_data_serie(title='sigma', filename=data_file, 
                               fields=[1,12],
                               style='line')

chart.plot()

mypy.get_bool('enter tot stop', default=True)
chart.close()
    