#!/usr/bin/env python3

#  FILENAME: historicaldata.py

#  Copyright (c) 2010, 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)

import os.path
import sys
from optparse import OptionParser
from datetime import datetime, timedelta
from time import sleep
from operator import attrgetter

import mypy
import roc_input as r_in
import sql_ib_db #import sql_IB_db
import TWSClient
import twsclientapps

import tws as Broker

class HistoricalDataError(Exception): pass
class NotImplemented(HistoricalDataError):pass
class ArgumentError(HistoricalDataError): pass
class DataNotAvailable(HistoricalDataError): pass

CLIENT_ID = 9   ## terugzetten naar 10!
IP = 'localhost' #'10.1.1.102'
PORT = 10911

DB_LOCATION = mypy.DB_LOCATION

def main():
    if len(sys.argv) == 1:
        interactive()
        exit()
    usage = 'Usage: %prog [options] IBcontractName'
    parser = OptionParser(usage=usage)
    #parser.add_option('-f', '--file', 
                      #dest='filename', default=False,
                      #help='Write output to FILE', metavar='FILE')
    parser.add_option('-d', '--barsize',
                      choices=list(Broker.rhd_bar_sizes),
                      default='1 day',
                      help='check Broker.rhd_bar_sizes for valid strings', 
                      metavar='BARSIZE')
    parser.add_option('-b', '--begin',
                      default=None,
                      help='set start date', metavar='YYYY/MM/DD HH:MM:SS')
    parser.add_option('-e', '--end',
                      default=datetime.now().strftime(mypy.DATE_TIME_STR),
                      help='set end date', metavar='YYYY/MM/DD HH:MM:SS')
    parser.add_option('-s', '--show',
                      choices=list(Broker.rhd_what_to_show),
                      default='TRADES',
                      help='check Broker.rhd_what_to_show for valid strings',
                      metavar='WHAT_TO_SHOW')
    (opts, args) = parser.parse_args()
    if len(args) != 1:
        print('Missing arguments, use historicaldta.py --help for info')
        return 'wrong number of arguments'
    contract_name = args[0]
    contract = Broker.contract_data(contract_name)
    print(opts.end)
    try:
        end_time = mypy.py_date_time(opts.end)
    except ValueError:
        print('end date, wrong format use YYYY/MM/DD HH:MM:SS')
        return
    if opts.begin:
        try:
            start_time = mypy.py_date_time(opts.begin)
        except ValueError:
            print('start date, wrong format use YYYY/MM/DD HH:MM:SS')
            return
    else:
        start_time = None    
    ip = mypy.get_string('ip ({})'.format(IP),
                         default=IP)
    client_id = mypy.get_int('client id ({})'.format(CLIENT_ID),
                             default=CLIENT_ID)
    try:
        historical_data(contract, end_time, start_time, opts.barsize,
                        opts.show, False, #opts.filename,
                        host_ip=ip, client_id=client_id,
                        verbose=True)
    except Broker.ContractNotInDB as err:
        print('Contract {} not in db'.format(err))
        
def interactive():
    twss = twsclientapps.set_up_tws_connection(client_id=CLIENT_ID,
                                               confirm=['host_ip', 'port_nr'])
    while True:
        contract = twsclientapps.select_contract(twss)
        if contract[0] == False:
            print(contract[1])
            continue
        barsize = mypy.get_from_list(list(Broker.rhd_bar_sizes), 'Select barsize')
        show = mypy.get_from_list(list(Broker.rhd_what_to_show), 'Select data')
        rth = not mypy.get_bool('Data outside regular trading hours (Y/n): ',
                                default=True)
        update = mypy.get_bool('Update existing db (y/N)? ', default=False)
        if update:
            start_date = ''
            end_date = mypy.now()
        else:
            mess = 'Start date, empty is last 32 days: '
            start_date = mypy.get_date(mess, empty=True)
            mess = 'End date, empty is current time: '
            #end_date = mypy.get_date(mess, default=str(mypy.now()))
            end_date = r_in.get_datetime(
                mess,
                time_format='%Y-%m-%d %H:%M:%S',
                default=str(mypy.now().strftime('%Y-%m-%d %H:%M:%S')))
        historical_data_to_db(contract.summary, end_date, start_date, barsize, 
                              show, rth, twss=twss, verbose=True,
                              update=update)
        if not mypy.get_bool('new request (Y/n)', default=True):
            break
    twss.close()
    
                           
def historical_data(contract, 
                    end_time = datetime.now(),
                    start_time = None,
                    barsize = '1 day',
                    show = 'TRADES',
                    rth = False,
                    host_ip=IP,
                    client_port=PORT,
                    client_id=CLIENT_ID,
                    twss = False,
                    verbose=False):
    '''returns a list of HistoricalData tuples
    
    
    '''  
    assert isinstance(contract, Broker.contract)
    if not twss:
        twss = TWSClient.TWSconnection(host_ip, client_port, client_id)
        local_twss = True
    else: local_twss = False
    max_historical_date = (mypy.now() - Broker.rhd_MAX_LOOKBACK).date()
    if not start_time:
        start_time = end_time - timedelta(days=32)
    if start_time > end_time:
        raise ArgumentError('end time is before start time')
    request_size = Broker.rhd_max_req_period[barsize][0]
    request_timedelta = Broker.rhd_max_req_period[barsize][1]
    received_data = []
    while end_time > start_time:
        # check and initialise parameters
        # Send historical request to Broker Interface
        if verbose: print('requesting data')
        next_reqeust_ok = twss.hist_data_request_manager.request_allowed()
        if not next_reqeust_ok is True:
            print('Too many requests in 10 minuter waiting for {} seconds'.
                  format(next_reqeust_ok))
            sleep(next_reqeust_ok)
        data_id = twss.req_historical_data(contract, end_time,  
                                           request_size,
                                           barsize,
                                           show,
                                           rth)
        if verbose: print('Waiting for an answer: ')
        while True:
            data = None
            try:
                data = twss.get_historical_request_data(data_id)
            except (TWSClient.ReceivingData, TWSClient.RequestSended):
                continue
            except TWSClient.PacingViolation:
                if verbose:
                    print('Pacing violation, waiting 90 secs to resend request')
                sleep(90)
                break
            except TWSClient.ExceededMaxLookback:
                request_size = reduce_request_size(request_size)
                break
            except TWSClient.QueryReturnedNoData:
                if not received_data and verbose:
                    received_data = 'checked'
                    mess = 'No data found, look further back (Y/n)?'
                    if not mypy.get_bool(mess, default=True):
                        return []
                if received_data == 'checked':
                    print('previous end time: {}'.format(end_time))
                    end_time = end_time - look_back_corr(request_size)
                    if verbose:
                        print('new end time: {}'.format(end_time))
                    received_data = []
                    break                
                if verbose:
                    print('no (more) data available')
                    print(contract, end_time,  
                                           request_size,
                                           barsize,
                                           show,
                                           rth)
                return received_data
            except TWSClient.RequestError as err:                
                if verbose: 
                    print(err)
                    retry = mypy.get_bool('New request to TWS? ')
                if retry == True:
                    break
                else:
                    return received_data
            else:
                break
        if data == None:            
            if end_time.date() == max_historical_date:
                if verbose:
                    print('max request date reached')
            elif request_size == None:
                if verbose:
                    print('duration reached zero, check it')
            else:
                continue
            return received_data
        if verbose: 
            print('last data pack: {} / {}'.format(data[0].date_, 
                                                           data[-1].date_))
            print('                {} new records'.format(len(data)))
        data.sort(key=attrgetter('date_'))
        data.extend(received_data)
        first_entry = data[0].date_ - timedelta(seconds=1) - request_timedelta
        received_data = data
        end_time = first_entry
    if local_twss: twss.disconnect()
    return received_data

    
#def make_historical_make_historical_db_namedb_name(contract):
    
    #assert isinstance(contract, Broker.contract)
    #ell = [contract.symbol.upper()]
    #ell.append(contract.secType)
    #if contract.right in ['C', 'P']:
        #ell.append('{}_{}'.format(contract.right, contract.strike))
    #if contract.multiplier:
        #ell.append('X{}'.format(contract.multiplier))
    #if contract.expiry:
        #ell.append(contract.expiry)
    #ell.append(contract.currency)
    #ell.append('{}@{}'.format(contract.localSymbol,contract.exchange))
    #return '.'make_historical_db_name.join([' '.join(ell),'db'])

def reduce_request_size(rs):
        
    #global request_size
    number, unit = rs.split()
    if unit == 'S':
        number = '1800'
    elif int(number) > 1:
        number = '1'
    elif unit in ['W', 'M', 'Y']:
        unit = 'D'
    else:
        return None
    rs = ' '.join([number, unit])
    print ('new rs: {}'.format(rs))
    return rs

def look_back_corr(rs):
    
    number, unit = rs.split()
    if unit == 'S':
        lbc = timedelta(days=1)
    elif unit == 'D':
        lbc = timedelta(days=int(number))
    elif unit == 'W':
        lbc = timedelta(days=7*int(number))
    elif unit == 'Y':
        lbc = timedelta(days=365*int(number))
    else:
        err_mess = 'correcting lookback for {} not defined'.format(unit)
        raise NotImplemented(err_mess)
    return lbc

def last_entry_datetime(db_name,table_name, db_path=DB_LOCATION):
    dbh = sql_ib_db.HistoricalDatabase(db_name, db_path)
    led = dbh.last_entry_date_time(table_name)
    dbh.close()
    return led
    
def historical_data_to_db(contract, 
                          end_time=datetime.now(),
                          start_time=None,
                          barsize='1 day',
                          show='TRADES',
                          rth=False,
                          db_name=False,
                          db_path=DB_LOCATION, 
                          host_ip=IP,
                          client_port=PORT,
                          client_id=CLIENT_ID,
                          twss = False,
                          verbose=False,
                          update=False):
    '''requests the historical data and writes it into a db'''
    
    if isinstance(contract, str):
        cntr_data =Broker.contract_data(contract)._asdict()
        broker_contract = twsclientapps.select_contract(twss, 
                                                        **cntr_data).summary
    else:
        broker_contract = contract
    assert isinstance(contract, Broker.contract)
    contract_db_name = sql_ib_db.make_historical_db_name(broker_contract)
    if not db_name:
        db_name = contract_db_name
    if verbose:
        print('db_name: {}'.format(db_name))
    table_name = sql_ib_db.make_table_name(show, barsize)
    if update:
        try:
            start_time = last_entry_datetime(db_name, table_name,db_path)
        except (sql_ib_db.DBNotFound, sql_ib_db.TableNotFound):
            mess = 'Could not find existing data, create a new db/table (Y/n)? '
            if verbose and mypy.get_bool(mess, default=True):
                start_time=None
            else:
                raise
    if verbose:
        print('requesting data from {} until {}'.format(start_time, end_time))
        
    data = historical_data(broker_contract, end_time, start_time, barsize,
                           show, rth, host_ip, client_port, client_id, twss,
                           verbose)
    dbh = sql_ib_db.HistoricalDatabase(db_name, db_path, create=True)
    if not dbh.table_exists(table_name):
        dbh.add_table(table_name)
    if verbose:
        print('writing data to db')
    for line in data:
        dbh.insert_record(table_name, sql_ib_db.Record(*line[1:]))
    dbh.commit()
    dbh.close()    
    
def historical_data_from_db(db_name=False,
                            contract=None,
                            end_time=datetime.now(),
                            start_time=None,
                            lookback=Broker.rhd_MAX_LOOKBACK,
                            barsize='1 day',
                            show='TRADES',
                            rth=False,
                            db_path=DB_LOCATION, ##change to real db_location
                            host_ip=None,
                            client_port=None,
                            client_id=None,
                            twss = False,
                            verbose=False):
    t = sql_ib_db.make_historical_db_name(contract) if contract else None
    if contract and not t == db_name:
        db_name = t
        if verbose:
            print('Changed db name to std db name for contract: {}'.
                  format(db_name))
    if verbose:
        print('end time: {}'.format(end_time))
    if not start_time:
        start_time = end_time - lookback
        if verbose:
            print('set start time to {}'.format(start_time))
    elif verbose:
        print('start time: {}'.format(start_time))
    table_name = sql_ib_db.make_table_name(show, barsize)
    if not db_data_available(db_name, table_name, start_time, end_time):
        if host_ip:
            try:
                twss = twsclientapps.set_up_tws_connection(
                    host_ip, client_port, client_id)
            except twsclientapps.AppFailed:
                twss = None           
        if twsclientapps.active_tws_available(twss=twss):
            download_not_available_data(contract, db_name, db_path,
                                        start_time, end_time,
                                        barsize, show,
                                        twss, verbose)
        else:
            if verbose:
                print('not all data in db, can not upload becaus no active tws')
    try:
        db_h = sql_ib_db.HistoricalDatabase(db_name, db_path)
    except sql_ib_db.DBNotFound:
        print('na db found')
        return []
    interval_dates = db_h.get_dates(table_name, start_time, end_time)
    data = []
    for date in interval_dates:
        print('reading data for date {}'.format(date))
        data += db_h.get_data_on_date(table_name, date,
                                      'datetime', 'open', 'high', 'low',
                                      'close', 'volume', 'counts', 'wap',
                                      'hasgaps')
    return data

def db_data_available(db_name, table_name, first, last=None,
                      db_path=DB_LOCATION):
    last = last or first
    try:
        hdb_h = sql_ib_db.HistoricalDatabase(db_name, db_path)
    except sql_ib_db.DBNotFound:
        return False
    if (hdb_h.table_exists(table_name) and
        hdb_h.first_entry_date_time(table_name) <= first and
        hdb_h.last_entry_date_time(table_name) >= last):
        answer = True
    else:
        answer = False
    hdb_h.close()
    return answer

def download_not_available_data(contract, db_name, db_path,
                                start_time, end_time, 
                                barsize, show,
                                twss, verbose):  
    table_name = sql_ib_db.make_table_name(show, barsize)
    try:
        hdb_h = sql_ib_db.HistoricalDatabase(db_name, db_path)  
        first_db_date = hdb_h.first_entry_date_time(table_name)
    except (sql_ib_db.DBNotFound, sql_ib_db.TableNotFound):
        if not verbose or mypy.get_bool(
              'can not find historical db, create it?'):
            print('creating historical db')
            historical_data_to_db(contract,
                                  end_time, start_time,
                                  barsize, show,
                                  db_name=db_name,
                                  twss=twss,
                                  verbose=verbose)
            return
        else:
            raise
    
    #table_name = sql_ib_db.make_table_name(show, barsize)
    #first_db_date = hdb_h.first_entry_date_time(table_name)
    last_db_date = hdb_h.last_entry_date_time(table_name)
    if verbose:
        print('start db {} |start req {}'.format(first_db_date, start_time))
        print('end db {} | last req {}'.format(last_db_date, end_time))
    if verbose and not mypy.get_bool('continue?'):
        raise
    if start_time < first_db_date:
        if verbose:
            print('extending oldest db data')
            if not mypy.get_bool('continue?'):
                raise
        historical_data_to_db(contract,
                              first_db_date, start_time,
                              barsize, show,
                              db_name=db_name,
                              twss=twss,
                              verbose=verbose)        
    if end_time > last_db_date:
        if verbose:
            print('extending new db data')
            if not mypy.get_bool('continue?'):
                raise
        historical_data_to_db(contract,
                              end_time, last_db_date,
                              barsize, show,
                              db_name=db_name,
                              twss=twss,
                              verbose=verbose)
                                
if __name__ == '__main__':
    main()
