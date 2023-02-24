#!/usr/bin/python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)

"""
This module creates and give acces an open gnuplot process.

"""

import sys
import subprocess as sub
import tempfile
from datetime import datetime
from time import sleep
from multiprocessing import Process
from collections import defaultdict


import mypy
import mycsv
import roc_string as r_str
import roc_datetime as r_dt
import roc_classes as r_cls

class GNUplotError(Exception): pass


class Canvas():
    def __init__(self, title=None, terminal='standard',
                 lock=r_cls.NoLock(), **terminal_settings_d):
        print('using lock:', str(lock))
        self.output_file = self.title = None
        #self.canvas = sub.Popen('gnuplot', shell=True, stdin=sub.PIPE,
                                #stdout=sub.PIPE, stderr=sub.PIPE)
        self.canvas = sub.Popen('gnuplot', shell=True, stdin=sub.PIPE,
                                stderr=sub.DEVNULL,)
        self.sended_code = r_str.SerialTextCreator()
        #self.vars = VarPool() # hier wil ik van af
        self.variables = set()
        self.set_type_variables = []
        self.non_gnuplot = {
            'labelstyle': dict(),
        }
        self.settings = Settings(level='canvas', 
                                 non_gnuplot=self.non_gnuplot)
        self.show_code = False
        self.file_acces_lock = lock
        self.set_terminal(terminal, title, terminal_settings_d)
        self.plotdata = []
        
    def set_terminal(self, terminal, title, terminal_settings_):
        set_terminal = {
            'x11': set_terminal_x11,
            'wxt': set_terminal_wxt,
            'png': set_terminal_png,
        }
        terminal_settings = terminal_settings_.copy()
        set_terminal[terminal](self, title, terminal_settings)
        if terminal_settings:
            print("!!! unprocessed terminal settings !!!")
            for setting, value in terminal_settings:
                print("{}: {}".format(setting, value))
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
        
    def close(self):
        if hasattr(self, 'p'):
            self.p.kill()
        self.canvas.stdin.close()
        self.canvas.stdout.close()
        self.canvas.stderr.close()
        self.print_code('returncode: ',self.canvas.returncode)
        self.canvas.terminate()
            
    def send(self, code):
        self.print_code(code)
        code = '{}\n'.format(code)
        self.sended_code.add_text(str(code))
        self.canvas.stdin.write(str(code).encode())
        self.canvas.stdin.flush()
         
    def var(self, name, value):
        if name in self.set_type_variables:
            raise GNUplotError('Variable already in use for type setting: {}'
                               .format(name))
        self.variables.add(name)
        if isinstance(value, str):
            value = '"{}"'.format(value)
        self.send('{} = {}'.format(name, value))
        
    def give_name_a_style_nr(self, name):
        if name in self.variables:
            raise GNUplotError('style name used as normal variable {}'
                               .format(name))
        if name not in self.set_type_variables:
            self.set_type_variables.append(name)
            self.send('{} = {}'.format(name, len(self.set_type_variables)+20))
        
    def linestyle(self, name, *arg_t):
        if isinstance(name, str):
            self.give_name_a_style_nr(name)
        if arg_t == 'unset':
            t = ['unset style line {}'.format(name)]
        else:            
            t = ['set style line {}'.format(name)]            
            if arg_t =='default':
                t.append(arg_t)
            else:
                arg_l = list(arg_t)
                linetype = type_pop(arg_l, LineType)
                linecolor = type_pop(arg_l, LineColor)
                if arg_l:
                    ua = [type(x) for x in arg_l]
                    raise GNUplotError("Unknown args: {}".format(ua))
                if linetype:
                    t.append('lt')
                    t.append(str(linetype))
                if linecolor:
                    if linetype:
                        t.append('lc')
                    else:
                        t.append('lt')
                    t.append(str(linecolor))
        self.send(' '.join(t))
            
    def labelstyle(self, name, *arg_t):
        # doesn't exist in gnuplot
        self.settings.labelstyle(name, *arg_t)
        
    def arrowstyle(self, name, *arg_t, linestyle=None):
        if isinstance(name, str):
            self.give_name_a_style_nr(name)
        if arg_t == 'unset':
            t = ['unset style arrow {}'.format(name)]
        else:
            t = ['set style arrow {}'.format(name)]
            if arg_t =='default':
                t.append(arg_t)
            else:
                arg_l = list(arg_t)
                head = type_pop(arg_l, ArrowHead)
                if arg_l:
                    ua = [type(x) for x in arg_l]
                    raise GNUplotError("Unknown args: {}".format(ua))
                if head:
                    t.append(str(head))
                    if linestyle:
                        t.append('ls')
                        t.append(linestyle)
        self.send(' '.join(t))
        
    def add_data_serie(self, name=None, title=None, 
                       function=False, filename=None,
                       x_range=(None, None), y_range=(None, None),
                       fields=None, style=None, linestyle=None,
                       diy=None):
        if name is None:
            name = title
        if name is None:
            raise GNUplotError("data serie must have a name")
        self.plotdata.append(DataSerie(name, title, function, filename,
                                      x_range, y_range, fields, style,
                                      linestyle, diy))
    
    def remove_data_serie(self, name):
        for i, serie in enumerate(self.plotdata):
            if serie.name == name:
                self.plotdata.pop(i)
                break

    def draw(self):
        print('DRAW >>>>>>>>>>>>>>>>>>>')
        code = r_str.SerialTextCreator(eof='\n')
        if self.title:
            code.add_line('set title "{}"'.format(self.title))
        if self.output_file:
            code.add_line('set output {}'.format(self.output_file))
        code.add_text(self.settings.code())
        code.add_chunk('plot')
        code.add_chunk(self.plotdata[0].code)
        for data in self.plotdata[1:]:
            code.add_text(', \\')
            code.next_line()
            code.add_chunk(data.code)
        with self.file_acces_lock:
            self.send(code)
        print('DRAW <<<<<<<<<<<<<<<<<<<<')

    def update(self):
        print('update >>>>>>>>>>>>>>>>>>>')
        if self.output_file:
            code = 'set output {} \nreplot\n'.format(self.output_file)
        else:
            code = "replot\n"
        with self.file_acces_lock:
            self.send(code)
        print('update <<<<<<<<<<<<<<<<<<<<')

        
    def zoom(self, 
             x_begin='', x_end='',
             y_begin='', y_end='',
             z_begin='', z_end='',
             restore = ''):
        self.settings.zoom(x_begin, x_end, y_begin, y_end, 
                          z_begin, z_end, restore)
        if not (x_begin and x_end and y_begin and y_end and
                z_begin and z_end and restore):
            with self.file_acces_lock:
                self.send('set autoscale')
        
    def add_vertical_line(self, name, x_value, linestyle=None, canvas=False):
        if isinstance(name, str):
            self.give_name_a_style_nr(name)
        if x_value is None:
            self.settings.remove_arrow(name)
        else:
            area = 'screen' if canvas else 'graph'
            self.arrowstyle(name, ArrowHead('nohead'), linestyle=linestyle)
            self.settings.arrow(
                name,
                start_position = Position('first', x_value, area, 0),
                end_position = Position('first', x_value, area, 1),
                arrow_style=name,
            )
            
    def add_label(self, name, text, position=None, labelstyle=None):
        if isinstance(name, str):
            self.give_name_a_style_nr(name)
        if text is None:
            self.settings.remove_label(name)
        else:
            self.settings.label(
                name,
                text,
                position,
                labelstyle,
            )  
            
    def print_code(self, *arg_l, **kw_d):
        if self.show_code:
            print(*arg_l, **kw_d)
        

#class Chart():
    #def __init__(self, name, title, non_gnuplot, 
                 #give_name_a_style_nr, arrowstyle):
        #self.name = name
        #self.title = title
        #self.show_code = False
        #self.settings = Settings('chart', non_gnuplot)
        #self.plotdata = []
        #self.give_name_a_style_nr = give_name_a_style_nr
        #self.arrowstyle = arrowstyle
        
    #def __contains__(self, title):
        #for serie in self.plotdata:
            #if serie.title == title:
                #return True
        #return False
        
    #def add_data_serie(self, name=None, title=None, 
                       #function=False, filename=None,
                       #x_range=(None, None), y_range=(None, None),
                       #fields=None, style=None, linestyle=None):
        #if name is None:
            #name = title
        #if name is None:
            #raise GNUplotError("data serie must have a name")
        #self.plotdata.append(DataSerie(name, title, function, filename,
                                      #x_range, y_range, fields, style,
                                      #linestyle))
    
    #def remove_data_serie(self, name):
        #for i, serie in enumerate(self.plotdata):
            #if serie.name == name:
                #self.plotdata.pop(i)
                #break

    #def code(self):
        #code = r_str.SerialTextCreator()
        #if self.title:
            #code.append('set title "{}"'.format(self.title))
        #code.add_text(self.settings.code())
        #code.add_chunk('plot')
        #code.add_chunk(self.plotdata[0].code)
        #for data in self.plotdata[1:]:
            #code.add_text(', \\')
            #code.next_line()
            #code.add_chunk(data.code)
        #code.next_line()
        #return str(code)   
        
    #def zoom(self, 
             #x_begin='', x_end='',
             #y_begin='', y_end='',
             #z_begin='', z_end='',
             #restore = ''):
        #self.settings.zoom(x_begin, x_end, y_begin, y_end, 
                          #z_begin, z_end, restore)
        
    #def add_vertical_line(self, name, x_value, linestyle=None):
        #if isinstance(name, str):
            #self.give_name_a_style_nr(name)
        #if x_value is None:
            #self.settings.remove_arrow(name)
        #else:
            #area = 'graph'
            #self.arrowstyle(name, ArrowHead('nohead'), linestyle=linestyle)
            #self.settings.arrow(
                #name,
                #start_position = Position('first', x_value, area, 0),
                #end_position = Position('first', x_value, area, 1),
                #arrow_style=name,
            #)
            
    #def add_label(self, name, text, position=None, labelstyle=None):
        #if isinstance(name, str):
            #self.give_name_a_style_nr(name)
        #if text is None:
            #self.settings.remove_label(name)
        #else:
            #self.settings.label(
                #name,
                #text,
                #position,
                #labelstyle,
            #)            
        
class DataSerie():
    def __init__(self, name, title=None, function=False, filename=None,
                 x_range=(None, None), y_range=(None, None),
                 fields=None, style=None, linestyle=None, diy=None
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
        self.diy = diy
    
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
        elif not self.title:
            code.add_chunk('notitle')
        if self.style:
            code.add_chunk('with {}'.format(self.style))
        if self.linestyle:
            code.add_chunk('ls {}'.format(self.linestyle))
        if self.diy:
            code.add_chunk(self.diy)
        return str(code)
     
                
class Settings():
    
    def __init__(self, level, non_gnuplot):
        self.level = level
        self.settings = []
        self.settings_ = dict()
        self.unset =dict()
        self.non_gnuplot = non_gnuplot
        
    def code(self):        
        t = r_str.SerialTextCreator(eof='\n')
        #for setting in self.settings:
            #t.add_chunk('{}'.format(setting[0]))
            #for parameter in setting[1]:
                #t.add_chunk('{}'.format(parameter))
            #t.next_line()
        for k, setting in self.settings_.items():
            t.add_line(setting)
        return str(t)
        
    def unset_code(self):        
        t = r_str.SerialTextCreator(eof='\n')
        print('unset code dict:', self.unset)
        for k, setting in self.unset.items():
            t.add_line(setting)
        return str(t)
            
    def add_setting(self, name, *parameters):
        self.settings.append((name, parameters))
        
    ####################
    # SETTINGS
    ####################           

    def datafile_seperator(self, separator):
        separator = '"{}"'.format(separator) if separator else 'whitespace'
        self.settings_['df_sep'] = (
            'set datafile separator {}'.format(separator))
        
    def time_format(self, time_format):
        if time_format:
            self.settings_['tf'] = (
                'set timefmt "{}"'.format(time_format))
        else:
            self.settings_.pop('tf', True)
        
    def timeseries_on_axis(self, axis, 
                           time_format=r_dt.ISO_8601_DATETIME_FORMAT):
        axis_command = {'x': 'xdata', 'y': 'ydata', 'z': 'zdata',
                        'x2': 'x2data', 'y2': 'y2data', 'cb': 'cbdata'}
        self.time_format(time_format)
        self.settings_[axis_command[axis]] = (
            'set {} time'.format(axis_command[axis]))
        self.unset[axis_command[axis]] = (
            'set {}'.format(axis_command[axis]))
                
    def range_for_axis(self, axis, start='', end='', 
                       reverse=False, writeback=False,
                       restore=False):
        axis_command = {'x': 'xrange', 'y': 'yrange', 'z': 'zrange'}
        if restore:
            self.settings_[axis_command[axis]] = (
                'set {} restore'.format(axis_command[axis]))
            return
        if start == '' and end == '':
            self.settings_.pop(axis_command[axis], None)
            self.unset.pop(axis_command[axis], None)
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
        self.settings_[axis_command[axis]] = (
            'set {} {}'.format(axis_command[axis], ' '.join(range_setting)))
        self.unset[axis_command[axis]] = (
            'set {} restore'.format(axis_command[axis])
            #'unset {}'.format(axis_command[axis])
        )
        
    def label(self, name, text, position=None, labelstyle=None):   
        parameters = []
        if position:
            parameters.append('at')
            parameters.append(position.as_set_parameter)
        if labelstyle:
            parameters.append(self.non_gnuplot['labelstyle'][labelstyle])
        self.settings_['L_{}'.format(name)] = (
            'set label {} "{}" {}'.format(name, text, ' '.join(parameters)))
        
    def remove_label(self, name):
        self.settings_['L_{}'.format(name)] = (
            'unset label {}'.format(name))    
    
    def labelstyle(self, name, *arg_t):
        if arg_t == 'unset':
            self.non_gnuplot['labelstyle'].pop(name, None)
            return
        t = r_str.SerialLineCreator(separator=' ')        
        arg_l = list(arg_t)
        textcolor = type_pop(arg_l, TextColor)
        if arg_l:
            ua = [type(x) for x in arg_l]
            raise GNUplotError("Unknown args: {}".format(ua))
        if textcolor:
            t.add_chunk("tc")
            t.add_chunk(str(textcolor))
        self.non_gnuplot['labelstyle'][name] = str(t) 
        
    def zoom(self, 
             x_begin='', x_end='',
             y_begin='', y_end='',
             z_begin='', z_end='',
             restore = ''):
        if ('x' in restore):
            self.range_for_axis('x', restore=True)
        if 'y' in restore:
            self.range_for_axis('y', restore=True)
        if 'z' in restore:
            self.range_for_axis('z', restore=True)
        if True: #x_begin or x_end:
            self.range_for_axis('x', x_begin, x_end)
        if True: #y_begin or y_end:
            self.range_for_axis('y', y_begin, y_end)
        if True: #z_begin or z_end:
            self.range_for_axis('z', z_begin, z_end)
        
    def arrow(self, name, 
              start_position=None, end_position=None, r_end_position=None,
              arrow_style=None):
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
        self.settings_['->{}'.format(name)] = (
            'set arrow {} {}'.format(name, ' '.join(parameters)))
        
    def remove_arrow(self, name):
        self.settings_['->{}'.format(name)] = (
            'unset arrow {}'.format(name))
        
    #def margin(self, type_, value):
        #typetxt = {
            #'left': 'lmargin',
        #}
        #self.settings_['margin'] = (
            #'set {} {}'.format(typetxt[type_], value))
        
    def mouse(self, active=True):
        if active is False:
            self.settings_['mouse'] = (
                'unset mouse')
        else:
            self.settings_['mouse'] = (
                'set mouse')
            
    def tics(self, axis, show=True, label=True, hide_value=None, r=False):
        axis_command = '{}tics'.format(axis)
        if show == False:
            self.settings_[axis_command[axis]] = (
                'unset {}'.format(axis_command[axis]))
            return
        t = r_str.SerialLineCreator(separator=' ')
        t.add_chunk('set {}'.format(axis_command))
        if label == False:
            t.add_chunk("format ''")
        if hide_value is not None:
            t.add_chunk('add ("" {})'.format(hide_value))
            axis_command += str(hide_value)
        if r:
            t.add_chunk('rangelimited')
        self.settings_[axis_command] = str(t)
        
    def margin(self, margin, value):
        margin_command = {
            'top': 'tmargin',
            'right': 'rmargin',
            'bottom': 'bmargin',
            'left': 'lmargin',
        }
        self.settings_[margin_command[margin]] = (
            'set {} {}'.format(margin_command[margin], value))
            
    def axislabel(self, axis, show=True, hide=None):
        axis_command = {'x': 'xlabel', 'y': 'ylabel', 'z': 'zlabel',
                        'x2': '', 'y2': '', 'cb': ''}
        if show == False:
            self.settings_[axis_command[axis]] = (
                'unset {}'.format(axis_command[axis]))
        
        else:
            self.settings_[axis_command[axis]] = (
                'set {}'.format(axis_comaand[axis]))
            
    def zeroaxis(self, axis, show=True, linestyle=None):
        axis_command = '{}zeroaxis'.format(axis)
        if show == False:
            self.settings_[axis_command] = (
                'unset {}'.format(axis_command))
            return
        t = r_str.SerialLineCreator(separator=' ')
        t.add_chunk('set {}'.format(axis_command))
        if linestyle:
            t.add_chunk('ls {}'.format(linestyle))
        self.settings_[axis_command] = str(t)
        
    def boxwidth(self, value=True, relative=False):
        if value == True:
            mss = 'set boxwidth'
        else:
            mss = 'set boxwidth {}'.format(value)
            if relative == True:
                mss += ' relative'
            else:
                mss += ' absolute'
        self.settings_['boxwidth'] = mss
        
    def grid(self, show=True):
        if show == False:
            mss = 'unset grid'
        else:
            mss = 'set grid'
        self.settings_['grid'] = mss
        
        
            
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
            if ((isinstance(value, str)                               and
                 ' ' in value)
                or
                (isinstance(value, datetime))
            ):
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
    
class TextColor():
    def __init__(self, type_=None, value=None):
        if type_ == 'palette':
            raise NotImplementedError('Color style Palette not implemented')
        elif type_ == 'from linetype':
            if isinstance(value, int):
                self.string = 'lt {}'.format(value)
            else:
                raise ValueError(
                    'linetype must be integer: {}'.format(value))
        elif type_ == 'from linestyle':
                self.string = 'ls {}'.format(value)
        elif type_ == 'rgb' or type_ == 'by_name':
            self.string = 'rgb "{}"'.format(self.value_as_string(value))
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
    
class Margin():
    def __init__(self, type_, value):
        self.string = '{} {}'.format(type_, value)
        
    def __str__(self):
        return self.string
        
    
#class MultiChart():
    #def __init__(self, nr_of_charts, title=None):
        #self.layout_defined = False
        #self.title = title
        #self.nr_of_charts = nr_of_charts
        #self.chart_pos = dict()
        
    #def pre_setting_code(self):
        #c = r_str.SerialTextCreator(eof='\n')
        #c.add_chunk('set multiplot')
        #if self.title:
            #c.add_chunk('"{}"'.format(self.title))
        #return str(c)
            
    #def post_setting_code(self):
        #c = r_str.SerialTextCreator(eof='\n')
        #c.add_line('unset multiplot')
        ##c.add_line('reset')
        #return str(c)
        
    #def set_char_positions(self, position_matrix=None):
        #self.chart_pos = dict()
        #total_hight = 0
        #for row in position_matrix:
            #total_hight += row[0]
        #curr_hight = 1
        #for row in position_matrix:
            #hight = row[0] / total_hight
            #curr_hight -= hight
            #total_width = 0
            #for col in row[1]:
                #total_width += col[0]
                #if col[1] not in self.chart_pos:
                    #self.chart_pos[col[1]] = []
            #curr_width = 0
            #for col in row[1]:
                #if col[1] is not None:
                    #width = col[0]/total_width
                    #origin = (curr_width, curr_hight)
                    #size = (width, hight)
                    #curr_width += width
                    #self.chart_pos[col[1]].append(
                        #(origin, size))
        #print(self.chart_pos)
        
    #def position_code(self, name):
        #pos = self.chart_pos[name]
        #for origin, size in pos:
            #c = r_str.SerialTextCreator(eof='\n')
            #c.add_line('set origin {},{}'.format(*origin))
            #c.add_line('set size {}, {}'.format(*size))
            ##c.add_line('clear')
            #yield str(c)

################################################################
##
## TERMINAL SETTINGS
##
################################################################
SET_TERMINAL = 'set term'

def set_terminal_x11(canvas, title, terminal_settings):
    text = [SET_TERMINAL, 'x11']
    if title:
        text.append('title "{}"'.format(title))
    raise_ = terminal_settings.pop('raise', True)
    if not raise_:
        text.append('noraise')
    canvas.send(' '.join(text))

def set_terminal_wxt(canvas, title, terminal_settings):
    text = [SET_TERMINAL, 'wxt']
    if title:
        text.append('title "{}"'.format(title))
    raise_ = terminal_settings.pop('raise', True)
    if not raise_:
        text.append('noraise')
    canvas.send(' '.join(text))
    
def set_terminal_png(canvas, title, terminal_settings):
    text = [SET_TERMINAL, 'png']
    canvas.output_file = '"{}.png"'.format(terminal_settings.pop('filename'))
    if title:
        canvas.title = title
    size = terminal_settings.pop('size', None)
    if size:
        text.extend(['size', '{},{}'.format(*size)])
    canvas.send(' '.join(text))    
    
    
def type_pop(a_list, a_type):
    for n , el in enumerate(a_list):
        if isinstance(el, a_type):
            break
    else:
        return None
    return a_list.pop(n)