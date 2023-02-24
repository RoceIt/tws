#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''talk with a running TWSClient thrue a backdoor file'''

import sys
from time import sleep

import mypy
import TWSClient

EOA = '###EOA###'
STOP = '###STOP###'

STANDARD_LIST = 1
ERROR_LIST = 2
OPEN_ORDERS = 3
EXECUTED_ORDERS = 4
ORDER_STATUS = 5
EXIT = -1

OPTIONS = [' 1: Standard List',
           ' 2: Error List',
           ' 3: Open Orders',
           ' 4: Executed Orders',
           ' 5: Order Status',
           '-1: Stop']

def main():
    
    comm_file = sys.argv[-1]
    peek(comm_file)

def create_info_backdoor(comm_file,
                         std_mess_list,
                         err_list,
                         current_time,
                         next_order_id,
                         open_orders_completed,
                         open_orders,
                         order_status,
                         executed_orders,
                         requested_info,
                         accounts,
                         portfolio,
                         tick_data,
                         real_bars):
    '''reads commands from comm_file and output goes to
    the file comm_file.twi'''
    output_file = '.'.join([comm_file, 'twi'])
    open(comm_file, 'w').close()
    with open(comm_file, 'r') as ifh, open(output_file, 'w') as ofh:
        while True:
            request = int(mypy.get_line_from_file(ifh))
            if request == STANDARD_LIST:
                mypy.print_list(std_mess_list, 'STANDARD LIST', file_=ofh)
            elif request == ERROR_LIST:
                mypy.print_list(err_list, 'ERROR LIST', file_=ofh)
            elif request == OPEN_ORDERS:
                mypy.print_dict(open_orders, 'OPEN ORDERDER', file_=ofh)
            elif request == EXECUTED_ORDERS:
                mypy.print_dict(executed_orders, 'EXECUTED ORDERS', file_=ofh)
            elif request == ORDER_STATUS:
                mypy.print_dict(order_status, 'ORDER STATUS', file_=ofh)
            if request == EXIT:
                print(STOP+'\n', file=ofh)
            else:
                print(EOA, file=ofh)
            ofh.flush()
            
def peek(comm_file):
    '''Asks for user input and displays requested info'''  
    answer_file = '.'.join([comm_file, 'twi'])
    with open(comm_file, 'a') as ofh, open(answer_file, 'r') as ifh:
        while True:
            mypy.print_list(OPTIONS)
            request = mypy.get_int('show: ')
            ofh.write(str(request)+'\n')
            ofh.flush()
            answer = 'message sent'
            while not answer == EOA:
                print(answer)
                answer = mypy.get_line_from_file(ifh).rstrip()
                if answer == STOP:
                    break
            if answer == STOP:
                break

if __name__ == '__main__':
    main()
