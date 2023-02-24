#!/usr/bin/env python3
#
#  Copyright (c) 2014, Rolf Camps (rolf.camps@scarlet.be)
from roc_settings import Error

VERSION = 0.1

class CommandLineInterface():
    """imitate a command line interface.
    
    settings:
      - 'prompt': standard promt to show
      
    commands:
      a dict with all the known commands, the keys are the commands,
      the values are tupples.
      value: ((alias1, alias2, ...), documentation string, (function1, function2, ...))
    """
    STOP = "Stop command line interface"
    
    def __init__(self, settings=dict(), commands=dict()):
        self.settings = settings
        self.commands = dict()
        for k, v in commands.items():
            try:
                if hasattr(v, 'def_t'):
                    v = v.def_t
                alias, doc, function_list = v
            except Exception:
                print("problem adding command < {} >".format(k))
                raise
            self.add_command(k, doc, function_list, alias)
            for a in alias:
                self.add_alias(a, k)       
    
    def add_command(self, name, doc, functions, alias):
        if name in self.commands:
            raise ValueError("command already defined: {}".format(name))
        self.commands[name] = (doc, functions, alias)
        
    def add_alias(self, alias, command):
        if alias in self.commands:
            raise ValueError("Alias already defined: {}".format(alias))
        command_settings = self.commands[command]
        self.add_command(alias, command_settings[0], command_settings[1], False)
            
    def start(self, line=None):
        self.set_settings()
        if self.start_mss:
            print("started roc_cli version: {}".format(VERSION))
        while 1:
            if line:
                try:
                    r = self.run_command(line)
                except NotImplementedError:
                    self.show_commands()
                    r = None
                if (isinstance(r, tuple)                          and 
                    r[0] == CommandLineInterface.STOP):
                    r = r[1]
                    break
                elif not r:
                    pass
                else:
                    print(r)
                line = ''
            while not line:
                try:
                    line = input(self.prompt)
                except KeyboardInterrupt:
                    print("\nWARNING: forced quit")
                    exit()
                if line:
                    break
                self.show_commands()
        return r
            
    def set_settings(self):
        self.prompt = self.settings.pop('prompt', '> ')
        self.start_mss = self.settings.pop('cli_start_mss', False)
        for k in self.settings:
            print("WARNING: unknown setting:", k)        
        
    
    def run_command(self, line):
        command, parameters = ('{} '.format(line)).split(' '.format(line), 1)
        parameters = parameters.rstrip()
        try:
            functions = self.commands[command][1]
        except KeyError:
            if command not in self.commands:
                print('ERROR: unknown command: ', command)
                raise NotImplementedError()
            else:
                raise
        for function in functions:
            r = function(parameters)
            parameters = r
        return r
        
    def show_commands(self):
        for k, v in self.commands.items():
            if v[2] is not False:
                print(k, end='')
                if v[2]:
                    print(" [ ", end='')
                    for a in v[2]:
                        print("{} ".format(a), end='')
                    print("]", end='')
                print("   ", v[0])
    
    @staticmethod
    def stop(arg_s):
        return CommandLineInterface.STOP, arg_s
            
        
def abort(parameters):
    return CommandLineInterface.STOP, "abort"
####
abort.def_t = (
    ("a",),
    "abort current action",
    (abort,),
)   

def up(parameters):
    return CommandLineInterface.STOP, ""
####
up.def_t = (
    ("..",),
    "go to previous cli menu",
    (up,),
)
