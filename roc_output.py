#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import sys
import csv
from time import sleep

from roc_settings import Error

def print_list(list_, title=None, format_=None, underline=False, 
               as_line=False, list_sep=' | ', file_=None):
    '''Prints a list in a nicer format.
    
    If file is None it prints to standard output.  
    
    You can choose a title for the list and set underline to ...
    
    You can use a format string to further addapt the output.
    
    You may set the file arg like in the print statement to choose an
    other place then standard out to print to.
    
    Parameter:
      list -- a list
      title -- title to print
      format -- format of the lines
      underline -- bool, underline title y/n
      file -- like in the print statement
    '''
    ###
    file_ is sys.stdout if not file_ else file_
    if as_line and not title.endswith(':'):
        title = ''.join([title.rstrip(':'), ': '])
    ###
    if title:
        print(title, end='', file=file_)
        if not as_line:
            print(file=file_)
            if underline: print('-'*len(title), file=file_)
            print(file=file_)
    if as_line:
        if_defined_print(*list_, sep=list_sep, file=file_)
    else:
        for item in list_:
            line = format_.format(*item) if format_ else item
            print(line, file=file_)
    print(file=file_)
    
def if_defined_print(*objects, sep=' ', end='\n', file=sys.stdout):
    '''Print the string if it's lenth is not 0.
    
    string must be a string or an Error is raised
    '''

    ###
    valid_objects = []
    for o in objects:
        if (o is not None and
            not o ==[] and
            not o == tuple() and
            not o == dict() and
            not 0 == ''):
            valid_objects.append(o)
    defined = bool(len(valid_objects))
    ###
    if defined:
        print(*valid_objects, sep=sep, end=end, file=file)
    
class AddExportSystem():
    '''Set an use an easy system to export info.
    
    You can choose to not use it by setting destination to False, or 
    export the object to the teriminal when it has a __str__ method or
    to a csv file when it has a to_csv_writer method.
    
    Attributes:
      aes_store_objects -- the number of objects to store, int or False
      aes_export_objects -- export system is active, bool
      aes_export_to -- 'csv' or 'terminal'
      aes_filename -- filename for csv mode
      aes_memory_list -- list with not exported objects
      aes_action_linked_export_systems -- linked export systems
      
      
    Methods:
      export_settings -- set export settings
      export_object -- insert object in exort system
      export_flush -- export all data in memory list, if active
      export_live_mode -- export every object when inserted, if active
      export_add_action_linked_export_system -- add export system to list
    '''    
    
    AES_CSV = 'csv'
    AES_TERMINAL = 'terminal'  
    #AES_EXPORTERS defined at the end of the class
    def __init__(self):
        self.aes_store_objects = self.aes_export_objects = False
        self.aes_export_to = None
        self.aes_memory_list = []
        self.aes_action_linked_export_systems = []
        
    def export_settings(self, 
                        destination='csv', 
                        filename='/tmp/export.tt', append=False,
                        live=False, on_request=True, max_objects=1000):
        '''Set export settings.
        
        íf destination is None, nothing will be exported, or saved in 
        memory. Every inserted object is added to the aes_memory_list
        and removed after exporting.
        You can choose the destination file with filename.  You can
        set append to True to continue writing to an existing file. 
        
        Arguments
          destination -- 'csv' or 'terminal'
          filename -- file to export to
          append -- append to existing file, bool
          live -- use live reporting, bool
          on_request -- only export on request, bool
          max_objects -- export when memory list reaches max objects
                    
        '''
        
        if not destination:
            self.aes_export_objects = self.aes_export_objects = False
        else:
            if destination == 'csv':
                self.aes_export_to = self.AES_CSV
                self.aes_filename=filename
                if not append:
                    open(self.aes_filename, 'w').close()
            elif destination == 'terminal':
                self.aes_export_to = self.AES_TERMINAL
            else:
                raise Error('Unknown destination: {}'.format(destination))
            if live: #export objecs when known
                self.aes_export_objects = True
                self.aes_store_objects = 1
            elif max_objects > 0: #export objects on request or every max_objects
                self.aes_export_objects = True
                self.aes_store_objects = max_objects
            elif request: #export bars on request
                self.aes_export_objects = False
                self.aes_store_objects = True
            else:
                raise Error('Unknown export settings')
            
    def export_add_action_linked_export_system(self, export_system):
        '''Run some actions on systems in this list to.
        
        If this export system gets flushed or is set to live mode,
        the export systems in this list get the same method call.
        '''
        ###
        ###
        self.aes_action_linked_export_systems.append(export_system)
        
    def export_object(self, obj):
        ###
        flush_mode = hasattr(self, 'AES_FLUSH')
        ###
        if self.aes_store_objects and not flush_mode:
            self.aes_memory_list.append(obj)            
        if (not self.aes_export_to
            or
            (not flush_mode and
             len(self.aes_memory_list) < self.aes_store_objects)):
            return
        try:
            self.AES_EXPORTERS[self.aes_export_to](self)
        except KeyError as err:
            raise Error('Unknown export protocol!')
        
    def export_objects_to_csv(self):
        ###
        with open(self.aes_filename, 'a') as export_file:
            csv_out = csv.writer(export_file)
            while self.aes_memory_list:
                self.aes_memory_list.pop(0).to_csv(csv_out)
    
    def export_objects_to_terminal(self):
        ###
        while self.aes_memory_list:
            print(self.aes_memory_list.pop(0))
            
    def export_flush(self):
        ###
        ###
        self.AES_FLUSH = True
        self.export_object(None)
        delattr(self, 'AES_FLUSH')
        for export_system in self.aes_action_linked_export_systems:
            export_system.export_flush()
        
    def export_switch_to_live_mode(self):
        ###
        ###
        self.aes_store_objects = 1   
        for export_system in self.aes_action_linked_export_systems:
            export_system.export_switch_to_live_mode()
          
    AES_EXPORTERS = {
        AES_CSV: export_objects_to_csv,
        AES_TERMINAL: export_objects_to_terminal,
    }    
                
def enerve(level):
    for i in range(level):
        print('\a', end='')
        sys.stdout.flush()
        sleep(0.15)
        
        
        
      
    
    