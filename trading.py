#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

"""
This module provides classes for processing and analysing 
intraday data
"""
import pickle

import mypy
from datetime import datetime, date, time

def load_ATrade(filename):
    the_trade = mypy.import_pickle(filename)
    return the_trade

class TradingParameters:
    """Container for trading parameters"""
    no_such_parameter = 'Parameter not in set: '
    def __init__ (self, all_parameters):
        self.parameter_set  = set(all_parameters)   
    def setParameter(self, parameter, value):        
        if parameter in self.parameter_set:
            self.__dict__[parameter] = value
        else:
            print(parameter)
            raise no_such_parameter
    def getParameter(self, name):
        if name in self.parameter_set:
            return self.__dict__[name]
        else:
            print(name)
            raise no_such_parameter

class ATrade:
    def __init__(self, algoritme, parameter_name='empty'):
        """check aTestSimulator for algoritme properties """
        #self.quotes     = {}
        self.algoritme  = algoritme
        self.p          = TradingParameters(algoritme.parameterset)
        self.advices    = []
    def setParameters(self, parameters):
        for key in parameters.keys():
            self.p.setParameter(key, parameters[key])
    def arm_simulator(self):
        self.arm_algoritme()
    def arm_algoritme(self):
        self.algoritme.arm(self.p)
    def new_quote(self, q_time, quote, **vars):
        #self.quotes[q_time] = quote
        advice = self.algoritme.run(q_time, quote, **vars)
        if advice:
            self.advices.append(advice)
        return advice
    def new_bar(self, bar, **vars):
        advice = self.algoritme.run(bar)
        if advice:
            self.advices.append(advice)
        return advice
    def getSimulatorParameter(self, parameter_name):
        self.getAlgoritmeParameter(parameter_name)
    def getAlgoritmeParameter(self, parameter_name):
        return self.algoritme.__dict__[parameter_name]
    def info (self, search_for):
        if search_for == 'simulator_CSV_trade_list':
            answer =  self.algoritme.make_csv_trade_file()
        if search_for == 'eop_proc':
            answer = self.algoritme.eop_proc()
        if search_for == 'restart_traders':
            answer = self.algoritme.restart_traders()
        return answer
    def run_procedure(self, procedure):
        self.info(procedure)
    def send_info(self, info_name, info_value=None):
        self.algoritme.send_info(info_name, info_value)
    def save(self,filename=None):
        if not filename:
            filename = '.'.join([self.algoritme.full_name, 'pickle'])
        with open(filename, 'wb') as ofh:
            pickle.dump(self, ofh)
