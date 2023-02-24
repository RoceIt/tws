#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)

import os.path
from time import sleep

import mypy
import gnuplot
from triads import Swing

def main():    
    def show_base_bars(plot, color):
        plot.add_data_serie('base_bars', filename=bar_data, 
                            #fields=[1,2,5,4,3],
                            fields=[1,2,4,3,5],
                            style='financebars', color=color)
        plot.add_data_serie('base_bars', filename=curr_bar_data, 
                            #fields=[1,2,5,4,3],
                            fields=[1,2,4,3,5],
                            style='financebars', color=color)
    def show_base_triad_swings(plot, color):
        plot.add_data_serie('base triad swings', filename=triad_data,
                            fields=[2,11],
                            style='line', color=color)
    def show_ascending_triads(plot, color):
        plot.add_data_serie('ascending_triads', filename=triad_data,
                            #fields=[2,3,6,5,4],
                            fields=[2,3,5,4,6],
                            style='financebars', color=color)
    def show_descending_triads(plot, color):
        plot.add_data_serie('descending_triads', filename=triad_data,
                            #fields=[2,7,10,9,8],
                            fields=[2,7,9,8,10],
                            style='financebars', color=color)
    
    def handle_swings_request(plot, foo):
        #level = mypy.get_int('level (0)): ', default=0)
        level = ''
        us_title = '_'.join(['upswing', str(level)])
        ds_title = '_'.join(['downswing', str(level)])
        uss_title = '_'.join(['up start', str(level)])
        dss_title = '_'.join(['down start', str(level)])
        if us_title in plot:
            plot.remove_data_serie(us_title)
            plot.remove_data_serie(uss_title)
            plot.remove_data_serie(ds_title)
            plot.remove_data_serie(dss_title)
            return
        #filename = data_file + level * '_' + '.plot_data'
        filename = data_file + 't'
        plot.add_data_serie(us_title, filename=filename,
                            fields=[1,2], style='points',
                            color=show_color['swings_up_mark'])    
        plot.add_data_serie(ds_title, filename=filename,
                            fields=[1,3], style='points',
                            color=show_color['swings_down_mark'])    
        plot.add_data_serie(uss_title, filename=filename,
                            fields=[1,4], style='points',
                            color=show_color['swings_up_mark'])    
        plot.add_data_serie(dss_title, filename=filename,
                            fields=[1,5], style='points',
                            color=show_color['swings_down_mark'])
        
    def handle_alerts(plot, foo):
        if 'warning level' in plot:
            plot.remove_data_serie('warning level')
            plot.remove_data_serie('warning ann')
            plot.remove_data_serie('entry level')
            return
        filename = data_file + '.pl_al'
        plot.add_data_serie('warning level', filename=filename,
                            fields=[2, 4], style='points',
                            color=show_color['alerts'])    
        plot.add_data_serie('warning ann', filename=filename,
                            fields=[3, 4], style='points',
                            color=show_color['alerts'])     
        plot.add_data_serie('entry level', filename=filename,
                            fields=[2, 5], style='points',
                            color=show_color['entry'])  
        
    def show_entry_stop(plot, color):
        filename = data_file + '.pl_al'
        plot.add_data_serie('entry stop', filename=filename,
                        fields=[2,6],
                        style='points', color=color)
        
    def show_current_bar(plot, color):
        filename = data_file + '.b_t_unfinshed'
        plot.add_data_serie('current bar', filename=filename,
                            fields = [2,3,6,5,4],
                            style='financebars', color=color)  
        plot.add_data_serie('curr ascending_triads', filename=filename,
                            fields=[2,7,10,9,8],
                            style='financebars', color=color)
        plot.add_data_serie('curr descending_triads', filename=filename,
                            fields=[2,11,14,13,12],
                            style='financebars', color=color)
        #experiment for labels
        #with open(filename, 'r') as ifh:
            #for line in ifh:
                #chunks = line.split(',')
                #for n in chunks[2:]:
                    #if n:
                        #n = float(n)
                        #break
                #else:
                    #n = 0
                #t = chunks[1]
                #plot.
                #print(t, n)
                        
        
    show_codex = {0: 0,
                  1: 'base bars',
                  2: 'base triad swings',
                  3: 'ascending_triads',
                  4: 'descending_triads',
                  5: 'swings_for_level',
                  6: 'alerts',
                  7: 'entry stop',
                  10:'current bar'}
    
    show_instruction = {'base bars': show_base_bars,
                        'base triad swings': show_base_triad_swings,
                        'ascending_triads': show_ascending_triads,
                        'descending_triads': show_descending_triads,
                        'swings_for_level': handle_swings_request,
                        'alerts': handle_alerts,
                        'entry stop': show_entry_stop,
                        'current bar': show_current_bar}
    
    show_color = {'base bars': 'black',
                  'base triad swings': 'greenyellow',
                  'ascending_triads': 'green',
                  'descending_triads': 'red',
                  'swings_for_level': None,
                  'swings_up_mark': 'green',
                  'swings_down_mark':  'red',
                  'alerts': 'blue',
                  'entry': 'pink',
                  'entry stop': 'pink',
                  'current bar': 'olive'}
    
    show = [10,2,3,4,1]
    std_if = 'out'
    std_if = mypy.get_string('filename ({}): '.format(std_if), default=std_if)
    
    data_file = std_if
    bar_data = '.'.join([data_file, "t0"])
    curr_bar_data = '.'.join([bar_data, "unfinished"])
    triad_data = '.'.join([data_file, "t1"])
    #xtra_data_file1 = os.path.join(mypy.TMP_LOCATION,'out.plot_data' )
    
    #chart = gnuplot.chart(std_if , automatic_redraw=2)
    chart = gnuplot.chart(std_if )
    chart.settings.add_pre_setting('datafile','separator','","')
    chart.settings.datafile_seperator(',')
    chart.settings.timeseries_on_axis('x')
    
    #experiment for labels
    #add_swing_counts(data_file, chart)
            #c += 1
    ######################################
    chart.add_plot()
    
    while show:
        try:
            serie = show_codex[show.pop()]
        except:
            break
        if serie in {'r', 'R'}:
            pass
        elif serie in chart.plotlist[0]:
            chart.plotlist[0].remove_data_serie(serie)
        elif not serie == 0:
            show_instruction[serie](chart.plotlist[0], show_color[serie])
        if show:
            continue
        add_swing_counts(data_file, chart)
        chart.plot(True)
        show.append(mypy.get_int('add/remove: ', default=555))
    chart.close()   

def add_swing_counts(data_file, chart):
    filename = data_file + '.t2'  
    #filename = data_file + '.resc' 
    chart.settings.remove_labels()
    c = 1
    with open(filename, 'r') as ifh:
        for line in ifh:
            ud, c, t, n, *foo = line.rstrip().split(',')
            pos = gnuplot.Position(t, n)
            if ud.startswith('*'):
                ud = ud[1:]
                live = False
            else:
                live = True
            allign = 'right' if ud == Swing.DOWN else ''
            color = 1 if ud == Swing.DOWN else 2
            text = str(c)
            if not live:
                if ud == Swing.UP:
                    ofset = gnuplot.Position(1, 0)
                else:
                    ofset = gnuplot.Position(-1,0)
                    text = ' '+text
                #color = 0
            else:
                ofset = ''
            chart.settings.label(c, str(c), pos, allign, color=color, offset=ofset)


if __name__ == '__main__':
    main()