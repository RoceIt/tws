#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

# Try to create a market simulater, it should simulate te worst realistic
# behaviour of the market to the buy and sell orders it gets. I would also like
# to have some in/out strategies it can simulate (also worst case simulations).

import logging
from datetime import timedelta, datetime, date
from time import sleep
from itertools import chain

import barData # to be removed, no longer maintained
import validate
from marketdata import DataBar, DataBarFeeder
from roc_input import get_bool
from roc_string import SerialTextCreator
from mypy import export_pickle, import_pickle

class Error(Exception):
    pass

class CancelRequestFailed(Error):
    '''Exception raised when order is already (parially) executed.'''
    def __init__(self, already_executed):
        self.already_executed = already_executed

class WorstCaseDataStream():
    '''An object that simulates a datastream, 
    
    It takes ticks or bars as input and creates the worst case bar data for buying
    and selling from it.  
    This should take care of the problem that indexes get opens that are the
    same as the closes of the privious bars and moves in bars between open and
    close
    '''
    
    TICKS = 0
    
    def __init__(self, name, input_size, *output_sizes):
        '''Create the stream.
        
        Make sure the input_size arg is an integer or the TICKS constant. The
        output_sizes must be multiples of the input size.
        
        '''
        
        self.name = name
        self.input_size = input_size
        self.buy_data = {x: barData.ochl(number_of_units=x)
                            for x in output_sizes}
        self.sell_data = {x: barData.ochl(number_of_units=x)
                            for x in output_sizes}
        if not isinstance(input_size, int):
            mss = 'WorstCaseDataStream: input_size argument must be an integer or WorstCaseDataSTream.TICKS'
            raise TypeError(mss)
        if not input_size == self.TICKS:
            for key in self.output_data:
                if not key % input_size == 0:
                    mss = "output size must be a multiple of input_size ({})"
                    mss = mss.format(input_size)
                    raise ValueError(mss)
        ##
        log_mss = "Created WorstCaseDataStream {};input={};available bars={}"
        input_size = "Ticks" if input_size == 0 else str(input_size)
        log_mss = log_mss.format(name, input_size, str(output_sizes))
        logging.info(log_mss)
        
    def data_info_file(self, filename):
        pass
        
        
    def insert_next_data_point(self, data):
        pass
    
BARS = 'bars'
TICKS = 'ticks'
    
class DevotedTrader():
    '''A devoted trader on one data source.
    
    The trader watches one source and handle the instructions you give
    it.  The trades can be written to a file.  Becaus it only runs on one
    data source instructions are very limmeted.  You can buy, sell or
    close a positon and remove a not yet executed trade.  You have to
    give a timestamp with every trade so the trader can move it's
    data source pointer.  You can also move the pointer in time to
    advance the trader.  All intructions send to the trader must respect
    the timeline, you can't jump around.
    
    Attributes:
      name -- Just a name
      info -- Just some extra info
      to_do -- a list with future tasks
      done -- a list with finished tasks
      position_changes -- All the buys and sells
      
    Methods:
      buy -- buy stuff
      sell -- self stuff
      close -- close positions
      request_order_cancel -- cancel an order if not already executed
      move -- advance time
      not_in_trade_at -- test if positions are being held
      '''
    
    BARS = 'bars'
    TICKS = 'ticks'
    
    def __init__(self, name, data_source, counting='normal'):
        '''Set the name and data source.
        
        Smart programmers will not try to change these later.
        
        Parameters:
          name -- an object with a __str__ attribute
          data_source -- a bar- or tickfeeder from marketdata
          counting -- choose the way points get counted
            normal --> what i think is normal
            loose --> what i think is to loose
            strict --> wath i think is overkill
        '''
        
        assert hasattr(name, '__str__'), 'name must be meaningfull when printed'
        assert isinstance(data_source, (DataBarFeeder,)), (
            'data_source must be an instance of DataBar- or TickFeeder')
        ###
        if isinstance(data_source, DataBarFeeder):
            datatype = self.BARS
            orderfunction = 'new_bar'
        else:
            datatype = self.TICKS
            orderfunction = 'new_tick'
            raise NotImplementedError('bar data for now!')
        
        ###
        self.name = name
        self.info = ''
        self.open_orders = {}
        self.filled_and_removed_orders = {}
        self.positions = {}
        self.closing_and_closed_positions = {}
        self.data = iter(data_source)
        self.datatype = datatype
        self.order_function = orderfunction
        self.curr_data = None
        self.next_data = next(self.data)
        self.data_counter = 1
        self.trade_counter = 0
        self.last_move_timestamp = datetime(1975,1,1,0,0,0)
        self.proces_open_orders_level = 0
        
    def move_to(self, timestamp):
        '''Move data to new_time and run required actions'''
        self.make_sure_the_request_is_not_chronological_biased(timestamp)
        #print('move to stamps: ', timestamp, ' | ', self.last_move_timestamp)
        ###
        ts = loop_ts = timestamp
        ###
        while self.next_data_available_at <= ts:
            self.advance()
            if isinstance(self.curr_data, DataBar):
                loop_ts = max(self.curr_data.time, self.last_move_timestamp)
                # mss checken of self.last_maove_timestamp in de huidige data ligt??
            else:
                raise NotImplementedError('only bars for now :-((')
            loop_ts = self.check_open_order(self.curr_data, loop_ts)
            #self.advance()
        self.last_move_timestamp = loop_ts
        #if (self.next_data_available_at - loop_ts > self.next_data.duration):
            #print('diff bigger then duration: {} | {}'.format(
                #loop_ts, self.next_data_available_at)) #, default=True)
        return self.advance_timestamp_for_one_request(ts)      
        
    def buy(self, timestamp, info, **buy_parameters):
        '''Send a buy order and return an id to manage it.
        
        Parameters:
          timestamp -- a datetime.datetime when the order is sended
          info -- info to attach in log when order is filled
          buy_parameters -- as in buy class
        '''
        ####
        ####
        return self.send_order(Buy, timestamp, info, **buy_parameters)
        
    def sell(self, timestamp, info, **sell_parameters):
        '''Send a sell order and return an id to manage it.
        
        Parameters:
          timestamp -- a datetime.datetime when the order is sended
          info -- info to attach in log when order is filled
          buy_parameters -- as in buy class
        '''
        ###
        ####
        return self.send_order(Sell, timestamp, info, **sell_parameters)
    
    def close_position(self, timestamp, info, order_id, volume_aware=False):
        '''Close positions.
        
        If order_id is 0, all positions will be closed.
        '''
        ts = self.move_to(timestamp)
        ###
        if order_id == 0:
            if self.open_orders:
                raise Error('@ {}: close all with open orders: {}'.format(
                    self.last_move_timestamp, self.open_orders))
            positions_to_close, ts = self.nr_of_items_held(self.positions, ts)
            ts = self.advance_timestamp_for_one_request(ts)
        else:
            if order_id in self.open_orders:
                raise Error('id {} has open orders.'.format(order_id))
            if order_id in self.positions:
                positions_to_close, ts = self.nr_of_items_held_by_id(
                                               self.positions, order_id, ts)
                ts = self.advance_timestamp_for_one_request(ts)
            else:
                positions = 0
        order = self.buy if positions_to_close < 0 else self.sell
        ###
        if not positions_to_close == 0:
            o, ts = order(
                timestamp=ts,
                info=info, 
                quantity=OrderValue(abs(positions_to_close)),
                start=OrderStartConditions('now'),
                until=(RemoveOrderCondition('GTC'),), 
                type='market',
                volume_aware=volume_aware,
                closes=order_id,
            )
            ts = self.advance_timestamp_for_one_request(ts)
        return o, ts
        
    def request_order_cancel(self, timestamp, id_):
        '''Request order cancel, if not already executed.
        
        Wrap it in a try statement, it reports failure with a
        CancelRequestFail exception.
        '''  
        ###
        ###        
        ts = self.move_to(timestamp)
        if id_ in self.filled_and_removed_orders:
            raise CancelRequestFailed('all')
        order = self.open_orders[id_]
        order['scheduled for cancel'] = True
        if id_ in self.positions:
            nr_of_positions, ts = self.nr_of_items_held_by_id(
                                                      self.positions, id_, ts)
            raise CancelRequestFailed(nr_of_positions)
        return ts
        
    def in_trade_at(self, timestamp):
        '''Return the nr of positions held at timestamp.
        
        You can use this as a boolean, 0 is False!
        This is a timestamped action, it returns the new timestamp to use,
        don't use the bar time, use a timestamp to walk thrue your funtions.
        '''
        if self.last_move_timestamp and timestamp < self.last_move_timestamp:
            print(timestamp, '<', self.last_move_timestamp)
            get_bool('think think!! looking for an older position!', default=True)
        ###
        ###
        ts = self.move_to(timestamp)
        nr_of_positions, ts = self.nr_of_items_held(self.positions, ts)
        return nr_of_positions, ts
    
    def avg_in(self, timestamp, order_id=0):
        '''Return the average price of order execution.
        
        if order_id is 0, average of all positions is calculated.
        '''
        ###
        ts = self.move_to(timestamp)
        if order_id == 0:
            calc_set = self.positions.values()
        else:
            calc_set = [self.positions[order_id]]
        all_actions = self.collect_actions_in(calc_set)
        position = cash_positition = 0
        for foo, nr, price in all_actions:
            position += nr
            cash_positition += -nr * price
        ###
        try:
            avg = abs(cash_positition/position)
        except ZeroDivisionError:
            raise Error('No positions.')
        #print('avg in: ', avg)
        return avg, ts
    
    def pickle_order_lists(self):
        info = (self.open_orders, self.positions, self.closing_and_closed_positions)
        export_pickle(info, '/tmp/dev_trader.pckl')
    
    def print_order(self, id_):
        order = self.open_orders.get(id_,
                self.positions.get(id_,
                self.closing_and_closed_positions.get(id, None)))
        print(order['order'])
        
    #######
    #
    # Not for the user
    #
    #
    #
            
    @staticmethod
    def advance_timestamp_for_one_request(timestamp):
        '''Advance timestamp to avoid chronological biasses.'''
        return timestamp + timedelta.resolution
    
    
    def nr_of_items_held_by_id(self, positions, order_id, timestamp):
        '''Count nr of items in positions due to order_id.'''
        if order_id not in positions:
            raise Error('no positions held by this order')
        ###
        ts = self.move_to(timestamp)
        positions = sum([y for x,y,z in positions[order_id]['actions']])
        ###
        return positions, ts

    def nr_of_items_held(self, positions, timestamp):
        '''Total position.'''
        ###
        ts = self.move_to(timestamp)
        positions = sum([y for foo in positions.values() 
                             for x,y,z in foo['actions']])
        ###
        return positions, ts
    
    def send_order(self, order, timestamp, info, **order_parameters):
        ''' Send an order and return an id to manage it.'''
        ###
        closing_order = order_parameters.pop('closes', None)
        order = order(**order_parameters)
        ###        
        ts = self.move_to(timestamp)
        self.trade_counter += 1
        self.open_orders[self.trade_counter] = {
            'time': timestamp,
            'info': info,
            'order': order,
            'closing order': 'ALL' if closing_order == 0 else closing_order,
        }
        ts = self.advance_timestamp_for_one_request(ts)
        #print(order)
        #self.small_dump(ts)
        return self.trade_counter, ts
    
    def check_open_order(self, data, timestamp):
        '''Run action if required.
        
        data is bar or tick data, in __init__ the self.order_function 
        is set to the right function name.
        '''
        ###
        ts = timestamp   
        count = 0
        self.proces_open_orders_level += 1
        if self.proces_open_orders_level > 1:
            get_bool(
                'check open order entering level {}'.format(self.proces_open_orders_level),
                default=True)
        safe_id_keys = list(self.open_orders.keys())
        safe_id_keys.sort()
        for id_ in safe_id_keys:
            order = self.open_orders.get(id_, None)
            if not order:
                pass
            count += 1
            #print('\n\n\n{} (lmt={}: processing id {} count is {}|{}\n'.format(
                        #ts, self.last_move_timestamp, id_, self.proces_open_orders_level, count))
            if ts < self.last_move_timestamp:
                raise Error('check times above!!')
                get_bool('check times above!!', default=True)
            real_order = order['order']
            send_data_to_order = getattr(real_order, self.order_function)
            action, ts = send_data_to_order(data, self, ts)
            if action is None:
                pass
            elif action == Order.PARTIALLY:
                print('order {} partially filled @ {}'.format(id_, ts))
                self.position_change(id_, ts)
            elif action == Order.FILLED:
                print('order {} filled @ {}'.format(id_, ts))
                self.small_dump(ts)
                self.position_change(id_, ts)            
            elif action is Order.CAN_BE_REMOVED_FROM_OPEN_ORDERS:  
                ##get_bool('denk nog eens na, zou dit mogen|kunnen gebeuren?')
                print('removing from open orders {} @ {}'.format(id_, ts))
                self.filled_and_removed_orders[id_] = self.open_orders.pop(id_)
            if order.get('scheduled for cancel', False):
                order.pop('scheduled for cancel')
                order['canceled'] = True
                self.finished_and_registered_orders.append(id_)
        self.proces_open_orders_level -= 1
        if self.proces_open_orders_level > 1:
            get_bool(
                'check open order leaving level'.format(self.proces_open_orders_level),
                default=True)
        return ts
            
    
    def advance(self):
        '''Advance the time e.g. read next data'''
        ###
        ###
        self.curr_data = self.next_data
        self.next_data = next(self.data)
        self.data_counter += 1
        if self.next_data == None:
            raise Error('Trader out of data')
        
    def position_change(self, id_, ts):
        '''Register action.'''
        ###
        order = self.open_orders[id_]
        action, time_, quantity, price = order['order'].action
        info = order['info']
        closes_order = order.get('closing order', None)
        if closes_order is not None:
            action_list = self.closing_and_closed_positions
        else:
            action_list = self.positions
        ###
        if not id_ in action_list:
            if closes_order == 'ALL':
                action_list.update(self.positions)
                self.positions.clear()            
            elif closes_order:
                #get_bool('closing {}'.format(closes_order), default = True)
                if closes_order not in self.positions:
                    mss = 'trying to close not open position: {}'
                    mss = mss.format(closes_order)
                    raise Error(mss)
                if closes_order in action_list:
                    mss = ('position {} already in closging list, are you trying'
                           ' to work with partialy filled orders?')
                    mss = mss.format(closes_order)
                    raise NotImplemented(mss)
                action_list[closes_order] = self.positions.pop(closes_order)
            action_list[id_] = {'info': info,
                                   'actions': []}
            if closes_order:
                action_list[id_]['closes'] = closes_order
        else:
            raise NotImplemented('Are you trying to work with partially filled orders?')
        if action == 'bought':
            action_list[id_]['actions'].append((time_, quantity, price))
        elif action == 'sold':
            action_list[id_]['actions'].append((time_, -quantity, price))
        else:
            raise Error('Unknown action: {}'.format(action))
        self.small_dump(ts)
        
    def small_dump(self, time_):
        return
        print('@ ', time_)
        print('open orders: ', self.open_orders)
        print('positions: ', self.positions)
        print('closing and closed: ', self.closing_and_closed_positions)
        print()
    
    def make_sure_the_request_is_not_chronological_biased(self, timestamp):
        '''Check chronological logic
        
        All instructions are given one after another, not at the same
        time, and not the next before the previous.
        
        Parameter:
          timestamp -- a datetime.datetime object
        '''
        ###
        ###
        if self.last_move_timestamp is not None and timestamp <= self.last_move_timestamp:
            print('curr: {} | next: {}'.format(self.curr_data, self.next_data))
            mss = 'chronological logic error: {} after {}'.format(
                                         timestamp, self.curr_data.time)
            raise Error(mss)
        
    @property    
    def next_data_available_at(self):
        '''Return the time a user would have received the data.
        
        It's a best guess;-))
        '''
        ###
        if self.datatype is self.BARS:
            #time_ = self.next_data.end_time()
            time_ = self.next_data.time
        else:
            raise NotImplemented()
        ###
        return time_
    
    @staticmethod
    def collect_actions_in(calc_set):
        '''Return a list with all the actions in the calc_set.'''
        ###
        ###
        return chain(*tuple((x['actions'] for x in calc_set)))

class Order():
    '''An order.
    
    After setting all buy parameters, you can start sending opportunities
    to a buy instance.  It returns a message: None, Order.PARTIAL, 
    Order.FINISHED or Order.CAN_BE_REMOVED.  
    
    Parameters:
      quantity -- number of units to buy
      start -- set a start datetime.datetime
      until -- set a stop datettime.datetime
      type -- c below
      
    Types:
      market -- trade at marketprice | no extra parameters expected
      limit -- trade when limit is reached | limit needed
      
    Attributes:
      actions -- the actions taken after last data input
      
    Methods:
      new_tick -- new tick data, returns message
      new_bar -- new bar data, returns a message
      
      
    '''    
    MANDATORY_ORDER_ATTRIBUTES = (
        'quantity', 'start', 'until', 'type', 'volume_aware'
    )
    OPTIONAL_ORDER_ATTRIBUTES = (
        'parent_order', 
    )
    MANDATORY_TYPE_ATTRIBUTES = {
        'market': tuple(),
        'limit': ('limit',),
        'stop_limit': ('limit', 'stop',)
    }
    OPTIONAL_TYPE_ATRIBUTES = {
        'market': tuple(),
        'limit': tuple(),
        'stop_limit': tuple(),
    }
    ORDER_TYPES = MANDATORY_TYPE_ATTRIBUTES.keys()
    #EXPIRE_CODES = {'GTC',}
    PARTIALLY = 'PARTIAL'
    FILLED = 'FILLED'
    CAN_BE_REMOVED_FROM_OPEN_ORDERS = 'READYFORREMOVAL'    
    
    def __init__(self, **kwds):
        '''Initiate the order.
        
        For keywords and valid values, c the class documentation
        '''
        ###
        ###
        for attr in self.MANDATORY_ORDER_ATTRIBUTES:
            try: parameter = kwds.pop(attr)
            except KeyError as err:
                raise Error('missing parameter {}'.format(attr))
            setattr(self, attr, parameter)
        if not self.type in self.ORDER_TYPES:
            raise Error('unknonw type {}'.format(self.type))
        for attr in self.MANDATORY_TYPE_ATTRIBUTES[self.type]:
            try: parameter = kwds.pop(attr)
            except KeyError as err:
                raise Error('missing parameter {}'.format(attr))
            setattr(self, attr, parameter)
        optional_parameters = self.OPTIONAL_ORDER_ATTRIBUTES
        optional_parameters += self.OPTIONAL_TYPE_ATRIBUTES[self.type]
        for attr in optional_parameters:
            setattr(self, attr, kwds.pop(attr, None))
        if kwds: # raise error when unused parameters are found
            raise Error('unknown Order parameters: {}'. format(kwds.keys()))
        self.action = None
        
    def __str__(self):
        ###
        text = SerialTextCreator()
        for arglist in (self.MANDATORY_ORDER_ATTRIBUTES,
                        self.OPTIONAL_ORDER_ATTRIBUTES,
                        self.MANDATORY_TYPE_ATTRIBUTES,
                        self.OPTIONAL_TYPE_ATRIBUTES):
            for arg in arglist:
                value = getattr(self, arg, None)
                if value:
                    text.add_line('{}: {}'.format(arg, value))
        try:
            action = self.__action
            text.add_line('action: {}'.format(action))
        except AttributeError:
            pass
        ###
        return str(text)
    
    def new_bar(self, bar, sim_environment, timestamp):
        '''check if order can be (partialy) filled with new data.'''
        assert isinstance(bar, DataBar)
        assert self.action is None, (
           'You must read out and reset the actions yourself, don\'t forget')
        ts = timestamp
        order_is_valid, ts = self.start.active(bar, self, sim_environment, ts)
        if not order_is_valid:
            return None, ts
        order_completed, ts = self.quantity.is_null(ts)
        for until in self.until:
            order_expired, ts = until.expired(bar, self, sim_environment, ts)
            if order_expired:
                #get_bool('order expired {}'.format(self), default=True)
                break
        if order_completed or order_expired:
            return Order.CAN_BE_REMOVED_FROM_OPEN_ORDERS, ts
        if self.volume_aware:
            if self.type in {'market', 'linmit'}:
                raise NotImplementedError(
                    'volume_aware for {}'.format(self.type))
        ###
        select_new_bar_function_for_order_type = {
            'market': self.new_bar_market_order,
            'limit': self.new_bar_limit_order,
            'stop_limit': self.new_bar_stop_limit_order,
        }
        new_bar = select_new_bar_function_for_order_type[self.type]
        ###
        new_bar, ts = new_bar(bar, sim_environment, ts)
        ts = sim_environment.advance_timestamp_for_one_request(ts)
        return new_bar, ts
        
        
    @property
    def action(self):
        '''Return the actions after the last data insert and resets them to None.
        
        The return value is None or a tuple: (action, time, quantity, price).
        The setter accepts None, or the same tuple values.
        '''
        ###
        ###
        action = self.__action
        self.__action = None
        ###
        return action
    
    @action.setter
    def action(self, tqp):
        ###
        ###
        if tqp is None:
            self.__action = None
        else:
            action, time_, quantity, price = tqp
            self.__action = (action, time_, quantity, price)
        
class Buy(Order):
    '''A buy order.
    '''    

    def __str__(self):
        ###
        text = SerialTextCreator()
        text.add_line('BUY order')
        text.underline()
        text.append(super().__str__())
        ###
        return str(text)
        
    def new_bar_market_order(self, bar, sim_environment, ts):
        ''' Simple market order.
        
        not counting aware, should it be?
        '''
        assert isinstance(bar, DataBar)
        ###
        order_quantity, ts = self.quantity.value(bar,self, sim_environment, ts)
        quantity = order_quantity # maybe volume aware systems can change this
        price = bar.high
        ###
        new_quantity = order_quantity - quantity
        self.quantity = OrderValue(new_quantity)
        self.action = ('bought', bar.end_time(), quantity, price)
        return Order.FILLED if new_quantity == 0 else Order.PARTIALLY, ts
    
    def new_bar_limit_order(self, bar, sim_environment, ts):
        assert isinstance(bar, DataBar)
        '''Buy for maximum limit price.
        
        This can be made counting aware, but it isn't :-((
        '''
        ###
        order_quantity, ts = self.quantity.value(bar, self, sim_environment, ts)
        quantity = order_quantity # maybe volume aware systems can change this
        limit, ts = self.limit.value(bar, self, sim_environment, ts)
        if bar.low <= limit:
            order_executed = True
            price = limit if bar.high > limit else bar.high
        else:
            order_executed = False
        # Could change the quantity here when bar.high == limit in 
        # volume aware systems??
        ###
        if order_executed:
            new_quantity = order_quantity - quantity
            self.quantity = OrderValue(new_quantity)
            self.action = ('bought', bar.end_time(), quantity, price)
            #print('bought on trigger', bar.end_time(), quantity, price)
            #print(self)
            return Order.FILLED if new_quantity == 0 else Order.PARTIALLY, ts
        return  None, ts
    
    def new_bar_stop_limit_order(self, bar, sim_environment, ts):
        '''Buy at limit price when stop is reached.
        
        This can be made counting aware, but it isn't :_((
        '''
        ###
        order_quantity, ts = self.quantity.value(bar, self, sim_environment, ts)
        quantity = order_quantity # maybe volume aware systems can change this
        limit, ts = self.limit.value(bar, self, sim_environment, ts)
        stop, ts = self.stop.value(bar, self, sim_environment, ts)
        if bar.high < stop:
            order_executed = False
            limit_active = False
        elif (limit is None
              or
              not bar.high > limit):
            order_executed = True
            price = bar.high
        elif not bar.close > limit:
            order_executed = True
            price = limit
        else:
            order_executed = False
            limit_active = True
        ###
        if order_executed:
            new_quantity = order_quantity - quantity
            self.quantity = OrderValue(new_quantity)
            self.action = ('bought', bar.end_time(), quantity, price)
            return Order.FILLED if new_quantity == 0 else Order.PARTIALLY, ts
        elif limit_active:
            self.type = 'limit'
        return None, ts
            
        
class Sell(Order):
    '''A sell order.
    ''' 
        
    def __str__(self):
        ###
        text = SerialTextCreator()
        text.add_line('Sell order')
        text.underline()
        text.append(super().__str__())
        ###
        return str(text)
        
    def new_bar_market_order(self, bar, sim_environment, ts):
        ''' Simple market order.
        not counting aware, should it be?'''
        assert isinstance(bar, DataBar)
        ###
        order_quantity, ts = self.quantity.value(bar, self, sim_environment, ts) 
        quantity = order_quantity # maybe volume aware systems can change this
        price = bar.low
        ###
        new_quantity = order_quantity - quantity
        self.quantity = OrderValue(order_quantity - quantity)
        self.action = ('sold', bar.end_time(), quantity, price)
        return Order.FILLED if new_quantity == 0 else Order.PARTIALLY, ts
    
    def new_bar_limit_order(self, bar, sim_environment, ts):
        '''Sell for minimum limit price.
        
        This can be made counting aware, but it isn't :-((
        '''
        assert isinstance(bar, DataBar)
        ###
        order_quantity, ts = self.quantity.value(bar, self, sim_environment, ts) 
        quantity = order_quantity # maybe volume aware systems can change this
        limit, ts = self.limit.value(bar, self, sim_environment, ts)
        if bar.high >= limit:
            order_executed = True
            price = limit if bar.low < limit else bar.low
        else:
            order_executed = False
        # Could change the quantity here when bar.high == limit in 
        # volume aware systems??
        ###
        if order_executed:
            new_quantity = order_quantity - quantity
            self.quantity = OrderValue(order_quantity - quantity)
            self.action = ('sold', bar.end_time(), quantity, price)
            #print('sold on trigger', bar.end_time(), quantity, price)
            #print(self)
            return Order.FILLED if new_quantity == 0 else Order.PARTIALLY, ts
        return None, ts
    
    def new_bar_stop_limit_order(self, bar, sim_environment, ts):
        '''Sell at limit price when stop is reached.
        
        This can be made counting aware, but it isn't :_((
        '''
        ###
        order_quantity, ts = self.quantity.value(bar, self, sim_environment, ts)
        quantity = order_quantity # maybe volume aware systems can change this
        limit, ts = self.limit.value(bar, self, sim_environment, ts)
        stop, ts = self.stop.value(bar, self, sim_environment, ts)
        if bar.low > stop:
            order_executed = False
            limit_active = False
        elif (limit is None 
              or
              not bar.low < limit):
            order_executed = True
            price = bar.low
        elif not bar.close < limit:
            order_executed = True
            price = limit
        else:
            order_executed = False
            limit_active = True
        ###
        if order_executed:
            new_quantity = order_quantity - quantity
            self.quantity = OrderValue(new_quantity)
            self.action = ('sold', bar.end_time(), quantity, price)            
            return Order.FILLED if new_quantity == 0 else Order.PARTIALLY, ts
        elif limit_active:
            self.type = 'limit'
        return None, ts
    
class OrderCondition():
    '''Shared functions for order conditions.'''
    
    def __init__(self, condition, *args, **kwds):
        ###
        self.args = args
        self.kwds = kwds
        self.condition = condition.lower()
        try:
            getattr(self, self.condition+'_check_parameters')()
        except KeyError as k:
            raise Error('unknown condition: {}'.format(self.condition))
        
    def __str__(self):
        ###
        str_function = getattr(self, self.condition+'_str')
        ###
        return str_function()
    
class OrderStartConditions(OrderCondition):
    '''Start parameters for an order.
    
    active method indicates if the order can be checked.
    
    Known conditions:
      now -- no extra parameters, just start now
      
    To add a new conditions foo, provide 3 function check code for
    further guidance: foo, foo_check_parameters, foo_str
    '''
    
    def active(self, data, order, sim_environment, timestamp):
        assert isinstance(data, DataBar)
        ###
        active = getattr(self, self.condition)
        ###
        active, ts = active(data, order, sim_environment, timestamp)
        return active, ts
    
    ### now ##########################################################
    ##
    ##    
    def now(self, data, order, sim_environment, ts):
        ###
        ###
        return True, ts
    ##
    def now_check_parameters(self):
        ###
        ###
        if self.args or self.kwds:
            return False
        return True
    ##
    def now_str(self):
        return 'now (active)'
    ##
    ##
    ##################################################################
    
    ### parent_filled ################################################
    ##
    ##
    def parent_filled(self, data, order, sim_environment, ts):
        assert isinstance(order, Order)
        assert isinstance(sim_environment, DevotedTrader)
        ##
        self.parent = order.parent_order
        self.order_active = (getattr(self, 'order_active', False)
                             or
                             self.parent in sim_environment.positions)
        ##
        return self.order_active, ts
    ##
    def parent_filled_check_parameters(self):
        ###
        ###
        if self.args or self.kwds:
            return False
        return True
    ##
    def parent_filled_str(self):
        ###
        parent = getattr(self, 'parent', '?')
        active = getattr(self, 'order_active', False)
        answer = 'after parent order (id={}) is filled'
        answer = answer.format(parent)
        if active:
            answer = ' '.join([answer, '(active)'])
        ###
        return answer
    ##
    ##
    ##################################################################
        
class RemoveOrderCondition(OrderCondition):
    '''Parameters to remove an order.
    
    ready_for_removal indicates if the order can be removed.
    
    Known conditions:
      GTC -- no extra parameters, it doesnt expire while it exists
      
    To add a new conditions foo, provide 3 function check code for
    further guidance: foo, foo_check_parameters, foo_str
    '''
    
    def expired(self, data, order, sim_environment, ts):
        assert isinstance(data, DataBar)
        ###
        expired = getattr(self, self.condition)
        ###
        expired, ts = expired(data, order, sim_environment, ts)
        return expired, ts
    
    ### GTC ##########################################################
    ##
    ##        
    def gtc(self, data, order, sim_environment, ts):
        '''GTC, Good Till Cancelled, doesn expire while it exists.'''
        ###
        ###
        return False, ts
    ##
    def gtc_check_parameters(self):
        ###
        ###
        if self.args or self.kwds:
            return False
        return True
    ##
    def gtc_str(self):
        return 'GTC'
    ##
    ##
    ##################################################################
    
    ### GTD ##########################################################
    ##
    ##
    def gtd(self, data, order, sim_environment, ts):
        '''GTD, Good Till Data or time, expires after date or time is reached'''
        assert isinstance(order, Order)
        assert isinstance(sim_environment, DevotedTrader)
        ###
        ###
        if self.test == 'date_test':
            test = data.time.date() > self.args[0]
        return test, ts
    
    def gtd_check_parameters(self):
        ###
        ###
        if (not len(self.args) == 1 
            or
            self.kwds):
            raise Error('GTD ordercondition wrong parameters')
        self.test = self.gtd_find_test()
        if self.test is None:
            raise Error('GTD ordercondition, unknown test value.')
        return True
    
    def gtd_str(self):
        return 'GTD {}'.format(self.args[0])
        
        
    def gtd_find_test(self):
        '''Returns a test depending on the type of the argument.'''
        ###
        arg = self.args[0]
        if isinstance(arg, date):
            #gtd_test = lambda curr: curr.date() > arg
            gtd_test = 'date_test'
        else:
            gtd_test = None
        return gtd_test
    
    ### parent_closed ################################################
    ##
    ##
    def parent_closed(self, data, order, sim_environment, ts):
        assert isinstance(order, Order)
        assert isinstance(sim_environment, DevotedTrader)
        ##
        self.parent = order.parent_order
        self.order_expired = (
            getattr(self, 'order_expired', False)
            or
            (self.parent in sim_environment.filled_and_removed_orders and
             self.parent not in sim_environment.positions))
        ##
        return self.order_expired, ts
    ##
    def parent_closed_check_parameters(self):
        ###
        ###
        if self.args or self.kwds:
            return False
        return True
    ##
    def parent_closed_str(self):
        ###
        parent = getattr(self, 'parent', '?')
        answer = 'parent order (id={}) is filled or removed'
        answer = answer.format(parent)
        ###
        return answer
    ##
    ##
    ##################################################################   
    
class OrderValue():
    '''To use in orders when you can not tell what a value will be at creation.
    
    It is called with the bar and the simulator environment, use and define
    with care. It must also return the new timestamp, becaus the user can not
    know what happens inside.
    
    Known calculations:
      fix_from_avg_in_order_id -- 
    '''
    def __init__(self, calculation, *args, **kwds):
        ###
        if isinstance(calculation, (int, float)):
            if not args and not kwds:
                args = [calculation]
                calculation = 'number'
            else:
                raise Error('args and kwds not alowed with number')
        self.args = args
        self.kwds = kwds
        self.calculation = calculation.lower()
        try:
            getattr(self, self.calculation+'_check_parameters')()
        except KeyError as k:
            raise Error('unknown calculator: {}'.format(self.calculation))
        
    def __str__(self):
        ###
        str_function = getattr(self, self.calculation+'_str')
        ###
        return str_function()
    
    def value(self, data, order, sim_environment, ts):
        assert isinstance(data, DataBar)
        ###
        calculation = getattr(self, self.calculation)
        ###
        calculation, ts = calculation(data, order, sim_environment, ts)
        return calculation, ts
    
    def is_null(self, ts):
        '''Function that doesn't move timestamp.'''
        if (not self.calculation == 'number'
            or
            not self.args[0] == 0):
            return False, ts
        return True, ts
    
    ### number #######################################################
    ##
    ##    
    def number(self, data, order, sim_environment, ts):
        '''Set and return an int or float.'''
        ###
        return self.args[0], ts
    ##
    def number_check_parameters(self):
        ###
        ###
        if (not len(self.args) == 1
            or
            self.kwds
            or
            not validate.as_int_or_float(self.args[0])):
            return False
        return True
    ##
    def number_str(self):
        ###
        ###
        return str(self.args[0])
    ##
    ##
    ##################################################################
    
    ### avg in parent ################################################
    ##
    ##
    def avg_in_parent(self, data, order, sim_environment, ts):
        assert isinstance(order, Order)
        assert isinstance(sim_environment, DevotedTrader)
        ##
        self.parent = order.parent_order
        avg_in, ts = sim_environment.avg_in(ts, self.parent)
        self.calculated_value = avg_in + self.args[0]
        ##
        return self.calculated_value, ts
    ##
    def avg_in_parent_check_parameters(self):
        ###
        ###
        if (not len(self.args) == 1
            or
            self.kwds
            or
            not validate.as_int_or_float(self.args[0])):
            return False
        return True
    ##
    def avg_in_parent_str(self):
        ###
        parent = getattr(self, 'parent', '?')
        calculated_value = getattr(self, 'calculated_value', False)
        if calculated_value:
            answer = str(calculated_value)
        else:
            answer = 'average in parent order (id={}) {:+}'
            answer = answer.format(parent, self.args[0])
        ###
        return answer
    ##
    ##
    ##################################################################
    
    ### no limit ################################################
    ##
    ##
    def no_limit(self, data, order, sim_environment, ts):
        assert isinstance(order, Order)
        assert isinstance(sim_environment, DevotedTrader)
        ##
        return None, ts
    ##
    def no_limit_check_parameters(self):
        ###
        ###
        if self.args or self.kwds:
            return False
        return True
    ##
    def no_limit_str(self):
        ###
        return 'no limit'
        
        
class OrderLists():
    """Analyser for order lists."""
    def __init__(self,
                 open_orders=None, positions=None, closing_and_closed=None,
                 from_file=None,):
        if from_file is not None:
            open_orders, positions, closing_and_closed = import_pickle(from_file)
        elif None in (open_orders, positions, closing_and_closed):
            raise Error('Needs a filename or 3 lists')
        self.open_orders = open_orders
        self.positions = positions
        self.closing_and_closed = closing_and_closed
        
    def print_c_and_c(self):
        positions = cash_account = previous_net = 0
        for k in sorted(self.closing_and_closed.keys()):
            for a in self.closing_and_closed[k]['actions']:
                time_, nr, price = a
                positions += nr
                cash_account += -nr * price
                if positions == 0:
                    result = cash_account - previous_net
                    in_trade = time_ - previous_time
                    print('{:6} | {} | {:4} | {:8} || {:6} | {:8.2f} | {:6.2f}'
                          ' | {}'.
                          format(k, time_, nr, price, 
                                 positions, cash_account, result, in_trade))
                    previous_net = cash_account
                else:
                    print('{:6} | {} | {:4} | {:8} || '.format(k,
                                    time_, nr, price))
                    previous_time = time_
                    
                