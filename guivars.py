#!/usr/bin/python3
#
#  Copyright (c) 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)

import types

from loadsavedefault import LoadSaveDefault
import guitkinter

DELETE = '$delete'
INSERT = '$insert'
REVALIDATE = '$revalidate'
ALL = '$all'

class GUIVar():
    
    def __init__(self,**basic_settings):
 
        self.__value = None
        self.__default = None
        self.auto_update_vars = set()
        self.output_gui_zones = set()
        self.raise_function_errors = True
        self.auto_save_dict = None
        self.auto_save_key = None
        self.gui_settings = dict()
        self.gui_settings_local = dict()
        settings = basic_settings.keys()
        if 'chars_output' in settings:
            self.gui_settings['width'] = basic_settings['chars_output']
            basic_settings.pop('chars_output')
            
            
    @property
    def value(self):
        
        return self.__value
    
    @value.setter
    def value(self, value):
        
        try:
            tr = self.translate(value)
        except TypeError:
            mess = self.translate_error_message.format(value)
            print(mess)
            print('setting value to default value or None')
            tr = self.default
        self.__value = tr
        if self.auto_save_dict:
            self.auto_save_dict[self.auto_save_key] = tr
        self.auto_calculate_dependent_vars()
        self.set_gui_value()
        
    def if_changed_calculate(self, *dependend_vars):
        
        for var in dependend_vars:
            self.auto_update_vars.add(var)
            
    def auto_calculate_dependent_vars(self):
        
        for var in self.auto_update_vars:
            try:
                var.calculate()
            except:
                if self.raise_function_errors:
                    raise
                            
    @property
    def gui_output(self):
        
        return self.output_gui_zones
            
    @gui_output.setter
    def gui_output(self, zone):
        
        self.output_gui_zones.add(zone)
        zone.new_value(str(self))
            
    def set_gui_value(self):
        for zone in self.output_gui_zones:
            text = str(self)
            if self.value == None:
                text = ''
            zone.new_value(text)
            
    def result_function(self, function, *parameters, 
                        auto_calculate_on_new=None, **named_parameters):
        self.function = function
        self.parameters = parameters
        self.named_parameters = named_parameters
        if auto_calculate_on_new == ALL:
            self.auto_calculate_on_new(*parameters)
        
    def auto_calculate_on_new(self, *parameters):
        
        for variable in parameters:
            variable.if_changed_calculate(self)
            
    def calculate(self):
        
        parameters =  []
        for v in self.parameters:
            try:
                val = v.value
            except AttributeError:
                val = v
            parameters.append(val)
        self.value = self.function(*parameters)
        
    def __str__(self):
        
        return str(self.value)
    
    @property
    def default(self):
        
        return self.__default
    
    @default.setter
    def default(self, default_value):
        
        if (isinstance(default_value, tuple) and
            isinstance(default_value[0], LoadSaveDefault)):
            self.auto_save_dict = default_value[0]
            self.auto_save_key = default_value[1]
            default_value = self.auto_save_dict[self.auto_save_key]    
        try:
            tr = self.translate(default_value)
        except ValueError:
            mess = self.translate_error_message.format(default_value)
            print(mess)
            print('default value wil not be changed')
            return
        self.value = tr
        self.__default = tr   
        
    def validate_on_key (*foo):
        return True
    def validate_on_focus_in(*foo):
        return True
    def validate_on_focus_out(*foo):
        return True
    def validate_on_force(*foo):
        return True        
    def invalid_on_key (self, invalid_info):
        return invalid_info.prior_value
    def invalid_on_focus_in(foo):
        return None
    def invalid_on_focus_out(foo):
        self.value = self.default
        return str(self)
    def invalid_on_force(foo):
        return None
        
class Integer(GUIVar):
    
    def __init__(self,**basic_settings):
        
        super().__init__(**basic_settings)
        self.translate_error_message = 'Could not translate \'{}\' to int'
        
        
    @staticmethod
    def translate(value):
        
        if not isinstance(value, int):
            value = int(value)        
        return value
    
    def validate_on_focus_out(self, validation_info):
        
        value = validation_info.new_value
        print('validating integer {}'.format(value))
        try:
            int(value)
            valid = True
        except ValueError:
            valid = False
        return valid
    
    def invalid_on_focus_out(self, foo):
        
        self.value = self.default
        return str(self)
    
    def validate_on_key(self, validation_info):
        
        key = validation_info.key
        print('validating key {}'.format(key))
        return key.isnumeric()
    
    def invalid_on_key(self, invalid_info):
        
        return invalid_info.prior_value
                    
class Float(GUIVar):
    
    def __init__(self,**basic_settings):
        
        super().__init__(**basic_settings)
        settings = basic_settings.keys()
        if 'precision' in settings:
            self.precision = basic_settings['precision']
            basic_settings.pop('precision')
        self.translate_error_message = 'Could not translate \'{}\' to float'
        
        
    @staticmethod
    def translate(value):
        
        if not isinstance(value, float):
            value = float(value)        
        return value
    
    def validate_on_focus_out(self, validation_info):
        
        value = validation_info.new_value
        print('validating float {}'.format(value))
        try:
            float(value)
            valid = True
        except ValueError:
            valid = False
        return valid
    
    def invalid_on_focus_out(self, foo):
        
        self.value = self.default
        return str(self)
    
    def validate_on_key(self, validation_info):
        if validation_info.type_of_action == DELETE:
            return True
        key = validation_info.key
        old_value = validation_info.prior_value
        action = validation_info.type_of_action
        valid_keys= '0123456789'
        valid_keys += '.' if not '.' in old_value else ''
        valid_keys += '.' if action == DELETE else ''
        print('validating key {}'.format(key))
        return key in valid_keys
    
    def invalid_on_key(self, invalid_info):
        
        print('invalid on key info: {}'.format(invalid_info))
        if (invalid_info.key in [',', 'KP_Delete'] and 
            not '.' in invalid_info.new_value and
            ',' in invalid_info.new_value):
            answer = invalid_info.new_value.replace(',', '.')
            index = answer.index('.') + 1
            answer = (answer, index)
        else:
            answer = invalid_info.prior_value
        return answer
    
    @property
    def precision(self):
        
        if 'precision' in self.gui_settings_local:
            return self.gui_settings_local['precision']
        else:
            return None
        
    @precision.setter
    def precision(self, value):
        
        self.gui_settings_local['precision'] = value
    
    
    def __str__(self):
        
        if self.precision and self.value:
            format_str = '{{:.{}f}}'.format(self.precision)
        else:
            format_str = '{}'
        return format_str.format(self.value)
            
class String(GUIVar):
    
    def __init__(self,**basic_settings):
        
        super().__init__(**basic_settings)
        settings = basic_settings.keys()
        self.translate_error_message = 'Could not translate \'{}\' to str'
    
    @staticmethod
    def translate(value):
        
        if not isinstance(value, str):
            value = str(value)
        return value
    
    