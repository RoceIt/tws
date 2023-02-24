#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''This module provides a class that can follow up a trade according to the
set rules
'''

import mypy
from collections import namedtuple 
from Rule import Rule
import TraderTest


class TraderError(Exception): pass
class TraderWarning(TraderError): pass

Action = namedtuple('Action', 'action data')

################################################################################
E_CANT_CLOSE_OPEN_POS = 'Can not close Trader, {} positions of {} open'

################################################################################
# trader status
################################################################################
EMPTY = '$EMPTY'
# empty trader
MONITORING = '$MONITORING'
# trader has tests
IN_TRADE = '$IN_TRADE'
# trading
STOPPED = '$STOPPED'
# trader is stopped
################################################################################

################################################################################
# trader lists
################################################################################
ENTRY_LIST = '$ENTRY_LIST'
# list with enter rules
EXIT_LIST = '$EXIT_LIST'
# list with exit rules
################################################################################

################################################################################
# data for functions
################################################################################
#
# Make sure following names are defined in the dictionary you send to the 
# functions that need data
#
################################################################################
#
TIME = '$TIME_Trader'
# The time of the bar
HIGH = '$HIGH_Trader'
# The high of the bar
LOW = '$LOW_Trader'
# The low of the bar
OPEN = '$OPEN_Trader'
# The open of the bar
CLOSE = '$CLOSE_Trader'
# The close of the bar
################################################################################


################################################################################
# actions
################################################################################
BUY = '$BUY'
# needs data NAME, QUANTITY, VALUE
SELL = '$SELL'
# needs data NAME, QUANTITY, VALUE
CLOSE_POSITION = '$CLOSE_POSITION'
# needs data Name, VALUE
STOP = 'STOP'
# stops the Trader or raises an error when positions are stil open
################################################################################

################################################################################
# action data
################################################################################
NAME = '$NAME_trader_action'
QUANTITY = '$QUANTITY_trader_action'
VALUE = '$VALUE_trader_action'
################################################################################

################################################################################
# messages
################################################################################
#
STR_ENTER_HOURS = 'Entering trades permitted from {} until {}\n'
STR_CLOSE_POSITIONS = 'Close all positions after {}\n'
#
################################################################################

def trader_data(ochl_bar):
    # give the bar you want to run the tests on
    data = {TIME: ochl_bar.time,
            OPEN: ochl_bar.open,
            CLOSE: ochl_bar.close,
            HIGH: ochl_bar.high,
            LOW: ochl_bar.low}
    return data

def value_(**data):
    value = data[VALUE]
    #print(type(value))
    if type(value) is str:
        return data[value]
    #print('value ', value, type(value))
    return value

class Trader:
    
    def __init__(self, name,
                 trading_permitted_from = False,
                 trading_permitted_until = False,
                 close_positions_after = False):
        self.name = name
        self.enter_rules = []
        self.exit_rules = []
        self.status = EMPTY
        self.positions = {}
        self.entry_log = []
        self.exit_log = []
        self.max_in_trade = 0
        self.min_in_trade = 0
        self.value = 0
        self.set_trading_hours(trading_permitted_from,
                               trading_permitted_until,
                               close_positions_after)

    def set_trading_hours(self,
                          trading_permitted_from = None,
                          trading_permitted_until = None,
                          close_positions_after = None):
        if not trading_permitted_from is None:
            self.trading_permitted_from = trading_permitted_from
        if not trading_permitted_until is None:
            self.trading_permitted_until = trading_permitted_until
        if not close_positions_after is None:
            self.close_positions_after = close_positions_after

    def trader_info(self, id_=False):
        output = 'id: {}\n'.format(self.name) if id_ else ''
        if not self.trading_permitted_from is False:
            st = mypy.time2format(self.trading_permitted_from)
            et = mypy.time2format(self.trading_permitted_until)
            output += STR_ENTER_HOURS.format(st, et)
        if not self.close_positions_after is False:
            output += STR_CLOSE_POSITIONS.format(self.close_positions_after)
        return output+'\n'

    def __str__(self):
        output = 'id: {}\n'.format(self.name)
        if self.trading_permitted_from:
            st = mypy.time2format(self.trading_permitted_from)
            et = mypy.time2format(self.trading_permitted_until)
            output += STR_ENTER_HOURS.format(st, et)
        for rule in self.enter_rules:
            output += ''.join(['ENTRY RULE: ', str(rule), '\n'])
        for rule in self.exit_rules:
            output += ''.join(['EXIT RULE: ', str(rule), '\n'])
        if self.positions:
            output += 'positions:\n'
            for name, number in self.positions.items():
                output += '         {}:{}\n'.format(name, number)
            output += 'value: {}\n'.format(self.value)
        output += 'status {} \n'.format(self.status)
        return output

    def new_positions_permitted(self, curr_time):
        start = self.trading_permitted_from
        stop = self.trading_permitted_until
        time_ = curr_time.time()
        #print(start, stop, time_)
        if stop == False:
            return True
        elif start < stop:
            return start <= time_ <= stop
        else:
            return time_ >= start or time_ <= stop

    def sim_buy(self,**data):
        name = data[NAME]
        number = data[QUANTITY]
        value = value_(**data)
        if name in self.positions:
            self.positions[name] += number
        else:
            self.positions[name] = number
        self.value = self.value - number * value
        return 'bought {} {} @ {}'.format(number, name, value)
        

    def sim_sell(self,**data):
        name = data[NAME]
        number = data[QUANTITY]
        value = value_(**data)
        if name in self.positions:
            self.positions[name] -= number
        else:
            self.positions[name] = -number
        self.value = self.value + number * value
        return 'sold {} {} @ {}'.format(number, name, value)

    def sim_close_position(self,**data):
        report = 'closing positions: '
        name = data[NAME]
        value = value_(**data)
        if self.positions:
            number = self.positions[name] if name in self.positions else 0
        else:
            number = 0
        if number > 0:
            sell_data = {NAME: name,
                         QUANTITY: abs(number),
                         VALUE: value}
            report += self.sim_sell(**sell_data)
        elif number < 0:
            buy_data = {NAME: name,
                        QUANTITY: abs(number),
                        VALUE: value}
            report += self.sim_buy(**buy_data)
        return report


    def stop(self,**data):
        print('in stop')
        for key, position in self.positions.items():
            if not position == 0:
                raise TraderError(E_CANT_CLOSE_OPEN_POS.format(position,
                                                               key))
        self.status = STOPPED
        return 'stopped'
        
    def run(self,action_list, **data):
        report_list = []
        for action in action_list:
            data.update(action.data)
            if action.action == BUY:
                report = self.sim_buy(**data)
            elif action.action == SELL:
                report = self.sim_sell(**data)
            elif action.action == CLOSE_POSITION:
                report = self.sim_close_position(**data)
            elif action.action == STOP:
                report = self.stop(**data)
            else:
                raise TraderError('unknown action')
            report_list.append((data[TIME],report))
        # If trader has open postions, set status to in_trade
        for key, position in self.positions.items():
            if not position == 0:
                self.status = IN_TRADE
                break
        return report_list

    

    def add_rule(self, rule_list, rule, position='end'):
        text = ''
        RULE_LIST={ENTRY_LIST: self.enter_rules,
                   EXIT_LIST: self.exit_rules}
        LIST_TEXT={ENTRY_LIST: 'Enter if ',
                   EXIT_LIST: 'Exit/ Stop if'}
        if isinstance(rule, Rule):
            if rule_list in RULE_LIST:
                RULE_LIST[rule_list].append(rule)
                text = 'id: {} |  {} '.format(self.name,
                                              LIST_TEXT[rule_list])
                text += str(rule)
                text += '\n'
            else:
                raise TraderError('Unkown list')
        else:
            raise TraderError('rule should be of type Rule.Rule')
        if self.status == IN_TRADE:
            raise TraderWarning('The trade you changed is in trade')
        elif self.status == STOPPED:
            raise TraderError('The trade you tried to change is stopped')
        if not self.enter_rules:
            self.status = EMPTY
        else:
            self.status = MONITORING
        return text

    def get_rule(self, rule_list, position=-1):        
        RULE_LIST={ENTRY_LIST: self.enter_rules,
                   EXIT_LIST: self.exit_rules}
        if rule_list in RULE_LIST:
            rule_list = RULE_LIST[rule_list]
        else:
            raise TraderError('Unkown list')
        if len(rule_list) == 0:
            raise TraderWarning('Empty rule list')
        return rule_list[position] 

    def clear_rules(self):
        text = ''
        if self.status == STOPPED:
            raise TraderError('you can\'t change a STOPPED trader')
        text = 'id: {} | REMOVED ALL ENTRY & EXIT RULES\n'.format(self.name)
        self.enter_rules = []
        self.exit_rules = []
        if self.status == IN_TRADE :
            raise TraderWarning('The trade you changed is in trade')
        self.status = EMPTY
        return text

    def suspend_entry_rules(self):
        text = ''
        mess = 'id: {} | (REMAINING) ENTRY RULES SUSPENDED\n'
        if not self.status == STOPPED:
            for rule in self.enter_rules:
                if rule.suspend():
                    text = mess.format(self.name)
        return text

    def reactivate_suspended_entry_rules(self):
        text = ''
        mess = 'id: {} | REACTIVATED ENTRY RULES\n'
        if not self.status == STOPPED:
            for rule in self.enter_rules:
                if rule.reactivate_suspend():
                    text = mess.format(self.name)
        return text
   
        

    #def planned_actions(self, **data):
    #    entry_actions = []
    #    exit_actions = []
    #    for rule in self.enter_rules:
    #        actions = rule.is_true(**data)
    #        if actions:
    #            entry_actions.append(actions)
    #    for rule in self.exit_rules:
    #        actions = rule.is_true(**data)
    #        if actions:
    #            exit_actions.append(actions)
    #    return entry_actions, exit_action

    def run_trader(self, **data):
        report = ''        
        data.update(TraderTest.test_data(self))
        if not self.status == STOPPED:
            for rule in self.exit_rules:
                actions = rule.is_true(**data)
                if actions:
                    print('Exit actions:',actions)
                    new_report = self.run(actions, **data)
                    self.exit_log += new_report
                    rule.flag_remove()
                    report += 80 * '<' +'\n'
                    for line in new_report:
                        report_lines = ['id: {}'.format(self.name),
                                        str(line[0]),
                                        line[1],
                                        '\n']
                        report += '\n'.join(report_lines)
                    report += 80 * '<' +'\n'

        if (not self.status == STOPPED 
            and self.new_positions_permitted(data[TIME])):
            for rule in self.enter_rules:
                actions = rule.is_true(**data)
                if actions:
                    new_report = self.run(actions, **data)
                    self.entry_log += new_report
                    rule.flag_remove()
                    report += 80 * '>' +'\n'
                    for line in new_report:
                        report_lines  = ['id: {}'.format(self.name),
                                         str(line[0]),
                                         line[1],
                                         '\n']
                        report += '\n'.join(report_lines)
                    report += 80 * '>' +'\n'

            if self.status == IN_TRADE:
                if self.max_in_trade == 0:
                    self.max_in_trade = data[HIGH]
                    self.min_in_trade = data[LOW]
                else:
                    self.max_in_trade = max(self.max_in_trade, data[HIGH])
                    self.min_in_trade = min(self.min_in_trade, data[LOW])


        return report
