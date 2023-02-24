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


class Canvas():
    def __init__(self, title=None, canvas_is_chart=False):
        self.title = title
        self.variables = VarPool()
        self.settings = Settings(level='canvas', var_pool = self.variables)
        self.charts = []
        self.canvas_is_chart = canvas_is_chart
        self.show_code = False
        self.canvas = None
        self.sended_code = r_str.SerialTextCreator()
        
    def close(self):
        if hasattr(self, 'p'):
            self.p.kill()
        self.canvas.stdin.close()
        self.canvas.stdout.close()
        self.canvas.stderr.close()
        self.print_code('returncode: ',self.canvas.returncode)
        self.canvas.terminate()
            
    def send(self, code):
        self.sended_code.add_text(str(code))
        self.canvas.stdin.write(str(code).encode())
        self.canvas.stdin.flush()
        
    def __getitem__(self, k):
        if isinstance(k, int):
            return self.charts[k]
        for chart in self.charts:
            if chart.name == k:
                return chart
        mess = 'no chart found with name {}'.format(k)
        raise KeyError(mess)
         
    def var(self, name, value):
        if interactive:
            chart_array = Settings(level='temp', var_pool = self.variables)
        else:
            chart_array = self.settings
        chart_array.variable(name, value)
        if interactive:
            code = chart_array.code()
            self.print_code(code)
            self.send(code)
        
    def linestyle(self, name, *arg_l, interactive=False):
        if interactive:
            chart_array = Settings(level='temp', var_pool = self.variables)
        else:
            chart_array = self.settings
        chart_array.linestyle(name, *arg_l)
        if interactive:
            code = chart_array.code()
            self.print_code(code)
            self.send(code)       

    def add_chart(self, name, title=None):
        if self.canvas_is_chart:
            raise GNUplotError(
                "Adding chart to canvas with canvas_is_chart True")
        self.charts.append(Chart(name, title))
        
    def add_data_serie(self, **what_and_how):
        if not self.canvas_is_chart:
            raise GNUplotError(
                "Adding data serie to canvas with canvas_is_chart False")
        if not self.charts:
            self.charts.append(Chart("canvas"))
        self[0].add_data_serie(**what_and_how)
        
    def add_vertical_line(self, id_, x_value, linestyle=None, interactive=False):
        if interactive:
            chart_array = Settings(level='temp', var_pool = self.variables)
        else:
            chart_array = self.settings
        if x_value is None:
            chart_array.remove_arrow(id_)
        else:
            chart_array.arrowstyle(id_, ArrowHead('nohead'), linestyle=linestyle)
            chart_array.arrow(
                id_,
                start_position = Position('first', x_value, 'graph', 0),
                end_position = Position('first', x_value, 'graph', 1),
                arrow_style=id_,
            )
        if interactive:
            code = chart_array.code()
            self.print_code(code)
            self.send(code)

    def draw(self):
        if self.canvas is None:
            self.canvas = sub.Popen('gnuplot', shell=True, stdin=sub.PIPE,
                                    stdout=sub.PIPE, stderr=sub.PIPE)
        general_info = {'label count': 1}
        code = r_str.SerialTextCreator(eof='\n')
        if self.title:
            code.add_line('set title "{}"'.format(self.title))
        self.settings.add_pre_settings_code_to(code, general_info)
        for chart in self.charts:
            code.add_line(chart.code(general_info))
        self.print_code(code)
        self.send(code)

    def update(self):
        code = "replot\n"
        self.print_code(code)
        self.send(code)
        
    def zoom(self, 
             x_begin='', x_end='',
             y_begin='', y_end='',
             z_begin='', z_end='',
             restore = '',
             interactive = False):
        if interactive:
            chart_array = Settings(level='temp', var_pool = self.variables)
        else:
            chart_array = self.settings
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
        if interactive:
            code = chart_array.code()
            self.print_code(code)
            self.send(code)
        
    @property
    def show_code(self):
        return self.__show_code
    
    @show_code.setter
    def show_code(self, true_or_false):
        self.__show_code = true_or_false
        for chart in self.charts:
            chart.show_code = true_or_false
            
    def print_code(self, *arg_l, **kw_d):
        if self.show_code:
            print(*arg_l, **kw_d)
        

class Chart():
    def __init__(self, name, title=None):
        self.name = name
        self.title = title
        self.show_code = False
        self.settings = []
        self.plotdata = []
        
    def __contains__(self, title):
        for serie in self.plotdata:
            if serie.title == title:
                return True
        return False
        
    def add_data_serie(self, name=None, title=None, 
                       function=False, filename=None,
                       x_range=(None, None), y_range=(None, None),
                       fields=None, style=None, linestyle=None):
        if name is None:
            name = title
        if name is None:
            raise GNUplotError("data serie must have a name")
        self.plotdata.append(DataSerie(name, title, function, filename,
                                      x_range, y_range, fields, style,
                                      linestyle))
    
    def remove_data_serie(self, name):
        for i, serie in enumerate(self.plotdata):
            if serie.name == name:
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
    
        
class DataSerie():
    def __init__(self, name, title=None, function=False, filename=None,
                 x_range=(None, None), y_range=(None, None),
                 fields=None, style=None, linestyle=None,
        ):
        self.name = name
        self.title = title
        self.function = function
        self.filename = filename
        self.x_range = x_range
        self.y_range = y_range
        self.fields = [] if fields == None else fields
        self.style = style
        self.linestyle = linestyle
    
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
        
    def set_linestyle(self, linestyle):
        self.linestyle = linestyle
    
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
            code.add_chunk('with {}'.format(self.style))
        if self.linestyle:
            code.add_chunk('ls {}'.format(self.linestyle))
        return str(code)
     
                
class Settings():
    
    def __init__(self, level, var_pool):
        self.level = level
        self.var_pool =  var_pool
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
            code.add_chunk('{}'.format(setting[0]))
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
        
    def variable(self, name, value):
        self.var_pool.add_variable(name)
        if isinstance(value,str):
            value = '"{}"'.format(value)
        self.add_pre_setting(name, '=', value)
        
    def linestyle(self, name, *arg_t):
        if isinstance(name, str):
            self.check_and_or_add_name_with_var_pool(name)
        if arg_t == 'unset':
            self.add_pre_setting('unset style line', name)
            return
        if arg_t =='default':
            args = [arg_t]
        else:
            args = []
            arg_l = list(arg_t)
            linetype = type_pop(arg_l, LineType)
            linecolor = type_pop(arg_l, LineColor)
            if arg_l:
                ua = [type(x) for x in arg_l]
                raise GNUplotError("Unknown args: {}".format(ua))
            if linetype:
                args.append('lt')
                args.append(str(linetype))
            if linecolor:
                if linetype:
                    args.append('lc')
                else:
                    args.append('lt')
                args.append(str(linecolor))
        self.add_pre_setting('set style line', name, *args)
        
    def arrowstyle(self, name, *arg_t, linestyle=None):
        if isinstance(name, str):
            self.check_and_or_add_name_with_var_pool(name)
        if arg_t == 'unset':
            self.add_pre_setting('unset style arrow', name)
            return
        if arg_t =='default':
            args = [arg_t]
        else:
            args = []
            arg_l = list(arg_t)
            head = type_pop(arg_l, ArrowHead)
            if arg_l:
                ua = [type(x) for x in arg_l]
                raise GNUplotError("Unknown args: {}".format(ua))
            if head:
                args.append(str(head))
            if linestyle:
                args.append('ls')
                args.append(linestyle)
        self.add_pre_setting('set style arrow', name, *args)
            

    def datafile_seperator(self, separator):
        separator = '"{}"'.format(separator)
        self.add_pre_setting('set datafile separator', separator)
        
    def time_format(self, time_format):
        self.add_pre_setting('set timefmt', '"{}"'.format(time_format))
        
    def timeseries_on_axis(self, axis, 
                           time_format=r_dt.ISO_8601_DATETIME_FORMAT):
        axis_command = {'x': 'xdata', 'y': 'ydata', 'z': 'zdata',
                        'x2': 'x2data', 'y2': 'y2data', 'cb': 'cbdata'}
        self.time_format(time_format)
        self.add_pre_setting(
            'set {}'.format(axis_command[axis]), 'time')
                
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
        self.add_pre_setting(
            'set {}'.format(axis_command[axis]), *range_setting)
        
        
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
        self.add_pre_setting('set label', *parameters)        
        
    def remove_labels(self):
        self.pre_settings = [x for x in self.pre_settings
                             if not x[0] == "label"]
        
    def arrow(self, name, 
              start_position=None, end_position=None, r_end_position=None,
              arrow_style=None):
        if isinstance(name, str):
            self.check_and_or_add_name_with_var_pool(name)
        parameters = []
        if start_position:
            parameters.append("from")
            parameters.append(start_position.as_set_parameter)
        if end_position:
            parameters.append("to")
            parameters.append(end_position.as_set_parameter)
        elif r_end_position:
            parameters.append("rto")
            parameters.append(r_end_position.as_set_parameter)
        if arrow_style:
            parameters.append('as')
            parameters.append(arrow_style)
        #if head:
            #parameters.append(head)
        #if size:
            #parameters.append('size')
            #paremeters.append(','.join(size))
        #if filled:
            #parameters.append(filled)
        #if front_back:
            #parameters.append(front_back)
        #if ls:
            #parameters.append(ls)
        #if lt:
            #parameters.append(lt)
        #if lw:
            #parameters.append(lw)
        self.add_pre_setting(self.arrow_def(name), *parameters)        
        
    def remove_arrow(self, id_):
        if self.arrow_def(id_) in [x[0] for x in self.pre_settings]:
            self.pre_settings = [x for x in self.pre_settings
                                 if not x[0] == self.arrow_def(id_)]
        else:
            self.add_pre_setting('unset arrow {}'.format(id_))        
    
    @staticmethod
    def arrow_def(id_):
        return 'set arrow {}'.format(id_)
    
    def check_and_or_add_name_with_var_pool(self, name):
        if name in self.var_pool:
            return
        else:
            id_nr = self.var_pool.new_name(name)
            self.variable(name, id_nr)
            
            
            
class Position():
    
    def __init__(self, *parameters):
        self.z = self.type_x = self.type_y = self.type_z = None
        nr_of_parameters = len(parameters)
        if nr_of_parameters == 2:
            self.x, self.y = parameters
        elif nr_of_parameters == 3:
            self.x, self.y, self.z = parameters
            if isinstance(self.x, datetime):
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
            output = '{} {},{} {},{} {}'
        elif self.z:
            output = '{1},{3},{5}'
        elif self.type_y:
            output = '{} {},{} {}'
        else:
            output = '{1},{3}'
        p = output.format(self.type_x, wrapped(self.x),
                          self.type_y, wrapped(self.y),
                          self.type_z, wrapped(self.z))
        return p

class VarPool():
    def __init__(self):
        self.var_set = set()
        self.name_set = set()
        self.auto_nr = 0
        
    def __contains__(self, name):
        return (name in self.var_set or name in self.name_set)
        
    def add_variable(self, var):
        if var in self.name_set and var in self.var_set:
            raise NameError("You can't change the value of a name var")
        self.var_set.add(var)
        
        
    def new_name(self, name):
        if name in self:
            raise NameError("Name already used")
        self.name_set.add(name)
        self.auto_nr += 1
        return self.auto_nr
    
class LineColor():
    def __init__(self, type_=None, value=None):
        if type_ == 'palette':
            raise NotImplementedError('Color style Palette not implemented')
        elif type_ == 'from linetype':
            if isinstance(value, int):
                self.string = str(value)
            else:
                raise ValueError(
                    'linetype must be integer: {}'.format(value))
        elif type_ == 'palette':
            raise NotImplementedError('Color style Palette not implemented')
        elif type_ == 'rgb' or type_ == 'by_name':
            if value == "variable":
                self.string = 'rgbcolor variable'
            else:
                self.string = 'rgbcolor "{}"'.format(self.value_as_string(value))
        else:
            raise GNUplotError('unknown Color style: {}'.format(type_))
        
    def __str__(self):
        return self.string
    
    @staticmethod
    def value_as_string(value):
        # You can test the string before sending it
        return str(value)
    
class LineType():
    def __init__(self, value):
        if isinstance(value, str):
            if value == 'std':
                value = -1
        if isinstance(value, int):
            self.string = str(value)
        else:
            raise GNUplotError('unknown line type: {}'.format(self.type_))
        
    def __str__(self):
        return self.string
    
class ArrowHead():
    def __init__(self, value):
        if value in ('nohead', 'head', 'heads'):
            self.string = value
        else:
            raise GNUplotError('unknown arrow head: {}'.format(self.type_))
        
    def __str__(self):
        return self.string   
    
def type_pop(a_list, a_type):
    for n , el in enumerate(a_list):
        if isinstance(el, a_type):
            break
    else:
        return None
    return a_list.pop(n)

##############################

def chart_list(data_list, name='CHART LIST', x_axis=None, chart_data=None):
    '''charts the data from the data list
    
    the list can be 1 or 2 dimentional
    chart_data is a list of tupples (column, name)
    chart_data can be ommited, if so the first column of the data_list will be 
    shown
    '''
    
    temp_file = mycsv.table2csv(data_list)
    my_chart = Canvas(name)
    my_chart.settings.add_pre_setting('datafile','separator','","')
    if not x_axis is None and isinstance(data_list[x_axis], datetime):
        my_chart.settings.add_pre_setting('timefmt','"%Y-%m-%d %H:%M:%S"')
        my_chart.settings.add_pre_setting('xdata','time')
        
    my_chart.settings.add_pre_setting('xrange', '[*:*] reverse')
        
    my_chart.add_chart()
    x_field = [x_axis+1] if not x_axis==None else [] 
    if not chart_data:
        my_chart.charts[0].add_data_serie(filename=temp_file, 
                                          fields=x_field+[1],
                                          style='line')
    else:

        for column, col_name in chart_data:
            print(x_field+[column+1])
            my_chart.charts[0].add_data_serie(col_name, filename=temp_file, 
                                              fields=x_field+[column+1],
                                              style='line')
    my_chart.draw()

    mypy.rmTempFile(temp_file)
    