#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import validate
from roc_settings import Error

class SerialLineCreator(list):
    '''Make a line of text.
    
    With add_text, you add text to the current chunk of data.  With
    add_chunk you add a chunk of text to line, if there was text in
    the current chunk, it will be stored as a chunk of text first and
    the new chunk is added. The current chunk will be empty so using
    add_text will create a new chunk. Chunks are seperated by the
    separator defined, it defaults to a space so the default chunks
    actualy are words. 
    
    Use str(object) to get the text you created as a string. len is
    defined so you can use if object to test for empty creator.
    
    methods
      add_text -- add text in current chunk
      add_chunk -- add a chunk of text to the line
      next_chunk -- store the  current chunk and start a new one
      clear -- remove all text and chunks
      
    properties
      separator -- text(char) used between chunks.
      first -- choose or change the first char of the line.
      last -- choose or change the last line of the line.
      capitalise -- capitalise first character in the lin.
    '''
    
    def __init__(self, separator=' ', first='', last='', capitalise=False):
        '''Initialise SerialLineCreator.
        
        The separator is used to separate chunks. When first and/or
        last are True, the separator is added in the beginning and/or 
        the end of the line. If they contain strings, they will be
        inserted first or last. If capitalise is True, the first
        character will be capitalised        
        '''
        ###
        ###
        self.separator = separator
        self.first = separator if first is True else first
        self.last = separator if last is True else last
        self.capitalise = capitalise
        self._current_chunk = []
        self.post_proces = self.first or self.last or self.capitalise
        
    def add_text(self, string):
        '''Add string to current chunk.'''
        
        assert isinstance(string, str)
        ###
        ###
        self._current_chunk.append(string)
        
    def add_chunk(self, string):
        '''Add a chunk of text.
        
        When there's text in the current string it will first be saved
        as a chunkt, the new chunk is added and new text will be added
        to a new current chunk.
        '''
        
        assert isinstance(string, str)
        ###
        ###
        self.next_chunk()
        self.append(string)
        
    def next_chunk(self):
        '''Close current chunk and prepare for new text.'''
        ###
        chunk = ''.join(self._current_chunk)
        ###
        if chunk:
            self.append(chunk)
            self._current_chunk = []
            
    def __str__(self):
        '''Return the created line of text.'''
        ###
        if self._current_chunk:
            chunks = self + [''.join(self._current_chunk)]
        else:
            chunks = self
        line = self.separator.join(chunks)
        if self.post_proces:
            if self.capitalise:
                line.capitalize()
            line = ''.join([self.first, line, self.last])
        ###
        return line
    
    def __len__(self):
        '''Returns the total number of chars in the creator.'''
        ###
        ###
        return len(str(self))
    
    def clear(self):
        '''Clear creator.'''
        ###
        ###
        super().clear()
        self._current_chunk = []
        
class SerialTextCreator(list):
    '''Make a text.
    
    add_text and add_chunk add to the current line. next_line closes
    the current line and start a new one.  You can underline the 
    current line (or the previous of current is empty) with the
    undeline function.
    
    Use str(object) to get the text. len is defined.
    
    methods    
      add_text -- add text in current chunk
      add_chunk -- add a chunk of text to the line
      next_chunk -- store the  current chunk and start a new one
      clear -- remove all text and chunks
      
    properties
      eol -- the end of line character(s)
      eof -- if True file stops with an eol
      + SerialLineCreator properties
    '''
    
    def __init__(self, eol='\n', eof='', **seriallinecreator):
        '''Initialise SerialTextCreator.'''
        assert isinstance(eol, str)
        assert isinstance(eof, str)
        ###
        ###
        self._current_line = SerialLineCreator(**seriallinecreator)
        self.eol = eol
        self.eof = eol if eof is True else eof
        
    def add_text(self, string):
        '''serial line creator method'''
        ###
        ###
        self._current_line.add_text(string)
        
    def add_chunk(self, string):
        '''serial line creator method'''
        ###
        ###
        self._current_line.add_chunk(string)
        
    def next_chunk(self):
        '''serial line creator method'''
        ###
        ###
        self._current_line.next_chunk()
        
    def next_line(self):
        '''close current line and prepare for new line.'''
        ###
        ###
        self.append(str(self._current_line))
        self._current_line.clear()
        
    def add_line(self, string):
        '''add string as a line.'''
        assert isinstance(string, str)
        ###
        ###
        if self._current_line:
            self.next_line()
        self.append(string)
        
    def add_lines(self, string):
        '''add the string line after line'''
        for line in string.split('\n'):
            self.add_line(line)
            
    def add_box(self, string, symbol='*'):
        '''add string in a bos of symbols'''
        string = ''.join((symbol, ' ', string, ' ', symbol))
        top_bottum = symbol * len(string)
        self.add_line(top_bottum)
        self.add_line(string)
        self.add_line(top_bottum)       
        
    def __str__(self):
        '''Return the created text.'''
        ###
        if self._current_line:
            lines = self + [str(self._current_line)]
        else:
            lines = self
        text = self.eol.join(lines)
        if self.nr_of_lines() == 0 or not lines[-1] == self.eof:
            text = ''.join([text, self.eof])
        ###
        return text
    
    def nr_of_lines(self):
        '''Returns the number of lines.'''
        return super().__len__()
    
    def __len__(self):
        '''Returns the total number of chars in the creator.'''
        ###
        ###
        return len(str(self))
    
    def clear(self):
        '''Clear creator.'''
        ###
        ###
        super().clear()
        self._current_line.clear()
        
    def underline(self, symbol='-'):
        '''Underline current or previous line with symbols.
        
        Underlines previous line if current line is empty.
        '''
        assert isinstance(symbol, str)
        ###
        len_curr_line = len(self._current_line)
        if len_curr_line == 0 and self.nr_of_lines() > 0:
            len_prev_line = len(self[-1])
        else:
            len_prev_line = 0
        underline_line = max(len_curr_line, len_prev_line) * symbol
        ###
        if len_curr_line:
            self.next_line()
        if underline_line:
            self.add_line(underline_line)
            
def dict_as_funtion_argument_str(a_dict):
    t = SerialLineCreator(separator=', ')
    for k,v in a_dict.items():
        if not isinstance(k, str):
            raise Error('all keys must be strings')
        t.add_chunk("'{}'={}".format(k, repr(v)))
    return str(t)