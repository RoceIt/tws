#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)
#

"""

this program should write all data from the input to the file
and flush directly
"""

import sys

check_arguments = len(sys.argv)
if check_arguments == 2:
    output_file = sys.argv[1]
elif check_arguments < 2:
    output_file = 'out.txt'
else:
    print('{} needs maximum 1 argument, the filename.\n'
          'If no argument is given\n'
          'data is written to \'out.txt\''.format(sys.argv[0]))

with open(output_file, 'a') as ofh:
    while 1:
        try:
            text_line = input()
            print(text_line, file=ofh)
            ofh.flush()
        except EOFError:
            break


