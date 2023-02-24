#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)
#
#  license: GNU GPLv3
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.

'''
Make a file with the daydata of the contract
'''

import tws
import mypy
import os.path
import io
import twsR as tws_interface # tws_interface is placeholder
from optparse import OptionParser
from datetime import datetime, timedelta

###
#Change these while programming to avoid dataloss on db
###
db_PATH = mypy.dblocation   #change to '' so db file is created in .

def main():
    usage = 'Usage: %prog [options] IBcontractName'
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--file', 
                      dest='filename', default=False,
                      help='Write output to FILE', metavar='FILE')
    #parser.add_option('-d', '--barsize',
    #                  choices=list(tws.rhd_bar_sizes),
    #                  default='1 day',
    #                  help='check tws.rhd_bar_sizes for valid strings', metavar='BARSIZE')
    #parser.add_option('-b', '--begin',
    #                  default='',
    #                  help='set start date', metavar='YYYY/MM/DD HH:MM:SS')
    #parser.add_option('-e', '--end',
    #                  default=datetime.now().strftime(mypy.stdDateTimeStr),
    #                  help='set end date', metavar='YYYY/MM/DD HH:MM:SS')
    parser.add_option('-s', '--show',
                      choices=list(tws.rhd_what_to_show),
                      default='TRADES',
                      help='check tws.rhd_what_to_show for valid strings', metavar='WHAT_TO_SHOW')
    (opts, args) = parser.parse_args()
    if len(args) != 1:
        print('probleem met argumenten, gebruik --help voor info')
        return 'wrong number of arguments'
    IBcontractName = args[0]
    print(opts.end)
    historicalData(IBcontractName, opts.end, opts.begin, opts.barsize, opts.show, opts.filename)

def historicalData(IBcontractName, 
                   end=datetime.now().strftime(mypy.stdDateTimeStr),
                   begin='',
                   barsize='1 day',
                   show='TRADES',
                   filename=False):
    # check contractname and load contract settings
    try:
        IBcontract = tws.IBcontracts[IBcontractName]
        print (IBcontract)
    except KeyError as err:
        print('Contract ', err, 'niet in contract db')
        print('gebruik ******* om gegevens in db te brengen')
        return 'wrong IB contract name'
    i_contract = tws_interface.setContract(IBcontract)
    print(i_contract)
    # check and set start and end time
    try:
        end_time = datetime.strptime(end, mypy.stdDateTimeStr)
    except ValueError:
        print('end date, verkeerd formaat. gebruik YYYY/MM/DD HH:MM:SS')
        return
    if begin == '':
        begin_time = end_time - timedelta(days=32)
        begin = begin_time.strftime(mypy.stdDateTimeStr)
    else:
        try:
            begin_time = datetime.strptime(begin, mypy.stdDateTimeStr)
        except ValueError:
            print('end date, verkeerd formaat. gebruik YYYY/MM/DD HH:MM:SS')
            return
    if begin_time > end_time:
        print('begintijd is groter dan eindtijd!')
        return
    # check barsize, set dateformat according to barsize
    if barsize in tws.rhd_intraday_bar_sizes:
        timeFormat = mypy.iso8601TimeStr
    elif barsize in tws.rhd_interval_bar_sizes:
        timeFormat = mypy.iso8601TimeStr[:8]
    else:
        print('geen geldige barsize opgegeven')
        return
    # open/create db eventualy set db filename
    if not filename:
        filename = IBcontractName+'.db'
    dblocation= db_PATH+filename
    dbTableName=  show+'_'+barsize.replace(' ','_')
    if not(os.path.exists(dblocation)):
        mypy.createDB(dblocation)
    mydb     = sqlite3.connect(dblocation)
    mydbCurs = mydb.cursor()
    mydbCurs.execute('CREATE TABLE IF NOT EXISTS {0} {1}'.format(dbTableName,
                                                                 mypy.tableDef_IBHist))
    db_insert_instruction = 'INSERT INTO {0} VALUES (?,?,?,?,?,?,?,?,?)'.format(dbTableName)
    tmpFileName = mypy.temp_file_name()   
    while end_time > begin_time:
        make_historical_request(i_contract, end_time, barsize,
                                tws.rhd_max_req_period[barsize][0],
                                whatToShow=show,
                                filename=tmpFileName)
        ioh = open(tmpFileName,'r')
        first_entry = mypy.py_time(ioh.readline().split(',')[0], timeFormat)
        ioh.seek(io.SEEK_SET)
        for line in ioh:
            items = line.split(',')
            items[0]= mypy.date_time2format(mypy.py_time(items[0], timeFormat),
                                       mypy.iso8601TimeStr)
            mydbCurs.execute(db_insert_instruction,tuple(items))
            #full_date = mypy.py_time(items[0], timeFormat)
            #print (full_date)
        ioh.close()
        mydb.commit()
        end_time = first_entry
    mydbCurs.close()
    mydb.close()
    mypy.rmTempFile(tmpFileName) 
        
        
        
#make_historical_request(contract)
    

    pass

def make_historical_request(contract, end, barsize, max_period, whatToShow, filename):
    tws.get_req_hist_slot(contract, end, barsize, max_period, whatToShow)
    request = tws_interface.program()
    request.add_instruction(contract.to_variable('contract'))
    request.add_instruction(tws_interface.reqHistoricalData('contract',
                                                            end, barsize,
                                                            max_period,
                                                            whatToShow=whatToShow,
                                                            filename=filename))
    request.run()

if __name__ == '__main__':
    main()
                      
