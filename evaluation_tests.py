#!/usr/bin/env python3
#
#  Copyright (c) 2014 Rolf Camps (rolf.camps@scarlet.be)
#

class StochMoves():
    
    # stochastic named situations
    A = 1 #'A'
    B = 2 #'B'
    GA = 3 #'GA'
    GB = 4 #'GB'
    A_TO_B = 'A to B'
    B_TO_A = 'B to A'
    
    def __init__(self, studie_name, foo):
        self.studie_name = studie_name
        self.name = self.make_name(self.studie_name)
        self.last_evaluation = {}
        
    @staticmethod
    def make_name(studie_name):
        return 'STOCH_AB_MOVES_FOR_{}'.format(studie_name)
        
    def extract_info(self, last_evaluation, previous_result_was_final):
        e = last_evaluation
        r = []
        if e is not None:
            #print(e)
            if e.stochastic_A:
                r.append(self.A)
            if e.stochastic_B:
                r.append(self.B)
            if e.ghost_A:
                r.append(self.GA)
            if e.ghost_B:
                r.append(self.GB)
        return r
    
    def moved_from_B_GB_to_A_GA(self, result_list, interval_bars, **kw_d):
        """Returns the negative index of the B-stoch event."""
        size = len(result_list)
        start_index = kw_d.pop('start', -1)
        if size > -start_index:
            last = result_list[start_index]
            if self.A in last or self.GA in last:
                for i in range(len(result_list) + start_index):
                    c = result_list[-i - 1 + start_index]
                    if not c:
                        continue
                    if self.B in c or self.GB in c:
                        return -i - 1 + start_index
                    return False # if c is self.A or self.GA
        return False
    
    def moved_from_A_GA_to_B_GB(self, result_list, interval_bars, **kw_d):
        """Returns the negative index of the A-stoch event."""
        size = len(result_list)
        start_index = kw_d.pop('start', -1)
        if (size > -start_index):
            last = result_list[start_index]
            if self.B in last or self.GB in last:
                for i in range(size + start_index):
                    c = result_list[-i - 1 + start_index]
                    if not c:
                        continue
                    if self.A in c or self.GA in c:
                        return - i - 1 + start_index
                    return False # if c is self.B or self.GB
        return False
    
    def last_stoch_move(self, result_list, interval_bars):
        """Returns a lot of information about the last move
        
        move, start_index, stop_index, start_value, stop_value
        """
        size = len(result_list)
        last_move = start_index = None
        if (size > 1):
            for i in range(size - 1):
                start_index = self.moved_from_B_GB_to_A_GA(
                    result_list, interval_bars, start=-i)
                if start_index:
                    last_move = self.B_TO_A
                else:
                    start_index = self.moved_from_A_GA_to_B_GB(
                    result_list, interval_bars, start=-i)
                    if start_index:
                        last_move = self.A_TO_B
                    else:
                        continue
                break
        stop_index = -i if last_move else  None
        return last_move, start_index, stop_index