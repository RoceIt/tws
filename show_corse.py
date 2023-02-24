#!/usr/bin/env python3
#
# Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)

# FILENAME: Show_Corse

import os.path
import sys
import pickle
from optparse import OptionParser
from time import sleep

import mypy
import tws as Broker
import sql_IB_db
import corse

class ShowCorseError(Exception):pass
class WrongShowSelector(ShowCorseError):pass

PERIODS_FOR_OCHL = ['D','h','m','s']
STANDARD_SOUND_LOCATION = '.new_corse.wav'
ALTERNATIVE_SOUND_LOCATION = ''
DFLT_UNIT = 's'
DFLT_NUMBER = '5'
DFLT_TABLE = 'TRADES_5_secs'
DB_PATH = mypy.DB_LOCATION

def main():
    ARG_ERROR_MESSAGE = 'Wrong number of arguments, use {} --help for info'
    usage = 'Usage: %prog [options] IBcontractName'
    parser = OptionParser(usage=usage)
    parser.add_option('-S', '--show',
                      choices = ['bull', 'bear'],
                      dest='show', default='bull',
                      help='Write output to FILE', metavar='FILE')
    parser.add_option('-u', '--unit',
                      choices=PERIODS_FOR_OCHL,
                      dest='unit', default=DFLT_UNIT,
                      help='choose from D, h, m, s')
    parser.add_option('-n', '--number',
                      type='int',
                      dest='number', default=DFLT_NUMBER,
                      help='number of units for 1 period')
    parser.add_option('-t', '--table',
                      dest='table', default = DFLT_TABLE,
                      help='choose the db contracttable you\'ld like to use, TRADES_5_secs is default')
    parser.add_option('-s', '--sound',
                      dest='play_sound', action='store_true', default=False,
                      help='play a sound, if a file is specified')
    (opts, args) = parser.parse_args()
    if len(args) >1:
        print(ARG_ERROR_MESSAGE.format(sys.argv[0]))
        raise
    sound = STANDARD_SOUND_LOCATION if opts.play_sound else None
    contract_name = args[0] if len(args) == 1 else 'AEX-index'
    try:
        show_corse(contract_name, opts.show, opts.unit, opts.number,
                   opts.table, sound)
    except Broker.ContractNotInDB as err:
        print('contract {} not in db'.format(err))
    except KeyboardInterrupt:
        pass

def show_corse(contract_name, show, unit=DFLT_UNIT, number=DFLT_NUMBER,
               table=DFLT_TABLE, sound=STANDARD_SOUND_LOCATION):
    # Check if contract is in the Brokers db
    test_existence = Broker.contract_data(contract_name)
    # Create full filename
    IB_db_table = table
    base_filename = '_'.join([contract_name , IB_db_table, str(number) + str(unit)])
    if show == 'bear' or show =='bull':
        corse_filename = '.'.join([base_filename, show])
        printHeader = '{} CORSE'.format(show.upper())
    else:
        raise WrongShowSelector('select bull or bear')
    print ('Base file:', corse_filename)
        
    soundfile = _set_sound_file(sound, STANDARD_SOUND_LOCATION, 
                                ALTERNATIVE_SOUND_LOCATION)

    if os.path.exists(corse_filename):
        last_corse_epoch = 0
        while 1:
            while os.path.getmtime(corse_filename) == last_corse_epoch:
                sleep(5)
            if soundfile:
                mypy.play_sound(soundfile)
            curr_corse = mypy.import_pickle(corse_filename)
            last_corse_epoch = os.path.getmtime(corse_filename)
            print(printHeader,mypy.datetime2format(mypy.now(),
                                                   mypy.DATE_TIME_STR))
            print('-'*len(printHeader))
            if curr_corse:
                curr_corse.print_set(corse.ALL, 'ltTmMAaBbCcs')
            else:
                print('no corses available')
            sys.stdout.flush()
    else:
        print('Filename doesn\'t exist')    

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
    return False



if __name__ == '__main__':
    main()
