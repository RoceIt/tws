#!/usr/bin/python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import os.path

import mypy

class LoadSaveDefault(dict):
    
    def __init__(self, filename, lOcAtIoN=mypy.VAR_LOCATION, **keys_defaults):
        super().__init__()
        self.default_file = os.path.join(lOcAtIoN, filename)
        if os.path.exists(self.default_file):
            saved_data = mypy.import_pickle(self.default_file)
            self.set_saved_data(saved_data, keys_defaults)
        else:
            self.set_defaults(keys_defaults)
            
            
    def set_saved_data(self, saved_data, keys_defaults):
        
        if saved_data.keys() == keys_defaults.keys():
            self.set_defaults(saved_data)
        else:
            self.set_defaults(keys_defaults)
        
            
    def set_defaults(self, keys_defaults):
        
        assert isinstance(keys_defaults, dict)
        for k, v in keys_defaults.items():
            self[k] = v
            
    def save(self):
        
        mypy.export_pickle(self, self.default_file)
        
            