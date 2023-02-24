#!/usr/bin/env python3

fibVal = input('Fib retracement value: ')
fibVal = float(fibVal)
while 1:
    a = input('A: ')
    b = input('B: ')
    if a == 's' or b == 's':
        break
    a = float(a)
    b = float(b)
    #try:
    print('{:n} fib retracement is {:n}'.format(fibVal, a+(b-a)*fibVal/100))
    #except: TypeError:
    #    pass
