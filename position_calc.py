#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)

from collections import namedtuple

import mypy
import pickle

import swing_performance_array

PICKLE_LOCATION = mypy.TMP_LOCATION
spa_result = namedtuple('spa_result', 'target percentage size profit '
                                      'maxloss rpr rrpr histres')

class SPA_Result(spa_result):
    
    def __str__(self):
        op = ('target: {7.2f}\n'
              'percentage: {:7.2%}\n'
              'size: {:7.2f}\n'
              'profit: {:7.2f}\n'
              'max loss: {:7.2f}\n'
              'rpr: {:7.2f}\n'
              'rrpr: {:7.2f}\n'
              'histres: {:7.2f}'.format(self.target,
                                        self.percentage,
                                        self.size,
                                        self.profit,
                                        self.maxloss,
                                        self.rpr,
                                        self.rrpr,
                                        self.histres))
        return op

class PositionCalculator():
    
    def __init__(self, 
                 spa_list=[], #spa or filename of an spa
                 spa_levels = [],
                 good_advices = {}#levels to use for spa calc
                 ):
        self.spa = {}
        for spa in spa_list:
            if isinstance(spa, str):
                spa = swing_performance_array.SwingPerformanceArray(load=spa)
            self.spa[spa.name] = spa
        self.spa_levels = spa_levels
        self.good_advices = good_advices
        #for testing, try to make it useless
        self.good_advices['4to5_0'] = 0.63
        self.good_advices['2to3_0'] = 0.82
        self.good_advices['4to5_4'] = 0.32
        self.good_advices['2to3_2'] = 0.61
        
        
        
    def single_spa_result(self,
                          spa_id, row_id, 
                          entry, swing_start, stop,
                          percentage, advice_type='4to5'):
        spa = self.spa[spa_id]
        max_loss = mypy.delta(entry, stop)
        exp_perc, exp_size = spa.data_for_percentage_at_level(
                                                   row_id, percentage)
        exp_perc *= self.good_advices[advice_type]
        exp_profit = exp_size - max_loss
        if entry > swing_start:
            target = swing_start + exp_size
        else:
            target = swing_start - exp_size
        rpr = exp_profit / max_loss
        rrpr = rpr * exp_perc
        histres = exp_perc * exp_profit + (exp_perc - 1) * max_loss
        return SPA_Result(target, exp_perc, exp_size, exp_profit,
                          max_loss, rpr, rrpr, histres)
    
    def loop_spa_levels(self,
                        spa_id, row_id,
                        entry, swing_start, stop,
                        advice_type='4to5',
                        print_result=False):
        results = {}
        for percentage in self.spa_levels:
            results[percentage] = self.single_spa_result(spa_id, row_id, entry, 
                                                         swing_start, 
                                                         stop, 
                                                         percentage, 
                                                         advice_type)
        if print_result:
            self.print_spa_loop(results)        
        return results
            
    @staticmethod
    def print_spa_loop(results):
        nr_of_spas = len(results)
        perc_line = '{:14}' + nr_of_spas * ' | {:^7.0%}'
        header_u = '===============' + nr_of_spas * '========'
        std_line = '{:14}' + nr_of_spas * ' | {:7.2f}'
        data = {}
        data['header perc'] = []
        data['target'] = []
        data['profit'] = []
        data['real perc'] = []
        data['rpr'] = []
        data['rrpr'] = []
        data['histres'] = []
        for percentage in sorted(results.keys(), reverse=True):
            data['header perc'].append(percentage)
            data['target'].append(results[percentage].target)
            data['profit'].append(results[percentage].profit)
            data['real perc'].append(results[percentage].percentage)
            data['rpr'].append(results[percentage].rpr)
            data['rrpr'].append(results[percentage].rrpr)
            data['histres'].append(results[percentage].histres) 
        for line_name in ['header perc', 'v_line',
                          'real perc', 'target', 'profit', 
                          'rpr', 'rrpr', 'histres']:
            if line_name == 'v_line':
                print(header_u)
                continue
            line = perc_line if 'perc' in line_name else std_line
            print(line.format(line_name, *data[line_name]))
        
                
        return results