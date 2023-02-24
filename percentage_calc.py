#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import guitkinter as gui
import guivars as g
from loadsavedefault import LoadSaveDefault

import mypy

def main():
    
    # define variables
    option_price = g.Float(chars_output=6)
    option_price.default = 0
    
    result1 = g.Float(precision=2)
    result1.result_function(
        result, option_price, 5)
    result1.auto_calculate_on_new(option_price) 
    
    result2 = g.Float(precision=2)
    result2.result_function(
        result, option_price, 10)
    result2.auto_calculate_on_new(option_price)
    
    result3 = g.Float(precision=2)
    result3.result_function(
        result, option_price, 15)
    result3.auto_calculate_on_new(option_price)
    
    result4 = g.Float(precision=2)
    result4.result_function(
        result, option_price, 20)
    result4.auto_calculate_on_new(option_price)
    
    result5 = g.Float(precision=2)
    result5.result_function(
        result, option_price, 25)
    result5.auto_calculate_on_new(option_price) 
    
    result6 = g.Float(precision=2)
    result6.result_function(
        result, option_price, 30)
    result6.auto_calculate_on_new(option_price) 
    
    result7 = g.Float(precision=2)
    result7.result_function(
        result, option_price, 35)
    result7.auto_calculate_on_new(option_price) 
    
    result8 = g.Float(precision=2)
    result8.result_function(
        result, option_price, 40)
    result8.auto_calculate_on_new(option_price)
    
     # define interface elements
    read_option_price = gui.ReadZone(option_price, 'PRICE: ')
    write_result1 = gui.WriteZone(result1,' 5%: ')
    write_result2 = gui.WriteZone(result2,'10%: ')
    write_result3 = gui.WriteZone(result3,'15%: ')
    write_result4 = gui.WriteZone(result4,'20%: ')
    write_result5 = gui.WriteZone(result5,'25%: ')
    write_result6 = gui.WriteZone(result6,'30%: ')
    write_result7 = gui.WriteZone(result7,'35%: ')
    write_result8 = gui.WriteZone(result8,'40%: ')
    
    # create & define application
    app = gui.Application()
    app.mode = gui.TEST_MODE
    app.window_title = 'percentage calculator'
    app.grid = [[read_option_price],
                [write_result1],
                [write_result2],
                [write_result3],
                [write_result4],
                [write_result5],
                [write_result6],
                [write_result7],
                [write_result8]]
    
    #start application
    app.start()
    
def result(base, percentage):
    return base*(1+percentage/100)
    
if __name__ == '__main__':
    main()