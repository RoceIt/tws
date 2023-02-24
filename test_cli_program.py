#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

from sys import argv
import subprocess

program, testinput = argv[1], argv[2]

with open(testinput, 'rb') as inf:
    subprocess.call(program, stdin=inf)


