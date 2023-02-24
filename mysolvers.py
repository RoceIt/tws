#!/usr/bin/env python3

#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import mypy

class SolverError(Exception): pass
class NoSolution(SolverError): pass

def solve_to_x_1u(function, y, start, stop, step=1, depth=1, verbose=False):
    
    prev_y = function(start)
    prev_x = start
    for x in mypy.f_range(start, stop, step):
        y_for_x = function(x)
        if (prev_y - y) * (y_for_x - y) <= 0:
            break
        prev_y, prev_x = y_for_x, x    
    else:
        raise NoSolution('interval did not cross y value')
    if prev_y == y:
        answer = prev_x
    elif y_for_x == y:
        answer = x
    else:        
        if abs(prev_y - y) <= abs(y_for_x - y):
            answer = prev_x
        else:
            answer = x
        if not depth == 1:
            start = x - step
            step = step / 10
            stop = x + step
            depth -= 1
            try:
                answer = solve_to_x_1u(function, y, start,stop, step, depth)
            except NoSolution:
                pass
    return answer

def solve_to_min_1u(function, start=50,step=1, depth=1,
                    min_range=-1000000, max_range=1000000):
    
    if step > 0:
        if function(start) > function(start+step):
            start, stop, step = start, max_range, step
        else:
            start, stop, step = start, min_range, -step
    elif step < 0:
        if function(start) > function(start+step):
            start, stop, step = start, min_range, step
        else:            
            start, stop, step = start, max_range, -step
    #print(start,stop,step)
            
    prev_y = function(start)
    prev_x = start
    for x in mypy.f_range(start+step, stop-step, step):
        y_for_x = function(x)
        #print(y_for_x, prev_y)
        if prev_y <= y_for_x :
            break
        prev_y, prev_x = y_for_x, x    
    else:
        raise NoSolution('value did not reverse in interval')
    if depth == 1:
        if function(x) < function(x-step):
            answer = x
        else:
            answer = x-step
    else:
        start = x
        step = step / 10
        depth -= 1
        answer = solve_to_min_1u(function, start, step, depth,
                                 min_range, max_range)
    return answer