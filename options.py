#!/usr/bin/env python3

#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import math
from datetime import datetime

import mypy
import tws
from mysolvers import solve_to_x_1u as find_x
from mysolvers import solve_to_min_1u as find_min
from mysolvers import NoSolution

CALL = 'C'
PUT = 'P'

BOUGHT = 'B'
SOLD = 'S'

class OptionError(Exception): pass

class Option():
    
    def __init__(self,
                 right, strike, expiry,
                 multiplier=None, currency='EUR'):
        self.right = right
        self.strike = strike
        self.expiry = expiry
        self.multiplier = multiplier
        self.currency = currency
        
    def __str__(self):
        
        s = ['Option:']
        s.append('PUT' if self.right == PUT else 'CALL')
        s.append(str(self.strike))
        s.append(mypy.datetime2format(self.expiry, mypy.DATE_STR))
        return ' '.join(s)
        
    @property
    def right(self):
        
        return self.__right
    
    @right.setter
    def right(self, right):
        
        set_error = 'option.right must be \'put\' or \'call\''
        assert isinstance(right, str), set_error
        right = right.upper()
        assert right in ('C', 'P', 'CALL', 'PUT'), set_error
        if right in ('C', 'CALL'):
            self.__right = CALL
        else:
            self.__right = PUT
            
    @property
    def strike(self):
        
        return self.__strike
    
    @strike.setter
    def strike(self, strike_value):
   
        set_error = 'option.strike must be integer or call'
        assert isinstance(strike_value, (int, float)), set_error
        self.__strike = strike_value
        
    @property
    def expiry(self):
        
        return self.__expiry
    
    @expiry.setter
    def expiry(self, expiry):
        
        set_error = 'option.expiry must be a date'
        assert isinstance(expiry, datetime), set_error
        self.__expiry = expiry
        
class BlackScholesFormula():
    
    def __init__(self,
                 option,
                 risk_free_interest_rate=None,
                 current_call_option_value=None,
                 current_stock_price=None,
                 time_to_expiration=None,
                 accror_deviation=None,
                 sentiment=0):        
        self.option = option
        self.risk_free_interest_rate = risk_free_interest_rate
        self.current_call_option_value = current_call_option_value
        self.current_stock_price = current_stock_price
        self.time_to_expiration = time_to_expiration
        self.accror_deviation = accror_deviation
        self.sentiment = sentiment
        #accror: annualized continuously compounded rate of return
        
    def __str__(self):
        
        s = []
        s.append('B&S_{}'.format(str(self.option)))
        s.append('B&S_risk free rate: {}'.
                 format(self.risk_free_interest_rate))
        s.append('B&S_time to expiration: {}'.format(self.time_to_expiration))
        s.append('B&S_accror: {}'.format(self.accror_deviation))
        s.append('B&S_sentiment: {}'.format(self.sentiment))
        s.append('B&S_curr stock price: {}'.format(self.current_stock_price))
        s.append('B&S_curr option price: {}'.
                 format(self.current_call_option_value))
        return '\n'.join(s)
        
        
    @property
    def risk_free_interest_rate(self):
        
        return self.__rfir
    
    @risk_free_interest_rate.setter
    def risk_free_interest_rate(self, interest):
        if interest == None:
            self.__rfir = None
            return
        set_error = '-1 is loosing all, you can\'t lose more I hope'
        assert interest > -1, set_error
        self.__rfir = interest
        
    @property
    def current_time(self):
        
        return self.__ct
    
    @current_time.setter
    def current_time(self, value):
        
        assert isinstance(value, datetime), 'current time must be a datetime'
        self.__ct = value
        tte = mypy.timegap_to_year_ratio(value, self.option.expiry)
        #print(tte)
        self.time_to_expiration = tte
    
    @property
    def est_option_value(self):
        
        if not (self.current_stock_price and
                not self.risk_free_interest_rate == None and
                self.time_to_expiration and
                self.accror_deviation):
            #print(self)
            raise OptionError('Not enough known parameters')
        if self.option.right == CALL:
            est_function = self.est_call_value
        else:
            est_function = self.est_put_value
        return est_function()
    
    def est_option_value_for_price(self, value):
        old, self.current_stock_price = self.current_stock_price, value
        answer = self.est_option_value
        self.current_stock_price = old
        return answer
    
    def est_call_value(self):
        
        t1 = self.current_stock_price * mypy.normsdist(self.d1)
        #print(t1)
        p1 = -1 * self.risk_free_interest_rate * self.time_to_expiration
        #print(p1)
        t2 = self.adj_option_strike * math.e ** p1 * mypy.normsdist(self.d2)
        #print(t2)
        value = t1 - t2
        #print('val: {}'.format(value))
        return value
    
    def est_put_value(self):
        
        p1 = -1 * self.risk_free_interest_rate * self.time_to_expiration
        #print(p1)
        t1 = self.adj_option_strike * math.e ** p1 * (1 - mypy.normsdist(self.d2))
        #print(t1)  
        t2 = self.current_stock_price * (1 - mypy.normsdist(self.d1))
        #print(t2)
        value = t1 - t2
        #print('val: {}'.format(value))
        return value
    
    def loop_over_current_price(self, start, stop, step):
        
        current_price = self.current_stock_price
        result_list = []
        for price in mypy.f_range(start, stop, step):
            self.current_stock_price = price
            result_list.append((price, self.est_option_value))
        self.current_stock_price = current_price
        return result_list     
    
    def loop_over_deviation(self, start, stop, step):
        
        dev = self.accror_deviation
        result_list = []
        for diviation in mypy.f_range(start, stop, step):
            self.accror_deviation = diviation
            result_list.append((diviation, self.est_option_value))
        self.accror_deviation = dev
        return result_list     
    
    def loop_over_days(self, start, stop, step):
        
        exp = self.current_stock_price
        result_list = []
        for day in mypy.f_range(start, stop, step):
            self.time_to_expiration = days/365
            result_list.append((day, self.est_option_value))
        self.time_to_expiration = exp
        return result_list     
    
    def loop_over_free_interest(self, start, stop, step):
        
        rate = self.risk_free_interest_rate
        result_list = []
        for rate in mypy.f_range(start, stop, step):
            self.risk_free_interest_rate =  rate
            result_list.append((rate, self.est_option_value))
        self.risk_free_interest_rate = rate
        return result_list       
        
    @property
    def d1(self):
        
        t1 = math.log(self.current_stock_price/self.adj_option_strike)
        
        t2 = (self.accror_deviation**2) / 2
        t2 += self.risk_free_interest_rate
        t2 *= self.time_to_expiration
        
        n = self.accror_deviation * math.sqrt(self.time_to_expiration)
        
        return (t1 + t2) / n
    
    @property
    def d2(self):
        
        t1 = self.d1
        
        t2 = self.accror_deviation * math.sqrt(self.time_to_expiration)
        
        return t1 - t2
    
    @property
    def adj_option_strike(self):
        
        if self.sentiment == 0:
            return self.option.strike
        else:
            adj = self.option.strike * self.sentiment / -10000
        return self.option.strike + adj
    
class OptionCombo():
        
    def __init__(self, *actions):
        self.bought_option_list = []
        self.sold_option_list = []
        for action, option in actions:
            self.register_action(action, option)
        assert len(self.sold_option_list) == 0, 'selling options not impl'
        self.bands_list = dict()
        for option in self.option_list:
            self.bands_list[str(option)] = BlackScholesFormula(option)
        #print(self.bought_option_list)
        
    @property
    def option_list(self):
        return self.bought_option_list + self.sold_option_list
    
    def add_bands(self, bands):
        option_name = str(bands.option)
        assert option_name in self.bands_list, 'unknown option'
        self.bands_list[option_name] = bands
       
    def register_action(self, action, option):
        if action == BOUGHT:
            self.bought_option_list.append(option)
        elif action == SOLD:
            self.sold_option_list.append(option)
            
    def est_value_for_price(self, price):
        value = 0
        for bands in self.bands_list.values():
            value += bands.est_option_value_for_price(price)
        return value
            
    def loop_over_current_price(self, start, stop, step):
        
        result_list = []
        for bands in self.bands_list.values():
            print(bands)
            result_list.append(
                bands.loop_over_current_price(start, stop, step))
        result = [(result_list[0][p][0], sum([x[p][1] for x in result_list])) 
                  for p in range(len(result_list[0]))]
        return result
    
    @property
    def low(self):
        def val(x):
            answer = sum([p.est_option_value_for_price(x)
                          for p in self.bands_list.values()])
            return answer
        try:
            answer = find_min(val, depth=3)
        except:
            return 0
        return find_min(val, depth=3)
    
    
class Strangle(OptionCombo):
    
    def __init__(self, c_strike, p_strike, c_exp, p_exp=None):
        if p_exp == None:
            p_exp = c_exp
        self.c_option = Option(CALL, c_strike, c_exp)
        self.p_option = Option(PUT, p_strike, p_exp)
        super().__init__((BOUGHT, self.c_option),(BOUGHT, self.p_option))
        self.accror_deviation = None
        
    def autoset_black_and_scholes(self, 
                                  asset_price, call_price, put_price, 
                                  time_till_expiration, risk_free_rate=0):
        try:
            c_bands, p_bands = est_b_and_s_formula_for_c_and_p_price(
                asset_price,
                self.c_option.strike, call_price,
                self.p_option.strike, put_price,
                time_till_expiration, risk_free_rate,
                option_expiry=self.c_option.expiry)
        except NoSolution:
            raise
        self.add_bands(c_bands)
        self.add_bands(p_bands)
        self.accror_deviation = c_bands.accror_deviation
        self.sentiment = c_bands.sentiment
        self.risk_free_interest_rate = c_bands.risk_free_interest_rate
        
    def set_black_and_scholes(self,
                              call_risk_free_interest_rate=0.05,
                              put_risk_free_interest_rate= None,
                              curr_call_price=None,
                              curr_put_price=None,
                              curr_stock_price=None,
                              time_delta=None,
                              call_accror=None, put_accror=None,
                              call_sentiment=0, put_sentiment=0):
        
        if not put_risk_free_interest_rate:
            put_risk_free_interest_rate = call_risk_free_interest_rate
        c_bands = BlackScholesFormula(self.c_option,
                                      call_risk_free_interest_rate,
                                      curr_call_price, curr_stock_price,
                                      accror_deviation=call_accror,
                                      sentiment=call_sentiment)
        p_bands = BlackScholesFormula(self.p_option,
                                      put_risk_free_interest_rate,
                                      curr_put_price, curr_stock_price,
                                      accror_deviation=put_accror,
                                      sentiment=put_sentiment)
        if isinstance(time_delta, datetime):
            c_bands.current_time = time_delta
            p_bands.current_time = time_delta
        else:
            if not c_option.expiry == p_option.expiry:
                mess = 'giving a fixed time till expiration for options with'
                mess += ' different expiries makes no sense!!'
                raise OptionError(mess)
            c_bands.time_to_expiration = time_delta
            p_bands.time_to_expiration = time_delta
        self.add_bands(c_bands)
        self.add_bands(p_bands)
        self.accror_deviation = c_bands.accror_deviation
        
            
def get_option():
    
    right=''
    while not right.upper() in ('C', 'P', 'CALL', 'PUT'):
        right = mypy.get_string('right (C/P): ')
    strike = mypy.get_float('strike: ')
    expiry = mypy.get_date('expiry (YYYYY/MM/DD): ', format_=mypy.DATE_STR)
    return Option(right, strike, expiry)

def option_from_tws_contract(tws_contract):
    
    ctr = tws_contract
    assert isinstance(ctr, tws.contract), 'can only convert from tws_contract'
    assert ctr.secType == 'OPT', 'contract must be option'
    ed = mypy.py_date_time(ctr.expiry, '%Y%m%d')
    option_date = datetime(ed.year, ed.month, ed.day, 16, 0, 0)
    #hard coded time convertion, if this gives an error check tws changes
    return Option(
        ctr.right, ctr.strike, option_date, ctr.multiplier, ctr.currency)

def get_black_scholes_formula(option=None):
   
    if not option:
        option = get_option()
    rfi = mypy.get_float('risk free interest rate: ', empty=True)
    ccov = mypy.get_float('current call option value: ', empty=True)
    csp = mypy.get_float('current stock price', empty=True)
    tte = mypy.get_float('time till expiration ', empty=True)
    adivi =  mypy.get_float('deviation on rate: ', empty=True)
    return BlackScholesFormula(option, rfi,ccov, csp, tte, adivi)

def est_b_and_s_formula_for_c_and_p_price(asset_price,
                                          call_strike, call_value,
                                          put_strike, put_value,
                                          time_delta,
                                          s0_risk_free_interest_rate=0.006,
                                          max_dist=0.025,
                                          option_expiry = datetime(2099,12,31),
                                          c_option_expiry = None,
                                          p_option_expiry = None):
    
    '''returns a black and scholes put and call formula
    
    time delta can be a number or a datetime object, if it is a number it is set as
    the part of a full year if it's a date, the ratio is calculated
    '''
    
    def set_bands_accror(c_bands, p_bands, cum_val):
        
        def sum_est_val(accror):
            c_bands.accror_deviation = accror
            p_bands.accror_deviation = accror
            return c_bands.est_option_value + p_bands.est_option_value
        new_accror = find_x(sum_est_val, cum_val, 0.01, 1, 0.01, 4)
        c_bands.accror_deviation = new_accror
        p_bands.accror_deviation = new_accror
        
    def set_bands_sentiment(c_bands, p_bands, c_val, p_val):
        
        if c_val > p_val:
            bands, val = c_bands, c_val
        else:
            bands, val = p_bands, p_val
        def sentiment_est_val(sentiment):
            bands.sentiment = sentiment
            return bands.est_option_value
        new_sentiment = find_x(sentiment_est_val, val, -1000, 1000, 100, 4)
        c_bands.sentiment = new_sentiment
        p_bands.sentiment = new_sentiment
        
    def set_bands_risk_free_rate(c_bands, p_bands, c_val, p_val):
        
        def est_value_delta_delta(free_rate):
            c_bands.risk_free_interest_rate = free_rate
            p_bands.risk_free_interest_rate = free_rate
            c_delta = c_val - c_bands.est_option_value
            p_delta = p_val - p_bands.est_option_value
            return c_delta - p_delta
        new_risk_free_rate = find_x(est_value_delta_delta, 0, -0.9, 1, 0.1,5)
        c_bands.risk_free_interest_rate = new_risk_free_rate
        p_bands.risk_free_interest_rate = new_risk_free_rate
        
    
    if c_option_expiry == None:
        c_option_expiry = option_expiry
    if p_option_expiry == None:
        p_option_expiry = c_option_expiry
    c_option = Option(CALL, call_strike, c_option_expiry)
    p_option = Option(PUT, put_strike, p_option_expiry)
    c_bands = BlackScholesFormula(c_option, s0_risk_free_interest_rate,
                                  current_stock_price=asset_price)
                                  #time_to_expiration=time_till_expiration)
    p_bands = BlackScholesFormula(p_option, s0_risk_free_interest_rate,
                                  current_stock_price=asset_price)
                                  #time_to_expiration=time_till_expiration)
    if isinstance(time_delta, datetime):
        c_bands.current_time = time_delta
        p_bands.current_time = time_delta
    else:
        if not c_option.expiry == p_option.expiry:
            mess = 'giving a fixed time till expiration for options with'
            mess += ' different expiries makes no sense!!'
            raise OptionError(mess)
        c_bands.time_to_expiration = time_delta
        p_bands.time_to_expiration = time_delta
    #print(c_bands)
    #print(p_bands)
    run = 0
    dist_test = False
    while not dist_test == True:
        #print('RUN ',run)
        #print('###############')
        set_bands_accror(c_bands, p_bands, call_value + put_value)
        #print(c_bands)
        #print(p_bands)
        #print('call est: {}'.format(c_bands.est_option_value))
        #print('put est: {}'.format(p_bands.est_option_value))
        set_bands_sentiment(c_bands, p_bands, call_value, put_value)
        #print(c_bands)
        #print(p_bands)
        #print('call est: {}'.format(c_bands.est_option_value))
        #print('put est: {}'.format(p_bands.est_option_value))
        set_bands_risk_free_rate(c_bands, p_bands, call_value, put_value)
        #print(c_bands)
        #print(p_bands)
        #print('call est: {}'.format(c_bands.est_option_value))
        #print('put est: {}'.format(p_bands.est_option_value))
        run += 1
        dist_test = abs(c_bands.est_option_value - call_value) < max_dist
    return c_bands, p_bands    
    