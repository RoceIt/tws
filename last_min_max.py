#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import marketdata

UP = 1
DOWN = 2

class LastMinMax():
    def __init__(self):
        ###
        self.new_max = self.new_min = False
        self.direction = None
        
    def insert_next_bar(self, a_bar):
        ###
        self.curr_max, self.curr_min = a_bar.high, a_bar.low
        ###
        if self.direction is UP:
            self.insert_bar_in_up_move()
        elif self.direction is DOWN:
            self.insert_bar_in_down_move()
        else:
            self.first_bar()
            
    ###intern
           
    def first_bar(self):
        self.running_max = self.last_max = self.curr_max
        self.running_min = self.last_min = self.curr_min
        self.direction = UP    

    def insert_bar_in_up_move(self):
        if self.curr_max > self.last_max:
            if self.new_min:
                self.last_min = self.running_min
            self.last_max = self.running_max = self.curr_max
            self.running_min = self.curr_min
            self.new_min = False
        if self.curr_min >= self.running_min:
            return
        if self.curr_min < self.last_min:
            self.direction = DOWN
            self.insert_bar_in_down_move()
        self.running_min = self.curr_min
        self.new_min = True
            
    def insert_bar_in_down_move(self):
        if self.curr_min < self.last_min:
            if self.new_max:
                self.last_max = self.running_max
            self.last_min = self.running_min = self.curr_min
            self.running_max = self.curr_max
            self.new_max = False
        if self.curr_max <= self.running_max:
            return
        if self.curr_max > self.last_max:
            self.direction = UP
            self.insert_bar_in_up_move()
        self.running_max = self.curr_max
        self.new_max = True
        