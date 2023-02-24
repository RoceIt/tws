#!/usr/bin/env python3
#
#  Copyright (c) 2012, Rolf Camps (rolf.camps@scarlet.be)

import os.path
import pickle

import mypy
from my_collections import DictArray

PICKLE_LOCATION = mypy.TMP_LOCATION

def main():
    create_new_spa()
    
def create_new_spa():
    print('Swing Performance Array')
    print('=======================')
    load = mypy.get_string('load exising array (enter is no): ', empty=True)
    if load:
        spa = SwingPerformanceArray(load=load)
        spa.name = mypy.get_string('name ({}): '.format(spa.name), default=spa.name)
    else:
        name = mypy.get_string('name: ')
        type_ = mypy.get_from_list(SwingPerformanceArray.known_types, 
                                   mess='Select type')
        info = mypy.get_from_list(SwingPerformanceArray.known_info, 
                                  mess='Select info')
        spa = SwingPerformanceArray(name, type_, info)
    while True:
        data = mypy.get_string('data (move perc value): ', empty=True)
        if not data:
            break
        move, perc, value = data.split()
        perc = float(perc)
        value = float(value)
        spa[move][perc] = value
    print(spa)
    if mypy.get_bool('pickle spa (y/N): ', default=False):
        filename = os.path.join(PICKLE_LOCATION, '.'.join([spa.name, 'spa']))
        #mypy.export_pickle(spa, filename)
        ##with open(filename, 'wb') as pf:
            ##pickle.dump(spa, pf)
        spa.save()
class SwingPerformanceArray(DictArray):
    
    """Historical data of swings
    
    Stores historical information about swings in an array.  The
    columns are the number of moves in the swing and the row the
    row is the percentage of times the stored information was reached.
    
    properties:
    
    - name: name of the  array
    - type: type of the array
    - info: information stored
    
    """
    
    #types's
    STANDARD = 'std'
    known_types = {STANDARD}
    
    #info's
    SIZE = 'size'
    known_info = {SIZE}
    
    def __init__(self, name=None, type_=None, info=None, load=None):
        assert not (name and load), 'Learn to choose, you can not have both'
        super().__init__()
        if load:
            self.load(load)
            return
        assert type_ in self.known_types, 'Unknown type for SwingPerformanceArray'
        assert info in self.known_info, 'Unknown info setting for SwingPerformanceArray'
        #super().__init__()
        self.name = name
        self.type = type_
        self.info = info
        
    def __str__(self):
        output = mypy.SerialTextCreator(separator='|')
        perc_width = 3
        data_width = 6
        total_width = 5 + perc_width + data_width
        for move in self.moves:
            output.add_chunk('{:^{width}}'.format(move, width=total_width))
        output.underline()
        sorted_array = DictArray()
        biggest_data_label_set = 0
        for i, move in enumerate(self.moves):
            for j, perc in enumerate(self.data_labels(move)):
                sorted_array[i][j] = (perc, self[move][perc])
            if j > biggest_data_label_set:
                biggest_data_label_set = j
        print(sorted_array)
        for j in range(biggest_data_label_set + 1):
            for i in range(len(self.moves)):
                try:
                    curr_data = sorted_array[i][j]
                    output.add_chunk('{:4.0%} '.format(curr_data[0]))
                    output.add_chunk('{:7.2f} '.format(curr_data[1]))
                except KeyError:
                    output.add_chunk(13*' ')
            output.next_line()
        return output.text
        
    def data_for_percentage_at_level(self, move, percentage):
        move = str(move)
        keys = self.data_labels(move) #sorted([x for x in self[move].keys()])
        for i, key in enumerate(keys):
            if not key < percentage:
                break
        if i == 0:
            return keys[0], self[move][keys[i]]
        low = keys[i-1]
        high = keys[i]
        if percentage - low < high - percentage:
            return keys[i-1], self[move][keys[i-1]]
        else:
            return keys[i], self[move][keys[i]]
        
    @property
    def filename(self):
        name = '_'.join([self.name, self.type, self.info])
        name = '.'.join([name, 'spa'])
        return name
    
    @property
    def moves(self):
        return sorted([x for x in self.keys()])
    
    def data_labels(self, move):
        return sorted([x for x in self[move].keys()])
    
    def save(self):
        filename = os.path.join(PICKLE_LOCATION, '.'.join([self.name, 'spa']))
        mypy.export_pickle((self.raw_data, self.name, self.type, self.info), filename)
        
    def load(self, filename):
        with open(filename, 'rb') as pf:
            data, name, type_, info = pickle.load(pf)
        print(data)
        print(name)
        print(type_)
        print(info)
        self.raw_data = data
        self.name = name
        self.type = type_
        self.info = info
        
    @property    
    def raw_data(self):
        d = {}
        for key in self.keys():
            d[key] = self[key].copy()
        return d
    
    @raw_data.setter
    def raw_data(self, d):
        for key in d.keys():
            self[key] = d[key]
        
if __name__ == '__main__':
    main()