#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#
import os
import datetime

import validate
from roc_settings import Error
from roc_output import if_defined_print
from roc_currency import to_currency

TIMEDELTA_PARAMETER_TRANSLATION = {
    'seconds': 'seconds', 'second': 'seconds', 'sec': 'seconds', 's': 'seconds',
    'secs': 'seconds',
    'minutes': 'minutes', 'minute': 'minutes', 'min': 'minutes', 'm': 'minutes',
    'hours': 'hours', 'hour': 'hours', 'h': 'hours',
    'days': 'days','day': 'days','d': 'days',
    'weeks': 'weeks', 'week': 'weeks', 'w': 'weeks',
    'years': 'years', 'year': 'years', 'y': 'years'
}

#####
# INPUT CLASSES
#####

class SelectionMenu():
    '''Easy to use CLI choice menu.
    
    Show a menu and return the users choice.
    
    '''
    
    def __init__(self,
            interface='TXT_LINE', 
            message=None,
            auto_number=False, 
            auto_return_value=True):
        '''Initialise menu.'''
        
        self.menu_items = []
        for menu_item in self.menu_items:
            self.add_menu_item(*menu_item)
        self.interface = interface
        self.message = message
        assert isinstance(auto_number, bool), 'auto_number must be bool'
        self.auto_number = auto_number
        self.auto_return_value = auto_return_value
        self.text_separator = '  |  '
        
    @property
    def interface(self):
        return self.__interface
    
    @interface.setter
    def interface(self, interface):
        txt_table_choice = self._txt_table_choice
        if interface == 'TXT_LINE':
            self.__interface = txt_table_choice            
            self.items_per_row = 0
        elif interface == 'TXT_ROW':
            self.__interface = txt_table_choice
            self.items_per_row = 1
    @property
    def auto_return_value(self):
        '''returns True, False or 'NR' '''
        return self.__auto_return_value
    
    @auto_return_value.setter
    def auto_return_value(self, value):
        '''Choose the way the choice is returned.
        
        True -- return the selected object
        False -- user will set the return value
        'NR'  -- Return the number the user choose
        '''
        if value in {True, False}:
            self.__auto_return_value = value
        elif value == 'NR':
            self.__auto_return_value = value
        else:
            mess = 'auto_return_value must be True, False or \'NR\''
            raise Error(mess)
    @property
    def existing_text_values(self):
        return [x[0] for x in self.menu_items]
    @property
    def existing_selector_values(self):
        return [x[1] for x in self.menu_items]
        
    def add_menu_item(self, text, selector=None, return_value=None):
        auto_number = self.auto_number
        auto_return_value = self.auto_return_value
        menu_items = self.menu_items
        existing_text_values = self.existing_text_values
        existing_selector_values = self.existing_selector_values
        if selector == None:
            if auto_number:
                selector = str(len(menu_items))
            else:
                selector = str(text)
        else:
            mess = 'auto_number is on, you can\'t choose a selector'
            assert auto_number == False, mess
            mess = 'selector must be string or int'
            assert isinstance(selector, (int, str)), mess
            selector = str(selector)                            
        if return_value == None:
            mess = 'auto_return_value is False, return value expected'
            assert not auto_return_value == False, mess
            if auto_return_value == True:
                return_value = text
            else:
                return_value = len(menu_items)
        if (existing_text_values                                             and
            text in existing_text_values                                     and
            not auto_number
        ):
            mess = 'text value already in menu'
            raise Error(mess)
        if (existing_selector_values                                         and
            selector in existing_selector_values
        ):
            mess = 'selector {} already used for menu'.format(selector)
            raise Error(mess)
        menu_items.append((str(text), selector, return_value))
        
    def add_items(self, iterator):
        ###
        for element in iterator:
            self.add_menu_item(element)
        
        
    def get_users_choice(self):
        return self.interface()
        
    def _txt_table_choice(self):
        #make text menu
        menu_items = self.menu_items
        items_per_row  = self.items_per_row
        separator = self.text_separator
        message = self.message
        existing_text_values = self.existing_text_values
        existing_selector_values = self.existing_selector_values
        text_menu = []
        for item_nr, menu_item in enumerate(menu_items):
            text = menu_item[0]
            selector = menu_item[1]
            return_value = menu_item[2]
            if not selector == text:
                selector_text = '({}) '.format(selector)
            else:
                selector_text = ''
            if item_nr == len(menu_items) - 1:
                end = ''
            elif items_per_row > 0 and (item_nr + 1) % items_per_row == 0 :
                end = '\n'
            else:
                end = separator
            text_menu.append(''.join([selector_text, text, end]))
        text_menu = ''.join(text_menu)
        if message == None:
            message = 'Choice: '
        while True:
            print(text_menu)
            print()
            answer = get_string(message)
            if answer in existing_selector_values:
                answer = menu_items[existing_selector_values.index(answer)][2]
                return answer
            print('Invalid choice')
            print()
            
    @staticmethod
    def pass_(*args, **kwds):
        '''A callable pass function.
        
        When the menu is used to return functions, you can return this
        one to do nothing.  It accepts all args and kwds and does
        absolutly noting with them.
        
        Parameters:
          whatever
        '''
        ###
        ###
        pass 

#####
# GET BUILT-IN VALUES
#####

def get_bool(message, default = None):
    '''Read boolean from CLI.
    
    If message has format accolades, the choices (with the default if
    present in caps) are added.
    
    The true and false values are defined in the roc_settings file. [TODO]
    
    Parameters:
      message -- message to show
      default -- bool
    '''
    ###
    if default is True:
        hint = '(Y/n)'
    elif default is False:
        hint = '(y/N)'
    else:
        hint = '(y/n)'
    while True:
        line = input(message.format(hint))
        if line == '' and not default is None:
            return default
        if line in ['N', 'No', 'NO', 'n', 'nee']:
            return False
        if line in ['Y', 'Yes', 'YES', 'y', 'j', 'ja']:
            return True

def get_string(message,
               max_length = None, ml_message=None, ml_auto_reduce=False,
               default = None,
               empty = False, el_message=None,
               err_message = None,
               valid_choices=None):
    '''Read string from CLI.
    
    Print message and reads user input.  If the input is valid the answer
    is returned.  The funtion will not return until a valid answer is
    provided.
    
    Parameters:
      message -- a string with information for the user
      max_lenth -- maximal legal lenth
      ml_message -- message shown when string is to long
      ml_auto_reduce -- return first max_len chars from the string
      default -- default answer
      empty -- if True, '' string is allowed
      el_message -- message shonw when string is empty and not allowed
      err_message -- general error message
      valid_choices -- a set of valid choices      
    '''
    def valid_parameters():
        if max_length is None and ml_message or ml_auto_reduce:
            raise Error('No max length with ml_message or ml_aut_reduce set')
        if default == '' and empty is False:
            raise Error('default \'\' and empty not allowed')
        if (not default is None and
            not valid_choices is None and
            not default in valid_choices):
            raise Error('default value not in valid_choices')
        return True    
    assert valid_parameters()
    ###
    message = message.format(default=default)
    while True:
        line = input(message)
        if line:
            if max_length:
                if len(line) > max_length:
                    if not ml_auto_reduce:
                        if_defined_print(ml_message)
                        continue
                    line = line[:max_length]
        elif default is not None:
            line = default
        elif empty:
            line = ''
        else:
            if_defined_print(el_message)
            continue
        if (line == ''
            or
            not valid_choices
            or
            valid_choices is not None and
            line in valid_choices):
            break
        if_defined_print(err_message)
    ###
    return line

def get_integer(message,
                default = None,
                empty = False, el_message=None,
                err_message = None,
                valid_choices=None,
                minimum=None, maximum=None, lim_message=None):
    '''Read date from CLI, returns a datetime.time object.
    
    Uses the get_string to read the line, default, empty, el_massage,
    err)message and valid_choices can be used.
    
    Extra parameter time_format, to define the format.  The err_message
    will be printed if the format is not ok.
    
    If minimum and/or maximum are set and the smaller and/or bigger the
    lim_message is shown (if present), it is formatted with the minimum,
    maximum.
    
    Parameters:
      from get_string
      time_format -- format_string
    '''
    
    ###
    if valid_choices: valid_choices = [str(x) for x in valid_choices]
    while True:
        int_text = get_string(message=message, default=default, empty=empty,
                              el_message=el_message, err_message=err_message,
                              valid_choices=valid_choices)
        if int_text:
            try:
                the_int = int(int_text)
            except ValueError as err:
                if_defined_print(err_message)
                continue
            if ((minimum and minimum > the_int)
                or
                (maximum and maximum < the_int)):
                if_defined_print(lim_message.format(minimum, maximum))
                continue
        else:
            the_int = int_text
        break
    ###
    return the_int

def get_float(message,
              default = None,
              empty = False, el_message=None,
              err_message = None,
              valid_choices=None,
              minimum=None, maximum=None, lim_message=None):
    '''Read date from CLI, returns a float number.
    
    Uses the get_string to read the line, default, empty, el_massage,
    err)message and valid_choices can be used.
    
    Extra parameter time_format, to define the format.  The err_message
    will be printed if the format is not ok.
    
    If minimum and/or maximum are set and the smaller and/or bigger the
    lim_message is shown (if present), it is formatted with the minimum,
    maximum.
    
    Parameters:
      from get_string
      time_format -- format_string
    '''
    
    ###
    if valid_choices: valid_choices = [str(x) for x in valid_choices]
    while True:
        float_text = get_string(message=message, default=default, empty=empty,
                                el_message=el_message, err_message=err_message,
                                valid_choices=valid_choices)
        if float_text:
            try:
                the_float = float(float_text)
            except ValueError as err:
                if_defined_print(err_message)
                continue
            if ((minimum and minimum > the_float)
                or
                (maximum and maximum < the_float)):
                if_defined_print(lim_message.format(minimum, maximum))
                continue
        else:
            the_float = float_text
        break
    ###
    return the_float


#####
# GET DATETIME RELATED VALUES
#####

def get_time(message, time_format,
             default = None,
             empty = False, el_message=None,
             err_message = None,
             valid_choices=None,
             minimum=None, maximum=None, lim_message=None):
    '''Read date from CLI, returns a datetime.time object.
    
    Uses the get_string to read the line, default, empty, el_massage,
    err)message and valid_choices can be used.
    
    Extra parameter time_format, to define the format.  The err_message
    will be printed if the format is not ok.
    
    If minimum and/or maximum are set and the smaller and/or bigger the
    lim_message is shown (if present), it is formatted with the minimum,
    maximum.
    
    Parameters:
      from get_string
      time_format -- format_string
    '''
    
    ###
    while True:
        time_text = get_string(message=message, default=default, empty=empty,
                               el_message=el_message, err_message=err_message,
                               valid_choices=valid_choices)
        if time_text:
            try:
                the_time = datetime.datetime.strptime(time_text, time_format)
                the_time = the_time.time()
            except ValueError as err:
                if_defined_print(err_message)
                continue
            if ((minimum and minimum > the_time)
                or
                (maximum and maximum < the_time)):
                if_defined_print(lim_message.format(minimum, maximum))
                continue
        else:
            the_time = time_text
        break
    ###
    return the_time

def get_datetime(message, time_format,
                 default = None,
                 empty = False, el_message=None,
                 err_message = None,
                 valid_choices=None,
                 minimum=None, maximum=None, lim_message=None):
    '''Read date from CLI, returns a datetime.time object.
    
    Uses the get_string to read the line, default, empty, el_massage,
    err)message and valid_choices can be used. if default is 'now' the
    current datetime will be returned.
    
    Extra parameter time_format, to define the format.  The err_message
    will be printed if the format is not ok.
    
    If minimum and/or maximum are set and the smaller and/or bigger the
    lim_message is shown (if present), it is formatted with the minimum,
    maximum.
    
    Parameters:
      from get_string
      time_format -- format_string
    '''
    
    ###
    while True:
        time_text = get_string(message=message, default=default, empty=empty,
                               el_message=el_message, err_message=err_message,
                               valid_choices=valid_choices)
        if time_text == 'now':
            the_datetime = datetime.datetime.now()
        elif time_text:
            try:
                the_datetime = datetime.datetime.strptime(time_text, time_format)
            except ValueError as err:
                if_defined_print(err_message)
                continue
            if ((minimum and minimum > the_datetime)
                or
                (maximum and maximum < the_datetime)):
                if_defined_print(lim_message.format(minimum, maximum))
                continue
        else:
            the_datetime = time_text
        break
    ###
    return the_datetime

def get_timedelta(message, 
                  default=None, 
                  empty=False, el_message=None,
                  err_message = None,
                  valid_choices=None,
                  minimum=None, maximum=None, lim_message=None):
    '''Read timedelta from CLI, returns a datetime.timedelta object.
    
    Uses the get_string to read the line, default, empty, el_massage,
    err)message and valid_choices can be used.
    
    If minimum and/or maximum are set and the smaller and/or bigger the
    lim_message is shown (if present), it is formatted with the minimum,
    maximum.
    
    Parameters:
      from get_string
    '''
    def as_timedelta_parameter(input_string):
        tr_unit = TIMEDELTA_PARAMETER_TRANSLATION
        value = input_string.split()
        if not len(value) == 2: raise TypeError()
        try:
            times = float(value[0])
        except ValueError:
            raise TypeError()
        unit = tr_unit.get(value[1].strip().lower(), value[1].strip())
        return {unit: times}
    ###
    while True:
        timedelta_text = get_string(message=message, default=default, 
                                    empty=empty, el_message=el_message, 
                                    err_message=err_message,
                                    valid_choices=valid_choices)
        if timedelta_text:      
            try:      
                request = as_timedelta_parameter(timedelta_text)
                delta = datetime.timedelta(**request)
            except TypeError as err:
                if_defined_print(err_message)
                continue
            if ((minimum and minimum > delta)
                or
                (maximum and maximum < delta)):
                if_defined_print(lim_message.format(minimum, maximum))
                continue
        else:
            delta = timedelta_text
        break
    ###
    return delta

def get_currency_value(message, 
                       default=None, 
                       empty=False, el_message=None,
                       err_message = None):
    '''Read date from CLI, returns a currency value.
    
    Uses the get_string to read the line, default, empty, el_massage
    and err message can be used.
    
    The err_message will be printed if the format is not ok.
    
    Parameters:
      from get_string
    '''
    while True:
        currency_text = get_string(
            message=message,
            default=default,
            empty=empty,
            el_message=el_message,
            err_message=err_message
        )
        if currency_text:
            try:
                currency = to_currency(currency_text)
            except Error as err:
                if_defined_print(err_message)
                continue
        else:
            currency = currency_text
        break
    ###
    return currency

#####
# GET FILE RELATED VALUES
#####

def get_existing_file_name(
        *get_string_args, warning_mss=None, ** get_string_kwds):
    '''Read existing file name from CLI.
    
    Print message and read user input.  If the input is valid the answer
    is returned.  The funtion will not return until a valid answer is
    provided.
    
    Parameters:
      from get_string
    '''
    ###
    while True:
        filename = get_string(*get_string_args, **get_string_kwds)
        if os.path.isfile(filename):
            break
        if_defined_print(warning_mss)
    ###
    return filename

def get_new_filename(
        *get_string_args, is_ok_mss=None, warning_mss=None,**get_string_kwds):
    '''Read file name from CLI.
    
    If warning_mss is set, warning is printed when the filename exists.
    The user can choose yes or no to continue.  If the message you send
    is answered True, the filename is excepted!  The mss can contain one
    format accolade that will show the yes/no option.  Without
    warning_mss existing filenames are not allowed.
    
    Parameters:
      from get_string
      warning_mss -- mss displayed when file exists.
    '''
    
    ###
    while True:
        filename = get_string(*get_string_args, **get_string_kwds)
        if (not os.path.exists(filename)
            or
            is_ok_mss is not None and
            get_bool(is_ok_mss)):
            break
        if_defined_print(warning_mss)
    ###
    return filename
        
         