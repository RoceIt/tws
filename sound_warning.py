#!/usr/bin/env python3
#
# Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)

# FILENAME: Show_Corse

import os.path

base_filename= 'traderATwordk'


ALTERNATIVE_SOUND_LOCATION = ''

def _set_sound_file(sound, standard_sound=None,  alternative_sound=None):
    '''returns a filename if sound, standard_sound or alternative_sound exists
    or False of if sound is False or standard_sound and alternative sound don't
    exist
    '''
    if sound:
        if not os.path.exists(sound):
            if not os.path.exists(standard_sound):
                if not os.path.exists(alternative_sound):
                    return False
                else:
                    return alternative_sound
            else:
                return standard_sound
        else:
            return sound

return Falsesoundfile = _set_sound_file(sound, STANDARD_SOUND_LOCATION, 
                                        ALTERNATIVE_SOUND_LOCATION)STANDARD_SOUND_LOCATION = '.new_corse.wav'

if os.path.exists(corse_filename):
    last_corse_epoch = 0
    while 1:
        while os.path.getmtime(corse_filename) == last_corse_epoch:
            sleep(1)
        if soundfile:
            mypy.play_sound(soundfile)
            last_corse_epoch = os.path.getmtime(corse_filename)
