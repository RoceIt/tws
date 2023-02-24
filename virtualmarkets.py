#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import marketdata

from  market import *
from roc_currency import point_


class VirtualSingleContractIndexMarketFromDataBarStream(Market):
    """Market that handles orders from a single bar data stream.
    
    Virtual is redundant in this case, you can not trade an index,
    there are no bid/asks. Al outcome is a best guess influenced by
    preset parameters and/or development decisions.
    
    The gray_zone_bar is the bar where we don't know what exectly
    happened. Once the virtual time is later then the end time of
    the bar, it becomes known data and can be processed. A new
    new grey_zone_bar can be loaded then to check the end time of
    the next period.
    """
    
    def __init__(self, datastream, *valid_contract_names, 
                 currency_multiplier=point_(1)):
        #assert isinstance(datastream, marketdata.DataBarFeeder)
        self.name = 'vscimfdbs'
        self.valid_contract_names = valid_contract_names
        self.data_feed = self._next_bar(datastream)
        self.gray_zone_bar = next(self.data_feed)
        #print('==== gzb:', self.gray_zone_bar)
        self.first_date_time_known = self.gray_zone_bar.time
        self.currency_multiplier = currency_multiplier
        super().__init__()
                
    ####################
    #
    # define market specific versions for all following functions
    # in derived subclasses
    #
    ####################
    def _initial_market_time(self):
        return self.first_date_time_known
    
    def _validate_contract_name(self, name): ### market specific ###
        return name in self.valid_contract_names
    
    def _activate_parent_child_group(self, parent, children):
        pass
        #self._advance_market_to_trader_time()
        
    def _activate_single_order(self, order):
        pass
        #self._advance_market_to_trader_time()
        
    def _sync_active_orders(self, target_sync_time):
        if self.gray_zone_bar.end_time() <= target_sync_time:
            self._gray_bar_finished_update_active_orders()
            intermediat_sync_time = self.gray_zone_bar.end_time()
            try:
                self.gray_zone_bar = next(self.data_feed)
            except StopIteration:
                raise Error('market out of data.')
            return intermediat_sync_time
        return target_sync_time
        
    def _warning_order_changed(self, order_id, attribute, new_value):
        pass
        #self._advance_market_to_trader_time()           
                
    ####################
    #
    # 
    #
    ####################

    def _next_bar(self, feeder):
        contract_name = self.valid_contract_names[0]
        if not isinstance(feeder, list):
            feeder = [feeder]
        for feed in feeder:
            for bar in feed:
                yield bar
                self.data_of_contracts.add_bar(
                    contract_name, bar)
            
    def _gray_bar_finished_update_active_orders(self):
        market_type_tr = {
            'buy': {
                'market': self._buy_at_market,
                'stop': self._buy_at_stop,
                'limit': self._buy_at_limit,
            },
            'sell': {
                'market': self._sell_at_market,
                'stop': self._sell_at_stop,
                'limit': self._sell_at_limit,
            }}
        for order_id in self.ordered_active_orders_ids():
            order_info = self.info[order_id] 
            real_order = order_info.order
            if (real_order.start() is not True
                or
                real_order.until() is False
            ):
                continue
            #print('trying')
            #print("{} @ {}".format(real_order.id, self.last_market_sync))
            try:
                market_type_tr[real_order.action][real_order.type](
                    real_order, 
                    order_info
                )
            except KeyError:
                raise Error('market type helper function not defined {}|{}'.
                      format(real_order.action, real_order.type))
            
    def _buy_at_market(self, real_order, order_info):
        """In this virtual market i presume the order to be atomic."""
        price = self._calculate_price_at(self.gray_zone_bar.high)
        order_info.register_new_action(self.last_market_sync_time,
                                       real_order.size(), price)
        print('$$$$ market >>>>> bought {} for {} @ {}'.format(
                real_order.size(), str(price), self.gray_zone_bar.end_time()))
        self.replace_finished_orders()
            
    def _sell_at_market(self, real_order, order_info):
        """In this virtual market i presume the order to be atomic."""
        price = self._calculate_price_at(self.gray_zone_bar.low)
        order_info.register_new_action(self.last_market_sync_time,
                                       -real_order.size(), price)
        print('$$$$ market >>>>> sold {} for {} @ {}'.format(
                real_order.size(), str(price), self.gray_zone_bar.end_time()))
        self.replace_finished_orders()
        
    def _buy_at_stop(self, real_order, order_info):
        """In this virtual market i presume the order to be atomic."""
        if self.gray_zone_bar.high >= real_order.stop():
            price = self._calculate_price_at(self.gray_zone_bar.high) 
            #price = real_order.stop() # best case
            order_info.register_new_action(self.last_market_sync_time,
                                           real_order.size(), price)
            print('$$$$ stop >>>>>>bought {} for {} @ {}'.format(
                real_order.size(), str(price), self.gray_zone_bar.end_time()))
            self.replace_finished_orders()
            
    def _sell_at_stop(self, real_order, order_info):
        """In this virtual market i presume the order to be atomic."""
        if self.gray_zone_bar.low <= real_order.stop():
            price = self._calculate_price_at(self.gray_zone_bar.low)
            #price = real_order.stop() # best case
            order_info.register_new_action(self.last_market_sync_time,
                                           -real_order.size(), price)
            print('$$$$ stop >>>>>>sold {} for {} @ {}'.format(
                real_order.size(), str(price), self.gray_zone_bar.end_time()))
            self.replace_finished_orders()    
            
    def _buy_at_limit(self, real_order, order_info):
        """In this virtual market i presume the order to be atomic."""
        limit = real_order.limit()
        if limit >= self.gray_zone_bar.low:
            if limit > self.gray_zone_bar.high:
                price = self._calculate_price_at(self.gray_zone_bar.high)
            else:
                price = limit
            order_info.register_new_action(self.last_market_sync_time,
                                           real_order.size(), price)
            print('$$$$ limit >>>>>> bought {} for {} @ {}'.format(
                real_order.size(), str(price), self.gray_zone_bar.end_time()))
            self.replace_finished_orders()
            
    def _sell_at_limit(self, real_order, order_info):
        """In this virtual market i presume the order to be atomic."""
        limit = real_order.limit()
        if limit <= self.gray_zone_bar.high :
            if limit < self.gray_zone_bar.low:
                price = self._calculate_price_at(self.gray_zone_bar.low)
            else:
                price = limit
            order_info.register_new_action(self.last_market_sync_time,
                                           -real_order.size(), price)
            print('$$$$ limit >>>>>> sold {} for {} @ {}'.format(
                real_order.size(), str(price), self.gray_zone_bar.end_time()))
            self.replace_finished_orders()
        
        
    def _calculate_price_at(self, value):
        return self.currency_multiplier * value