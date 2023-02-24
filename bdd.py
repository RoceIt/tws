#!/usr/bin/env python3

import gnuplot

filename='/home/rolcam/roce/Data/bigdata/AEX'


chart = gnuplot.chart('big data')
chart.settings.add_pre_setting('datafile','separator','","')
#chart.settings.datafile_seperator(',')
#chart.settings.timeseries_on_axis('x')

chart.add_plot()


chart.plotlist[0].add_data_serie('base_bars', filename=filename, 
                                 fields=[2,5,4,3],
                                 style='financebars')

chart.plot(True)

input('drukken')
