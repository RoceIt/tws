#!/usr/bin/env python3

#  FILENAME: poel.py

#  Copyright (c) 2011, Rolf Camps (rolf.camps@scarlet.be)
import os
from collections import namedtuple

import mypy
import barData
import sql_ib_db as db_manager

position = namedtuple('position', 'size price entered')

class Poel():
    
    def __init__(self, nr_of_contracts, multiplier, profit_per_trade,
                 margin_per_contract, trade_step,
                 start_procedure):
        
        self.nr_of_contracts = nr_of_contracts
        self.multiplier = multiplier
        self.profit_per_trade = profit_per_trade
        self.margin_per_contract = margin_per_contract
        print('margin per contract: {}'.format(margin_per_contract))
        self.trade_step = trade_step
        print('trade_step: {}'.format(trade_step))
        self.start_procedure = start_procedure
        self.active_trades = []
        self.last_trade_level = None
        self.next_sell_level = self.next_buy_level = None
        self.gains = 0
        
    def standard_start_setup(self, bar):
        
        assert isinstance(bar, barData.ochlBar)
        if not self.last_trade_level:
            self.last_trade_level = bar.open
            self.next_sell_level = self.last_trade_level + self.trade_step / 2
            self.next_buy_level = self.last_trade_level - self.trade_step / 2
        if bar.open > self.next_sell_level:
            self.sell_at(bar.open, bar.time)
        elif bar.open < self.next_buy_level:
            self.buy_at(bar.open, bar.time)
        elif self.next_sell_level in bar:
            self.sell_at(self.next_sell_level, bar.time)
        elif self.next_buy_level in bar:
            self.buy_at(self.next_buy_level, bar.time)
        if self.positions:
            self.start_procedure = None
            self.last_trade_level = self.active_trades[0].price            
            self.next_sell_level = self.last_trade_level + self.trade_step
            self.next_buy_level = self.last_trade_level - self.trade_step
            print(self.last_trade_level, self.next_buy_level, self.next_sell_level)
            
            
        
    def insert_bar(self, bar):
        
        if self.start_procedure:
            self.start_procedure(bar)
        else:
            try:
                open_delta = bar.open - self.last_trade_level
                #print(bar.open, self.last_trade_level, open_delta)
                opening_gap = abs(open_delta) // self.trade_step
                #print(opening_gap)
                opening_gap = opening_gap * (-1 if open_delta < 0 else 1)
                #print(opening_gap)
            except TypeError:
                print('!! seems to be something wrong with data bar !!')
                print(bar)
                input('hit enter ...')
                return
            if opening_gap > 0:
                print('action 1')
                print('opening gap: ', opening_gap)
                print(bar)
                self.sell_at(bar.open, bar.time, opening_gap)
            elif opening_gap < 0:
                print('action 2')
                print('opening gap: ', opening_gap)
                print(bar)
                self.buy_at(bar.open, bar.time, abs(opening_gap))
            elif self.next_sell_level in bar:
                print('action 3')
                self.sell_at(self.next_sell_level, bar.time)
                opening_gap = 1
            elif self.next_buy_level in bar:
                print('action 4')
                self.buy_at(self.next_buy_level, bar.time)
                opening_gap = -1
            new_trade_level_delta = opening_gap * self.trade_step
            #print(new_trade_level_delta)
            if new_trade_level_delta:
                self.last_trade_level += new_trade_level_delta
                self.next_sell_level += new_trade_level_delta
                self.next_buy_level += new_trade_level_delta
                #input('hit enter ...')
            
    def sell_at(self, price, time_, quant=1):
        
        size = quant * self.nr_of_contracts
        print('{}: sold {} for {}'.format(time_,size, price))
        while quant:
            if self.positions > 0:
                sold_pos = self.active_trades.pop()
                profit = (price - sold_pos.price) * sold_pos.size
                self.gains += profit
                print('{} made {} profit'.format(time_, profit))
                print('      total profit td: {}'.format(self.gains))
            else:
                self.active_trades.append(position(-self.nr_of_contracts,
                                                   price, time_))
            quant -= 1
        print('new position size {}'.format(self.positions))
        
    def buy_at(self, price, time_, quant=1):
        
        size = quant * self.nr_of_contracts
        print('{}: bought {} for {}'.format(time_, size, price))
        while quant:
            if self.positions < 0:
                bought_pos = self.active_trades.pop()
                profit = (bought_pos.price - price ) * -bought_pos.size
                self.gains += profit
                print('{} made {} profit'.format(time_, profit))
                print('      total profit td: {}'.format(self.gains))
            else:
                self.active_trades.append(position(self.nr_of_contracts,
                                                   price, time_))
            quant -= 1
        print('new position size {}'.format(self.positions))
            
    @property
    def positions(self):
        
        return sum([x.size for x in self.active_trades])
            
        
        
class CashPoel(Poel):
    
    def __init__(self, nr_of_contracts, multiplier, profit_per_trade):
        
        margin_per_trade = nr_of_contracts / multiplier
        trade_step = profit_per_trade / nr_of_contracts
        start_produre = self.set_up_start_procedure()
        super().__init__(nr_of_contracts, multiplier, profit_per_trade,
                         margin_per_trade, trade_step,
                         start_produre)
    
        
    def set_up_start_procedure(self):
        print('set standard setup method')
        return self.standard_start_setup
    
def main():
    
    db_PATH= mypy.DB_LOCATION
    ochl_info = ['datetime', 'open', 'close', 'high', 'low']
    IBContractName = 'euro-dollar'
    start_date = '2010/11/01'
    IB_db = IBContractName+'.db'
    if not os.path.isfile(os.path.join(db_PATH, IB_db)):
        print('Geen database gegevens voor gegeven contract: {}', (IB_db,))
        raise
    #IB_dbTable = 'MIDPOINT_30_mins'
    IB_dbTable = 'MIDPOINT_5_secs'
    simulator = CashPoel(100000,40, 1850)
    dbh = db_manager.HistoricalDatabase(IB_db)
    #dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable, start = mypy.py_date(start_date))
    dates = dbh.get_dates(IB_dbTable)   
    for date in dates:    
        data = dbh.get_data_on_date(IB_dbTable, date, *ochl_info)
        for row in data:
            simulator.insert_bar(barData.ochlBar(*row))
            
if __name__ == '__main__':
    print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
    main()
    
