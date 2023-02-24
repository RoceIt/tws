#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#
from collections import defaultdict
from math import ceil

import roc_input as r_in
import roc_output as r_out
import roc_string as r_str
import roc_classes as r_class

from roc_currency import *

class Error(Exception): pass

class Order():
    '''An order.
    
    A complete order definition, to send to a market. All possible
    order settings are in this class. Not all settings may be 
    implemented by all markets.
    Where numbers are required you can also use a an OrderValue 
    tupple. The market then takes care of calculating the value.
    Three other attributes must be filled in by the markets the order
    is send to:
    the market_id, id_ and the time the order was received.    
    
    Parameters:
      id -- unique id to track order or get info
      action -- buy or sell or close
      size -- number of units to buy/ or part of parent to close
      contract -- unique contract name/id or from parent
      start -- list with start conditions tupples
      until -- list with valid until conditions tupples
      type -- type of the order
     [parent_order_id -- linked order, used in some conditions]
     [message -- a message that the order can use]
     [minimal_tick -- min tick size to round calculated prizes]
     
    Start conditions:
      parent_filled -- start when parent is filled
      now -- becomes active immediately
      
    Until conditions:
      GTC -- good till cancel
      GTD -- good till date(time)
          * date(time)
      parent_closed  -- until parent order is removed or closed
      
    Types:
      market -- trade at marketprice
          * no extra parameters expected
      limit -- trade when limit is reached
          * limit
      stop -- (send) market order when stop is at or over stop
          * stop
      stop_limit -- becomes a limit order when the stop is reached
          * stop
          * limit
          
      OrderValues:
        avg_in_parent -- add/subtract ofset from  avg price in parent order
          * ofset
      
    '''    
    REQUIRED_ORDER_ATTRIBUTES = (
        'id', # string, can't change during existance  
        'action', # string, some strings can change in preprocessing(pp),
                  # can't change after preprocessing
        'size', # number or tuple, can change during existance
                # changed to size returning ManagedOrderValue during pp
        'contract', # string, can't change during existance
        'start', # empty or tuple, can change during existance
                 # changed to text/True returning ManagedOrderValue during pp
        'until', # empty or tuple, can change during existance
                 # changed to text/True returning ManagedOrderValue during pp 
        'type', # string, can't change during existance
    )
    OPTIONAL_ORDER_ATTRIBUTES = (
        'parent_order_id', # sring, can't change during existance,
        'message', # string, can change during existance
                   # changed to string returning ManagedOrderValue during pp
        'minimal_tick', # float or int to set the minimal tick size for
                        # calculated values
    )
    REQUIRED_TYPE_ATTRIBUTES = {
        'market': tuple(),
        'limit': ('limit', # number or tuple, can change during existance
                           # changed to number returning ManagedOrderValue
                           # during pp
        ),
        'stop': ('stop', # number or tuple, can change during existanc
                         # changed to number returning ManagedOrderValue
                         # during pp
        ),
        'stop_limit': ('limit', # see limit ^ 
                       'stop', # see stop ^
        )
    }
    OPTIONAL_TYPE_ATTRIBUTES = {
        'market': tuple(),
        'limit': tuple(),
        'stop' : tuple(),
        'stop_limit': tuple(),
    }
    ORDER_TYPES = REQUIRED_TYPE_ATTRIBUTES.keys()
    TYPE_ATTRIBUTES = set()
    for a in (
        REQUIRED_TYPE_ATTRIBUTES.values(), 
        OPTIONAL_TYPE_ATTRIBUTES.values()
    ):
        for attribute_list in a:
            for attribute in attribute_list:
                TYPE_ATTRIBUTES.add(attribute)
    
    def __init__(self, **kwds):
        '''Initiate the order.
        
        For keywords and valid values, c the class documentation
        '''
        ###
        ###
        for attr in self.REQUIRED_ORDER_ATTRIBUTES:
            try: parameter = kwds.pop(attr)
            except KeyError as err:
                raise Error('missing parameter {}'.format(attr))
            setattr(self, attr, parameter)
        if not self.type in self.ORDER_TYPES:
            raise Error('unknonw type {}'.format(self.type))
        for attr in self.REQUIRED_TYPE_ATTRIBUTES[self.type]:
            try: parameter = kwds.pop(attr)
            except KeyError as err:
                raise Error('missing parameter {}'.format(attr))
            setattr(self, attr, parameter)
        optional_parameters = self.OPTIONAL_ORDER_ATTRIBUTES
        optional_parameters += self.OPTIONAL_TYPE_ATTRIBUTES[self.type]
        for attr in optional_parameters:
            setattr(self, attr, kwds.pop(attr, None))
        if kwds: # raise error when unused parameters are found
            raise Error('unknown Order parameters: {}'. format(kwds.keys()))
        self.signal = None
        
    def __str__(self):
        ###
        t = r_str.SerialTextCreator()
        t.add_chunk('order')
        t.underline()
        for arglist in (self.REQUIRED_ORDER_ATTRIBUTES,
                        self.OPTIONAL_ORDER_ATTRIBUTES,
                        self.TYPE_ATTRIBUTES,
        ):
            for arg in arglist:
                value = getattr(self, arg, None)
                if value:
                    if callable(value):
                        value = value()
                    t.add_line('{}: {}'.format(arg, value))
        ###
        return str(t)

class OrderInfo(r_class.FixedAttributes):
    
    def __init__(self, order):
        self.order = order
        self.activated = False
        self.filled = False   
        self.stopped = False
        self.size = 0
        self.total_value = Currency(0)
        self.__history = []
        self.children = []
        super().__init__()
        
    def __str__(self):
        t = r_str.SerialTextCreator()
        t.add_chunk('activated:')
        t.add_chunk(str(self.activated))
        t.next_line()
        t.add_chunk('filled:')
        t.add_chunk(str(self.filled))
        t.next_line()
        t.add_chunk('stopped:')
        t.add_chunk(str(self.stopped))
        t.next_line()
        t.add_chunk('size:')
        t.add_chunk(str(self.size))
        t.next_line()
        t.add_chunk('total_value:')
        t.add_chunk(str(self.total_value))
        if self.children:
            t.next_line()
            t.add_chunk('children: ')
            for child in self.children:
                t.add_chunk(child)
        return str(t)
    
    @property
    def order(self):
        return self.__order
    
    @order.setter
    def order(self, an_order):
        assert isinstance(an_order, Order),(
            'bad init type for order: {}'.format(type(an_order)))
        try:
            self.order
            raise Error('You can\'t change the orderinfo order.')
        except AttributeError:
            self.__order = an_order
    
    @property
    def total_value(self):
        return self.__total_value
    
    @total_value.setter
    def total_value(self, value):
        assert isinstance(value, Currency), 'value must be a currency'
        self.__total_value = value
    
    @property
    def history(self):
        return self.__history
    
    def register_new_action(self, time_, size, value):
        print('registering {} | {} for {} @ {}'.format(
                        self.order.id, str(size), str(value), time_))
        assert self.activated, 'order must be active first'
        assert self.order.start() is True, 'order must have start True'
        assert not self.stopped, 'order was already stopped!'
        self.__history.append((time_, size, value))
        action = self.order.action
        if action == 'sell' and size > 0:
            raise Error('sell order, add size must be < 0')
        elif action == 'buy' and size < 0:
            print(' | ', size, ' | ')
            raise Error('buy order, add size must be > 0')
        if self.size:
            self.size += size
        else:
            self.size = size
        if (action == 'buy' and self.size > self.order.size()
            or
            action == 'sell' and self.size < -self.order.size()
        ):
            raise Error('order overfilled??')
        if abs(self.size) == self.order.size():
            self.filled = True
            self.stopped = True
        else:
            self.filled = abs(self.size / self.order.size())
        added_value = value * size
        if self.total_value.is_zero():
            self.total_value = added_value
        else:
            self.total_value += added_value
            
    @property
    def average_price(self):
        try:
            return self.total_value / self.size
        except ZeroDivisionError:
            return None
        
    @property
    def signal(self):
        return self.order.signal
        
            
class ManagedOrderValue():
    """Order values for activated orders.
    
    When an order is activated all values (except id's &
    contract name) must be translated to order specific values.
    """
    def __init__(self, value):
        """Initialize the market specific order."""
        self.value = value
        
    def __call__(self):
        """Return the content of value."""
        self.update_value()
        return self.value
    
    def update_value(self):
        """Updete the the value.
        
        If it can be updated, it must be implemented in the subclas!
        """
        pass
  
    
DEFAULT_MARKET_NAME = '!! default manual market mode !!'
class Market():
    """API baseclass to a 'real word' market.
    
    The class itself implements an interactive market interface. The
    last 2 sectoins of methods are market specific.  The before last
    section methods must all be reimplemented in markets you derive
    from this class, they are used in the standerd (dont mess with
    them) methods. The last section are all helper methods for the 
    market specific methods, remome them for derived classes and add
    your own as needed.
    
    The trader_time attribute is holding the current time of the 
    trader (actualy the time the last request was send).  Live 
    markets may not need this. But it's vital for simulations where
    you have to move the market forward yourself. And who knows
    maybe it will find some usefull purposes in the future?
    """
    
    def __init__(self):
        ###
        ###
        self.new_orders = dict()
        self.active_orders = dict()
        self.finished_orders = dict()
        self.info = dict()
        self.last_market_sync_time = self._initial_market_time()
        self.data_of_contracts = MarketDataLog()
        
    def __str__(self):
        ###
        t = r_str.SerialTextCreator()
        t.add_line(self.name)
        t.add_chunk('# active orders: ')
        t.add_chunk(str(len(self.active_orders)))
        t.next_line()
        t.add_chunk('# finished orders: ')
        t.add_chunk(str(len(self.finished_orders)))
        ###
        return str(t)
        
    @property
    def name(self):
        """Return/set the name of the market.
        
        Whenever you create a subclass, you must give it an explicit
        name or an Error will be raised.
        If Market is used directly as a market, it is called 
        DEFAULT_MARKET_NAME. This market is completly interactive. 
        You'll have to manually immitate a market.
        
        """
        ###
        try:
            name = self.__name
        except AttributeError:
            name = None
        ###
        if name is None:
            if self.__class__.__name__ == 'Market':
                name = DEFAULT_MARKET_NAME
            else:
                mss = ('No name defined in Market subclass: {}'.
                       format(self.__class__.__name__))
                raise Error(mss)
        return name
    
    @name.setter
    def name(self, name):
        try:
            self.__name
            raise Error('You can set name only once')
        except AttributeError:
            pass
        ###
        ###
        self.__name = name
    
    def validate_contract_name(self, name):
        """Return True if market can handle contract.
        
        'default' is not allowed as name, all other names will be send
        to the market specific function.
        """
        valid = (
            not name == 'default'                                            and
            self._validate_contract_name(name)
        )
        return valid
    
    def new_order(self, order):
        """Put order in new_order waiting list.
        
        The order is just added to the dict new_orders, maybe some of
        the values it wants to use depend on other orders.  Or maybe
        the market has some features to handle some situations
        involving multiple orders.
        So add as much new orders to the market as you want and then
        activate them (don't forget!). The market specific  
        _activate_new_orders function must do the checking and
        translation of the new orders and direct them in the most
        ideal form to the real world market.
        """
        ###
        ###
        self.new_orders[order.id] = order
        self.info[order.id] = OrderInfo(order)
        
    def activate_new_orders(self, at_time):
        """Check new orders and instruct the 'real world' market.
        
        First the orders are preprocessed, all non market specific &
        market specific information that should be available to the
        orders at this point is placed in the orders.
        Next it searches for the grouped orders and activated them.
        Finally the single orders are activated.
        """
        ###
        ###
        #self.trader_time = at_time
        self.sync_with_trader(at_time)
        for order in self.new_orders.values():
            self.preproces(order)
        self.activate_grouped_orders()
        self.activate_single_order()
        if self.new_orders:
            raise Error('Not all new orders are activated!')
        
    def change_existing_order(self, 
                    order_id, attribute, new_value, at_time, min_tick):
        print(order_id, attribute, new_value, at_time)
        self.sync_with_trader(at_time)
        try:
            requested_order = self.active_orders[order_id]
        except KeyError:
            pass
        if attribute == "stop":
            new_value = self.round_up_to_min_tick(
                new_value, requested_order.action,
                requested_order.type, min_tick)
            requested_order.stop = ManagedOrderValue(new_value)
        self._warning_order_changed(order_id, attribute, new_value)
    
    def status_report(self, order_id, at_time):
        '''Check current status of order on market and send report
        '''
        ###
        ###
        self.sync_with_trader(at_time)
        try:
            info = self.info[order_id]
        except KeyError:
            raise Error('order not found: {}'.format(order_id))        
        return info
    
    ### not for users        
    #
    #
    
    def preproces(self, order):
        """If order attribute values are tuples, check if action is needed.
        """
        print('preprocessing: ', order)
        optional_preprocessors = {
            'limit': self.preproces_limit,
            'stop': self.preproces_stop,
        }
        self.preproces_action(order)
        self.preproces_size(order)
        self.preproces_start(order)
        self.preproces_until(order)
        for attribute, preprocesmethod in optional_preprocessors.items():
            if hasattr(order, attribute):
                preprocesmethod(order)
        if hasattr(order, 'message'):
            self.preproces_message(order)
            
    def preproces_action(self, order):
        """Set order action."""
        ###
        action = order.action.lower()
        ###
        if action in ('buy', 'sell'):
            pass
        elif action == 'close':
            self.preproces_close_action(order)
        else:
            raise Error('Undefined action: {}'.format(action))
        
    def preproces_close_action(self, order): 
        """Make changes to enable creation of a close order.
        
        - checking a parent order is defined
        - change the order action to the opposite action of the parent
        - check if order contract, order start and order until are empty
        - set order contract to parent contract
        - set start to get active when parent has positions
        - set until to when parent group has no positions left
        """
        assert hasattr(order, 'parent_order_id'), (
            'Close action needs parent_order_id')
        assert order.parent_order_id in self.info, (
            'Unknown parent order')
        assert self.info[order.parent_order_id].order.action in ('buy', 'sell'),(
            'Unknown parent order action')
        assert not(order.contract or order.until), (
            'No contract,or until alowed in close order')
        ###
        parent_order = self.info[order.parent_order_id].order
        parent_order_action = parent_order.action
        action = 'sell' if parent_order_action == 'buy' else 'buy'
        ###
        order.action = action
        order.contract = parent_order.contract
        #self.preproces_start_when_parent_has_positions(order)
        if not order.start:
            order.start = ('parent',)
        self.preproces_until_positions_in_parent_group(order)
        
    def preproces_size(self, order):
        """Set order size."""
        if isinstance(order.size, ManagedOrderValue):
            return
        ###
        condition, *parameters = order.size
        condition = condition.lower()
        ###
        if condition == 'number':
            if not len(parameters) == 1:
                raise Error('number size takes just 1 paremeter, '
                            'the number.')
            order.size = ManagedOrderValue(parameters[0])
        elif condition == 'parent':
            if not len(parameters) == 1:
                raise Error('parent size takes just 1 parameter, '
                            'percentage of parent size position')
            self.preproces_parent_size(order, percentage=parameters[0])
        else:
            raise Error('Undefined size definer')
        
    def preproces_parent_size(self, order, percentage):
        """Set size to a percentage of the parent size."""
        assert hasattr(order, 'parent_order_id'), (
            'Close action needs parent_order_id')
        assert order.parent_order_id in self.info, (
            'Unknown parent order')
        ###
        mss = ('{percentage}% of parent order ({parent_order_id}) postions'.
               format(percentage=percentage, 
                      parent_order_id=order.parent_order_id,
        ))
        class Size(ManagedOrderValue):
            def __init__(size, value):
                size.parent_order_info = self.info[order.parent_order_id]
                super().__init__(value)
            def update_value(size):
                parent_size = abs(size.parent_order_info.size)
                if not parent_size == 0:
                    size.value = ceil(parent_size * percentage / 100) 
        order.size = Size(mss)
        
    def preproces_start(self, order):
        """Set order start to ManagedOrderValue."""
        if isinstance(order.start, ManagedOrderValue):
            return
        set_start_manager_tr = {
            'now': self.set_start_now,
            'gat': self.set_start_gat,
            'parent': self.set_start_when_parent_has_positions,
            'on signal': self.set_start_when_signalled,
        }
        ###
        condition, *foo = order.start
        ###
        try:
            set_start_manager_tr[condition](order)
        except KeyError:
            raise Error('Undefined start condition: {}'.format(until))
        
    def set_start_now(self, order):
        """Make start always return True."""
        ###
        order.start = ManagedOrderValue(True)
        
    def set_start_gat(self, order):
        """Make start return True after gat time is reached."""
        foo, date_time = order.start
        class Starter(ManagedOrderValue):
            def __init__(starter, value):
                starter.date_time = date_time
                super().__init__(value)
            def update_value(starter):
                if self.last_market_sync_time > starter.date_time:
                    order.start = ManagedOrderValue(True)
        order.start = Starter('after {}'.format(date_time))
        
    def set_start_when_parent_has_positions(self, order):
        """Make start return True when parent has position."""
        ###
        mss = ('Order waiting for parent order {} to take a position'.
               format(order.parent_order_id))
        class Starter(ManagedOrderValue):
            def __init__(starter, value):
                #starter.parent_order_info = self.info[order.parent_order_id]
                starter.parent_order_id = order.parent_order_id
                super().__init__(value)
            def update_value(starter):
                #if starter.parent_order_info.filled is not False:
                if self.info[starter.parent_order_id].filled is not False:
                    order.start = ManagedOrderValue(True)
        order.start = Starter(mss)
        
    def set_start_when_signalled(self, order):
        """Make start return True when order signal has set value."""
        foo, expected_signal = order.start
        mss = ('order waiting for signal: {}'.format(expected_signal))
        class Starter(ManagedOrderValue):
            def __init__(starter, value):
                starter.expected_signal = expected_signal
                super().__init__(value)
            def update_value(starter):
                #print('*', order.signal, type(order))
                if order.signal == starter.expected_signal:
                    print('***************************')
                    order.signal = None
                    order.start = ManagedOrderValue(True)
        order.start = Starter(mss)
        
    def preproces_until(self,order):
        """Set order until to ManagedOrderValue.
        
        If you create a new update function, make sure it also sets
        the self.stopped attribute to True! For gtc this is not
        nescessary becaus the order is manually removed by the user.
        """
        if isinstance(order.until, ManagedOrderValue):
            return
        set_until_manager_tr = {
            'gtc': self.set_until_gtc,
            'gtd': self.set_until_gtd,
        }
        ###
        condition, *foo = order.until
        ###
        try:
            set_until_manager_tr[condition](order)
        except KeyError:
            raise Error('Undefined until condition: {}'.format(until))
        #if until.lower() == 'gtc':
            #if parameters:
                #raise Error('until gtc doesn\'t take parameters')
            #self.preproces_until_gtc(order)
        #else:
            #raise Error('Undefined until condition: {}'.format(until))
    
    def set_until_gtc(self, order):
        """Make until always return True.
        
        The order is valid until the user takes it away.
        """
        ###
        order.until = ManagedOrderValue('good until cancel.')
        
    def set_until_gtd(self, order):
        """good till date.
        
        The order is valid while gtd after current time.
        """
        foo, gtd = order.until
        class ValidUntil(ManagedOrderValue):
            def __init__(until, value):
                until.last_valid_time = gtd
                super().__init__(value)
            def update_value(until):
                if self.last_market_sync_time > until.last_valid_time:
                    order.until = ManagedOrderValue(False)
        order.until = ValidUntil('Good Till Date: {}'.format(gtd))
        
            
    def preproces_until_positions_in_parent_group(self, order):
        """Make until return false when parent group has no positions."""
        order_id = order.id
        parent_id = order.parent_order_id
        mss1 = ('Order not started yet, waiting for for positions in parent {}'.
                format(parent_id))
        mss2 = ('until positions left in parent group {}.'.
                format(parent_id))
        class ValidUntil(ManagedOrderValue):
            def __init__(valid_until, value):
                valid_until.mss_after_started = mss2
                super().__init__(value)
            def update_value(valid_until):
                group_ids = self.parent_and_sibling_ids(parent_id)
                positions_in_group = self.positions_in_group(group_ids)
                parent_info = self.info[parent_id]
                if (parent_info.filled is not False
                    or
                    parent_info.stopped is True
                ):
                    if positions_in_group:
                        valid_until.value = valid_until.mss_after_started
                    else:
                        order.until = ManagedOrderValue(False)
        order.until = ValidUntil(mss1)
        
    def preproces_stop(self, order):
        """Set stop value."""
        if isinstance(order.stop, ManagedOrderValue):
            return
        set_stop_manager_tr = {
            'number': self.set_stop_number,
            'ofset': self.set_stop_ofset,
            'percentage': self.set_stop_percentage,
        }
        ###
        condition, *foo = order.stop
        ###
        try:
            set_stop_manager_tr[condition](order)
        except KeyError:
            raise Error('Unknown stop definer')
            
    def set_stop_number(self, order):
        """Set stop as number."""
        foo, number = order.stop
        ###
        order.stop = ManagedOrderValue(number)
        
    def set_stop_ofset(self, order):
        """Set stop value as ofset."""
        foo, base, ofset, min_tick = order.stop
        base = self.calculate_base_function(base, order)
        class Stop(ManagedOrderValue):
            def __init__(stop, value):
                stop.base = base
                stop.ofset = ofset
                stop.min_tick = min_tick
                stop.action = order.action
                if stop.action == 'sell':
                    stop.ofset *= -1
                super().__init__(value)
            def update_value(stop):
                base = stop.base()
                if base is not None:
                    stop.value = self.round_up_to_min_tick(
                        base + base.__class__(stop.ofset),
                        stop.action, "stop",
                        stop.min_tick,
                    )                        
        order.stop = Stop(base)
        
    def set_stop_percentage(self, order):
        """Set stop value as percentage."""
        foo, base, percentage, min_tick = order.stop
        base = self.calculate_base_function(base, order)
        class Stop(ManagedOrderValue):
            def __init__(stop, value):
                stop.base = base
                stop.percentage = percentage
                stop.min_tick = min_tick
                stop.action = order.action
                if stop.action == 'sell':
                    stop.percentage *= -1
                super().__init__(value)
            def update_value(stop):
                base = stop.base()
                if base is not None:
                    stop.value = self.round_up_to_min_tick(
                        base * (1 + stop.percentage / 100),
                        stop.action, "stop",
                        stop.min_tick,
                        )
                    if stop.action == "sell":
                        stop.value -= stop.value.__class__(0.5)
                    else:
                        stop.value += stop.value.__class__(0.5)
        order.stop = Stop(base)
        
    def preproces_limit(self, order):
        """Set limit value."""
        if isinstance(order.limit, ManagedOrderValue):
            return
        set_limit_manager_tr = {
            'number': self.set_limit_number,
            'ofset': self.set_limit_ofset,
            'percentage': self.set_limit_percentage,
        }
        ###
        condition, *foo = order.limit
        ###
        try:
            set_limit_manager_tr[condition](order)
        except KeyError:
            raise Error('Unknown limit definer')
            
    def set_limit_number(self, order):
        """Set limit as number."""
        foo, number = order.limit
        ###
        order.limit = ManagedOrderValue(number)
        
    def set_limit_ofset(self, order):
        """Set limit value as ofset."""
        foo, base, ofset, min_tick = order.limit
        base = self.calculate_base_function(base, order)
        class Limit(ManagedOrderValue):
            def __init__(limit, value):
                limit.base = base
                limit.ofset = ofset
                limit.min_tick = min_tick
                limit.action = order.action
                if limit.action == 'buy':
                    limit.ofset *= -1
                super().__init__(value)
            def update_value(limit):
                base = limit.base()
                if base is not None:
                    limit.value = self.round_up_to_min_tick(
                        base + base.__class__(limit.ofset),
                        limit.action, "limit",
                        limit.min_tick,
                    )
        order.limit = Limit(base)
        
    def set_limit_percentage(self, order):
        """Set limit value as percentage."""
        foo, base, percentage, min_tick = order.limit
        base = self.calculate_base_function(base, order)
        class Limit(ManagedOrderValue):
            def __init__(limit, value):
                limit.base = base
                limit.percentage = percentage
                limit.min_tick = min_tick
                limit.action = order.action
                if limit.action == 'buy':
                    limit.percentage *= -1
                super().__init__(value)
            def update_value(limit):
                base = limit.base()
                if base is not None:
                    limit.value = self.round_up_to_min_tick(
                        base * (1 + limit.percentage / 100),
                        limit.action, "limit",
                        limit.min_tick,
                        )
        order.limit = Limit(base)
        
    def calculate_base_function(self, base, order):
        '''Return a managed value instance.
        
        If the base can't be defined yet, return 0.
        '''
        calculate_base_tr = {
            'avg_parent_in': self.cbf_average_parent_in,
        }
        return calculate_base_tr[base](order)
    
    def cbf_average_parent_in(self, order):
        '''Return the average parent in.
        
        If the parent order has positions, return the average
        in, else return None.
        '''
        parent_id = order.parent_order_id
        class AverageParentIn(ManagedOrderValue):
            def __init__(api):
                api.parent_order_id = parent_id
                super().__init__(None)
            def update_value(api):
                api.value = self.info[api.parent_order_id].average_price
        return AverageParentIn()
    
    def preproces_message(self, order):
        """Return a ManagedOrderValue that formats the string.
        
        Must be the last preprocessor, so it knows what the type
        of every order attribute is.
        """
        mutable_attributes = [
            'size', 'start', 'until', 'stop', 'limit',
            # don't add 'message' here
        ]
        class Message(ManagedOrderValue):
            def __init__(message, value):
                message.base_massage = value
                message.basedict = {
                    'id': order.id,
                    'action': 'bought' if order.action=='buy' else 'sold',
                    'contract': order.contract,
                    'type': order.type,
                }
                if hasattr(order, 'parent_order_id'):
                    message.basedict['parent_order_id'] = order.parent_order_id
                message.update_list = [
                    x for x in mutable_attributes if hasattr(order, x)
                ]
                message.update_value()
                
            def update_value(message):
                for attribute in message.update_list:
                    message.basedict[attribute] = getattr(order, attribute)()
                message.value = message.base_massage.format(**message.basedict)
        order.message = Message(order.message)
        
    def sync_with_trader(self, at_time):
        """Update all orders.
        
        When this function is finished, all active orders are synced
        with the current(at_time) market situation. Live servers can
        check the at_time and do something, can't think of anything
        now. Symulated markets will sync to the bar that includes
        at_time. If the bar starts at_time it will only be evaluated
        after the next call to this function. 
        All this must be implementen in the market specific functions.
        """
        if at_time < self.last_market_sync_time:
            raise Error('time reversed!??')
        while self.last_market_sync_time < at_time:       
            self.last_market_sync_time = self._sync_active_orders(at_time)
            self.replace_finished_orders()
        # Not all orders are informed about all the changes, i run the
        # order attribute updater a last time, so eveything is 
        # synced (time and info). It should be enough to do this once,
        # since updating attributes should not depend on the attributes
        # of other orders but on synced time and info of other orders.
        # the info of an orders should not change by updating attributes.
        for order_id in self.active_orders.keys():
            self.update_order_attributes(order_id)
        self.replace_finished_orders()
        
    def activate_grouped_orders(self):
        """Look for specially grouped orders and activate them.
        
        special groups:
          * parent_child
                Child orders get active when parent is (partially)
                filled.
        """
        ###
        self.activate_parent_child_orders()
        
    def activate_parent_child_orders(self):
        """Find and activate parent and child orders."""
        parent_childs_groups = {
            getattr(order, 'parent_order_id', None) 
            for order in self.new_orders.values()
        }
        parent_childs_groups.discard(None)
        for parent_order_id in parent_childs_groups:
            if parent_order_id not in self.new_orders:
                raise Error('Missing new parent for new child order: {}'.
                            format(parent_order_id))
            children = [
                order.id 
                for order in self.new_orders.values()
                if getattr(order, 'parent_order_id', None) == parent_order_id
            ]
            self.info[parent_order_id].children = children
            self._activate_parent_child_group(
                parent=self.new_orders[parent_order_id],
                children=[self.new_orders[x] for x in children],
            )
            self.move_orders_to_active_list(parent_order_id, children)
            
    def activate_single_order(self):
        """Activate stand alone orders."""
        for order_id in self.new_orders:
            self._activate_single_order(self.new_orders[order_id])
            self.move_orders_to_active_list(order_id)
            
    def move_orders_to_active_list(self, *args):
        """Move order_id's in args from new to active list.
        
        args can be order_id's or iterables with order_id's
        """
        for order_id in args:
            if isinstance(order_id, list):
                self.move_orders_to_active_list(*order_id)
            else:
                order = self.new_orders.pop(order_id)
                self.active_orders[order_id] = order
                self.info[order_id].activated = True
                
    #def update_active_orders(self):
        
        ##active_orders = list(self.active_orders.keys())
        ##while active_orders:
            ##curr_id = active_orders.pop(0)
            ##order_info = self.info[curr_id]
            ##parent_order = getattr(order_info.order, 'parent_order_id', None)
            ##if parent_order in active_orders:
                ##active_orders.append(curr_id)
                ##continue
            ##self.update_order(curr_id)
            ##for id_ in order_info.children:
                ##self.update_order(id_)
                ##active_orders.remove(id_)        
        #active_orders = list(self.active_orders.keys())
        #while active_orders:
            #curr_id = active_orders.pop(0)
            #order_info = self.info[curr_id]
            #parent_order = getattr(order_info.order, 'parent_order_id', None)
            #if parent_order in active_orders:
                #active_orders.append(curr_id)
                #continue
            #self.update_order(curr_id)
            #for id_ in order_info.children:
                #self.update_order(id_)
                #active_orders.remove(id_)
            
    #def update_order(self, id_):

        #self.update_order_attributes(id_)
        #if self.active_orders[id_].until() is not False:
            #self._update_order(id_)
        #else:
            #self.info[id_].stopped=True
        
    def update_order_attributes(self, id_):
        
        mutable_attributes = [
            'size', 'start', 'until', 'stop', 'limit', 'message'
        ]
        order = self.active_orders[id_]
        for attribute in mutable_attributes:
            update_action = getattr(order, attribute, None)
            if update_action:
                update_action()
    
    def replace_finished_orders(self):
        active_orders = list(self.active_orders.keys())
        for k in active_orders:
            if (self.info[k].filled is True
                or
                self.info[k].stopped
                or
                self.active_orders[k].until() is False
            ):
                self.finished_orders[k] = self.active_orders.pop(k)
                if self.info[k].stopped is False:
                    self.info[k].stopped = True
                
    def ordered_active_orders_ids(self):
        """Return list with sorted active orderd keys.
        
        ordered as:
          p1 ch1a ch1b p2 ch2 p3 ch3a ch3b ch3c p4 ...
        """
        order_order = []
        for order_id in sorted(self.active_orders.keys()):
            if order_id in order_order: continue
            parent_id = getattr(
                self.info[order_id].order,
                'parent_order_id',
                None
            )
            if parent_id:
                if (parent_id in self.active_orders                          and
                    parent_id not in order_order
                ):
                    order_order.append(parent_id)
                for child in self.info[parent_id].children:
                    order_order.append(child)
            else:
                order_order.append(order_id)
            #if order_order:
                #print('$$$%$$$', order_order)
        return order_order
        
                
    def parent_and_sibling_ids(self, parent_id):
        parent_order_info = self.info[parent_id]
        ids = [parent_id]
        ids.extend(parent_order_info.children)
        return ids
    
    def positions_in_group(self, ids):
        
        positions = defaultdict(int)
        for id_ in ids:
            info = self.info[id_]
            positions[info.order.contract] += info.size
        positions = {
            k:v 
            for k,v in positions.items()
            if not v == 0
        }
        return positions
    
    def round_up_to_min_tick(self, value, action, order_type, min_tick):
        if min_tick is None:
            return value
        if action == 'sell':
            if order_type == "limit":
                return value.round_up_to(min_tick)
            if order_type == "stop":
                return value.round_down_to(min_tick)
        if action == 'buy':
            if order_type == "limit":
                return value.round_down_to(min_tick)
            if order_type == "stop":
                return value.round_up_to(min_tick)
    
                
    ####################
    #
    # define market specific versions for all following functions
    # in derived subclasses
    #
    ####################
    CALL_MARKET = '>>> Hey market!!'
    
    def _initial_market_time(self): ###market specific ###
        """Return the first time known to this market."""
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('_valid_contract_name not redefined')
        ###
        ask_the_market, date_format = (
            '{} What is the first time known to this market (yy/dd/mm H:M:S)? '.
            format(self.CALL_MARKET),
            '%y/%m/%d %H:%M:%S')
        initial_time = r_in.get_datetime(
            message=ask_the_market,
            time_format=date_format,
            default='now')
        return initial_time        
    
    def _validate_contract_name(self, name): ### market specific ###
        """Return True if market can handle contract.
        
        name is checked OTC.
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('_valid_contract_name not redefined')
        ###
        ask_the_market = (
            '{} Is {} a valid contract name? '.
            format(self.CALL_MARKET, name)
        )
        ###
        valid =  r_in.get_bool(ask_the_market)
        return valid
        
    def _activate_parent_child_group(self, parent, children):
        """Activate parent child group.
        
        The interactive default market is verbose as always and sends 
        the instructions as text to the user.
        
        I think in virtual markets, this function will be short. All
        work have to be done in the _update function.
        
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('_activate_parent_child_group not redefined')
        ###
        ###
        print(self.CALL_MARKET)
        print('>')
        print('> Parent order with {nr_of_children} children'.
              format(nr_of_children=len(children)))
        print('>')
        self._print_order(parent)
        print('>')
        print('> CHILDREN: ')
        for child in children:
            print('> ')
            self._print_order(child)
        
    def _activate_single_order(self, order):
        """Activate single order.
        
        The interactive default market is verbose as always and sends 
        the instructions as text to the user.
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('_activate_single_order not redefined')
        ###
        type_ = order.type
        ###
        print(self.CALL_MARKET)
        if type_ == 'market':
            self._print_market_order_instructions(order)
        else:
            raise Error('Unknown order type: {}'.format(type_))
        
    def _sync_active_orders(self, target_sync_time):
        """update info for all orders.
        
        It must not update until the target_sync_time, the method
        will be called again until it's reached. Make sure to
        return the time to where you have updated the active
        orders.
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('_activate_single_order not redefined')
        ###
        for order_id in self.ordered_active_orders_ids():
            print('moving market to time {}'.format(target_sync_time))
            # placing this update take some considertions. Is it
            # appropriate to move the attribures to a future time
            # while the sync_time is still the old. In live markets
            # there is no problem, you can check if the order was
            # executed. In this interactive market i decided it's up
            # to the user to decide. In other markets think about it.
            self.update_order_attributes(order_id)
            self._update_order(order_id)
        return target_sync_time
    
    def _warning_order_changed(self, order_id, attribute, new_value):
        """IMPORTANT when using an other market (eg live).
        
        When using an other market it can not know about the changes
        made in this market. Make sure to take the approriate actions.
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('_activate_single_order not redefined')
        pass
        
    ####################
    #
    # market specific helper functions, make sure they are only used
    # by the required market specific functions above or other helper 
    # functions defined below.
    # They don't have to be redefined in subclasses, use this place in 
    # subclasses to define you're own helper functions.
    #
    
    def _print_order(self, order):
        print_tr = {
            'market': self._print_market_order_instructions,
            'limit': self._print_limit_order_instructions,
            'stop': self._print_stop_order_instructions,
        }
        try:
            print_tr[order.type](order)
        except KeyError:
            raise Error('Unknown order type: {}'.format(order.type))
        
    def _print_market_order_instructions(self, order):
        """Activate market order.
        
        The interactive default market is verbose as always and sends 
        the instructions as text to the user.
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('Market specific helper function only for {}'.
                        format(DEFAULT_MARKET_NAME))
        ###
        start, until = order.start(), order.until()
        if start is True:
            start = 'now'
        if until is False:
            until = 'no longer valid.'
        ###
        print('> ORDER: {}'.format(order.id))
        print('> market order: {action} {size} {contract} {start}, {until}'.
              format(action=order.action,
                     size=order.size(),
                     contract=order.contract,
                     start=start,
                     until=until,
        ))
        print('>    reason if executed --> {}'.format(order.message()))
        
    def _print_stop_order_instructions(self, order):
        """Activate stop order.
        
        The interactive default market is verbose as always and sends 
        the instructions as text to the user.
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('Market specific helper function only for {}'.
                        format(DEFAULT_MARKET_NAME))
        ###
        start, until = order.start(), order.until()
        if start is True:
            start = 'now'
        if until is False:
            until = 'no longer valid'
        if order.action == 'sell':
            condition = 'lower or equal then '
        else:
            condition = 'higher or equal then '
        ###
        print('> ORDER: {}'.format(order.id))
        print('> stop order: {action} {size} {contract}\n' 
              '>             if {contract} {condition} {stop}\n'
              '>             {start}, {until}'.
              format(action=order.action,
                     size=order.size(),
                     contract=order.contract,
                     start=start,
                     until=until,
                     condition=condition,
                     stop=order.stop()
        ))
        print('>    reason if executed --> {}'.format(order.message()))
        
    def _print_limit_order_instructions(self, order):
        """Activate limit order.
        
        The interactive default market is verbose as always and sends 
        the instructions as text to the user.
        """
        if not self.name == DEFAULT_MARKET_NAME:
            raise Error('Market specific helper function only for {}'.
                        format(DEFAULT_MARKET_NAME))
        ###
        start, until = order.start(), order.until()
        if start is True:
            start = 'now'
        if until is False:
            until = 'no longer valid'
        if order.action == 'sell':
            condition = 'higher or equal then '
        else:
            condition = 'lower or equal then '
        ###
        print('> ORDER: {}'.format(order.id))
        print('> limit order: {action} {size} {contract}\n' 
              '>              if {contract} {condition} {limit}\n'
              '>              {start}, {until}'.
              format(action=order.action,
                     size=order.size(),
                     contract=order.contract,
                     start=start,
                     until=until,
                     condition=condition,
                     limit=order.limit()
        ))
        print('>    reason if executed --> {}'.format(order.message()))        
            
    def _update_order(self, id_):  
        order_info = self.info[id_] 
        real_order = order_info.order
        print('\n\n\nManual Mode, update order {} status'.format(id_))
        print('current status')
        print('--------------')
        parent_order_id = getattr(real_order, 'parent_order_id', None)
        self._print_order(real_order)
        if (order_info.stopped is True
            or
            real_order.until() is False
        ):
            if order_info.filled is True:
                print('Order FILLED.\n')
            else:
                print('Order STOPPED.\n')
            return
        if parent_order_id and not self.info[parent_order_id].filled:
            print('Waiting for parent order to fill.\n')
            return
        self._print_order_info(real_order)
        update = self._order_update_menu().get_users_choice()
        if update == 'deactivate order':
            order_info.stopped = True
        elif update == 'no changes':
            pass
        elif update == 'add/remove positions':
            added_size = r_in.get_integer(
                message='size added: ',
                default=1,
            )
            value = r_in.get_currency_value(
                message='price per size unit: '
            )
            order_info.register_new_action(self.last_market_sync_time,
                                           self.added_size, value)
    
    @staticmethod
    def _order_update_menu():
        m = r_in.SelectionMenu(
            message = 'choice: ',
            auto_number=True,
        )
        m.add_items(['add/remove positions', 
                     'deactivate order',
                     'no changes',
        ])
        return m
        
    def _print_order_info(self, order):
        print('>\n>Current status:')
        print(self.info[order.id])
        
class MarketDataLog():
    
    def __init__(self):
        self.data = dict()
        
    def add_bar(self, contract, bardata):
        if not contract in self.data:
            self.data[contract]=[]
        data_handle = self.data[contract]
        data_handle.append([bardata.time, '+', bardata.open_, None])
        data_handle.append([bardata.end_time(), '-', bardata.high, bardata.low])
        data_handle.append([bardata.end_time(), '-', bardata.close, None])
        
    def max_since(self, contract, a_datetime):
        #print(contract)
        #print([x for x in self.data.keys()])
        data_handle = self.data[contract]
        count = -1
        d = data_handle[count]
        maximum = d[2]
        while d[0] >= a_datetime:
            count -= 1
            d = data_handle[count]            
            maximum = max(maximum, d[2])
        return maximum
            
    def min_since(self, contract, a_datetime):
        data_handle = self.data[contract]
        count = -1
        d = data_handle[count]
        minimum = d[3] or d[2]
        while d[0] >= a_datetime:
            count -= 1
            d = data_handle[count]            
            minimum = min(minimum, d[2])
        return minimum
    
    def last(self, contract):
        data_handle = self.data[contract]
        return data_handle[-1][2]
    
    def last_max(self, contract):
        data_handle = self.data[contract]
        return data_handle[-2][2]
    
    def last_min(self, contract):
        data_handle = self.data[contract]
        return data_handle[-2][3]