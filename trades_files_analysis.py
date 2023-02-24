#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import glob
import os
import csv

import mypy
import mycsv

def main():
    #mypy.get_string('Directory: ')
    underlying_ = mypy.get_string('underlying: ', default='EUR')
    start_date = mypy.get_date('start (yyyy/mm/dd): ', format_='%Y/%m/%d',
                               default='2010/1/1')
    directory = '/home/rolcam/roce/tmp/Trades'
    all_files = os.path.join(directory, '*')
    trades = {'BOT': [], 'SLD': []}
    avvv, avv, av, a = None, None, None, None
    position = 0
    result = 0
    actions =[['date_and_time', 'position', 'gap', 'result']]
    for file in sorted(glob.glob(all_files)):
        file_content = csv.DictReader(open(file))
        for line in file_content:
            try:
                underlying = line['Underlying']
                date_and_time = ' '.join([line['Date'], line['Time']])
                quantity = int(line['Quantity'])
                price = float(line['Price'])
                action = line['Action']
            except:
                print('problem reading data from file {}, check file!'.
                      format(file))
                print(line.keys())
                raise
            if not underlying == underlying_:
                continue
            direction = '>>>'
            date_and_time = mypy.py_date_time(date_and_time,
                                              '%Y%m%d %H:%M:%S')
            avvv, avv, av, a = avv, av, a, date_and_time
            if avvv == avv == av == a:                
                print('timing problem data from file {}, check file!'.
                      format(file))
                print(avvv, avv, av, a)
                exit()
            if date_and_time < start_date:
                break
            trades[action].append((quantity, price))
            while not len(trades['BOT']) == 0 and not len(trades['SLD']) == 0:
                direction = '<<<'
                old_result = result
                bot, sld = trades['BOT'].pop(), trades['SLD'].pop()
                bot_quant, bot_price = bot
                sld_quant, sld_price = sld
                if bot_quant == sld_quant:
                    result += bot_quant * (sld_price - bot_price)
                    print(bot_quant, bot_price, sld_price)
                if bot_quant < sld_quant:
                    result += bot_quant * (sld_price - bot_price)
                    trades['SLD'].append((sld_quant-bot_quant, sld_price))
                    print(sld_quant-bot_quant, bot_price, sld_price)
                if sld_quant < bot_quant:
                    result += sld_quant * (sld_price - bot_price)
                    trades['BOT'].append((bot_quant-sld_quant, bot_price))
                    print(bot_quant-sld_quant, bot_price, sld_price)
            if len(trades['BOT']) > 0:
                #print('xs in bot', trades['BOT'])
                position = sum([x[0] for x in trades['BOT']])
            else:
                #print('xs in bot', trades['SLD'])
                position = -sum([x[0] for x in trades['SLD']])
            print('{}{} {:8} {:10}'.format(direction, date_and_time, 
                                           position, result))
            if direction == '<<<':
                actions.append([date_and_time, position, 
                                result-old_result, result])
                
            
        #mypy.get_bool(file+' processed, hit enter', default=True)
    file = mycsv.table2csv(actions, file_name='tfa.cvs')
    
        
    

if __name__ == '__main__':
    main()