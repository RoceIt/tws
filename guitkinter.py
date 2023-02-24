#!/usr/bin/python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

from tkinter import *
from tkinter import ttk
from collections import namedtuple
import guivars

ValidationInfo = namedtuple('ValidationInfo',
                            'type_of_action pos_of_change new_value '
                            'prior_value key validate_value '
                            'trigger system_zone_name')

PRODUCTION_MODE = '$production_mode'
TEST_MODE = '$test_mode'

DELETE = guivars.DELETE
INSERT = guivars.INSERT
REVALIDATE = guivars.REVALIDATE
VALIDATE_ACTION = {'0':DELETE, '1':INSERT, '-1':REVALIDATE}

class GuiError(Exception): pass
class NotImplemented(GuiError): pass

class Application():
    
    def __init__(self, parent= None, log='console'):
        
        self.parent = parent
        self.log = log
        self.window_title = None
        self.menu = None
        self.toolbar = None
        self.__grid = None
        self.mode = PRODUCTION_MODE
        self.initial_focus = None   
        self.exit_action = None
        self.auto_save_dict = []
        self.exit_action = []
        self.zone_width = None
        
    @property
    def grid(self):
        
        return self.__grid
        
    @grid.setter
    def grid(self, grid):
        
        self.__grid = grid
        
    @property
    def zone_width(self):
        
        return self.__zone_width
    
    @zone_width.setter
    def zone_width(self, width):
        
        self.__zone_width = width
        
    def start(self):
        if self.parent == None:
            self.root = Tk()
            if self.window_title:
                self.root.title(self.window_title)
            self.frame = ttk.Frame(self.root)
            self.frame.grid(column=0, row=0, sticky=(N, W, E, S))
            self.frame.columnconfigure(0, weight=1)
            self.frame.rowconfigure(0, weight=1)
            self.root.minsize(220, 1)
        else:
            raise NotImplemented('passing parents')
        if self.grid:
            self.create_grid()
        else:
            raise GuiError('no application layout descriptor present')
        if self.initial_focus:
            self.initial_focus.set_focus
        if self.auto_save_dict:
            self.on_exit(self.auto_save, self.auto_save_dict)
        if self.exit_action:
            self.root.bind('<Destroy>', self.run_exit)
        self.root.mainloop()
        
    
    def create_grid(self):
        
        for row_nr, line in enumerate(self.grid):
            self.create_line(line, row_nr)
            
    def create_line(self, line, row_nr):
        for column_nr, zone_def in enumerate(line):
            zone = self.insert_zone(zone_def)
            zone.grid(column=column_nr, row=row_nr) #, sticky='e')            
            
    def insert_zone(self, zone):
        new_zone = zone.create_in(self)
        if zone.has_focus:
            self.initial_focus = zone
        if (zone.auto_save_dict and
            not zone.auto_save_dict in self.auto_save_dict):
            self.auto_save_dict.append(zone.auto_save_dict)
        return new_zone
    
    def on_exit(self, function, *parameters):
        self.exit_action.append((function, parameters))
        
    def run_exit(self,*foo):
        print(foo[0].widget)
        if foo[0].widget == self.root:
            print('Running exit functions')
            for function, parameters in self.exit_action:
                function(*parameters)
        
    @staticmethod
    def auto_save(dictionaries):
        print('Running auto save')
        for dictionary in dictionaries:
            dictionary.save()
    
class Zone():
    
    def __init__(self):
        self.variable = None
        self.raise_not_implemented = False
        self.__focus = False
        self.auto_save_dict = None
        
    def create_in(self, parent):
        
        self.program_mode = parent.mode
        if self.program_mode == PRODUCTION_MODE:
            if not self.variable is None:
                self.variable.raise_function_errors = False
        self.zone_parameters = dict()
        if parent.zone_width:
            self.zone_parameters['width']=parent.zone_width
    @property            
    def focus(self):
        
        if type(self) in INPUT_ZONES:
            self.__focus = True
        else:
            print('!! Trying to set focus to a not interactive zone !!')
        return self
    
    @property
    def has_focus(self):
        return self.__focus
        
        
    @property
    def testmode(self):
        self.raise_not_implemented = True
        
    @property
    def variable(self):
        return self.__variable
    
    @variable.setter
    def variable(self, variable):
        
        self.__variable = variable
        if variable:
            self.auto_save_dict = variable.auto_save_dict
        
        
class ReadZone(Zone):
    
    def __init__(self, variable, text=None):
        super().__init__()
        self.variable = variable
        self.text = text
        
    def validate(self, type_of_action, pos_of_change, new_value,
                 prior_value, text_string, validate_value, trigger,
                 widget_name):
        passed_info = ValidationInfo(VALIDATE_ACTION[type_of_action],
                                     pos_of_change, new_value,
                                     prior_value, text_string, validate_value,
                                     trigger, widget_name)
        print('validating {} for {}'.format(widget_name, trigger))
        print(passed_info)        
        if trigger == 'key':
            validate_test = self.variable.validate_on_key
        elif trigger == 'focusin':
            validate_test = self.variable.validate_on_focus_in
        elif trigger == 'focusout':
            validate_test = self.variable.validate_on_focus_out
        elif trigger == 'forced':
            validate_test = self.variable.validate_on_force
        else:
            mess = 'unknown trigger for validation'
            mypy.raise_not_implemented(self.raise_not_implemented, mess)
            validate_test = validate_ok
        print('test is {}'.format(validate_test.__name__))
        if validate_test(passed_info):
            if trigger == 'focusout':
                self.variable.value = new_value
            valid = True
        else:
            valid = False
        return valid
    
    def invalid(self, type_of_action, pos_of_change, new_value,
                prior_value, text_string, validate_value, trigger,
                widget_name):
        passed_info = ValidationInfo(VALIDATE_ACTION[type_of_action],
                                     pos_of_change, new_value,
                                     prior_value, text_string, validate_value,
                                     trigger, widget_name)
        print('solving invalid')
        print(passed_info)        
        if trigger == 'key':
            invalid_action = self.variable.invalid_on_key
        elif trigger == 'focusin':
            invalid_action = self.variable.invalid_on_focus_in
        elif trigger == 'focusout':
            invalid_action = self.variable.invalid_on_focus_out
        elif trigger == 'forced':
            invalid_action = self.variable.invalid_on_force
        else:
            mess = 'unknown trigger for invalid'
            mypy.raise_not_implemented(self.raise_not_implemented, mess)
        value = invalid_action(passed_info)
        if isinstance(value, tuple):
            new_index = value[1]
            value = value[0]
        else:
            new_index = False
        assert isinstance(value, str), 'invalid action should return a string'
        value = value if not value == 'None' else ''
        self.var.set(value)
        if new_index:
            self.entry_zone.icursor(new_index)
        
    def var2variable(self, event):
        
        print('cought <Return>')
        self.variable.value = self.var.get()
        
    def create_in(self, parent):
         
        super().create_in(parent)   
        self.zone = ttk.Frame(parent.frame,padding=2)# **self.zone_parameters)
        self.validation_funcion = (self.zone.register(self.validate), '%d', 
                                   '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.invalid_function = (self.zone.register(self.invalid), '%d', 
                                 '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.validation_trigger = 'all'
        self.var = StringVar()
        self.variable.gui_output = self            
        self.entry_zone = ttk.Entry(self.zone, textvariable=self.var,
                                    validate=self.validation_trigger,
                                    validatecommand=self.validation_funcion,
                                    invalidcommand=self.invalid_function,
                                    justify='right',  #make instruction
                                    **self.variable.gui_settings)
        self.entry_zone.bind('<Return>', self.var2variable)
        self.entry_zone.bind('<KP_Enter>', self.var2variable)
        if self.text:
            self.text_zone = ttk.Label(self.zone, width=None, text=self.text)
            self.text_zone.grid(column=0, row=0)
            self.entry_zone.grid(column=1, row=0)
        else:
            self.entry_zone.grid(column=0, row=0)
        return self.zone
    
    @property
    def set_focus(self):
        self.entry_zone.focus()
    
    def new_value(self, value):
        print('making sure entry box is showing current value {}'.
              format(value))
        self.var.set(value)     
        
class WriteZone(Zone):
    
    def __init__(self, variable, text=None):
        super().__init__()
        self.variable = variable
        self.text = text    
        
    def create_in(self, parent):
        super().create_in(parent)
        zone = ttk.Frame(parent.frame, padding=2)
        self.var = StringVar()
        self.variable.gui_output = self
        var_zone = ttk.Label(zone, textvariable=self.var,
                             **self.variable.gui_settings)
        if self.text:
            text_zone = ttk.Label(zone, text=self.text)
            text_zone.grid(column=0, row=0)
            var_zone.grid(column=1, row=0)
        else:
            var_zone.grid(column=0, row=0)
        return zone
    
    def new_value(self, value):
        print('setting new value {}'.format(value))
        self.var.set(value)
        print('result', self.var.get())
        
class SelectFromListZone(Zone):
    
    def __init__(self, variable, list_of_values, text=None, 
                 free_answers_allowed=False):
        super().__init__()
        self.variable = variable
        self.list_of_values = [str(x) for x in list_of_values]
        self.text = text
        self.free_answers_allowed=free_answers_allowed
        
    def var2variable(self, event):
        
        print('cought <Return> as: ', event)
        answer = self.var.get()
        if (answer in self.list_of_values
            or
            self.free_answers_allowed):
            self.variable.value = self.var.get()
        else:
            self.entry_zone.current(0)
        
    def create_in(self, parent):
         
        super().create_in(parent)   
        self.zone = ttk.Frame(parent.frame,padding=2)# **self.zone_parameters)
        self.var = StringVar()
        self.variable.gui_output = self            
        self.entry_zone = ttk.Combobox(self.zone, textvariable=self.var,
                                       values=self.list_of_values,
                                    justify='right',  #make instruction
                                    **self.variable.gui_settings)
        self.entry_zone.bind('<Return>', self.var2variable)
        self.entry_zone.bind('<KP_Enter>', self.var2variable)
        self.entry_zone.bind('<FocusOut>', self.var2variable)
        self.entry_zone.bind('<FocusIn>', self.var2variable)
        self.entry_zone.bind('<ButtonRelease-1>', self.var2variable)
        if self.text:
            self.text_zone = ttk.Label(self.zone, width=None, text=self.text)
            self.text_zone.grid(column=0, row=0)
            self.entry_zone.grid(column=1, row=0)
        else:
            self.entry_zone.grid(column=0, row=0)
        return self.zone
    
    @property
    def set_focus(self):
        self.entry_zone.focus()
    
    def new_value(self, value):
        print('making sure entry box is showing current value {}'.
              format(value))
        self.var.set(value)     
        
INPUT_ZONES = {ReadZone}
OUTPUT_ZONES = {WriteZone}
    
def validate_ok(*foo):
    '''function always returns True'''
    return True

def print_1_function_test(l):
    print(1)
    help(l)