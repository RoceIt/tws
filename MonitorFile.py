#!/usr/bin/env python3
#
# Copyright (c) 2010,2011 Rolf Camps (rolf.camps@scarlet.be)

# FILENAME: MonitorFile

import os.path
from optparse import OptionParser
from time import sleep

import mypy

# ACTIONS is a dict, key is the name of the action and value
# the number of arguments that are required

class MonitorFileError(Exception):pass
class Alert(MonitorFileError):pass

STD_SOUND = os.path.join(mypy.SOUND_LIB, 'std_warning.wav')
DFLT_DELTA = 60
DFLT_ACTION = 'play_sound'
DFLT_MONITOR = ''


def main():
    usage = 'Usage: %prog [options] filename'
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--delta',
                      type='int',
                      dest='delta', default=DFLT_DELTA,
                      help='Interval to check file', metavar='seconds')
    parser.add_option('-a', '--action',
                      dest='action', default=DFLT_ACTION,
                      help='action when test is true (or false)', 
                      metavar='ACTION')
    parser.add_option('-n', '--not',
                      dest='not_', action='store_true', default=False,
                      help='reverse test')
    parser.add_option('-m', '--monitor',
                      dest='monitor', default=DFLT_MONITOR,
                      help='', metavar='')
    (opts, args) = parser.parse_args()
    if len(args) < 1 :
        print('Filename missing')
        return 'wrong number of arguments'
    filename = args[0]
    arguments = args[1:]
    monitor_file(filename, *arguments, interval=opts.delta, action=opts.action,
                 inverse=opts.not_, monitor=opts.monitor)


def monitor_file(filename, *arguments, interval=DFLT_DELTA, action=DFLT_ACTION,
                 inverse=False, monitor=DFLT_MONITOR ):
    run_monitor = dict(growing=_growing)
    raise_alert = dict(play_sound=_play_sound)

    try:
        run_monitor[monitor](filename, interval, inverse, *arguments)
    except Alert as alert:
        raise_alert[action](filename, interval, inverse, alert, *arguments)
        # print('MONITORFILE: {}'.format(alert)) learn to log!!


def _growing(filename, interval, inverse, *arguments):
    mess = '{} did not grow last {} seconds'
    inv_mess = '{} grew last {} seconds'
    message = inv_mess if inverse else mess
    filesize = os.path.getsize
    size = filesize(filename)
    while 1:
        sleep(interval)
        new_size = filesize(filename)
        result = new_size > size
        result = not result if inverse else result
        size = new_size
        if result == False:
            raise Alert(message.format(filename, interval))


def _play_sound(filename, interval, inverse, alert, *arguments):
    mypy.play_sound(arguments[-1])


if __name__ == '__main__':
    main()
