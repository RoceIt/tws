#!/usr/bin/env python3

from time import sleep
import pickle
import os

import mypy
#import TWSClientServerMessages as M

    
contract = mypy.get_string('contract name:')
filename = os.path.join(mypy.TMP_LOCATION, contract+'.data')
with open(filename, 'rb') as ifh:
    while True:
        try:
            lp = pickle.load(ifh)
            print(lp)
        except EOFError:
            sleep(0.5)
    
