#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import os.path
import csv
import datetime
from operator import itemgetter
from collections import namedtuple

import mypy
import position_manager
#from trade_manager import VirtualSinglePositions as Positions
import barData

class BlokCodeError(Exception):pass

def main():
    
    #rule_script = "simpletrader.cr"
    rule_script = "wtf_trader.cr"
    basefile = "lout"
    output_file = '.'.join([basefile, "t9"])
    simulator = TradeSimulationByRules(rule_script)
    permanent_swing_count_file = os.path.join(mypy.TMP_LOCATION,
                                              '.'.join([basefile, 't2']))
    for line in open(permanent_swing_count_file, "r"):
        perm_line = line.split(',')
        perm_line[1] = int(perm_line[1])
        perm_line[3] = float(perm_line[3])
        perm_line[5] = float(perm_line[5])        
        simulator.register([perm_line])
    simulator.export_action_log(output_file)
    
class TradeSimulationByArgs():
    '''ssiaw: Simple Stop Management, In At Wavecount'''
    
    def __init__(self,                 
                 stoploss_handler='kiss',
                 profit_handler='kiss',
                 wavecount_in=2,
                 trailing_exit=False, start_trailing_at=0,
                 fix_exit=False, fix_at=0,
                 max_gap_to_curr=False, max_gap=0,
                 min_gap_to_curr=False, min_gap=0,
                 cap_stop=False, cap=0,
                 sph=False):
        self.stoploss_handler = stoploss_handler
        self.profit_handler = profit_handler
        self.wavecount_in = wavecount_in
        if trailing_exit:
            if not trailing_exit in ('entry+fix', 'entry+percent'):
                mss = 'trailing_exit must be entry+fix or entry+percent'
                raise Exception(mss)
            if start_trailing_at == 0:
                raise Exception('start_trailing_at must be > 0')
        else:
            if start_trailing_at:
                raise Exception('start trailing at set with trail exit false?')
        self.trailing_exit = trailing_exit
        self.start_trailing_at = start_trailing_at
        if fix_exit:
            if not fix_exit in ('fix', 'percent'):
                raise Exception('fix_exit must be fix or percent')
            if fix_at == 0:
                raise Exception('fix_at must be > 0')
        else:
            if fix_at:
                raise Exception('fix_at at set with fix exit false?')
        self.fix_exit = fix_exit
        self.fix_at = fix_at
        self.max_gap_to_curr, self.max_gap = max_gap_to_curr, max_gap
        self.min_gap_to_curr, self.min_gap = min_gap_to_curr, min_gap
        self.cap_stop, self.cap = cap_stop, cap
        self.long_stop = self.short_stop = None #
        self.up_count = self.down_count = 0     #
        self.up_swing_comp = []
        self.down_swing_comp = []
        self.day_trade_mode = False
        self.trading_allowed = True
        self.positions = position_manager.VirtualSinglePositions()
        self.simulator_parameters_history = None if not sph else [] 
        
         
    def use_daytrader_mode(self, std_end_time=None, last_in=None, 
                           managed_out=None, last_out=None):
        self.day_trade_mode = DaytradeMode(
            std_end_time, last_in, managed_out, last_out)
        
        
    def save_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        outputfile = os.path.join(location, filename)
        info = (self.stoploss_handler, self.profit_handler,
                self.wavecount_in,
                self.trailing_exit, self.start_trailing_at,
                self.fix_exit, self.fix_at,
                self.max_gap_to_curr, self.max_gap,
                self.min_gap_to_curr, self.min_gap,
                self.cap_stop, self.cap,
                self.long_stop, self.short_stop,  #
                self.up_count, self.down_count,   #
                #self.up_swing_comp, self.down_swing_comp,
                self.day_trade_mode, self.trading_allowed)
        mypy.export_pickle(info, outputfile, id_="trade_sim : minimal_restart_info")
        self.positions.save_minimal_restart_info('.'.join([filename, "positions"]),
                                                location)
        
    def load_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        #if not self.action_log == []:
            #raise Exception("trying to load data in a running manager")
        inputfile = os.path.join(location, filename)
        (self.stoploss_handler, self.profit_handler, self.wavecount_in,
         self.trailing_exit, self.start_trailing_at, self.fix_exit, self.fix_at,
         self.max_gap_to_curr, self.max_gap,
         self.min_gap_to_curr, self.min_gap,
         self.cap_stop, self.cap,
         self.long_stop, self.short_stop, self.up_count, self.down_count, #
         #self.up_swing_comp, self.down_swing_comp,
         self.day_trade_mode, self.trading_allowed) = mypy.import_pickle(
                        inputfile, id_="trade_sim : minimal_restart_info")
        self.positions.load_minimal_restart_info('.'.join([filename, "positions"]),
                                                location)
        
    def save__action_log(self, filename, location=mypy.TMP_LOCATION):
        self.positions.save_action_log(filename, location)
        
    def load_action_log(self, filename, location=mypy.TMP_LOCATION):
        self.positions.load_action_log(filename, location)
        
    def export_action_log(self, filename, location=mypy.TMP_LOCATION):
        self.positions.export_action_log(filename, location)
        if not self.simulator_parameters_history == None:
            filename += ".simulator_vars"
            outputfile = os.path.join(location, filename)
            with open(outputfile, 'w', newline='') as ofh:
                csv_out = csv.writer(ofh)
                csv_out.writerow(("time", "reason", "up count", "down count",
                                  "long stop", "short stop"))
                csv_out.writerows(self.simulator_parameters_history)
        
    def export_positions(self, filename, location=mypy.TMP_LOCATION):
        self.positions.export_positions(filename, location)
        
    def export_stoploss_actions(self, filename, location=mypy.TMP_LOCATION):     
        outputfile = os.path.join(location, filename)
        #mypy.get_bool(outputfile, default=True)
        with open(outputfile, 'w', newline='') as ofh:
            if self.positions.current_postitions() == None:
                ofh.write("no positions\n")
                return
            curr_list = self.positions.current_postitions()[:]
            t = 0
            for position in curr_list: #self.positions.current_postitions():
                t += 1
                if t > 10:
                    raise Exception ("dtrurmud")
                ofh.write("position\n")
                ofh.write(str(position))
                ofh.write("\n")
                self.positions.work_with_copy()
                orig_long_stop = self.long_stop   #
                orig_short_stop = self.short_stop #
                orig_up_count = self.up_count     #
                orig_down_count = self.down_count #
                #orig_up_swing_comp = self.up_swing_comp
                #orig_down_swing_comp = self.down_swing_comp
                if position.direction == "long":
                    w = position.stop - 0.01
                    v = "< "
                else:
                    w = position.stop + 0.01
                    v = "> "
                virtual_ochl = barData.ochlBar(mypy.now(), w, w, w, w)
                self.check_and_handle_stoplosses(virtual_ochl)
                ofh.write("position after stoploss\n")
                if self.positions.current_postitions() == None:
                    ofh.write("no positions")
                else:
                    for p in self.positions.current_postitions():
                        ofh.write(str(p))
                        ofh.write("\n")
                self.positions.work_with_original()
                self.long_stop = orig_long_stop   #
                self.short_stop = orig_short_stop #
                self.up_count = orig_up_count     #
                self.down_count = orig_down_count #
                #self.up_swing_comp = orig_up_swing_comp
                #self.down_swing_comp = orig_down_swing_comp
    
    
    def register(self, perm_lines):    
        
        perm_lines = sorted(perm_lines, key=itemgetter(1))
        actions = []
        curr_time = perm_lines[-1][-2]
        for perm_line in perm_lines:
            if ((self.short_stop == None and #
                 #len(self.down_swing_comp) == 0 and
                 perm_line[0] == "down" and
                 not perm_line[1] == 0)
                or
                (self.long_stop == None and #
                 #len(self.up_swing_comp) == 0 and
                 perm_line[0] == "up" and
                 not perm_line[1] == 0)):
                continue
            action = self.register_perm_line(perm_line)
            if action: actions.append(action)
            if not self.simulator_parameters_history == None:
                self.simulator_parameters_history.append(
                    (curr_time, perm_line[0] + str(perm_line[1]),
                     self.up_count, self.down_count,
                     self.long_stop, self.short_stop,
                     ))
        return actions 
            
    def register_perm_line(self, perm_line):
        
        def min_gap_to_curr(type_, min_gap, stop):
            #stop = self.long_stop if direction == 'up' else self.short_stop
            if type_ == "entry+fix":
                number = stop - triad_exit_value
            elif type_ == "entry+percent":
                number = ((stop / triad_exit_value) - 1) * 100
            return abs(number) > min_gap  
        
        def max_gap_to_curr(type_, max_gap, stop):
            #stop = self.long_stop if direction == 'up' else self.short_stop
            if type_ == "entry+fix":
                number = stop - triad_exit_value
            elif type_ == "entry+percent":
                number = ((stop / triad_exit_value) - 1) * 100
            return abs(number) < max_gap
        
        (direction, wavecount, triad_top_time, triad_top_value,
         triad_exit_time, triad_exit_value) = perm_line
        if direction == 'up':
            if wavecount == 0: 
                self.long_stop = triad_top_value #
                #self.up_swing_comp = [triad_top_value]
            else:
                pass
                #t = self.up_swing_comp[:wavecount]
                #self.up_swing_comp = t.append(triad_top_value)
            self.up_count = wavecount #
            stop = self.long_stop
        else:
            if wavecount == 0: 
                self.short_stop = triad_top_value #
                #self.down_swing_comp = [triad_top_value]
            else:
                pass
                #t = self.down_swing_comp[:wavecount]
                #self.down_swing_comp = t.append(triad_top_value)
            self.down_count = wavecount #
            stop = self.short_stop
        if (not self.positions.in_trade() and            
            wavecount == self.wavecount_in):
            # if not in trade or wavecount is not 
            #return None
            trade_direction = 'long' if direction == 'up' else 'short'
            if ((self.min_gap_to_curr and 
                 not min_gap_to_curr(self.min_gap_to_curr, self.min_gap, stop))
                or
                (self.max_gap_to_curr and 
                 not max_gap_to_curr(self.max_gap_to_curr, self.max_gap, stop))):
                return None 
            if not self.trading_allowed: return None
            self.positions.enter(0, 'nd', trade_direction, 1, 
                                 triad_exit_time, triad_exit_value, 
                                 'no trade: enter on wavecount {}'.format(
                                                           self.wavecount_in),
                                 stop)        
            if self.cap_stop:
                type_ = 'entry+' if self.cap_stop == "fix" else "entry+%"
                self.positions.cap_stop(0, type_, self.cap)
            if self.trailing_exit == 'entry+fix':
                self.positions.set_out_type(0, 'entry+', self.start_trailing_at)
            elif self.trailing_exit == 'entry+percent':
                self.positions.set_out_type(0, 'entry+%', self.start_trailing_at)
            elif self.fix_exit == 'fix':
                self.positions.set_profittaker(0, 'entry+', self.fix_at)
            elif self.fix_exit == 'percent':
                self.positions.set_profittaker(0, 'entry+%', self.fix_at)
            else:
                raise Exception('No profittaker set, use trailing or set profittaker')
            action = [0, 'nd', trade_direction, 1,
                      triad_exit_time, triad_exit_value, 
                      'no trade: enter on wavecount {}'.format(self.wavecount_in)]
        else:
            action = None
        return action
        
    def handle_stoploss(self, position, curr_ochl):
        actions = []
        if self.stoploss_handler == 'kiss':
            action = self.default_stoploss_handler(position, curr_ochl)
            if action:
                actions.append(action)
        else:
            raise Exception('Unknown stoploss handler')
        if not self.simulator_parameters_history == None:
            self.simulator_parameters_history.append(
                (curr_ochl.time, 'S',
                 self.up_count, self.down_count,
                 self.long_stop, self.short_stop,
                 ))
        return actions

    def default_stoploss_handler(self, position, curr_ochl):
        id_ = position.id
        name, direction, size = self.positions.exit_parameters(id_)
        time_ = curr_ochl.time
        price = position.stop
        if (price == None) or (not price in curr_ochl):
            price = curr_ochl.open
        reason = 'Hit stoploss'
        self.positions.exit(id_, name, direction, size, time_, price, reason)
        return [id_, name, direction, size, time_, price, reason]
        
    def handle_profittaker(self, position, curr_ochl):
        actions = []
        if self.profit_handler == 'kiss':
            action = self.default_profit_handler(position, curr_ochl)
            if action:
                actions.append(action)
        else:
            raise Exception('Unknown profit handler')
        if not self.simulator_parameters_history == None:
            self.simulator_parameters_history.append(
                (curr_ochl.time, 'S',
                 self.up_count, self.down_count,
                 self.long_stop, self.short_stop,
                 ))
        return actions

    def default_profit_handler(self, position, curr_ochl):
        id_ = position.id
        name, direction, size = self.positions.exit_parameters(id_)
        time_ = curr_ochl.time
        price = position.profit
        if not price in curr_ochl:
            price = curr_ochl.open
        reason = 'Exit, profit triggered'
        self.positions.exit(id_, name, direction, size, time_, price, reason)
        return [id_, name, direction, size, time_, price, reason]
    
    def check_and_handle_stoplosses(self, curr_ochl):
        if self.positions.in_trade():
            #print(self.positions)
            for position in self.positions.current_postitions():
                if position.stop == None:
                    print(positition)
                    mypy.get_bool("position without stop")
                    return
                if ((position.direction == "long" and
                    curr_ochl.low <= position.stop)
                    or
                    (position.direction == "short" and
                     curr_ochl.high >= position.stop)):
                    self.handle_stoploss(position, curr_ochl)
        if self.short_stop and curr_ochl.high > self.short_stop:
            self.short_stop = None
            self.down_count = 0
            reset = True
            #mypy.get_bool("resetting short")
        elif self.long_stop and curr_ochl.low < self.long_stop:
            self.long_stop = None
            self.up_count = 0
            reset = True
            #mypy.get_bool("resetting long")
        else: reset = False
        if (not self.simulator_parameters_history == None and
            reset):
            self.simulator_parameters_history.append(
                (curr_ochl.time, "RS",
                 self.up_count, self.down_count,
                 self.long_stop, self.short_stop,
                 ))
            
    def check_and_handle_profittakers(self, curr_ochl):
        if self.positions.in_trade():
            for position in self.positions.current_postitions():
                if position.out_type == None and position.profit == None:
                    return
                if position.profit == None:
                    if position.out_type[0][0] == "trailing":
                        return
                    print(position)                    
                    mypy.get_bool("position without profit")
                    return
                if ((position.direction == "long" and
                    curr_ochl.high >= position.profit)
                    or
                    (position.direction == "short" and
                     curr_ochl.low <= position.profit)):
                    self.handle_profittaker(position, curr_ochl)
                            
    def life_bar_checks_and_actions(self, curr_ochl):
        if self.day_trade_mode:
            eod_actions_to_take = self.day_trade_mode.actions_to_take(
                                                     curr_ochl.time.time())
            if eod_actions_to_take:
                if DaytradeMode.RESET in eod_actions_to_take:
                    self.trading_allowed = True
                if DaytradeMode.NO_NEW_TRADES in eod_actions_to_take:
                    self.trading_allowed = False
                if DaytradeMode.CLOSE_ALL_POS_NOW in eod_actions_to_take:
                    self.positions.exit_all_pos(curr_ochl.time, curr_ochl.close,
                                            "closing all positions, end of day")
        if self.positions.in_trade() and self.positions.pending_enter:
            self.positions.check_pending_enter(curr_ochl)
        self.check_and_handle_stoplosses(curr_ochl)
        self.check_and_handle_profittakers(curr_ochl)
                            
                    
    def finished_bar_checks_and_actions(self, finished_ochl):
        if self.positions.in_trade():
            for position in self.positions.current_postitions():
                if position.out_type == None:
                    return
                if position.out_type[0][0] == "trailing":
                    if not position.out_type[0][1] == "active":
                        if position.out_type[0][1] == "entry+":
                            value = position.out_type[1]
                            corr = 1 if position.direction == "long" else -1
                            trigger_price = position.price + corr * value
                        elif position.out_type[0][1] == "entry+%":
                            value = position.out_type[1]
                            corr = 1 if position.direction == "long" else -1
                            trigger_price = (
                                position.price * (1 + corr * value / 100))
                        else:
                            raise Exception("Unknown profittaker type")
                        if ((position.direction == "long" and
                             finished_ochl.high >= trigger_price)
                            or
                            (position.direction == "short" and
                             finished_ochl.low <= trigger_price)):
                            position.out_type = (("trailing", "active"),)
                    if position.out_type[0][1] == "active":
                        if position.direction == "long":
                            position.stop = finished_ochl.low
                        else:
                            position.stop = finished_ochl.high
            
        
        
    
class TradeSimulationByRules():
    
    def __init__(self, rules_script=None, sph=False):
        if rules_script: self.make_rule_book(rules_script)  #creates self.rule_book
        self.long_stop = self.short_stop = None
        self.up_count = self.down_count = 0
        self.day_trade_mode = False
        self.trading_allowed = True
        self.positions = position_manager.VirtualSinglePositions()
        self.simulator_parameters_history = None if not sph else []
        
        
    def use_daytrader_mode(self, std_end_time=None, last_in=None, 
                           managed_out=None, last_out=None):
        self.day_trade_mode = DaytradeMode(
            std_end_time, last_in, managed_out, last_out)
        
        
    def save_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        outputfile = os.path.join(location, filename)
        info = (self.rule_book, self.long_stop, self.short_stop,
                self.up_count, self.down_count,
                self.day_trade_mode, self.trading_allowed)
        mypy.export_pickle(info, outputfile, id_="trade_sim : minimal_restart_info")
        self.positions.save_minimal_restart_info('.'.join([filename, "positions"]),
                                                location)
        
    def load_minimal_restart_info(self, filename, location=mypy.TMP_LOCATION):
        #if not self.action_log == []:
            #raise Exception("trying to load data in a running manager")
        inputfile = os.path.join(location, filename)
        (self.rule_book, self.long_stop, self.short_stop,
                self.up_count, self.down_count,
                self.day_trade_mode, self.trading_allowed) = mypy.import_pickle(
                        inputfile, id_="trade_sim : minimal_restart_info")
        self.positions.load_minimal_restart_info('.'.join([filename, "positions"]),
                                                location)
        
    def save__action_log(self, filename, location=mypy.TMP_LOCATION):
        self.positions.save_action_log(filename, location)
        
    def load_action_log(self, filename, location=mypy.TMP_LOCATION):
        self.positions.load_action_log(filename, location)
        
    def export_action_log(self, filename, location=mypy.TMP_LOCATION):
        self.positions.export_action_log(filename, location)
        if not self.simulator_parameters_history == None:
            filename += ".simulator_vars"
            outputfile = os.path.join(location, filename)
            with open(outputfile, 'w', newline='') as ofh:
                csv_out = csv.writer(ofh)
                csv_out.writerow(("time", "reason", "up count", "down count",
                                  "long stop", "short stop"))
                csv_out.writerows(self.simulator_parameters_history)
                #for info in self.simulator_parameters_history:
                    #csv_out.writerow(info)
        
    def export_positions(self, filename, location=mypy.TMP_LOCATION):
        self.positions.export_positions(filename, location)
        
    def export_stoploss_actions(self, filename, location=mypy.TMP_LOCATION):     
        outputfile = os.path.join(location, filename)
        #mypy.get_bool(outputfile, default=True)
        with open(outputfile, 'w', newline='') as ofh:
            if self.positions.current_postitions() == None:
                ofh.write("no positions\n")
                return
            curr_list = self.positions.current_postitions()[:]
            t = 0
            for position in curr_list: #self.positions.current_postitions():
                t += 1
                if t > 10:
                    raise Exception ("dtrurmud")
                ofh.write("position\n")
                ofh.write(str(position))
                ofh.write("\n")
                self.positions.work_with_copy()
                orig_long_stop = self.long_stop
                orig_short_stop = self.short_stop
                orig_up_count = self.up_count
                orig_down_count = self.down_count
                if position.direction == "long":
                    w = position.stop - 0.01
                    v = "< "
                else:
                    w = position.stop + 0.01
                    v = "> "
                virtual_ochl = barData.ochlBar(mypy.now(), w, w, w, w)
                self.check_and_handle_stoplosses(virtual_ochl)
                ofh.write("position after stoploss\n")
                if self.positions.current_postitions() == None:
                    ofh.write("no positions")
                else:
                    for p in self.positions.current_postitions():
                        ofh.write(str(p))
                        ofh.write("\n")
                self.positions.work_with_original()
                self.long_stop = orig_long_stop
                self.short_stop = orig_short_stop
                self.up_count = orig_up_count
                self.down_count = orig_down_count
                
                
                ## hier nu de posities afdrukken >>>>>

        
    def make_rule_book(self, script):
        #
        def smart_split(line):
            print("proc lin: ", line)
            line, foo, bar = line.partition('#')
            if not line or line.isspace(): return []
            STRING = "__$_$_$__"
            strings = []
            line = line.split('|||')
            if len(line) > 1:
                if line[-1] == line[-2] == '': line.pop()
                for i in range(2, len(line)):
                    if line[i] == '':
                        strings.append(line[i-1])
                        line[i-1] = STRING
            line = "".join(line)
            level = 0
            while line[0] == ' ':
                level += 1
                line = line[1:]
            ell = line.strip().split(' ')
            ell = [x.strip() for x in ell if x]
            if ell: ell.insert(0, level)
            ell__ = []
            for e in ell:
                if e == STRING:
                    e = strings.pop(0)
                ell__.append(e)
            return ell__
        #
        def format_rules(rule_list, min_blok_level=-1):
            blok_instructions = {"if", "case", "loop"}
            blok_level = rule_list[0][0]
            if blok_level <= min_blok_level:
                raise BlokCodeError('blok must indent')
            codeblok = []
            while rule_list:
                if rule_list[0][0] < blok_level: break
                if rule_list[0][0] > blok_level:
                    raise BlokCodeError("blokcode must be on the same level")
                print(rule_list[0])
                foo, curr_instruction, *parameters = rule_list.pop(0)
                codeline = [curr_instruction, parameters]
                if curr_instruction in blok_instructions:
                    codeline.append(format_rules(rule_list, blok_level))
                codeblok.append(codeline)
            return codeblok            
        #
        code_text = []
        with open(script, "r") as rules_book:
            for line in rules_book:
                line_ell = smart_split(line)
                if line_ell: code_text.append(line_ell)
        self.rule_book = format_rules(code_text)
        
    
    def register(self, perm_lines):            
        
        perm_lines = sorted(perm_lines, key=itemgetter(1))
        actions = []      
        ns = {"__COMMANDS__": self.commands,
              "__TESTS__": self.tests,
              "__INFO__": self.info,
              #"__PERM_LINE__": perm_line,
              "__POSITIONS__": self.positions,
              "__LONG_STOP__": self.long_stop,
              "__SHORT_STOP__": self.short_stop,
              "__UP_COUNT__": self.up_count,
              "__DOWN_COUNT__": self.down_count,
              "__ACTIONS__": actions,
              }
        curr_time = perm_lines[-1][-2]
        for perm_line in perm_lines:
            if ((self.short_stop == None and
                 perm_line[0] == "down" and
                 not perm_line[1] == 0)
                or
                (self.long_stop == None and
                 perm_line[0] == "up" and
                 not perm_line[1] == 0)):
                continue                 
            print("\nSTART REGISTER")
            ns["__PERM_LINE__"] = perm_line
            run_data = self.run_blok(self.rule_book, ns)
            print("ran {} commands".format(run_data["__COMMANDS_COUNTER__"]))
            self.long_stop, self.short_stop = ns["__LONG_STOP__"], ns["__SHORT_STOP__"]
            self.up_count, self.down_count = ns["__UP_COUNT__"], ns["__DOWN_COUNT__"]
            #mypy.get_bool('druk ergens op enter of zo', default=True)
            print("=====================================================")
            if not self.simulator_parameters_history == None:
                self.simulator_parameters_history.append(
                    (curr_time, perm_line[0] + str(perm_line[1]),
                     self.up_count, self.down_count,
                     self.long_stop, self.short_stop,
                     ))
        return ns["__ACTIONS__"]
        
        #if hasattr(ns, "EXPORT"):
            #export(ns)
            
    def handle_stoploss(self, position, curr_ochl):
        actions = []      
        ns = {"__COMMANDS__": self.commands,
              "__TESTS__": self.tests,
              "__INFO__": self.info,
              "__POSITIONS__": self.positions,
              "__LONG_STOP__": self.long_stop,
              "__SHORT_STOP__": self.short_stop,
              "__UP_COUNT__": self.up_count,
              "__DOWN_COUNT__": self.down_count,
              "__ACTIONS__": actions,
              "__POSITION_WITH_TRIGGERED_STOP__": position,
              "__OCHL__": curr_ochl,
              } 
        print("HANDLE TRIGGERED STOP")        
        run_data = self.run_blok(self.rule_book, ns)
        print("ran {} commands".format(run_data["__COMMANDS_COUNTER__"]))
        self.long_stop, self.short_stop = ns["__LONG_STOP__"], ns["__SHORT_STOP__"]
        self.up_count, self.down_count = ns["__UP_COUNT__"], ns["__DOWN_COUNT__"]
        if not self.simulator_parameters_history == None:
            self.simulator_parameters_history.append(
                (curr_ochl.time, 'S',
                 self.up_count, self.down_count,
                 self.long_stop, self.short_stop,
                 ))
        return ns["__ACTIONS__"]
    
    
    def handle_profittaker(self, position, curr_ochl):
        actions = []      
        ns = {"__COMMANDS__": self.commands,
              "__TESTS__": self.tests,
              "__INFO__": self.info,
              "__POSITIONS__": self.positions,
              "__LONG_STOP__": self.long_stop,
              "__SHORT_STOP__": self.short_stop,
              "__UP_COUNT__": self.up_count,
              "__DOWN_COUNT__": self.down_count,
              "__ACTIONS__": actions,
              "__POSITION_WITH_TRIGGERED_PROFIT__": position,
              "__OCHL__": curr_ochl,
              } 
        print("HANDLE TRIGGERED PROFIT")        
        run_data = self.run_blok(self.rule_book, ns)
        print("ran {} commands".format(run_data["__COMMANDS_COUNTER__"]))
        self.long_stop, self.short_stop = ns["__LONG_STOP__"], ns["__SHORT_STOP__"]
        self.up_count, self.down_count = ns["__UP_COUNT__"], ns["__DOWN_COUNT__"]
        if not self.simulator_parameters_history == None:
            self.simulator_parameters_history.append(
                (curr_ochl.time, 'P',
                 self.up_count, self.down_count,
                 self.long_stop, self.short_stop,
                 ))
        return ns["__ACTIONS__"]
    
    def check_and_handle_stoplosses(self, curr_ochl):
        if self.positions.in_trade():
            #print(self.positions)
            for position in self.positions.current_postitions():
                if position.stop == None:
                    print(positition)
                    mypy.get_bool("position without stop")
                    return
                if ((position.direction == "long" and
                    curr_ochl.low < position.stop)
                    or
                    (position.direction == "short" and
                     curr_ochl.high > position.stop)):
                    self.handle_stoploss(position, curr_ochl)
        if self.short_stop and curr_ochl.high > self.short_stop:
            self.short_stop = None
            self.down_count = 0
            reset = True
            #mypy.get_bool("resetting short")
        elif self.long_stop and curr_ochl.low < self.long_stop:
            self.long_stop = None
            self.up_count = 0
            reset = True
            #mypy.get_bool("resetting long")
        else: reset = False
        if (not self.simulator_parameters_history == None and
            reset):
            self.simulator_parameters_history.append(
                (curr_ochl.time, "RS",
                 self.up_count, self.down_count,
                 self.long_stop, self.short_stop,
                 ))
            
    def check_and_handle_profittakers(self, curr_ochl):
        if self.positions.in_trade():
            for position in self.positions.current_postitions():
                if position.out_type == None and position.profit == None:
                    return
                if position.profit == None:
                    if position.out_type[0][0] == "trailing":
                        return
                    print(position)                    
                    mypy.get_bool("position without profit")
                    return
                if ((position.direction == "long" and
                    curr_ochl.high >= position.profit)
                    or
                    (position.direction == "short" and
                     curr_ochl.low <= position.profit)):
                    self.handle_profittaker(position, curr_ochl)
                            
    def life_bar_checks_and_actions(self, curr_ochl):
        if self.day_trade_mode:
            eod_actions_to_take = self.day_trade_mode.actions_to_take(
                                                     curr_ochl.time.time())
            if eod_actions_to_take:
                if DaytradeMode.RESET in eod_actions_to_take:
                    self.trading_allowed = True
                if DaytradeMode.NO_NEW_TRADES in eod_actions_to_take:
                    self.trading_allowed = False
                if DaytradeMode.CLOSE_ALL_POS_NOW in eod_actions_to_take:
                    self.positions.exit_all_pos(curr_ochl.time, curr_ochl.close,
                                            "closing all positions, end of day")
                if DaytradeMode.OUT_OF_DAY_BAR and self.positions.in_trade():
                    mss = "{}, daytrade mode, out of rth still in trade?"
                    raise Exception(mss)
        if self.positions.in_trade() and self.positions.pending_enter:
            self.positions.check_pending_enter(curr_ochl)
        self.check_and_handle_stoplosses(curr_ochl)
        self.check_and_handle_profittakers(curr_ochl)
                            
                    
    def finished_bar_checks_and_actions(self, curr_ochl):
        if self.positions.in_trade():
            for position in self.positions.current_postitions():
                if position.out_type == None:
                    return
                if position.out_type[0][0] == "trailing":
                    if not position.out_type[0][1] == "active":
                        if position.out_type[0][1] == "entry+":
                            value = position.out_type[1]
                            corr = 1 if position.direction == "long" else -1
                            trigger_price = position.price + corr * value
                        elif position.out_type[0][1] == "entry+%":
                            value = position.out_type[1]
                            corr = 1 if position.direction == "long" else -1
                            trigger_price = (
                                position.price * (1 + corr * value / 100))
                        else:
                            raise Exception("Unknown profittaker type")
                        if ((position.direction == "long" and
                             curr_ochl.high >= trigger_price)
                            or
                            (position.direction == "short" and
                             curr_ochl.low <= trigger_price)):
                            position.out_type = (("trailing", "active"),)
                    if position.out_type[0][1] == "active":
                        if position.direction == "long":
                            position.stop = curr_ochl.low
                        else:
                            position.stop = curr_ochl.high
                                
    def run_blok(self, blok, ns):
        blok = blok[:]
        blok_ns = {"__LAST_COMMAND__": None,
                   "__COMMANDS_COUNTER__": 0,}
        commands_ran = 0
        for command, *parameters in blok:
            print("\n",ns["__COMMANDS__"][command])
            i = ns["__COMMANDS__"][command](self, parameters, ns, blok_ns)
            blok_ns["__COMMANDS_COUNTER__"] += i
            if "__STOP__" in ns: break
            blok_ns["LAST_COMMAND"] = command
        return blok_ns 
            
    ########
    # COMMANDS
    ########
    
    def sr_stop(self, parameters, ns, blok_ns):
        ns["__STOP__"] = True
        return 1
    
    def sr_set(self, parameters, ns, blok_ns):
        print("in sr set")
        if len(parameters) > 1:
            raise BlokCodeError("set: no blok part needed")
        parameters = parameters[0]
        if len(parameters) < 3:
            print(parameters)
            err = "set use: set [local|global] name function parameters"
            raise BlokCodeError(err)
        scope, *parameters = parameters
        if scope == "local": i = self.p_set(blok_ns, parameters, ns, blok_ns)
        elif scope == "global": i = self.p_set(ns, parameters, ns, blok_ns)
        else: raise BlokCodeError("set must have local or global attribute")
        return i
        
    def sr_if(self, parameters, ns, blok_ns):
        if len(parameters) > 2:
            raise BlokCodeError("if: ??? 3 parameters")
        if len(parameters) < 2:
            raise BlokCodeError("if: needs blok part")
        test, blok = parameters
        blok = blok[:]
        print("    ",test)
        print("    ",blok)
        if self.test_result(test, ns, blok_ns) == True:
            nr_of_comm = self.run_blok(blok, ns)["__COMMANDS_COUNTER__"]
            blok_ns["__LAST_IF_SUCCESFULL__"] = True
            return nr_of_comm + 1
        blok_ns["__LAST_IF_SUCCESFULL__"] = False
        return 1
    
    def sr_compare(self, parameters, ns, blok_ns):               
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")        
        parameters = parameters[0]
        try:
            at_at = parameters.index('&')
        except ValueError:
            raise BlokCodeError("compare needs '&' ell")
        val1 = self.get_info(parameters[0:at_at], ns, blok_ns)
        val2 = self.get_info(parameters[at_at+1:], ns, blok_ns)
        try:
            if val1 == val2: result = 0
            elif val1 > val2: result = 1
            else: result = 2
        except TypeError:
            raise BlokCodeError("compare: uncomparable types")
        print("{}/{} comp {}/{}: {}".format(type(val1), val1, 
                                            type(val2), val2, result))
        blok_ns["__LAST_COMPARE__"] = result
        return 3
        
    
    def sr_case(self, parameters, ns, blok_ns):
        if len(parameters) > 2:
            raise BlokCodeError("case: ??? 3 parameters")
        if len(parameters) < 2:
            raise BlokCodeError("case: needs blok part")
        options, blok = parameters
        blok = blok[:]
        print("    ",options)
        print("    ",blok)
        if_in_case = False
        nr_of_comm = 0
        while blok:
            case_blok = [blok.pop(0)]
            while blok:
                if not case_blok[-1][0] == "if":
                    case_blok.append(blok.pop(0))
                else: break
            run_data = self.run_blok(case_blok, ns)
            nr_of_comm += run_data["__COMMANDS_COUNTER__"]
            try:
                if run_data["__LAST_IF_SUCCESFULL__"]:
                    break
                else: if_in_case = True
            except KeyError:
                if if_in_case:
                    err = "case: no commands allowed after last if"
                    raise BlokCodeError(err)
                else:
                    raise BlokCodeError("case: if commonds required")
        return nr_of_comm
    
    def sr_loop(self, parameters, ns, blok_ns):        
        if len(parameters) > 2:
            raise BlokCodeError("case: ??? 3 parameters")
        if len(parameters) < 2:
            raise BlokCodeError("case: needs blok part")
        nr_of_comm = 0
        repeat, blok = parameters
        repeat = self.get_info(repeat, ns, blok_ns)        
        blok = blok[:]
        print("    max repeat {}".format(repeat))
        print("    ",blok)
        for i in range(repeat):
            run_data = self.run_blok(blok, ns)
            nr_of_comm += run_data["__COMMANDS_COUNTER__"]
            #print (ns)
            if "__EXIT_LOOP__" in ns:
                ns.pop("__EXIT_LOOP__")
                blok_ns["__FULL_LOOP__"] = False
                break
        else: blok_ns["__FULL_LOOP"] = True 
        return nr_of_comm
    
    def sr_exit_loop(self, parameters, ns, blok_ns):     
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")
        parameters = parameters[0]
        ns["__EXIT_LOOP__"] = True
        return 0
        
    def sr_print(self, parameters, ns, blok_ns):        
        if not len(parameters) == 1:
            raise BlokCodeError("register_triad: no blok part allowed")
        parameters = parameters[0]
        val = self.get_info(parameters, ns, blok_ns)
        print(val)
        return 1
    
    def r_reset_stop(self, parameters, ns, blok_ns):
        c = {"up": "__LONG_STOP__",
             "down": "__SHORT_STOP__"}
        if not len(parameters) == 1:
            raise BlokCodeError("enter_trade: no blok part allowed")
        parameters = parameters[0]
        direction = ns["__PERM_LINE__"][0]
        stop = ns["__PERM_LINE__"][3]
        ns[c[direction]] = stop
        return 1
    
    def r_set_direction_wave_count(self, parameters, ns, blok_ns):
        c = {"up": "__UP_COUNT__",
             "down": "__DOWN_COUNT__"}
        if not len(parameters) == 1:
            raise BlokCodeError("enter_trade: no blok part allowed")        
        direction = ns["__PERM_LINE__"][0]
        count = ns["__PERM_LINE__"][1]
        ns[c[direction]] = count
        return 1
    
    def r_enter_trade(self, parameters, ns, blok_ns):
        if not self.trading_allowed:
            ns["__LAST_COMMAND_EXECUTED__"] = False
            return 0
        c = {"up": "long",
             "down": "short"}
        c_rev = {"up": "short",
                 "down": "long"}
        if not len(parameters) == 1:
            raise BlokCodeError("enter_trade: no blok part allowed")
        parameters = parameters[0]
        if len(parameters) == 1:
            id_ = 0
            name = "aex"
            direction = c[ns["__PERM_LINE__"][0]]
            size = 1
            time = ns["__PERM_LINE__"][4]
            price = ns["__PERM_LINE__"][5]
            reason = parameters[0]
            stop = ns["__LONG_STOP__"] if direction == "long" else ns["__SHORT_STOP__"]
        elif parameters[0] == "rev_swing":
            id_ = 0
            name = 'test'
            direction = c_rev[ns["__PERM_LINE__"][0]]
            size = 1
            time = ns["__PERM_LINE__"][4]           
            price = ns["__PERM_LINE__"][5]
            reason = parameters[1]
            stop = ns["__PERM_LINE__"][3]
        self.positions.enter(id_, name, direction, size, time, price, 
                             reason, stop)
        ns["__LAST_COMMAND_EXECUTED__"] = True
        ns["__ACTIONS__"].append([id_, name, direction, size, 
                                                time, price, reason])
        return 1
    
    def r_exit_trade(self, parameters, ns, blok_ns):
        if not len(parameters) == 1:
            raise BlokCodeError("enter_trade: no blok part allowed")
        parameters = parameters[0]
        id_ = 0
        name, direction, size = ns["__POSITIONS__"].exit_parameters(id_)
        if parameters[-1] == "NO_TIME":
            # used for (overnight) gaps before the separateted stoploss
            # mode was introduced.
            time = "???"
            price = self.get_info(parameters[1: -1], ns, blok_ns)
        elif parameters[-1] == "STOPLOSS_MODE":
            time = ns["__OCHL__"].time
            price = self.get_info(parameters[1: -1], ns, blok_ns)            
            if (price == None 
                or
                not price in ns["__OCHL__"]):
                price = ns["__OCHL__"].open
        elif parameters[-1] == "PROFIT_MODE":
            time = ns["__OCHL__"].time
            price = self.get_info(parameters[1: -1], ns, blok_ns)
            if not price in ns["__OCHL__"]:
                price = ns["__OCHL__"].open
        else:
            time = ns["__PERM_LINE__"][4]
            price = ns["__PERM_LINE__"][5]
        reason = parameters[0]
        self.positions.exit(id_, name, direction, size, time, price, reason)
        ns["__ACTIONS__"].append([id_, name, direction, size, 
                                                time, price, reason])
        return 1
    
    def r_reverse_trade(self, parameters, ns, blok_ns):
        if not self.trading_allowed:
            nr_of_commands = self.r_exit_trade(parameters, ns, blok_ns)
            ns["__LAST_COMMAND_EXECUTED__"] = False
            return nr_of_commands
        if not len(parameters) == 1:
            raise BlokCodeError("enter_trade: no blok part allowed")
        parameters = parameters[0]
        id_ = 0
        name, direction, size = ns["__POSITIONS__"].reverse_parameters(id_)
        if parameters[-1] == "NO_TIME":
            time = "???"
            price = self.get_info(parameters[1: -1], ns, blok_ns)
        elif parameters[-1] == "STOPLOSS_MODE":
            time = ns["__OCHL__"].time
            price = self.get_info(parameters[1: -1], ns, blok_ns)
            if not price in ns["__OCHL__"]:
                price = ns["__OCHL__"].open
        else:
            time = ns["__PERM_LINE__"][4]
            price = ns["__PERM_LINE__"][5]
        reason = parameters[0]
        stop = ns["__LONG_STOP__"] if direction == "long" else ns["__SHORT_STOP__"]
        self.positions.reverse(id_, name, direction, size, time, price, 
                               reason,  stop)
        ns["__ACTIONS__"].append([id_, name, direction, size, 
                                                time, price, reason])
        return 1
    
    def r_cap_stop(self, parameters, ns, blok_ns):
        if not len(parameters) == 1:
            raise BlokCodeError("cap_stop: no blok part allowed")
        parameters = parameters[0]
        id_ = 0
        type_ = parameters[0]
        if type_ == "entry+":
            value = self.get_info(parameters[1:3], ns, blok_ns)
        elif type_ == "entry+%":
            value = self.get_info(parameters[1:3], ns, blok_ns)
        else:
            raise BlokCodeError("unknown profittaker type")
        self.positions.cap_stop(id_, type_, value)
        return 1
    
    def r_increase_stop(self, parameters, ns, blok_ns):
        if not len(parameters) == 1:
            raise BlokCodeError("increase_stop: no blok part allowed")
        parameters = parameters[0]
        id_ = 0
        type_ = parameters[0]
        if type_ == "entry+":
            value = self.get_info(parameters[1:3], ns, blok_ns)
        elif type_ == "entry+%":
            value = self.get_info(parameters[1:3], ns, blok_ns)
        else:
            raise BlokCodeError("unknown profittaker type")
        self.positions.increase_stop(id_, type_, value)
        return 1
    
    def r_set_profittaker(self, parameters, ns, blok_ns):     
        if not len(parameters) == 1:
            raise BlokCodeError("enter_trade: no blok part allowed")
        parameters = parameters[0]
        id_ = 0
        type_ = parameters[0]
        if type_ == "entry+":
            value = self.get_info(parameters[1:3], ns, blok_ns)
        elif type_ == "entry+%":
            value = self.get_info(parameters[1:3], ns, blok_ns)
        else:
            raise BlokCodeError("unknown profittaker type")
        self.positions.set_profittaker(id_, type_, value)
        return 1
    
    def r_trailing_exit(self, parameters, ns, blok_ns):    
        if not len(parameters) == 1:
            raise BlokCodeError("enter_trade: no blok part allowed")
        parameters = parameters[0]
        id_ = 0
        type_ = parameters[0]
        if type_ in {"entry+", "entry+%"} :
            value = self.get_info(parameters[1:3], ns, blok_ns)
        else:
            raise BlokCodeError("unknown trailing_exit type")
        self.positions.set_out_type(id_, type_, value)
        return 1
        
        
    commands = {"stop": sr_stop,
                "set": sr_set,
                "if": sr_if,
                "loop": sr_loop,
                "exit_loop": sr_exit_loop,
                "compare": sr_compare,
                "case": sr_case,
                "print": sr_print,
                "enter_trade": r_enter_trade,
                "exit_trade": r_exit_trade,
                "reverse_trade": r_reverse_trade,
                "reset_stop": r_reset_stop,
                "set_direction_wave_count": r_set_direction_wave_count,
                "set_profittaker": r_set_profittaker,
                "trailing_exit": r_trailing_exit,
                "cap_stop": r_cap_stop,
                "increase_stop": r_increase_stop,
                }
    
    def p_set(self, target_ns, parameters, ns, blok_ns ):
        name, *parameters = parameters
        #print(parameters)
        target_ns[name] = self.get_info(parameters, ns, blok_ns)
        #print(target_ns)\
        return 1
        
    def p_clear_list(self, a_list):
        while a_list: a_list.pop()
        
        
            
    ########
    # TESTS
    ########
    
    FROM_PARAMETERS = 1
    OPTIONAL = 2

    def test_result(self, test, ns, blok_ns):
        test, *parameters = test
        print("      test: {}, with para: {}".format(test, str(parameters)))
        test, ns_vars = ns["__TESTS__"][test]
        if ns_vars == "NS":
            args = [[ns, blok_ns], parameters]
        else:
            args = []
            optional = False
            for var in ns_vars:
                popped = False
                if var is self.OPTIONAL:
                    optional = True
                    continue
                if var is self.FROM_PARAMETERS: 
                    try:
                        var = parameters.pop(0)
                        popped = True
                    except IndexError:
                        if not optional:
                            err = "{}: missing arguments".format(reader_)
                            raise BlokCodeError(err)
                        else:
                            optional = False
                            continue
                try:
                    if var.startswith("G:"): 
                        v = ns[var[2:]]
                    elif var in blok_ns: 
                        v = blok_ns[var]                    
                    elif var in ns:
                        v = ns[var]
                    else: raise IndexError()
                except IndexError:
                    if not optional:
                        err = "{}: unknown var".format(reader_)
                        raise BlokCodeError(err)
                    else:
                        if popped: parameters.insert(0, var)
                        optional = False
                        continue
                args.append(v)
                optional = False
            args +=  parameters
        print("      test: {}, with args: {}".format(test, str(args)))
        return test(self,*args)
    
    def st_not(self, nss, test):
        return not self.test_result(test, nss[0], nss[1])
    
    def st_bool(self, boolean, *parameters):
        return bool(boolean)
    
    def st_collection_size(self, list, *parameters):
        test = parameters[0]
        if test in {"empty", "even", "odd"}:
            if not len(parameters) == 1:
                err = "list test {}: no parameters allowed".format(test)
                raise BlokCodeError(err)
        elif test in {"==", ">", "<"}:
            if not len(parameters) == 2:
                err = "list test use: list {} number".format(test)
                raise BlokCodeError(err)
        print("len test list: {}".format(len(list)))
        if test == "empty": return len(list) == 0
        if test == "even": return len(list) % 2 == 0
        if test == "odd": return len(list) % 2 == 1
        if test == "==": return len(list) == int(parameters[1])
        if test == '>': return len(list) > int(parameters[1])
        if test == '<': return len(list) < int(parameters[1])
        raise BlokCodeError("list test: unknown args")
    
    def st_compare_result(self, result, *parameters):
        test_val = {"==": 0, ">":1, "<": 2,
                    "equal": 0,}
        if result == "is":
            raise BlokCodeError(
                "compare_results: no compare data, run compare first!")
        compare_value = test_val[parameters[-1]]
        return result == compare_value
    
    def st_variable_exists(self, *parameters):
        nr_of_parameters = len(parameters)
        if nr_of_parameters > 1:
            raise BlokCodeError("wrong use of st_variable_exists, max 1 var to test")
        elif nr_of_parameters == 1:
            return True
        else:
            return False
    
    def t_in_trade(self, positions, *parameters):
        return positions.in_trade()
    
    def t_new_direction(self, perm_line, *parameters):
        return perm_line[1] == 0
    
    def t_stoploss_triggered(self, perm_line, position, 
                             long_stop, short_stop, *parameters):
        top = perm_line[3]
        trade_direction = position.direction()
        stop = long_stop if trade_direction == 'long' else short_stop
        if trade_direction == 'long':
            return top < stop
        else:
            return top > stop
    
    tests = {"not": (st_not, "NS"),
            "compare_result": (st_compare_result, 
                               [OPTIONAL, FROM_PARAMETERS,
                                OPTIONAL, "__LAST_COMPARE__"]),
            "in_trade": (t_in_trade, ["__POSITIONS__"]),
            "new_direction": (t_new_direction, ["__PERM_LINE__"]),
            "stoploss_triggered": (t_stoploss_triggered, 
                                   ["__PERM_LINE__", "__POSITIONS__",
                                    "__LONG_STOP__", "__SHORT_STOP__"]),
            "handle_stoploss_mode": (st_variable_exists,
                                     [OPTIONAL, "__POSITION_WITH_TRIGGERED_STOP__"]),
            "handle_profittaker_mode": (st_variable_exists,
                                     [OPTIONAL, "__POSITION_WITH_TRIGGERED_PROFIT__"]),
            "perm_line_mode": (st_variable_exists,
                               [OPTIONAL, "__PERM_LINE__"])
            }    
    
    ########
    # INFO
    ########    

    
    def get_info(self, reader_chunk, ns, blok_ns):
        reader_, *parameters = reader_chunk
        if not reader_ in ns["__INFO__"]:
            parameters.insert(0, reader_)
            reader_ = "var"
        reader, ns_vars = ns["__INFO__"][reader_]
        print("*i*",reader, ": ", parameters)
        args = []
        for var in ns_vars:
            if var is self.FROM_PARAMETERS:
                try:
                    var = parameters.pop(0)
                except IndexError:
                    err = "{}: missing arguments".format(reader_)
                    raise BlokCodeError(err)
            try:
                if var.startswith("G:"): v = ns[var[2:]]
                elif var in blok_ns: v = blok_ns[var]
                elif var in ns: v = ns[var]
                else: raise IndexError()
            except IndexError:
                err = "{}: unknown var".format(reader_)
                raise BlokCodeError(err)
            args.append(v)
        args += parameters
        val = reader(self, *args)
        print("*i*result: ", val)
        return val;
    
    def si_read(self, value, *parameters):
        return value
    
    def si_int(self, value, *parameters):
        return int(value)
    
    def si_float(self, value, *parameters):
        return float(value)
    
    def si_collection_info(self, collection, *parameters):
        test, *parameters = parameters
        try:
            if test == "size": return len(collection)
            if test == "max": return max(collection)
            if test == "min": return min(collection)
            if test == "index":
                #i = self.get_info(reader_chunk, ns, blok_ns)
                i = parameters[0]
                return collection[i]
        except TypeError:
            raise BlokCodeError("collection info: unorderable collection")
        raise BlokCodeError("collection info: unknown request")
    
    def i_wavecount(self, perm_line, *parameters):
        return perm_line[1]
    
    def i_reverse_trade_wavecount(self, position, up_count, down_count, *parameters):
        c = {"long": down_count, "short": up_count}
        direction = position.direction()
        return c[direction]
    
    def i_trend_trade_wavecount(self, position, up_count, down_count, *parameters):
        c = {"long": long_count, "short": short_count}
        direction = position.direction()
        return c[direction]
    
    def i_stoploss(self, position, long_stop, short_stop, *parameters):
        c = {"long": long_stop, "short": short_stop}        
        direction = position.direction()
        return c[direction]
    
    def i_gap_current_to_stop(self, perm_line, long_stop, short_stop, *parameters):        
        c = {"up": long_stop, "down": short_stop}
        return abs(perm_line[5] - c[perm_line[0]])
    
    def i_gap_current_to_stop_perc(self, perm_line, long_stop, short_stop, *parameters):        
        c = {"up": long_stop, "down": short_stop}
        return (abs(perm_line[5] - c[perm_line[0]])) * 100 / perm_line[5]
    
    def i_triggered_stop(self, position, *parameters):
        return position.stop
    
    def i_profit(self, position, *parameters):
        return position.profit
    
    def i_trade_direction(self, position, *parameters):
        c = {"long": "up", "short": "down"}             
        direction = position.direction()
        return c[direction]
    
    def i_perm_line_direction(self, perm_line, *parameters):
        return perm_line[0]
    
    info = {"var": (si_read, [FROM_PARAMETERS]),
            "string": (si_read, []),
            "int": (si_int, []),
            "float": (si_float, []),
            "wavecount": (i_wavecount, ["__PERM_LINE__"]),
            "reverse_trade_wavecount": (i_reverse_trade_wavecount,
                                        ["__POSITIONS__",
                                         "__UP_COUNT__", "__DOWN_COUNT__"]),
            "trend_trade_wavecount": (i_trend_trade_wavecount,
                                        ["__POSITIONS__",
                                         "__UP_COUNT__", "__DOWN_COUNT__"]),
            "stoploss": (i_stoploss, ["__POSITIONS__",
                                      "__LONG_STOP__", "__SHORT_STOP__"]),
            "triggered_stop": (i_triggered_stop, 
                                     ["__POSITION_WITH_TRIGGERED_STOP__"]),
            "profit": (i_profit, ["__POSITION_WITH_TRIGGERED_PROFIT__"]),
            "gap_current_to_stop": (i_gap_current_to_stop, ["__PERM_LINE__",
                                      "__LONG_STOP__", "__SHORT_STOP__"]),
            "gap_current_to_stop%": (i_gap_current_to_stop_perc, ["__PERM_LINE__",
                                      "__LONG_STOP__", "__SHORT_STOP__"]),
            "trade_direction": (i_trade_direction, ["__POSITIONS__"]),
            "perm_line_direction": (i_perm_line_direction, ["__PERM_LINE__"]),
            }
    
#class TradeSimulationByRulesEM(TradeSimulationByRules):    
class TradeSimulationByRulesEM(TradeSimulationByArgs):
    
    def __init__(self, *parameters):
        super().__init__(*parameters)
        self.positions = position_manager.VirtualSinglePositionsEM()
    
    def register(self, *parameters, finished=True):
        self.positions.reset_unfinished_mode_output_file()
        if not finished:
            self.positions.finished_mode = False
            orig_long_stop = self.long_stop
            orig_short_stop = self.short_stop
            orig_up_count = self.up_count
            orig_down_count = self.down_count
        action = super().register(*parameters)
        if not finished:
            self.long_stop = orig_long_stop
            self.short_stop = orig_short_stop
            self.up_count = orig_up_count
            self.down_count = orig_down_count
            self.positions.finished_mode = True
        return action
    
    def no_unfinished_perms(self):
        self.positions.reset_unfinished_mode_output_file()
    
    def hot_start(self, minimal_restart_info, mri_location=mypy.TMP_LOCATION,
                  full_action_log=None, fal_location=mypy.TMP_LOCATION):
        self._mri = minimal_restart_info
        self._mri_location = mri_location
        self.load_minimal_restart_info(minimal_restart_info, mri_location)
        if full_action_log:
            self.full_action_log_filename = full_action_log
            self.full_action_log_location = fal_location
            self.load_action_log(full_action_log, fal_location)
        self.positions.hot_start()
        self._hot_start = True
        
    def clean_exit(self):
        if hasattr(self, "_ufb_file"):
            self._ufb_file.close()
            print("unfinished bar report file closed")
        #if (hasattr(self, "_hot_start") and 
        print("bar_extra_modes clean exit")
    
    def text_output(self, *parali, **paradi):
        self.positions.text_output(*parali, **paradi)
            
    def safe_restart_mode(self, easy_restart_file=None, 
                          er_location=mypy.TMP_LOCATION):
        if easy_restart_file == None:
            if hasatrr(self, "_mri"):
                self.easy_restart_filename = self._mri,
                self.easy_restart_location = self._mri_location
                self.positions.safe_restart_mode(easy_restart_file, er_location)
                return
            else:
                raise("bardata, no easy restart filename known")
        else:
            self.easy_restart_filename = easy_restart_file
            self.easy_restart_location = er_location
            self.positions.safe_restart_mode('.'.join([easy_restart_file, "position"]),
                                             er_location)
            
class DaytradeMode():
    
    CLOSE_ALL_POS_NOW = 1
    START_MANAGED_EXIT = 2
    NO_NEW_TRADES = 3
    RESET = 4
    OUT_OF_DAY_BAR = 5
    
    def __init__(self, std_end_time, last_in=None,
                 managed_out=None, last_out=None):
        self.std_end_time = std_end_time 
        self.last_in = last_in if last_in else -1
        self.managed_out = managed_out if managed_out else -1
        self.last_out = last_out if last_out else -1
        if (not((self.last_in > self.managed_out > self.last_out)
                or
                (self.last_in == -1 and
                 self.managed_out > self.last_out)
                or
                (self.last_in == -1 and self.managed_out == -1 and
                 self.last_out > 0)
                or
                (self.managed_out == -1 and
                 self.last_in > self.last_out))):
            raise Exception("init problem daytrademode, wrong parameters")
        else:
            self.reset_gap = max(
                          [self.last_in, self.last_out, self.managed_out])
            if self.last_in == -1:
                self.last_in = self.reset_gap + 1
                self.reset_gap = self.last_in
        self.reset_sended_actions()
        
    def reset_sended_actions(self):
        self.close_all_pos_sended = False
        self.start_managed_exit_sended = False
        self.no_new_trades_sended = False
        self.actions_sended = False
                
    def actions_to_take(self, time_):
        actions = []
        gap = mypy.time_diff(self.std_end_time, time_)
        if time_ > self.std_end_time:
            actions.append(self.OUT_OF_DAY_BAR)
        elif gap > self.reset_gap:
            if self.actions_sended:
                self.reset_sended_actions()
                actions.append(self.RESET)
        elif gap > self.managed_out > 0:
            if not self.no_new_trades_sended:
                actions.append(self.NO_NEW_TRADES)
                self.no_new_trades_sended = True
                self.actions_sended = True
        elif gap > self.last_out:            
            if not self.no_new_trades_sended:
                actions.append(self.NO_NEW_TRADES)
                self.no_new_trades_sended = True
                self.actions_sended = True
            elif (self.managed_out > 0 and
                  not self.start_managed_exit_sended):
                actions.append(self.START_MANAGED_EXIT)
                self.start_managed_exit_sended = True
                self.actions_sended = True
        else:  
            actions.append(self.CLOSE_ALL_POS_NOW)
            self.close_all_pos_sended = True
            self.actions_sended = True
        return actions
            
    
if __name__ == '__main__':
    main()