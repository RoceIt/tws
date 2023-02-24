#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)

from datetime import datetime

import roc_output as r_out
import roc_string as r_str
import roc_classes as r_class

import strategies
from market import Order, Market

class Error(Exception):pass
class RequestRejectedError(Error):pass
    
class TraderRequest():
    '''Request to send to a trader.
    
    TraderRequests are one direction instructions carriers.
    Everything a trader should know to open and close the trade
    should be in this information blob. This is not used to get
    information from the trader. 
    
    The id_ is a str and must be unique to the trader it is send to,
    or the request will be rejected.
    
    The markets is a dictionary that maps names local to this request
    to market names in the trader. Make sure you map to names that
    exists in the trader or your request will be rejected.  The
    strategies must refer to this local names, so the strategies are
    generic.  There is a special default mapping named
    'default' for cases where only one market is needed and no local
    name is required.
    
    The contracts dictionary, maps local contract names to generic
    contract names. Make sure the markets, you're strategies instruct
    the trader to use, know the contract name. The purpose is also the 
    same, keep the strategies as generic as posible. For traders that
    only work with one contract there is alse a default mapping option
    available. Set the fixed_contract attribute of the trader to
    unique contract.
    
    Direction as always, you can take a long position or a short 
    position, the strategies must figure out what actions are needed.
    
    The size is the number of contracts the strategies will use as
    number of contracts. Read the strategies documtantion to fully
    understand how the strategy uses this number.
    
    Enter strategy is the method used to aquire the requested 
    positions.  Read it's docs to see how it's done.
    
    The exit strategy manages the aquired positons. Make sure it's
    compatible with the enter strategy.  If your lucky the strategy
    will try to figure out if they are. But you never know. Check the
    docs.
    
    The creation time is just some information, might be usefull for
    later analysis.  The creator can choose this so you can not trust
    this value to be correct, usefull for testing and simulation.
    
    Use virtual when you want to warn the trader there might be a
    request comming but it still can be cancelled. Some strategies can
    also act on these request.
    
    If the originator if this requests wants more information about 
    the request he can try to get it through the traders status_update 
    method.  
    
    As said the TraderRequest is an information carrier so beside  
    __str__ and to_csv,  no real methods are defined.
    
    Properties:
      id_ -- a str to identify the request in the trader
      markets -- a dict, to map local market names to tradermarket names
      contracts -- a dict, to map local contract names to trader contract names
      direction -- 'long' or 'short'
      size -- the size of the strategies
      enter_strategy -- strategy to aquire a postion
      exit_strategy -- strategy to close the position
      created -- datetime of request creation
      virtual -- a bool, virual request yes or no.
      
    Methods:
      __str__ -- as always
      to_csv -- as always
      
    '''
    
    def __init__(self,
            id_,
            markets=None,
            contracts=None,
            direction=None,
            size=0,
            enter_strategy=None,
            exit_strategies=None,
            created=None,
            virtual=False
        ):
        '''Define the TraderRequest.
        
        id_, size, created, enter_strategy, exit_strategy and virtual
        as discribed in class and strategy documentation.
        
        markets can be a dict, a str or omitted.  If it's a dict that
        value will be used.  In case of a str, a dict will be created
        and the local name 'default' will be mapped to the str.
          {'default': str}. 
        When omitted a dict {'default': 'default'} will be created.
        This is only valid when the trader has only 1 unnamed market 
        defined. Check market documentation.
        
        For contract names the same logic is followed as for the market
        names.
    
        Parameters:
          All class attributes
                
        '''
        ###
        ###
        self.id_ = id_
        if isinstance(contracts, dict):
            self.contract_dict = contracts
        elif isinstance(contracts, str):
            self.contract_dict = {
                'default': contracts}
        elif contracts is None:
            self.contract_dict = {
                'default': 'default'}
        else:
            raise Error('unknown contract settings: {}'.format(contract))
        self.direction = direction
        self.size = size
        self.enter_strategy = enter_strategy
        self.provided_strategy_locals = set(enter_strategy.provides_locals)
        self.exit_strategies = exit_strategies
        for strategy in self.exit_strategies:
            self.provided_strategy_locals.update(set(strategy.provides_locals))
        if isinstance(markets, dict):
            self.markets = markets
        elif isinstance(markets, str):
            self.markets = {
                'default': markets}
        elif markets is None:
            self.markets = {
                'default': 'default'}
        else:
            raise Error('unknown market settings: {}'.format(market))
        self.created = created
        self.virtual = virtual
    
    def __str__(self):
        '''TraderRequests string representation'''
        t = r_str.SerialTextCreator()
        if self.virtual:
            t.add_chunk('VIRTUAL')
        t.add_chunk('REQUEST:')
        t.add_chunk(self.id_)
        t.underline()
        t.add_chunk(str(self.size))
        t.add_chunk(self.direction)
        t.add_chunk(', '.join(self.contract_dict))
        t.next_line()
        t.add_chunk('markets: ')
        t.add_chunk(', '.join(self.markets))
        t.next_line()
        t.add_chunk('sended: ')
        t.add_chunk(str(self.created))
        t.add_lines('more work is more info') # make this bigger
        return str(t)
    
    
    def default_market(self):
        '''Return the only available market.
        
        If more the one or no markets are defined, an error is raised.
        If just one market is defined it is returned.
        '''
        nr_of_markets_available = len(self.markets)
        if nr_of_markets_available == 0:
            raise Error('No markets defined.')
        if nr_of_markets_available > 1:
            raise Error('More then one market available')
        return list(self.markets.values())[0]
    
    def default_contract(self):
        '''Return the only available contract.
        
        If more the one or no contracts are defined, an error is raised.
        If just one contract is defined it is returned.
        '''
        nr_of_contracts_available = len(self.contract_dict)
        if nr_of_contracts_available == 0:
            raise Error('No contracts defined.')
        if nr_of_contracts_available > 1:
            raise Error('More then one contract available')
        return list(self.contract_dict.values())[0]
        
    def to_csv(self, csv_writer):
        '''Export TraderRequest to a csv file.'''
        ###
        info = (
            self.id_,
            self.created,
            self.direction, 
            self.size)
        csv_writer.writerow(info)

class FullRequest(r_class.FixedAttributes):
    
    def __init__(self, request):
        assert isinstance(request, TraderRequest)
        self.request = request
        self.rejected = False
        self.orders = None
        self.managers = None
    
    @property    
    def virtual(self):
        return self.request.virtual
    
    @property
    def id_(self):
        return self.request.id_
        
        
class Trader():
    """Sends requests to markets.
    
    The markets dict maps market names to market.Market objects.  You
    can add as many markets as you want. In the special case there is
    only one market, you can choose to not give it a name,  it will
    be called 'default'.  You can not mix default mode with named
    markets.
    
    If the trader will only have to worry about one contract, you can
    set the fixed_contract to that name. When a fixed contract is
    defined you don't have to define the contract in the TraderRequests.
    The Trader will change the reqeusts contract_dict value to the
    fixed_contract name.
    
    A request sended will be extended to a full request. All methods
    on requests expects full requests. The original request is part
    of the full request.
    
    If it's rejected, the full request is placed in the list with 
    rejected requests a good description of the problem should be 
    found in the full requests rejected attribute. Since a dubious
    situation is at hand, a RequestRejectedError is raised. Only 
    catch it when you're sure you can really handle it!
    
    If the request is valid, the enter and exit strategies will be 
    asked to create there orders and managers. The orders are stored 
    in the full request order attribute and sended to the market. The 
    managers are stored in the full request manager attribute.
    
    The trader should constantly watch it's active requests by running
    the check_active_requests method. When the request has no more
    active managers the full request is moved to the appropriate list.
    If the request was never filled it's moved to the unfilled requests
    list. If filled and it still has open positions with all managers
    finished, it's moved to the erroneous list, this should never happen.
    If filled and all positions closed, perfect,  Full request is moved 
    to the finished requests list.
    
    Properties:
      rejected_requests -- the list with rejects requests
      active_requests -- the list with active requests
      unfilled_requests -- the list with unfilled requests
      finished_requests -- the list with finished requests
      erroneous_requests -- the list with erroneous requests
      self.markets -- dict mapping names to market.Market's
      self.fixed_contracts -- the fixed contract (ddunder)
      
    Methods:
      __str__ -- as always
      active -- returns True if trader is/was active
      add_market -- add a name/market mapping to the trader
      add_requests -- add the list of requests sended
      last_sync -- returns the last syncronisation time of the market
      
    
    """
       
    ATOMIC = 0
    MOVED = 1    
    
    def __init__(self):
        '''Initiate the trader.'''
        self.rejected_requests = dict()
        self.active_requests = dict()
        self.unfilled_requests = dict()
        self.finished_requests = dict()
        self.erroneous_requests = dict()
        self.markets = dict()
        self.fixed_contract = None
        self._env_time = None
        self._env_mode = 'setup'
        
    def __str__(self):
        '''Traders string representation'''
        t = r_str.SerialTextCreator()
        t.add_line('a simple standard default trader')
        if self.fixed_contract:
            t.add_chunk('  fixed contract:')
            t.add_chunk(self.fixed_contract)
            t.next_line()
        if self.markets:
            t.add_chunk('available markets')
            t.add_chunk(', '.join(self.markets))
            t.next_line()
        t.add_chunk('nr of rejected requests:')
        t.add_chunk(str(len(self.rejected_requests)))
        t.next_line()
        t.add_chunk('nr of active requests:')
        t.add_chunk(str(len(self.active_requests)))
        t.next_line()
        t.add_chunk('nr of unfilled requests:')
        t.add_chunk(str(len(self.unfilled_requests)))
        t.next_line()
        t.add_chunk('nr of finished requests:')
        t.add_chunk(str(len(self.finished_requests)))
        t.next_line()
        t.add_chunk('nr of erroneous requests:')
        t.add_chunk(str(len(self.erroneous_requests)))
        t.next_line()
        return str(t)
        
    @property
    def fixed_contract(self):
        '''Use a fixed contract.
        
        Only possible when the trader will never use another contract. You can
        only set it once, Strategies should know how to handle this.
        '''
        try:
            fixctr = self.__fixed_contract
        except AttributeError:
            fixctr = None
        return fixctr
    
    @fixed_contract.setter    
    def fixed_contract(self, contract_name):
        assert self.fixed_contract is None, 'you can only set this once'
        assert not self.active(),(
            'you can not set a fixed contracts when trader is/was active')
        ###
        for name, market in self.markets.items():
            if not market.validate_contract_name(contract_name):
                mss = ('{contract_name} not known to {market_name} market'.
                       format(contract_name=contract_name,
                              market_name=name
                ))
                raise Error(mss)
        self.__fixed_contract = contract_name        
    
    def active(self):
        '''Return True if trader is/was active.
        
        A trader is name active when it once had an active request.
        '''
        active = bool(self.active_requests)
        ###
        return active
     
    def add_market(self, market, name=None):
        '''Add a name/market mapping to the trader.
        
        The market must be a market.Market object. 
        When you only want to add one market, you can ommit the name
        and 'default' will be used. Make sure the strategies knows
        how to deal with this.
        
        If a fixed contract is set, it will be checked if the market
        knows the contract. if not, an Error is raised.
        
        You can not assign a new market to the same name.
        '''
        
        assert isinstance(market, Market), ('market type expected: {}'.
                                            format(type(market)))
        assert 'default' not in self.markets, (
            'In default market mode, trader only accepts 1 market.')
        ###
        market_name = name if name else 'default'
        ###
        if name == 'default':
            mss = 'default is reserved market name'
            raise Error(mss)
        if self.markets and market_name == 'default':
            mss = 'no unnamed markets allowed when using more then one market'
            raise Error(mss)
        if market_name in self.markets:
            mss = 'market name already excists: {}'.format(market_name)
            raise Error(mss)
        if not (self.fixed_contract                                          and
                market.validate_contract_name(self.fixed_contract)
        ):
            mss = ('{contract_name} nor known to {market_name} market'.
                   format(contract_name=self.fixed_contract,
                          market_name=name
                ))
        self.markets[market_name] = market
        
    def add_requests(self, requests, at_time):
        '''Check and process the list of reqeusts.
        
        Takes a list of TraderRequests and dispatch them.
        I don't know how to handel the virtual requests yet. Still have
        to figure out. For now they'll raise an error.
        Normal requests are send to the add_request method. They are 
        validated and processed to create and send the orders and managers.
        When more then one request is send the method stops validating and
        processing after the first invalid request. When you catch the
        RequestRejectedError's check which requests are processed.
        '''       
        
        self.set_environment(at_time)
        for request in requests:
            if request.virtual:
                self.use_virtual_info(request)
            else:
                request = FullRequest(request)
                self.add_request(request)
    
    def check_active_requests(self, at_time):
        '''Run the managers.
        
        Do this as often as possible. When the request has run out of
        managers, it is moved to the approriate list: finished,
        unfilled or erroneous requests.
        '''      
        
        self.set_environment(at_time)
        if self.environment_mode is self.ATOMIC:
            return
        self.run_all_request_managers()
        #for request in self.active_requests.values():
            #new_manager_list = []
            #for manager in request.managers:
                #new_manager = manager(at_time)
                #if new_manager is None:
                    #continue
                #new_manager_list.append(new_manager)
            #request.managers = new_manager_list
        self.remove_requests_without_managers_from_active_list()
        
    def status_report(self, id_, at_time):
        '''Return the requested FullRequest.'''      
        
        self.set_environment(at_time)
        if self.environment_mode is self.MOVED:
            self.run_all_request_managers()
            self.remove_requests_without_managers_from_active_list()
        request_lists = (
            self.rejected_requests,
            self.active_requests,
            self.unfilled_requests,
            self.finished_requests,
            self.erroneous_requests,
        )
        for request_list in request_lists:
            if id_ in request_list:
                return request_list[id_]
        raise Error('request not found: {}'.format(id_))
    
    def last_sync(self, market_id='default'):
        return self.markets[market_id].last_market_sync
### not for users        
#
#

    def set_environment(self, at_time):
        """Sets the environment mode and time.
        
        Mode can be:
          ATOMIC -- last time reported was equal with existing time
          MOVED -- time moved between last and before last time report
          
        Raise an Error when time moves backward.
        """
        if self._env_time == at_time:
            self._env_mode = self.ATOMIC
        elif (self._env_time is None
              or
              self._env_time < at_time
        ):
            self._env_mode = self.MOVED
        else:
            raise Error('time moved backward')
        self._env_time = at_time
        
    @property
    def environment_mode(self):
        return self._env_mode
    
    @property
    def environment_time(self):
        return self._env_time         
        
    def add_request(self, request):
        assert isinstance(request, FullRequest)
        assert not request.virtual, 'you can\'t add virtual requests'
        ###
        valid_request = self.validate_request(request)
        ###
        if  valid_request is True:
            if self.fixed_contract:
                self.update_contract_dict(request)
            self.arm(request)
            self.send_orders(request)
            self.active_requests[request.id_] = request
        else:
            request.rejected = valid_request
            self.rejected_requests[request.id_] = request
            raise RequestRejectedError(valid_request)
        
    def validate_request(self, request):        
        assert isinstance(request, FullRequest)
        ###
        valid = True
        trader_request = request.request
        validators = (
            # Don't change the order of the test.
            self.id_validator,            # check id's
            self.market_validator,        # market
            self.contract_dict_validator, # fixed contract vs contract_dict
            self.enter_validator,         # enter_strategy
                                          # check ctrct, drctn & sz
            self.exit_validators,         # exit_strategy
            self.request_allowed,         # check with settings            
        )
        for validator in validators:
            valid = validator(trader_request)
            if valid is not True: break
        ###
        return valid
                
    def id_validator(self, trader_request):
        '''Check if trader_request id_ is unique.
        
        Avoid dubious situations with different requests in different
        lists with the same id_.
        '''
        ###
        id_ = trader_request.id_
        unique_id = (id_ in self.rejected_requests                           and
                     'request id used in rejected requests'
                     or
                     id_ in self.erroneous_requests                          and
                     'request id used in erroneous requests'
                     or
                     id_ in self.active_requests                             and
                     'request id used in active requests'
                     or
                     id_ in self.unfilled_requests                           and
                     'request id used in unfilled requests'
                     or 
                     id_ in self.finished_requests                           and
                     'request id used in finished requests'
                     or
                     True
        )
        ###
        return unique_id
    
    def market_validator(self, trader_request):
        '''Check availability of requested markets.
        
        Return True if at least one market is defined and all the
        requested market names are available. The trader can't now
        what market(s) the request (actually it's strategies) is
        expecting so the straties' validators may run extra tests.
        The strategies can at least be sure the names will return a
        market.
        '''
        assert isinstance(trader_request, TraderRequest)
        ###
        available_markets = self.markets
        markets_required = trader_request.markets.values()
        valid = True
        if not available_markets:
            valid = (
                 'No markets defined, can\'t route orders to a market.')
        else:
            for market in markets_required:
                if market not in available_markets:
                    valid = 'Market not known to trader: '.format(market)
                    break
        ###
        return valid
    
    def contract_dict_validator(self, trader_request):
        '''Check trader_request contract_dic when fixed_contract is set.
        
        When the fixed contract is set, the request (stragegies) can
        not freely choose it's contract.  Since the trader does not
        know in advance what contracts will be assigned to wich markets
        it's the stragies' validator responsablity to check this.
        
        This validator only says that the requests contracts list is 
        valid for the traders' fixed_contract setting.
        '''
        assert isinstance(trader_request, TraderRequest)
        ###
        nr_of_required_contracts = len(trader_request.contract_dict)
        contract_name_is_default = (
            list(trader_request.contract_dict.values())[0] == 'default'
        )
        valid = True
        if self.fixed_contract:
            if nr_of_required_contracts > 1:
                valid = ('fixed trader is set, request can only have '
                         'one  contract in it\'s contract dic')
            elif not contract_name_is_default:
                valid = ('fixed trader is set, request can not '
                         'freely choose it\'s contract')
        elif (nr_of_required_contracts == 1                                  and
              contract_name_is_default                                       and
              not self.fixed_contract
        ):
            valid = ('No fixed trader set, you can\'t use default as '
                     'contract name.')
        return valid
                
    def enter_validator(self, trader_request):
        assert isinstance(trader_request, TraderRequest)
        ###
        if not isinstance(trader_request.enter_strategy,
                           strategies.EnterStrategy):
            return 'enter strategy not an enter strategy class object.'
        else:
            return True
    
    def exit_validators(self, trader_request):
        assert isinstance(trader_request, TraderRequest)
        ###
        for exit_strategy in trader_request.exit_strategies:
            if not isinstance(exit_strategy,strategies.ExitStrategy):
                return ('exit strategy {strat_name}, not an exit '
                        'stratagy class object.'.
                        format(strat_name=exit_strategy.name)
                )
            else:
                valid = exit_strategy.validate(
                    request=trader_request,
                    the_trader=self
                )
            if valid is not True:
                break
        return valid
    
    def request_allowed(self, trader_request):
        assert isinstance(trader_request, TraderRequest)
        ###
        valid = True
        #run the tests, daytrading and things like that i thought
        ###
        return valid
    
    def update_contract_dict(self, request):
        assert isinstance(request, FullRequest)
        ###
        trader_request = request.request
        k, v = trader_request.contract_dict.popitem()
        trader_request.contract_dict[k] = self.fixed_contract
    
    def arm(self, request):
        assert isinstance(request, FullRequest)
        ###
        trader_request = request.request
        request.orders, request.managers = trader_request.enter_strategy.arm(
            request=trader_request,
            the_trader=self,
        )
        exit_orders, exit_managers = self.arm_exit_strategies(trader_request)
        request.orders.update(exit_orders)
        request.managers.extend(exit_managers)
        return
    
    def arm_exit_strategies(self, trader_request):
        assert isinstance(trader_request, TraderRequest)
        orders, managers = dict(), list()
        for exit_strategy in trader_request.exit_strategies:
            new_orders, new_managers = exit_strategy.arm(
                request=trader_request,
                the_trader=self,
            )
            orders.update(new_orders)
            managers.extend(new_managers)
        return orders, managers
            
    def send_orders(self, request):
        assert isinstance(request, FullRequest)
        ###
        touched_markets = set()
        for destination, order in request.orders.items():
            market, foo = destination
            touched_markets.add(market)
            self.markets[market].new_order(order)
        for market in touched_markets:
            self.markets[market].activate_new_orders(self.environment_time)
     
    def run_all_request_managers(self):
        for request in self.active_requests.values():
            new_manager_list = []
            for manager in request.managers:
                new_manager = manager(self.environment_time)
                if new_manager is not None:
                    new_manager_list.append(new_manager)
            request.managers = new_manager_list        
            
    def remove_requests_without_managers_from_active_list(self):
        active_requests = list(self.active_requests.keys())
        for k in active_requests:
            request = self.active_requests[k]
            if request.managers:
                continue
            self.find_final_destination_for(request)[k] = request 
            self.active_requests.pop(k)
            
    def find_final_destination_for(self, request):
        assert not request.managers
        ###
        filled = False
        contract_dict = dict()
        for order_location in request.orders:
            market, order_id = order_location
            info = self.markets[market].status_report(
                order_id, 
                self.environment_time
            )
            contract = info.order.contract
            if contract in contract_dict:
                contract_dict[contract] += info.size
            else:
                contract_dict[contract] = info.size
            filled |= info.filled
        if not filled:
            return self.unfilled_requests
        else:
            for open_positions in contract_dict.values():
                if not open_positions == 0:
                    return self.erroneous_requests
        return self.finished_requests
                
        
            
    