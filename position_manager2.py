#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import os.path
import csv
from collections import namedtuple

import mypy
import roc_output as r_output
    
#_action = namedtuple("Action", "id name direction size time price reason")
#class Action(_action):
class Action():
    
    def __init__(self, id_, name, direction, size, time_, price, reason):
        self.id = id_
        self.name = name
        self.direction = direction
        self.size = size
        self.time = time_
        self.price = price
        self.reason = reason
        
    def __iter__(self):
        return iter((self.id, self.name, self.direction, self.size,
                     self.time, self.price, self.reason))
    
    def to_csv(self, csv_writer):
        csv_writer.writerow((self.id, self.name, self.direction, self.size,
                             self.time, self.price, self.reason))
        
#_position = namedtuple("Position", "id name direction size time "
                                   #"price reason stop profit "
                                   #"in_type out_type")
#class Position(_position):
class Position():
    
    def __init__(self, id_, name, direction, size, time_, price,
                 reason, stop, profit, in_type, out_type):
        self.id = id_
        self.name = name
        self.direction = direction
        self.size = size
        self.time = time_
        self.price = price
        self.reason = reason
        self.stop = stop
        self.profit = profit
        self.in_type = in_type
        self.out_type = out_type
        
    def __str__(self):
        t = mypy.SerialTextCreator()
        if self.id:
            t.add_chunk('trade id: ')
            t.add_chunk(str(self.id))
        t.next_line()
        t.add_chunk(self.direction.upper())
        t.add_chunk('opened @')
        t.add_chunk(str(self.time))
        t.next_line()
        if self.direction == 'short':
            t.add_chunk('(')
        t.add_chunk(str(self.size))
        if self.direction == 'short':
            t.add_chunk(')')
        if self.size > 1:
            t.add_chunk('contracts')
        else:
            t.add_chunk('contract')
        t.add_chunk(self.name)
        t.add_chunk('price:')
        t.add_chunk(str(self.price))
        t.next_line()
        t.add_chunk("reason:")
        t.add_chunk(self.reason)
        t.next_line()
        t.next_line()
        t.add_chunk("stop:")
        if self.stop:
            t.add_chunk('{:8.2f}'.format(self.stop))
        if self.profit:
            t.add_chunk("          profit:")
            t.add_chunk('{:8.2f}'.format(self.profit))
        t.next_line()
        t.add_chunk("in type:")
        t.add_chunk(str(self.in_type))
        t.add_chunk("          out type:")
        t.add_chunk(str(self.out_type))
        return t.text
        
        
        
    def __iter__(self):
        return iter((self.id, self.name, self.direction, self.size,
                     self.time, self.price, self.reason, self.stop,
                     self.profit, self.in_type, self.out_type))
    
    def to_csv_writer(self, writer):
        writer.writerow((self.id, self.name, self.direction, self.size,
                        self.time, self.price, self.reason, self.stop,
                        self.profit, self.in_type, self.out_type))
        
SERVER = "$SERVER"
REPORTERS = {SERVER,}

class VirtualSinglePositions(r_output.AddExportSystem):  
    
    def __init__(self, report=None, position=None):
        #report = "std_trade_report" if not report else report
        #if report in REPORTERS:
            #raise NotImplementedError("special reporters not yet included")
        #else:
            #self.reporter = FileReporter(report)
        self.position = position if position else None
        self.action_log = []
        self.original = None
        super().__init__()
        
    def __str__(self):
        print("VirtualSinglePosition")
        print("  ", self.position)
        print("  # actions: ", len(self.action_log))
        print("  mode: ", "real" if not self.original else "strange")
        #return ""
        
    def work_with_copy(self):
        if self.original:
            raise Exception("virualsinglepos: selfcopy actif")
        self.original = (self.position, len(self.action_log))
        
    def work_with_original(self):
        if not self.original:
            raise Exception("virtualsinglepos: no selfcopy actif")
        self.position, old_len = self.original
        while len(self.action_log) > old_len:
            self.action_log.pop()  
        self.original = None
        
    def in_trade(self):
        return not self.position == None
    
    def direction(self):
        return self.position.direction
    
    def current_postitions(self):
        if self.position == None: return [] #None
        return [self.position]
    
    def enter(self, *action_, pending_enter=0.00):
        if not self.position == None:
            raise Exception("single position manager, already in trade")
        position = list(action_)
        self.pending_enter = pending_enter
        while len(position) < 11:
            position.append(None)
        action = action_[:7]
        check_action_parameters(*action)
        the_a = Action(*action)
        #print("position: ", self.position)
        #print("action: ", the_a)
        #check_action_parameters(*action)
        #self.position = the_a
        #self.reporter.report(*action)
        self.position = Position(*position)
        #self.action_log.append(the_a)
        if pending_enter == 0:
            self.action_log.append(action_)
        else:
            self.original_action = action_
        self.export_object(the_a)
        return the_a
    
    def check_pending_enter(self, ochl):
        #print(self.position)
        #print(ochl)
        #mypy.get_bool('ssf', default=True)
        if ((self.position.direction == 'long' and
             self.position.price - self.pending_enter > ochl.low)
            or
            (self.position.direction == 'short' and
             self.position.price + self.pending_enter < ochl.high)):
            self.pending_enter = 0
            self.action_log.append(self.original_action)
        
    def exit(self, *action):
        print('in exit')
        if self.position == None:
            raise Exception("single position manager, no trade to exit")
        the_a = Action(*action)
        #print("position: ", self.position)
        #print("action: ", the_a)
        exit_para = the_a
        if (not self.position.name == exit_para.name or
            not self.position.size == exit_para.size or
            self.position.direction == exit_para.direction):
            raise Exception("wrong exit parameters")
        #self.reporter.report(*action)
        self.position = None
        #self.action_log.append(the_a)
        if self.pending_enter == 0:
            self.action_log.append(action)
        self.export_object(the_a)
        return the_a
    
    def exit_all_pos(self, time_, price, reason):
        if self.position == None:
            return False        
        print('in exit all positions')        
        name, direction, size = self.exit_parameters(0)
        action = self.exit(0, name, direction, size, time_, price, reason)
        print('exit_all_positions', [0, name, direction, size, time_, price, reason])
        return [[0, name, direction, size, time_, price, reason]]
        
    def reverse(self, *action_):
        if self.position == None:
            raise Exception("single position manager, no trade to reverse")
        position = list(action_)
        while len(position) < 11:
            position.append(None)
        position[3] //= 2
        action = action_[:7]
        the_a = Action(*action)
        #print("position: ", self.position)
        #print("action: ", the_a)
        reverse_para = the_a
        if not self.position.name == reverse_para.name:
            raise Exception("wrong reverse parameters: name")
        if not 2 * self.position.size == reverse_para.size:
            raise Exception("wrong reverse parameters: size")
        if self.position.direction == reverse_para.direction:
            raise Exception("wrong reverse parameters: direction")
        #self.reporter.report(*action)
        self.position = Position(*position)
        #self.action_log.append(the_a)
        self.action_log.append(action_)
        self.export_object(the_a)
        return the_a
    
    def set_profittaker(self, id_, type_, value):
        if type_ == "entry+":
            corr = 1 if self.position.direction == "long" else -1
            self.position.profit = self.position.price + corr * value
        elif type_ == "entry+%":
            corr = 1 if self.position.direction == "long" else -1
            self.position.profit = (
                self.position.price * (1 + corr * value / 100))
        else:
            raise Exception("Unknown profittaker type")
    
    def cap_stop(self, id_, type_, value):
        #print('in cap stop: ', id_, type_, value)
        #print('old stop: ', self.position.stop)
        if self.position.direction == "long":
            corr = -1
            pick_test = max
        else:
            corr = 1
            pick_test = min
        if type_ == "entry+":
            self.position.stop = pick_test(
                self.position.price + corr * value,
                self.position.stop)
        elif type_ == "entry+%":
            self.position.stop = pick_test(
                self.position.price * (1 + corr * value / 100),
                self.position.stop)
        else:
            raise Exception("Unknown profittaker type")
        #print('new stop: ', self.position.stop)
        #mypy.get_bool('hitit', default=True)
        
    def increase_stop(self, id_, type_, value):
        if self.position.direction == "long":
            corr = -1
            pick_test = min
        else:
            corr = 1
            pick_test = max
        if type_ == "entry+":
            self.position.stop = pick_test(
                self.position.price + corr * value,
                self.position.stop)
        elif type_ == "entry+%":
            self.position.stop = pick_test(
                self.position.price * (1 + corr * value / 100),
                self.postion.stop)
        else:
            raise Exception("Unknown profittaker type")        
        
    def set_out_type(self, id_, type_, value):
        self.position.out_type = (("trailing",type_), value)
                
    def exit_parameters(self, id_):
        return exit_position_parameters(*self.position)
    
    def reverse_parameters(self, id_):
        return reverse_position_parameters(*self.position)
    
#class FileReporter():
    
    #def __init__(self, filename, directory=mypy.TMP_LOCATION):
        #self.filename = os.path.join(mypy.TMP_LOCATION,
                                     #'.'.join([filename, 'trades']))        
        #open(self.filename, 'w').close()
        
    #def report(self, *position):
        #report = ','.join([str(x) for x in position])
        #with open(self.filename, 'a') as ofh:
            #ofh.write(report)
            #ofh.write('\n')
            
class VirtualSinglePositionsEM(VirtualSinglePositions):
    def __init__(self, *parameters):
        super().__init__(*parameters)
        self.pending_enter = 0
        self.finished_mode = True
        
    def em_action(self, action, *action_parameters):
        if not self.finished_mode:            
            orig_position = self.position
            log_len = len(self.action_log)
        if action == "enter":
            the_a = super().enter(*action_parameters)
        elif action == "exit":
            the_a = super().exit(*action_parameters)
        elif action == "reverse":
            the_a = super().reverse(*action_parameters)
        else:
            raise Exception("unknown em action")
        if self.original == None and the_a:
            if self.finished_mode and hasattr(self, "trade_filename"):
                with open(self.trade_filename, 'a', newline='') as ofh: 
                    writer = csv.writer(ofh)
                    the_a.to_csv_writer(writer)
            if self.finished_mode and hasattr(self, "position_filename"):
                self.export_positions(self.position_filename, '')
            if self.finished_mode and hasattr(self, "easy_restart_filename"):
                self.save_minimal_restart_info(self.easy_restart_filename)
            if not self.finished_mode:
                if hasattr(self, "advise_filename"):
                    with open(self.advise_filename, 'a', newline='') as ofh: 
                        writer = csv.writer(ofh)
                        the_a.to_csv_writer(writer)
                self.action_log.pop()
        if not self.finished_mode:
            self.position = orig_position
        return the_a
    
    def enter(self, *action):
        self.em_action("enter", *action)
        
    def exit(self, *action):
        self.em_action("exit", *action)
        
    def reverse(self, *action):
        self.em_action("reverse", *action)
            
    def set_profittaker(self, id_, type_, value):        
        if not self.finished_mode:
            return
        super().set_profittaker(id_, type_, value)
        
    
    def cap_stop(self, id_, type_, value):        
        if not self.finished_mode:
            return
        super().cap_stop(id_, type_, value) 
        
    def increase_stop(self, id_, type_, value):      
        if not self.finished_mode:
            return
        super().increase_stop(id_, type_, value)
        
    def set_out_type(self, id_, type_, value):     
        if not self.finished_mode:
            return
        super().set_out_type(id_, type_, value)
        
    #def clear_advice_file(self):
        #open(self.advise_filename, 'w').close()
        
    def hot_start(self):
        self._hot_start = True
        
    def clean_exit(self):
        if hasattr(self, "_ufb_file"):
            self._ufb_file.close()
            print("unfinished bar report file closed")
        #if (hasattr(self, "_hot_start") and 
        print("bar_extra_modes clean exit")
    
    def text_output(self, 
                    trades_file=None, tf_location=mypy.TMP_LOCATION,
                    position_file= None, pf_location=mypy.TMP_LOCATION,
                    advise_file=None, af_location=mypy.TMP_LOCATION):
        if trades_file == None and unfinished_bars_file == None:
            raise Exception("Live data mode started without files to export to")
        if trades_file:
            self.trade_filename = os.path.join(tf_location, 
                                                       trades_file)
            if not hasattr(self, "_hot_start"):
                open(self.trade_filename, 'w').close()
        if position_file == True:
            position_file = '.'.join([trades_file, "positions"])
            pf_location = tf_location
        if position_file:
            self.position_filename = os.path.join(pf_location,
                                                    position_file)
        if advise_file == True:
            advise_file = '.'.join([trades_file, "unfinished"])
            af_location = tf_location
        if advise_file:
            self.advise_filename = os.path.join(af_location,
                                                    advise_file)
            
    def reset_unfinished_mode_output_file(self):
        try:
            open(self.advise_filename, 'w').close()
        except AttributeError:
            pass
            
    def safe_restart_mode(self, easy_restart_file=None, 
                          er_location=mypy.TMP_LOCATION):
        if easy_restart_file == None:
            if hasatrr(self, "_mri"):
                self.easy_restart_filename = self._mri,
                self.easy_restart_location = self._mri_location
                return
            else:
                raise("bardata, no easy restart filename known")
        else:
            self.easy_restart_filename = easy_restart_file
            self.easy_restart_location = er_location
    
            
def check_action_parameters(*action):
    
    id_, name, direction, size, time, price, reason = action
    if not direction in {"long", "short"}:
        raise Exception("direction must be long or short")
        
def reverse_position_parameters(*position):
    (id_, name, direction, size, time, price, reason, 
                       stop, profit, in_type, out_type) = position
    id_ = time = price = reason = None
    direction = "long" if direction == "short" else "short"
    size *= 2
    return name, direction, size

def exit_position_parameters(*position):
    (id_, name, direction, size, time, price, reason, 
                       stop, profit, in_type, out_type) = position
    id_ = time = price = reason = None
    direction = "long" if direction == "short" else "short"    
    return name, direction, size

    
        
        