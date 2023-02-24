#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''This module provides a class 'You can add conditions to, 
conditions are functions that return True or False
And action to take if ...
'''

from collections import namedtuple 

Condition = namedtuple('Condition', 'condition data')

class Rule():
    '''You can add conditions to this class, functions that return True or False
    and if they are all True the action list returned
    '''        
    
    def __init__(self):
        self.conditions = []
        self.actions = []
        self.remove = False

    def __str__(self):
        output = 'R: ' if self.remove else '-> '
        for cond in self.conditions:
            val = [v for k, v in cond.data.items()]
            if len(val) == 0:
                d = ''
            elif len(val)== 1:
                d = str(val[0])
            else:
                d = ' and '.join([str(val[0]), str(val[1:])])
            output = ' '.join([output, cond.condition.__name__, d])
        output += '\n'
        for action in self.actions:
            
            output += ''.join(['----->',
                               str(action.action),
                               str(action.data),
                               '\n'])
        return output

    def add_condition(self, condition):
        self.conditions.append(condition)

    def get_condition(self, position=0):
        if len(self.conditions) > position:
            return self.conditions[position]
        else:
            return None
        

    def add_action(self, action):
        self.actions.append(action)

    def is_true(self, **data):
        for cond in self.conditions:
            full_data = dict(cond.data.items() | data.items())
            if self.remove or not cond.condition(**full_data) == True:
                return False
        else:
            return self.actions      

    def flag_remove(self):
        self.remove = True

    def remove_set(self):
        return self.remove

    def suspend(self):
        if self.remove == False:
            self.remove = 'SUSPEND'
            return True
        return False

    def reactivate_suspend(self):
        if self.remove == 'SUSPEND':
            self.remove = False
            return True
        return False
