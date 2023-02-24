#!/usr/bin/env python3
#
#  Copyright (c) 2012, Rolf Camps (rolf.camps@scarlet.be)

import itertools
import mypy

class Plot():
    
    AUTO = 'auto'
    STANDARD = 'standard'
    NUMBER = 'f'
    PERCENT = '%'
    def __init__(self, **settings):
        self.settings={'type': self.STANDARD,
                       'fill': False,
                       'hight': self.AUTO, 'width': self.AUTO,
                       'min_hight': 0, 'min_width': 0,
                       'max_hight': 0,  'max_width': 0,
                       'x_step': 0, 'y_step': 0,
                       'min_x_step': 1, 'min_y_step': 1,
                       'x_column_width': 0, 'x_label_frac': 0,
                       'y_label_width': 8, 'y_label_frac': 2, 
                       'y_label_type': self.NUMBER,
                       'draw_0': True,}
        for setting, value in settings.items():
            self.settings[setting] = value
    
    def plot(self, data):
        type_ = self.settings['type']
        data_type = type(data)
        if type_ is self.STANDARD:
            if data_type is list:
                plot = self.standard_plot_from_list(data)
            else:
                mess = ('{} not implemented data type for standard plot'.
                        format(data_type))
                raise Exception(mess)
        else:
            mess = 'unknown plot type: {}'.format(type_)
        return plot
    
    def standard_plot_from_list(self, data):
        y_label_width = self.settings['y_label_width']
        y_label_frac = self.settings['y_label_frac']
        y_label_type = self.settings['y_label_type']
        fill = self.settings['fill']
        draw_0 = self.settings['draw_0']
        x_column_width = self.x_settings(data)
        y_step, y_top, y_lines = self.y_settings(data)
        y_correction = 0.5 * y_step
        plotted = [] # helper to see wich items are already plotted
        plot = mypy.SerialTextCreator(separator='')
        line = itertools.count(y_lines, -1)
        #plot.add_line(str(data))
        while next(line):
            plot.add_chunk('{:{label_width}.{label_frac}{label_type}} |'.format(
                 y_top, label_width=y_label_width, label_frac=y_label_frac,
                 label_type=y_label_type))
            for i, ell in enumerate(data):
                if ell >= 0 and y_top > -y_correction:
                    plot_value = True if ell >= y_top else False
                    if not fill and i in plotted:
                        plot_value = False
                    elif plot_value:
                        plotted.append(i)
                elif ell < 0 and y_top < y_correction:
                    plot_value = True if ell <= y_top else False
                    if not fill and ell <= y_top - y_step:
                        plot_value = False                    
                else:
                    plot_value = False
                plot_symbol = '*' if plot_value else ''
                column = ('{:^{column_width}}'.format(
                              plot_symbol, column_width= x_column_width))
                if draw_0 and y_top <= y_correction and y_top >= -y_correction:
                    background_symbol = '-'
                else:
                    background_symbol = ' '
                plot.add_chunk(column.replace(' ', background_symbol).format(
                     plot_symbol, column_width= x_column_width))
            y_top -= y_step
            plot.next_line()
        return plot.text
    
    def x_settings(self, data):        
        width = self.settings['max_width']
        width = width if width else 80
        column_width = self.settings['x_column_width']
        column_width = column_width if column_width else 5
        nr_of_columns = len(data)
        while nr_of_columns * column_width + 2 > width:
            column_width -= 1
            if column_width == 1:
                break
        return column_width
    
    def y_settings(self, data):
        hight = self.settings['max_hight']
        hight = hight if hight else 10
        min_y_step = self.settings['min_y_step']
        ##maximum_y_value = max(data)
        ##minimum_y_value = min(data)
        maximum_y_value = mypy.d_round(max(data) + 0.51 * min_y_step, min_y_step)
        minimum_y_value = mypy.d_round(min(data) - 0.51 * min_y_step, min_y_step)
        #y_span = maximum_y_value - minimum_y_value + 2 * min_y_step
        y_span = maximum_y_value - minimum_y_value
        #y_step = max((mypy.d_round(y_span / hight + 0.5 * min_y_step, min_y_step),
                      #min_y_step))
        y_step = max((mypy.d_round(y_span / (hight -1), min_y_step),
                      min_y_step))
        #y_top = mypy.d_round(maximum_y_value + 0.51 * min_y_step, y_step)
        y_top = mypy.d_round(maximum_y_value, y_step)
        y_lines = y_span // y_step + 2
        y_lines = 3 if y_lines < 3 else y_lines
        while y_lines > hight:
            y_step += min_y_step
            y_top = mypy.d_round(maximum_y_value, y_step)            
            y_lines = y_span // y_step + 2
            y_lines = 3 if y_lines < 3 else y_lines
        #print('y: ',y_span, y_step, y_top, y_lines)
        if y_top - (y_lines - 1) * y_step > minimum_y_value:
            y_step += min_y_step
            y_top = mypy.d_round(maximum_y_value, y_step) 
        #print('y: ',y_span, y_step, y_top, y_lines)
        return y_step, y_top, y_lines
        
    
        