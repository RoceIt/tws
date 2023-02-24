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

"""
This is "mypy" module

This module provides my own set of variables, functions and classes
"""

import sys
import urllib
import csv
import sqlite3
import tempfile
import os
from math import *
from time import mktime
from datetime import datetime, date, time
from collections import namedtuple
from subprocess import Popen

mydir          = '/home/rolcam/TraderZone/'
dblocation     = mydir+'Data/db/'
tmplocation    = mydir+'tmp/'
varlocation    = mydir+'var/' 
octavelocation = mydir+'bin/octave/'
stdDateStr     = '%Y/%m/%d'
stdTimeStr     = '%H:%M:%S'
iso8601TimeStr = '%Y-%m-%d %H:%M:%S'
stdDateTimeStr = stdDateStr+' '+stdTimeStr
octaveDateStr  = '%Y%m%d'

Advice = namedtuple('Advice', 'time action item reason')

class ColumnName:
    def __init__(self, provider='Yahoo'):
        if provider == 'Yahoo':
            self.date=0
            self.open=1
            self.high=2
            self.low=3
            self.close=4
            self.volume=5
            self.adjclose=6
        elif provider == 'Intraday_db':
            self.date='date'
            self.time='time'
            self.symbol='symbol'
            self.volume='volume'
            self.price='price'
        elif provider == 'IBdata':
            self.time=3
            self.open=4
            self.high=5
            self.low=6
            self.close=7
            self.volume=8
            self.wap=9
            self.count=10
        elif provider == 'IB_db':
            self.datetime='datetime'
            self.date='date(datetime)'
            self.time='time(datetime)'
            self.open='open'
            self.high='high'
            self.low='low'
            self.close='close'
            self.volume='volume'
            self.wap='wap'
            self.hasgaps='hasgaps'
            self.count='count'
        else:
            print('Oops in class Comumnname')



def url2str(url, code='utf8'):
    """
    Read a url, decode as 'code', return string
    """
    urlp=urllib.request.urlopen(url)
    byteread=urlp.read()
    urlp.close()
    return byteread.decode(code)

def octaveDate(date):
    """
    Returns octave date string from std date string
    """
    myDate=datetime.strptime(date, stdDateStr)
    return myDate.strftime(octaveDateStr)

def table2csv(table, columns, filename):
    """
    Writes columns(a list) from table to filename
    """
#    spamWriter = csv.writer(open('eggs.csv', 'w'), delimiter=' ',
#                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
#    spamWriter.writerow(['Spam'] * 5 + ['Baked Beans'])
#    spamWriter.writerow(['Spam', 'Lovely Spam', 'Wonderful Spam'])
    csvh=csv.writer(open(filename, 'w'), dialect='excel')
    for line in table:
        csvh.writerow([line[col] for col in columns])

###
# Input
###

def get_float(msg, 
              minimum = sys.float_info.min,
              maximum = sys.float_info.max,
              default=None):
    while True:
        try:
            line = input(msg)
            if not line and default is not None:
                return default
            f = float(line)
            if (f < minimum):
                print('number must be >=', minimum)
            elif (f > maximum):
                print('number must be <=', maximum)
            else:
                return f
        except ValueError as err:
            print(err)

###
# Output
###

def beep(signal):
    sound=dict(buy  ='-f 2500 -r 3 -n -f 2000 -r 3 -n -f 1500 -r 3',
               sell ='-f 2000 -r 3 -n -f 2500 -r 3 -n -f 2000 -r 3')
    Popen('beep '+sound[signal], shell=True)
    Popen('paplay --volume 50000 ../Sources/buy.wav', shell=True)
           

###
# Statistical
###

def mean(numbers):
    return fsum(numbers)/len(numbers)

def sumQuad(numbers):
    return fsum(ell**2 for ell in numbers)

def quadSum(numbers):
    return fsum(numbers)**2

def sumProd(numbers1, numbers2):
    return fsum([numbers1[i]*numbers2[i] for i in range(0,len(numbers1))])

def s_x_x(numbers):
    return sumQuad(numbers)-quadSum(numbers)/len(numbers)

def s_x_y(numbers1, numbers2):
    sum_prod = sumProd(numbers1, numbers2)
    return sum_prod-fsum(numbers1)*fsum(numbers2)/len(numbers1)
    
def variance(numbers):
    return s_x_x(numbers)/(len(numbers)-1)

def correlation(numbers1, numbers2):
    return s_x_y(numbers1, numbers2)/sqrt(s_x_x(numbers1)*s_x_x(numbers2))

def correlation_I(numbers2):
    return correlation(range(1,len(numbers2)+1), numbers2)

def lsLine(numbers1, numbers2):
    sxy = s_x_y(numbers1, numbers2)
    sxx = s_x_x(numbers1) or 1.0e-16
    syy = s_x_x(numbers2) or 1.0e-16
    rc = sxy/sxx
    q  = (fsum(numbers2)-rc*fsum(numbers1))/len(numbers1)
    r_sq = sxy**2/(sxx*syy)
    return rc, q, r_sq

def lsLine_I(numbers2):
    return lsLine(range(1,len(numbers2)+1), numbers2)

###
# Time
###
   
def py_time(a_time, time_format=stdTimeStr):
    '''Geeft datetime object voor string a_time volgens format'''
    return datetime.strptime(a_time, time_format)

def py_date_time(a_date_time, date_time_format=stdDateTimeStr):
    '''Geeft datetime object voor string a_date_time volgens format'''
    return datetime.strptime(a_date_time, date_time_format)
def py_date(a_date, date_format=stdDateStr):
    '''Geeft datetime object voor string a_date volgens format'''
    return datetime.strptime(a_date, date_format)
def date_time2epoch(date_time):
    '''Geeft unix time (GMT) voor date_time
    unix time is seconds sinds epoch (1/1/1970)'''
    return int(mktime(date_time.timetuple()))
def date_time2format(date_time, format):
    '''Geeft date_time terug in format'''
    return date_time.strftime(format)
def input_date(text, format=stdDateStr):
    '''Lees een tijd van stdin in in formaat format'''
    while 1:
        time = input(text)
        try:
            datetime.strptime(time, format)
            break
        except ValueError as err:
            print('De data heeft een verkeerd formaat! ', err)
    return time

###
# for Simulators
###
def qualify_diff(first, second):
    '''returns movement between first and second
    first > second: 'up'
    second > first: 'down'
    second = first: 'eq'
    '''
    qualification = ''
    if first < second:
        qualification = 'up'
    elif first > second:
        qualification = 'down'
    else:
        qualification = 'eq'
    return qualification

def rendement_perc(start, stop, trade):
    if (trade == 'long') or (trade == 'U'):
        rend = ((stop/start)-1)
    elif (trade == 'short') or (trade == 'D'):
        rend = (1-(stop/start))
    return rend

def rendement_BS(advices, quotes, verbose=False):
    '''Berkent het rendement van een strategie die koopt en verkoopt,
    steeds in deze volgorde, anders foutmelding en waarde 1 komt terug'''

    rend       = 1
    buyed      = False
    buy_price  = 0
    sell_price = 1
    for advice in advices:
        if (buyed and (advice.action == 'buy')) or (not(buyed) and (advice.action == 'sell')):
            print('De simulator geeft verkeerde signalen!! Check simulator!!')
            return 1
        if advice.action == 'buy':
            buy_price = quotes[advice.time]
            buyed = advice.item
        if advice.action == 'sell':
            sell_price = quotes[advice.time]
            last_rend = rendement_perc(buy_price, sell_price, buyed)
            if verbose:
                print('Rend: {0:.3p}'.format(last_rend * 100))
            buyed = False
            rend *= (1 + last_rend)
    if buyed:
        print('De simulator heeft een positie gehouden op het einde van de trade!!')
        return 1
    return (rend -1) * 100

###
# sqlite3
###

tableDef_IBHist = ('(datetime text UNIQUE ON CONFLICT IGNORE, open real, high real, low real, '+
                   'close real, volume integer, wap real, hasgaps integer, counts integer)')

def createDB(location, tableName=None, tableFormat=None):
    mydb=sqlite3.connect(location)
    dbh=mydb.cursor()
    if tableName:
        exstr = 'create table '+tableName+' '+tableFormat
        dbh.execute(exstr)
    mydb.commit()
    dbh.close()
    mydb.close()

###
# temporary files
###

# zou gegeven bestandsnamen moeten onthouden in testen of ze nog in dienst zijn,
# en bij rmTempFile of het wel een tempfile is.
def tempFileName(directory=None):
    fd, filename = tempfile.mkstemp(dir=directory)
    os.close(fd)
    return filename

def rmTempFile(name):
    os.remove(name)
