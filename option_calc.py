#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#import os.path

import guitkinter as gui
import guivars as g
from loadsavedefault import LoadSaveDefault

import mypy

AUTOSAVE = 'option_calc.as'
D_OPTION_PRICE = 0
D_OPTION_MULTIPLIER = 100
D_ACCOUNT1 = D_ACCOUNT2 = D_ACCOUNT3 =0

def main():
    
    defaults = LoadSaveDefault(AUTOSAVE,
                               option_price=D_OPTION_PRICE,
                               option_multiplier=D_OPTION_MULTIPLIER,
                               account1=D_ACCOUNT1, account2=D_ACCOUNT2,
                               account3=D_ACCOUNT3)
    
    # define variables
    option_price = g.Float(chars_output=6)
    option_price.default = (defaults, 'option_price')
    
    option_multiplier = g.Integer(chars_output=5)
    option_multiplier.default = (defaults, 'option_multiplier')
    
    account1 = g.Integer(chars_output=10)
    account1.default = (defaults, 'account1')
    
    account2 = g.Integer(chars_output=10)
    account2.default = (defaults, 'account2')
    
    account3 = g.Integer(chars_output=10)
    account3.default = (defaults, 'account3')
    
    max_nr_of_options1 = g.Integer(chars_output=5)
    max_nr_of_options1.result_function(
        max_nr_of_options, 
        account1, option_price, option_multiplier,
        auto_calculate_on_new=g.ALL)
    
    max_nr_of_options2 = g.Integer(chars_output=5)
    max_nr_of_options2.result_function(
        max_nr_of_options, 
        account2, option_price, option_multiplier)
    max_nr_of_options2.auto_calculate_on_new(account2, option_price,
                                             option_multiplier) 
    
    max_nr_of_options3 = g.Integer(chars_output=5)
    max_nr_of_options3.result_function(
        max_nr_of_options, 
        account3, option_price, option_multiplier)
    max_nr_of_options3.auto_calculate_on_new(account3, option_price,
                                             option_multiplier)
    
    # define interface elements
    read_option_price = gui.ReadZone(option_price, 'PRICE: ')
    read_multiplier = gui.ReadZone(option_multiplier, 'multiplier: ')
    read_account1 = gui.ReadZone(account1, 'Account 1: ')
    read_account2 = gui.ReadZone(account2, 'Account 2: ')
    read_account3 = gui.ReadZone(account3, 'Account 3: ')
    write_max_option_account1 = gui.WriteZone(max_nr_of_options1,'# of options: ')
    write_max_option_account2 = gui.WriteZone(max_nr_of_options2,'# of options: ')
    write_max_option_account3 = gui.WriteZone(max_nr_of_options3,'# of options: ')
        
    # create & define application
    app = gui.Application()
    app.mode = gui.TEST_MODE
    app.window_title = 'Option Calculator'
    app.zone_width = 5000
    
    app.grid = [[read_option_price.focus, read_multiplier],
                [read_account1, write_max_option_account1],
                [read_account2, write_max_option_account2],
                [read_account3, write_max_option_account3]]
        
    #start application
    app.start()
    
    
def max_nr_of_options(account_size, option_price, option_multiplier):
    if (not(account_size == None or option_price == None) and
        not(option_multiplier == 0 or option_price == 0)):
        print('calculating max number of options')
        return account_size // (option_price * option_multiplier)
    
def load_defaults():
    if os.path.exists(AUTOSAVE):
        obj = mypy.import_pickle(AUTOSAVE)
    else:
        obj = make_default_dic(D_OPTION_PRICE, D_OPTION_MULTIPLIER,
                               D_ACCOUNT1, D_ACCOUNT2)
        
    return obj

def save_defaults(option_price, option_multiplier, account1, account2):
    obj = make_default_dic(option_price, option_multiplier,
                           account1, account2)
    mypy.export_pickle(obj, AUTOSAVE)
    
def make_default_dic(option_price, option_multiplier, account1, account2):
    datadic = {'option_price': option_price,
               'option_multiplier': option_multiplier,
               'account1': account1,
               'account2': account2}
    
if __name__ == '__main__':
    main()
    