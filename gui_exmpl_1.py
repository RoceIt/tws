#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import guitkinter as gui
import guivars as g

def main():
    app = gui.Application()
    app.mode = gui.TEST_MODE
    app.window_title = 'Simple Sum'
    a = g.Integer()
    a.default = 0
    b = g.Integer()
    b.default = 0
    c = g.Float()
    c.default = 1.0
    d = g.String()
    d.default = 'hond'
    e = g.Integer()
    
    result = g.Integer()
    result.result_function(sum, a, b)
    result.auto_calculate_on_new(a, b)
    
    read_a = gui.ReadZone(a, 'a: ')
    read_b = gui.ReadZone(b, 'b: ')
    read_c = gui.ReadZone(c, 'foo: ')
    read_d = gui.ReadZone(d, 'some text: ')
    write_result = gui.WriteZone(result, 'result: ')
    write_d = gui.WriteZone(d, 'Your text: ')
    write_e = gui.WriteZone(e, 'a number:')
    list_selector1 = gui.SelectFromListZone(d, ['aap', 'beer'], 'select')
    list_selector2 = gui.SelectFromListZone(e, [1, 2], 'select number')
    
    #app.grid=[[read_a],
              #[read_b],
              #[write_result]]    
    app.grid=[[read_a, read_b],
              [read_c],
              [write_result],
              [read_d, write_d, list_selector1],
              [list_selector2, write_e]]
    
    app.start()
    
    
def sum(a, b):
    if not(a == None or b == None):
        print('in som ({} + {}) = {}'.format(a, b, a+b))
        return a + b

if __name__ == '__main__':
    main()