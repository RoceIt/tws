#!/usr/bin/python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)

"""
This module creates and give acces an open gnuplot process.

"""

import subprocess as sub
import tempfile
from datetime import datetime
from time import sleep
from multiprocessing import Process


import mypy
import mycsv
import roc_string as r_str
import roc_datetime as r_dt

class GNUplotError(Exception): pass


class chart():
    def __init__(self, title=None, automatic_redraw=False):
        self.title = title
        self.settings = Settings(level='chart')
        self.plotlist = []
        self.automatic_redraw = automatic_redraw
        self.gnuplot = sub.Popen('gnuplot', shell=True, stdin=sub.PIPE,
                                 stdout=sub.PIPE, stderr=sub.PIPE)
        
    def __getitem__(self, k):
        if isinstance(k, int):
            return self.plotlist[k]
        for plot in self.plotlist:
            if plot.name == k:
                return plot
        mess = 'no plot found with name {}'.format(k)
        raise KeyError(mess)

    def add_plot(self,title=None):
        #when you use more then one plot in the chart dont forget to add
        #it, only one plot is added automatically with the add_plotdata function
        self.plotlist.append(Plot(title))
        
    def add_data_serie(self, **what_and_how):
        '''runs the add_plotdata function for the choosen plot,
        if no plot is defined by name or order of definition(not yet
        implemented) and there is only one plot defined, the data is
        sended to that plot'''
        if len(self.plotlist) > 1:
            mess = 'plot undefined, use add_data_serie on specific plot'
            raise GNUplotError(mess)
        if len(self.plotlist) == 0:
            self.add_plot()
        self[0].add_data_serie(**what_and_how)

    def plot(self, show=False):
        general_info = {'label count': 1}
        code = r_str.SerialTextCreator(eof='\n')
        if self.title:
            code.add_line('set title "{}"'.format(self.title))
        self.settings.add_pre_settings_code_to(code, general_info)
        for plot_ in self.plotlist:
            code.add_line(plot_.code(general_info))
        if show:
            print(code)
        self.gnuplot.stdin.write(str(code).encode())
        self.gnuplot.stdin.flush()
        if not hasattr(self, 'p') and self.automatic_redraw:
        #if self.automatic_redraw:
            self.p = Process(target= auto_update_chart, args=(self, self.automatic_redraw))
            self.p.start()
        return str(code)

    def replot(self, show=False):
        action = "replot\n"
        if show:
            print(action, end='')
        self.gnuplot.stdin.write(action.encode())
        self.gnuplot.stdin.flush()
        
    def zoom(self, 
             x_begin='', x_end='',
             y_begin='', y_end='',
             z_begin='', z_end='',
             restore = '',
             show = False):
        chart_array = Settings(level='temp')
        if ('x' in restore):
            chart_array.range_for_axis('x', restore=True)
        if 'y' in restore:
            chart_array.range_for_axis('y', restore=True)
        if 'z' in restore:
            chart_array.range_for_axis('z', restore=True)
        if x_begin or x_end:
            chart_array.range_for_axis('x', x_begin, x_end)
        if y_begin or y_end:
            chart_array.range_for_axis('y', y_begin, y_end)
        if z_begin or z_end:
            chart_array.range_for_axis('z', z_begin, z_end)
        if show:
            print(chart_array.code())
        self.gnuplot.stdin.write(chart_array.code().encode())
        self.gnuplot.stdin.flush()
    
    @property
    def automatic_redraw(self):
        return self.__ar
    
    @automatic_redraw.setter
    def automatic_redraw(self, value):
        if isinstance(value, int):
            self.__ar = value
        else:
            nr, units = value.split(' ')
            if units in {'secs', 'sec'}:
                self.__ar = value
            else:
                mess = '{} unknown time unit for automatic redraw'.format(nr)
                raise GNUplotError(mess)
        
    def close(self):
        if hasattr(self, 'p'):
            self.p.kill()
        self.gnuplot.stdin.close()
        self.gnuplot.stdout.close()
        self.gnuplot.stderr.close()
        print('returncode: ',self.gnuplot.returncode)
        #self.gnuplot.kill()
        self.gnuplot.terminate()
        

class Plot():
    def __init__(self, name=None,title=None):
        self.name = name
        self.title = title if title else name
        self.settings = []
        self.plotdata = []
        
    def __contains__(self, title):
        for serie in self.plotdata:
            if serie.title == title:
                return True
        return False
        
    def add_data_serie(self, title=None, function=False, filename=None,
                     x_range=(None, None), y_range=(None, None),
                     fields=None, style=None, color=None):
        self.plotdata.append(plotdata(title, function, filename,
                                      x_range, y_range, fields, style,
                                      color))
    
    def remove_data_serie(self, title):
        for i, serie in enumerate(self.plotdata):
            if serie.title == title:
                self.plotdata.pop(i)
                break

    def code(self, genaral_info):
        code = r_str.SerialTextCreator()
        if self.title:
            code.append('set title "{}"'.format(self.title))
        code.add_chunk('plot')
        code.add_chunk(self.plotdata[0].code)
        for data in self.plotdata[1:]:
            code.add_text(', \\')
            code.next_line()
            code.add_chunk(data.code)
        return str(code)      
    
        
class plotdata():
    def __init__(self, title=None, function=False, filename=None,
                 x_range=(None, None), y_range=(None, None),
                 fields=None, style=None, color=None):
        self.title = title
        self.function = function
        self.filename = filename
        self.x_range = x_range
        self.y_range = y_range
        self.fields = [] if fields == None else fields
        self.style = style
        self.color = color
    
    def set_title(self, title):
        self.title = title
        return title

    def set_function(self, function):
        self.function = function
        self.unset_filename()
        return self.function

    def unset_function(self):
        self.function = None
        return None

    def set_filename(self, filename):
        self.filename = filename
        self.unset_function()
        return self.filename

    def unset_filename(self):
        self.filename = None
        
    def set_x_range(self, start, stop):
        self.x_range = (start, stop)

    def unset_x_range(self):
        self.x_range = (None, None)

    def set_y_range(self, start, stop):
        self.y_range = (start, stop)

    def unset_y_range(self):
        self.y_range = (None, None)

    def set_fields(self, fields):
        self.fields = fields

    def set_style(self, style):
        self.style = style
    
    @property
    def code(self):
        code = r_str.SerialLineCreator()
        if self.x_range[0] and self.x_range[1]:
            code.add_chunk('[{}:{}]'.format(self.x_range[0],self.x_range[1]))
            if self.y_range[0] and self.y_range[1]:
                code.add_chunk('[{}:{}]'.format(self.y_range[0],self.y_range[1]))
        if self.function:
            code.add_chunk('{}'.format(self.function))
        if self.filename:
            code.add_chunk('"{}"'.format(self.filename))
            if self.fields:
                code.add_chunk('using {}'.format(self.fields[0]))
                for field in self.fields[1:]:
                    code.add_text(':{}'.format(field))
        if self.title:
            code.add_chunk('title "{}"'.format(self.title))
        elif self.title == False:
            code.add_chunk('notitle')
        if self.style:
            code.add_chunk(' with {}'.format(self.style))
        if self.color:
            code.add_chunk('lc')
        if self.color:
            code. add_chunk('rgb "{}"'.format(self.color))
        return str(code)
     
                
class Settings():
    
    def __init__(self, level):
        self.level = level
        self.pre_settings = []
        self.post_settings = []
        
    def code(self, general_info=None):        
        t = r_str.SerialTextCreator(eof='\n')
        self.add_pre_settings_code_to(t, general_info)
        self.add_post_settings_code_to(t, general_info)
        return str(t)
        
    def add_pre_settings_code_to(self, code, general_info):
        self._add_code(code, 0, general_info)
        
    def add_post_settings_code_to(self, code, general_info):
        self._add_code(code, 1, general_info)
        
    def _add_code(self, code, pre_post, general_info):
        settings = self.pre_settings if pre_post == 0 else self.post_settings
        for setting in settings:
            code.add_chunk('set {}'.format(setting[0]))
            for parameter in setting[1]:
                if isinstance(parameter, str) and parameter.startswith('gi_'):
                    gi = parameter.lstrip('gi_')
                    parameter = general_info[gi]
                    general_info[gi] += 1
                code.add_chunk('{}'.format(parameter))
            code.next_line()
            
    def add_pre_setting(self, name, *parameters):
        self.pre_settings.append((name, parameters))

    def add_post_setting(self, name, *parameters):
        self.post_settings.append((name, parameters))

    def datafile_seperator(self, separator):
        separator = '"{}"'.format(separator)
        self.add_pre_setting('datafile', 'separator', separator)
        
    def time_format(self, time_format):
        self.add_pre_setting('timefmt', '"{}"'.format(time_format))
        
    def timeseries_on_axis(self, axis, 
                           time_format=r_dt.ISO_8601_DATETIME_FORMAT):
        axis_command = {'x': 'xdata', 'y': 'ydata', 'z': 'zdata',
                        'x2': 'x2data', 'y2': 'y2data', 'cb': 'cbdata'}
        self.time_format(time_format)
        self.add_pre_setting(axis_command[axis], 'time')
                
    def range_for_axis(self, axis, start='', end='', 
                       reverse=False, writeback=False,
                       restore=False):
        axis_command = {'x': 'xrange', 'y': 'yrange', 'z': 'zrange'}
        if restore:
            self.add_pre_setting(axis_command[axis], 'restore')
            return
        start = '*' if start == 'auto' else start
        end = '*' if end == 'auto' else end
        if isinstance(start, datetime):
            start = '"{}"'.format(start.strftime(r_dt.ISO_8601_DATETIME_FORMAT))
        if isinstance(end, datetime):
            end = '"{}"'.format(start.strftime(r_dt.ISO_8601_DATETIME_FORMAT))
        range_setting = ['[{}:{}]'.format(start, end),]
        if reverse:
            range_setting.append('reverse')
        if writeback:
            range_setting.append('writeback')
        self.add_pre_setting(axis_command[axis], *range_setting)
        
        
    def label(self, name, text, position=None, allign=None,
              rotate=None, font=None, enhanced=False,
              front=False, color=None, point=False, offset=None):
        parameters = ['gi_label count', '"{}"'.format(text)]
        if position:
            parameters.append('at')
            parameters.append(position.as_set_parameter)
        if allign:
            parameters.append(allign)
        if rotate == True:
            parameters.append('rotate')
        elif isinstance(rotate, int):
            parameters.append('rotate by {}'.format(rotate))
        if font:
            parameters.append(font)
        if enhanced:
            parameters.append('enhanced')
        if front:
            parameters.append('front')
        if color:
            parameters.append('tc ls {}'.format(str(color)))
        if point:
            parameters.append('point ls {}'.format(str(color)))
        if offset:
            parameters.append('offset')
            parameters.append(offset.as_set_parameter)
        self.add_pre_setting('label', *parameters)
        
    def remove_labels(self):
        self.pre_settings = [x for x in self.pre_settings
                             if not x[0] == "label"]
            
            
            
class Position():
    
    def __init__(self, *parameters):
        self.z = self.type_x = self.type_y = self.type_z = None
        nr_of_parameters = len(parameters)
        if nr_of_parameters == 2:
            self.x, self.y = parameters
        elif nr_of_parameters == 3:
            self.x, self.y, self.z = parameters
            if isinstance(self.x):
                self.x = '"{}"'.format(self.x)
        elif nr_of_parameters == 4:
            self.type_x, self.x, self.type_y, self.y = parameters
        elif nr_of_parameters == 6:
            (self.type_x, self.x, self.type_y, self.y, 
                                self.type_z, self.z) = parameters
        else:
            raise Exception('wrong parameters')
    
    @property    
    def as_set_parameter(self):
        def wrapped(value):
            if isinstance(value, str) and ' ' in value:
                value = '"{}"'.format(value)
            return value
        if self.type_z:
            output = '{}{},{}{},{}{}'
        elif self.z:
            output = '{1},{3},{5}'
        elif self.type_y:
            output = '{}{},{}{}'
        else:
            output = '{1},{3}'
        p = output.format(self.type_x, wrapped(self.x),
                          self.type_y, wrapped(self.y),
                          self.type_z, wrapped(self.z))
        return p
    
def auto_update_chart(chart, interval_secs):
    while True:
        sleep(interval_secs)
        chart.plot()



##############################

def chart_list(data_list, name='CHART LIST', x_axis=None, chart_data=None):
    '''charts the data from the data list
    
    the list can be 1 or 2 dimentional
    chart_data is a list of tupples (column, name)
    chart_data can be ommited, if so the first column of the data_list will be 
    shown
    '''
    
    temp_file = mycsv.table2csv(data_list)
    my_chart = chart(name)
    my_chart.settings.add_pre_setting('datafile','separator','","')
    if not x_axis is None and isinstance(data_list[x_axis], datetime):
        my_chart.settings.add_pre_setting('timefmt','"%Y-%m-%d %H:%M:%S"')
        my_chart.settings.add_pre_setting('xdata','time')
        
    my_chart.settings.add_pre_setting('xrange', '[*:*] reverse')
        
    my_chart.add_plot()
    x_field = [x_axis+1] if not x_axis==None else [] 
    if not chart_data:
        my_chart.plotlist[0].add_data_serie(filename=temp_file, 
                                          fields=x_field+[1],
                                          style='line')
    else:

        for column, col_name in chart_data:
            print(x_field+[column+1])
            my_chart.plotlist[0].add_data_serie(col_name, filename=temp_file, 
                                              fields=x_field+[column+1],
                                              style='line')
    my_chart.plot()

    mypy.rmTempFile(temp_file)
    