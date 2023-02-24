#!/usr/bin/python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)

# corse, correction search engine
# bepaald aan de hand van reducerdata of de grafiek in een correctie zit
# probeert abc correcties te herkennen

import pickle
import logging

from collections import namedtuple

import mypy
import barData


#######################################################################
# helper om te debuggen,
# daar heeft python3 zeker en vast een betere oplossing voor ;)
verbose = True
def vprint(message):
    if verbose:
        print(message)
#######################################################################

###
# Mogelijke toestanden van de corse_engines
INITIALISING  = 'initialising'
WAITING_FOR_A = 'to_a'
WAITING_FOR_B = 'to_b'
WAITING_FOR_C = 'to_c'
VALIDATE_C    = 'wait_for_overlap'
IN_DOUBT      = 'new_top_or_to_c?'
OVERLAP_HIGH  = 'max_signal_in_overlap'
OVERLAP_MIN   = 'min_signal_in_overlap'
C_AT_RISC     = 'no_overlap_c_at_risc'
ERROR         = 'error'
STOPPED       = 'stopped'

ALL = {INITIALISING, WAITING_FOR_A, WAITING_FOR_B, WAITING_FOR_C,
       VALIDATE_C, IN_DOUBT, OVERLAP_HIGH, OVERLAP_MIN,
       C_AT_RISC, ERROR, STOPPED}
CORRECTION_CANDIDATES = {WAITING_FOR_C, VALIDATE_C, IN_DOUBT,C_AT_RISC }
RUNNING_CORRECTIONS = {OVERLAP_HIGH, OVERLAP_MIN}
HOTLIST = CORRECTION_CANDIDATES.union(RUNNING_CORRECTIONS)


###
# Some global definitions
ABCCorrection = namedtuple('ABCCorrection',
                           'id a a_time b b_time c c_time '
                           'max max_time min min_time')


FIELDS = [['l', 'Level', 6, 'd'],
          ['t', '  First time', 20, 's'],
          ['T', ' extreme time', 20, 's'],
          ['m', 'Minimum', 8, 'f'],
          ['M', 'Maximum', 8, 'f'],
          ['A', '   A Time', 20, 's'],
          ['a', '    A', 8, 'f'],
          ['B', '   B Time', 20, 's'],
          ['b', '    B', 8, 'f'],
          ['C', '   C Time', 20, 's'],
          ['c', '    C', 8, 'f'],
          ['s', 'Status', 25, 's']]

class corse():
    ##########
    # class om abc correcties te zoeken aan de hand van data uit de reducer
    ##########
    def __init__(self):
        self.bull_engine          = None             # * engine voor bull markt
        self.bear_engine          = None             # * engine voor bear markt
        self.time_of_last_signals = []               # * houd tijd van de signalen bij
                                                     #   helper voor controle op
                                                     #   oudere signalen
        self.type_of_last_signal  = False            # * wordt gebruikt om de signalen
                                                     #   controleren. piek -> dal -> piek ...
        self.corse_reversed       = False            # * staat op False in nieuw signaal
                                                     #   cronologisch juist is, anders
                                                     #   geeft hij het aantal verwijderde
                                                     #   signalen aan
        
    def insert(self, red_data):
        ###
        # specifieke functies voor corse.insert
        def _manage_stopped_engines(initialise=False):
            # initialise is een hack om op het einde van de insert, getopte
            # corses terug op te starten en onmiddelijk te initialiseren
            # de corse die vroeger gestopt worden worden geinitialiseerd tijden
            # de normale loop van het programma
            if self.bull_engine and self.bull_engine.stopped:
                #vprint('toplevel bull engine stopped')
                if red_data.type == barData.BOTTOM:
                    self.bull_engine = bull_corse()
                    if initialise:
                        self.bull_engine.insert(red_data)
                else:
                    self.bear_engine = None
            if self.bear_engine and self.bear_engine.stopped:
                #vprint('toplevel bear engine stopped')
                if red_data.type == barData.TOP:
                    self.bear_engine = bear_corse()
                    if initialise:
                        self.bear_engine.insert(red_data)
                else:
                    self.bear_engine = None

        def _reverse_engines(number_of_signals):
            if self.bull_engine:
                self.bull_engine.reverse(number_of_signals)
            if self.bear_engine:
                self.bear_engine.reverse(number_of_signals)
            _manage_stopped_engines()
            #vprint('{} signa(a)l(en) verwijdert'.format(number_of_signals))

 

        ###
        # START insert
        ###
        #vprint('\n' + str(red_data))

        ###
        # controleer of nieuw signaal een tegengestelde piek is van het vorige signaal
        # zo niet, verwijder vorig signaal
        max_extended = False          # variabele wordt gebruikt om in de volgende stap
                                      # de variabele corse_reversed juist in te kunnen
                                      # stellen
        if red_data.type == barData.BOTTOM or red_data.type == barData.TOP:
            if red_data.type != self.type_of_last_signal:
                self.type_of_last_signal = red_data.type
            else:
                #vprint('laatste signaal hernemen, piek blijkt nog groter')
                max_extended = True
                self.time_of_last_signals.pop()
                _reverse_engines(1)
                _manage_stopped_engines()
        ###
        # controleer of nieuw signaal 1 of meerdere oudere signalen voorafgaat
        # verwijder de nodige signalen
        self.time_of_last_signals.append(red_data.time)
        removed_signals = 0
        while len(self.time_of_last_signals) >= 2:
            if self.time_of_last_signals[-1] <= self.time_of_last_signals[-2]:
                self.time_of_last_signals.pop(-2)
                removed_signals +=1
            else:
                break
            if removed_signals:
                _reverse_engines(removed_signals)
        ###
        # Stel corse_reversed in zodat clients weten hoeveel signalen verwijderd zijn
        removed_signals += 1 if max_extended else 0
        self.corse_reversed = False if not removed_signals else removed_signals
        ###
        # creëer engines indien ze nog niet bestaan
        if (not self.bull_engine and 
            (red_data.type == barData.BOTTOM)):
            self.bull_engine = bull_corse()
            # self.bull_engine.insert(red_data)
        if (not self.bear_engine and
            (red_data.type == barData.TOP)):
            self.bear_engine = bear_corse()
            # self.bear_engine.insert(red_data)
        ###
        # stuur data naar bestaande engines
        if self.bull_engine:
            self.bull_engine.insert(red_data)
        if self.bear_engine:
            self.bear_engine.insert(red_data)
        ###
        # Herstart/verwijder gestopte engines
        _manage_stopped_engines(initialise=True)
        ###
        # Geef de statuswaarden van de engines terug
        # tupple: status bull_engine, status bear_engine
        
        ### Dit moet veranderen aangezien er zoveel statussen zijn om door
        ### te geven, misschien eerder aangeven of er gereversed is of aangeven
        ### dat er iets is misgelopen. Specifieke analyse van de corse moet
        ### gebeuren door de client eventueel geholpen door functies in deze corse
        ### die op verzoek bepaalde zaken opzoeken, bevestigen, analyseren.
        bull_status = self.bull_engine.status if self.bull_engine else None
        bear_status = self.bear_engine.status if self.bear_engine else None
        return bull_status, bear_status

    def pickle_corses(self, bull_name, bear_name):
        #print('exporting corses')
        with open(bull_name, 'wb') as ofh:
            pickle.dump(self.bull_engine, ofh)
        with open(bear_name, 'wb') as ofh:
            pickle.dump(self.bear_engine, ofh)

    #def print_set(self, selector, subset, content, reverse = False):
    #    def printData(engine, subset, content, reverse):
    #        engineData = {'l': engine.level,
    #                      't': engine.time,
    #                      'm': engine.minimum[-1] if engine.minimum else None,
    #                      'M': engine.maximum[-1] if engine.maximum else None,
    #                      'a': engine.a[-1] if engine.a else None,
    #                      'b': engine.b[-1] if engine.b else None,
    #                      'c': engine.c[-1] if engine.c else None,
    #                      's': engine.status[-1] if engine.status else None}
    #        def printContent(engine, content):
    #            for code, x, size, typeOfData in FIELDS:
    #                if code in content:
    #                    if typeOfData == 'd':
    #                        fstr = '{{:{:d}d}}'
    #                    elif typeOfData == 'f':
    #                        fstr = '{{:{:d}f}}'
    #                    else:
    #                        fstr = '{{:{:d}}}'
    #                    fstr = fstr.format(size)
    #                    print(fstr.format(engineData[code]))
    #        if reverse and engine.child:
    #            printData(engine.child, subset, content, reverse)
    #        if engine.status[-1] in subset:
    #            printContent(engine, content)
    #        if not reverse and engine.child:
    #            printData(engine.child, subset, content, reverse)
    #        
    #    ### print header
    #    for code, fullname, size, x in FIELDS:
    #        #print (code, fullname, size)
    #        if code in content:
    #            fstr = '{{:{:d}}}'.format(size)
    #            print(fstr.format(fullname), end='')
    #        print()
    #        print()
    #    ### select engine
    #    if selector == 'bull':
    #        engine = self.bull_engine
    #    elif selector == 'bear':
    #        engine = self.bear_engine
    #    else:
    #        print('slechte selector in corse.corse.print_set')
    #    ### start printing
    #    if engine:
    #        printData(engine, subset, content, reverse)

    def get_signals(self, signals=HOTLIST):
        bear_eng = self.bear_engine
        bull_eng = self.bull_engine
        return (bear_eng.get_signals(signals) if bear_eng else [], 
                bull_eng.get_signals(signals) if bull_eng else [])

            

class bull_corse():
    ##########
    # corse om abc correcties te herkennen in bullish markten
    ##########

    def _atomise_values(self):
        # Zorgt er voor dat alle lijsten altijd de zelfde lengte hebben
        # zodat de corse betrouwbaar ingekort kan worden
        base = len(self.status)
        if len(self.maximum) < base:
            self.maximum.append(self.maximum[-1] if self.maximum else None)
        if len(self.a) < base:
            self.a.append(self.a[-1] if self.a else None)
        if len(self.b) < base:
            self.b.append(self.b[-1] if self.b else None)
        if len(self.c) < base:
            self.c.append(self.c[-1] if self.c else None)        
        if len(self.maximumT) < base:
            self.maximumT.append(self.maximumT[-1] if self.maximumT else None)
        if len(self.aT) < base:
            self.aT.append(self.aT[-1] if self.aT else None)
        if len(self.bT) < base:
            self.bT.append(self.bT[-1] if self.bT else None)
        if len(self.cT) < base:
            self.cT.append(self.cT[-1] if self.cT else None)            

    def _remove_stopped_children(self):
        if self.child and self.child.stopped:
            self.child = None

    def __init__(self, level=0):
        # al de waarden die moeten kunnen worden teruggedraait als er een signaal
        # komt dat ouder is dan het vorige zijn lists
        self.level    = level              # * 0 voor toplevel, anders 1 hoger dan parent
        self.time     = None               # * datetime van het begin van de bull periode
        self.minimum  = 0                  # * de laagste waarde
        self.maximum  = []                 # * geschiedenis van de hoogste waarde
        self.maximumT = []
        self.a        = []                 # * geschiedenis waarde van mogelijke a piek
        self.aT       = []
        self.b        = []                 # * geschiedenis waarde van mogelijke b piek
        self.bT       = []
        self.c        = []                 # * geschiedenis waarde van mogelijke c piek
        self.cT       = []
        self.status   = []                 # * geschiedenis van de statussen van de corse
        self.child    = None               # * lijst van bull_corses met een hoger minima
        self.stopped  = False              # * Geeft aan of corse nog actief is, gestopte
                                           #   corses kunnen verwijdert worden

    def summary(self):
        '''return the important values from this corse as ABCCorrection'''
        return ABCCorrection(self.level, 
                             self.a[-1], self.aT[-1],
                             self.b[-1], self.bT[-1],
                             self.c[-1], self.cT[-1],
                             self.minimum, self.time,
                             self.maximum[-1], self.maximumT[-1])
                                  
    def insert(self, red_data):
        #######
        # bereken de fase waarin de correctie zit aan de hand van de meest
        # recente reducer data
        #######
        def _make_descendant():
            #if self.child and self.child.minimum > red_data.value:
            #    vprint('level {}:{} child levels removed, create new child'.format(self.level,
            #                                                                       self.time,
            #                                                                       self.minimum))
            if not self.child or self.child.minimum > red_data.value:
                self.child = bull_corse(self.level+1)            
            
        def _initialise():
            #####
            # start een nieuwe bull corse, stel het minimum in
            #####
            self.time    = red_data.time
            self.minimum = red_data.value
            self.status.append(INITIALISING)
            #vprint('level {}:{} initialise new bull_corse, min: {}'.format(self.level,
            #                                                               self.time,
            #                                                               self.minimum))
            
        def _set_maximum():
            #####
            # stel (nieuw) maxima van de bull corse in
            #####
            self.maximum.append(red_data.value)
            self.maximumT.append(red_data.time)
            self.a.append(None)
            self.b.append(None)
            self.c.append(None)
            self.aT.append(None)
            self.bT.append(None)
            self.cT.append(None)
            self.status.append(WAITING_FOR_A)
            #vprint('level {}:{} (new) max: {}'.format(self.level,
            #                                          self.time,
            #                                          self.maximum[-1]))

        def _stop_engine():
            #####
            # Engine buiten dienst stellen
            #####
            self.stopped  = True
            self.child    = None
            self.status.append(STOPPED)
            #vprint('level {}:{} engine_stopped'.format(self.level,
            #                                           self.time))  

        def _set_a():
            #####
            # a instellen en nieuwe bull corse opstarten
            #####            
            self.a.append(red_data.value)
            self.b.append(None)
            self.c.append(None)            
            self.aT.append(red_data.time)
            self.bT.append(None)
            self.cT.append(None)
            self.status.append(WAITING_FOR_B)
            #vprint('level {}:{} A-waarde ingesteld op: {}'.format(self.level,
            #                                                      self.time,
            #                                                      self.a[-1]))

        def _set_b():
            #####
            # b instellen
            #####
            self.b.append(red_data.value)
            self.c.append(None)
            self.bT.append(red_data.time)
            self.cT.append(None)
            self.status.append(WAITING_FOR_C)
            #vprint('level {}:{} B-waarde ingesteld op: {}'.format(self.level,
            #                                                      self.time,
            #                                                      self.b[-1]))

        def _set_c():
            #####
            # c instellen
            #####
            self.c.append(red_data.value)
            self.cT.append(red_data.time)
            self.status.append(VALIDATE_C)
            #vprint('level {}:{} C-waarde ingesteld op: {}, wachten op validering'.format(self.level,
            #                                                                             self.time,
            #                                                                             self.c[-1]))

        def _new_max_or_to_c():
            #####
            # grafiek heeft A B zone nog niet verlaten , verander status om te blijven zoeken
            #####
            self.status.append(IN_DOUBT)
            #vprint('level {}:{} engine twijfelt, A niet doorbroken, wacht op niewe data'
            #       .format(self.level, self.time))

        def _reset_ABC():
            #####
            # B is doorbroken voor een C werd ingesteld, herbegin zoektocht naar A   
            #####
            # versie !
            ###
            #self.status.append(WAITING_FOR_A)
            #self.a.append(None)
            #self.b.append(None)
            #self.c.append(None)
            #vprint('level {}:{} B is doorbroken, zoekt nieuwe A'
            #       .format(self.level, self.time))
            ###
            # versie 2: de b wordt gewoon bijgesteld
            ###
            #vprint('level {}:{} B is doorbroken voor C werd bereikt'
            #       .format(self.level, self.time))
            _set_b()

        def _is_next_c():
            #####
            # piek blijft tussen A en B, verander status om te blijven zoeken
            #####
            self.status.append(WAITING_FOR_C)
            #vprint('level {}:{} engine blijft twijfelen,  B niet doorbroken, zoek naar C'
            #       .format(self.level, self.time))

        def _corr_complete_new_max():
            #####
            # Correctie is afgelopen, nieuw maximum is gezet
            #####
            #self.a.append(None)   now in _set_maximum()
            #self.b.append(None)
            #self.c.append(None)
            #vprint('level {}:{} corretie is beïndigd, max doorbroken.'
            #       .format(self.level, self.time))
            #vprint('level {}:{} ***GAIN***'
            #       .format(self.level, self.time))
            _set_maximum()

        def _corr_complete_no_new_max():
            #####
            # Correctie is theoretisch afgelopen, beschouw dit punt als nieuwe B
            # Vorige correctie heeft nog potentieel voor nieuwe max
            #####
            # self.c.append(None) now in _set_b()
            #vprint('level {}:{} corretie is beïndigd, mogelijk nog verdere steiging voorbij max.'
            #       .format(self.level, self.time))
            #vprint('level {}:{} ***GAIN***'
            #       .format(self.level, self.time))
            _set_b()

        def _c_confirmed():
            #####
            # overlap is een feit, officieel een correctie. data verder opvolgen
            # potentieel tot boven max
            #####
            self.status.append(OVERLAP_HIGH)
            #vprint('level {}:{} correctie in overlap, data opvolgen.'
            #       .format(self.level, self.time))

        def _c_not_confirmed():
            #####
            # Correctie nog niet bevestigd want a is niet doorbroken
            #####
            self.status.append(C_AT_RISC)
            #vprint('level {}:{} correctie nog niet in overlap, C wordt mogelijk doorbroken?.'
            #       .format(self.level, self.time))

        def _correction_failed_on_c():
            #####
            # Correctie is vals, laatste waarden lager dan C
            #####
            #vprint('level {}:{} C is doorbroken, correctie uitgediept, c instellen en valideren.'
            #       .format(self.level, self.time))
            #vprint('level {}:{} ***LOSS***'
            #       .format(self.level, self.time))
            _set_c()

        def _corr_to_new_high():
            #####
            # Correctie verder opvolgen
            #####
            self.status.append(OVERLAP_MIN)
            #vprint('level {}:{} correctie verder opvolgen.'
            #       .format(self.level, self.time))
        
        def _validate_c():
            #####
            # C nog niet gevalideerd, zoek bevestiging
            #####
            self.status.append(VALIDATE_C)
            #vprint('level {}:{} blijven wachten op validatie.'
            #       .format(self.level, self.time))

        ###
        # START insert
        ###
        if not self.status:
            _initialise()
        else:
            if self.status[-1] == INITIALISING:
                _set_maximum()
            elif self.status[-1] == WAITING_FOR_A:
                if red_data.value < self.minimum:       # bodem is uit de engine geslagen
                    _stop_engine()
                else:
                    _make_descendant()                  # elk minimum leidt mogelijk naar een
                                                        # een nieuwe bull
                    _set_a()
            elif self.status[-1] == WAITING_FOR_B:
                if red_data.value > self.maximum[-1]:   # Kan ik hier ook groter of gelijk aan van maken
                    _set_maximum()                      # misschien wel eens interessant om te testen welk
                else:                                   # verschil dat eventueel kan maken
                    _set_b()
            elif self.status[-1] == WAITING_FOR_C:
                if red_data.value < self.minimum:       # bodem is uit de engine geslagen
                    _stop_engine()
                else:
                    _make_descendant()                  # elk minimum leidt mogelijk naar een
                                                        # een nieuwe bull
                    if red_data.value < self.a[-1]:
                        _set_c()
                    else:
                        _new_max_or_to_c()
            elif self.status[-1] == IN_DOUBT:
                if red_data.value > self.maximum[-1]:   # Kan ik hier ook groter of gelijk aan van maken
                    _set_maximum()                      # misschien wel eens interessant om te testen welk
                elif red_data.value > self.b[-1]:       # verschil dat eventueel kan maken
                    _reset_ABC()
                else:
                    _is_next_c()                    
            elif ((self.status[-1] == VALIDATE_C) or
                  (self.status[-1] == OVERLAP_MIN)):
                if red_data.value > self.maximum[-1]:
                    _corr_complete_new_max()
                elif red_data.value > self.b[-1]:
                    _corr_complete_no_new_max()
                elif ((red_data.value > self.a[-1]) or
                      (self.status[-1] == OVERLAP_MIN)):
                    _c_confirmed()
                else:
                    _c_not_confirmed()
            elif ((self.status[-1] == OVERLAP_HIGH) or
                  (self.status[-1] == C_AT_RISC)):
                if red_data.value < self.minimum:       # bodem is uit de engine geslagen
                    _stop_engine()
                else:
                    _make_descendant()                               # elk minimum leidt mogelijk naar een
                                                                     # een nieuwe bull                  
                    if red_data.value < self.c[-1]:
                        if self.status[-1] == OVERLAP_HIGH:
                            _correction_failed_on_c()
                        else:
                            _set_c()
                    elif self.status[-1] == OVERLAP_HIGH:
                        _corr_to_new_high()
                    else:
                        _validate_c()                   
            else:
                print('level {}:{} What am i doing here???'.format(self.level, self.time))
                self.status = 'bull_not yet defined'
        if type(self.status) == list:
            self._atomise_values()
        if self.child:
            self.child.insert(red_data)
        self._remove_stopped_children()
          

    def reverse(self, number_of_signals):
        #####
        # verwijder de laatste 'number of signals' signalen uit de
        # corse lijsten
        #####
        if number_of_signals >= len(self.status):
            self.stopped = True
            self.child   = None
            #vprint('level {}:{} Stopped'.format(self.level,
            #                                    self.time))
        else:
            self.maximum = self.maximum[:-number_of_signals]
            self.a       = self.a[:-number_of_signals]
            self.b       = self.b[:-number_of_signals]
            self.c       = self.c[:-number_of_signals]
            self.maximumT = self.maximumT[:-number_of_signals]
            self.aT       = self.aT[:-number_of_signals]
            self.bT       = self.bT[:-number_of_signals]
            self.cT       = self.cT[:-number_of_signals]
            self.status  = self.status[:-number_of_signals]
            if self.child:
                self.child.reverse(number_of_signals)
            self._remove_stopped_children()

    def get_signals(self, subset=HOTLIST, lastMax=-1):
        #print('in bull get_signals')
        if (self.status[-1] in subset) and (self.maximum[-1] != lastMax):
            signals_list = [self.summary()]
        else:
            signals_list = []
        if self.child:
            return signals_list + self.child.get_signals(subset,
                                                         self.maximum[-1])
        else:
            return signals_list

    def print_set(self, subset, content, reverse = False):
        def printData(engine, subset, content, reverse, lastMax=-1):
            engineData = {'l': engine.level,
                          't': str(engine.time),
                          'T': str(engine.maximumT[-1]) if (engine.maximumT and
                                                            engine.maximumT[-1]) else '#',
                          'm': engine.minimum, # if engine.minimum else None,
                          'M': engine.maximum[-1] if (engine.maximum and
                                                      engine.maximum[-1]) else 0,
                          'a': engine.a[-1] if (engine.a and engine.a[-1]) else 0,
                          'A': str(engine.aT[-1]) if (engine.aT and engine.aT[-1]) else '#',
                          'b': engine.b[-1] if (engine.b and engine.b[-1]) else 0,
                          'B': str(engine.bT[-1]) if (engine.bT and engine.bT[-1]) else '#',
                          'c': engine.c[-1] if (engine.c and engine.c[-1]) else 0,
                          'C': str(engine.cT[-1]) if (engine.cT and engine.cT[-1]) else '#',
                          's': engine.status[-1] if engine.status else None}
            def printContent(engine, content):
                for code, x, size, typeOfData in FIELDS:
                    if code in content:
                        if typeOfData == 'd':
                            fstr = '{{:{:d}d}}'
                        elif typeOfData == 'f':
                            fstr = '{{:{:d}.2f}}'
                        else:
                            fstr = '{{:{:d}}}'
                        fstr = fstr.format(size)
                        print(fstr.format(engineData[code]), end=' | ')
                print()
            if reverse and engine.child:
                printData(engine.child, subset, content, reverse, engine.maximum[-1])
            if engine.status[-1] in subset:
                if engine.maximum[-1] != lastMax:
                    printContent(engine, content)
            if not reverse and engine.child:
                printData(engine.child, subset, content, reverse, engine.maximum[-1])
            
        ### print header
        header_len = 0
        for code, fullname, size, x in FIELDS:
            #print (code, fullname, size)
            if code in content:
                header_len += size + 3
                fstr = '{{:{:d}}}'.format(size)
                print(fstr.format(fullname), end=' | ')
        print()
        print('='*header_len)
        ### start printing
        if self:
            printData(self, subset, content, reverse)
            print('-' * header_len)
            print('\n')


class bear_corse():
    ##########
    # corse om abc correcties te herkennen in bearish markten
    ##########
    
    def _atomise_values(self):
        # Zorgt er voor dat alle lijsten altijd de zelfde lengte hebben
        # zodat de corse betrouwbaar ingekort kan worden
        base = len(self.status)
        if len(self.minimum) < base:
            self.minimum.append(self.minimum[-1] if self.minimum else None)
        if len(self.a) < base:
            self.a.append(self.a[-1] if self.a else None)
        if len(self.b) < base:
            self.b.append(self.b[-1] if self.b else None)
        if len(self.c) < base:
            self.c.append(self.c[-1] if self.c else None)         
        if len(self.minimumT) < base:
            self.minimumT.append(self.minimumT[-1] if self.minimumT else None)
        if len(self.aT) < base:
            self.aT.append(self.aT[-1] if self.aT else None)
        if len(self.bT) < base:
            self.bT.append(self.bT[-1] if self.bT else None)
        if len(self.cT) < base:
            self.cT.append(self.cT[-1] if self.cT else None)          

    def _remove_stopped_children(self):
        if self.child and self.child.stopped:
            self.child = None

    def __init__(self, level=0):
        # al de waarden die moeten kunnen worden teruggedraait als er een signaal
        # komt dat ouder is dan het vorige zijn lists
        self.level    = level              # * 0 voor toplevel, anders 1 hoger dan parent
        self.time     = None               # * datetime van het begin van de bull periode
        self.minimum  = []                 # * geschiedenis de laagste waarde
        self.minimumT = []
        self.maximum  = 0                  # * de hoogste waarde
        self.a        = []                 # * geschiedenis waarde van mogelijke a piek
        self.aT       = []
        self.b        = []                 # * geschiedenis waarde van mogelijke b piek
        self.bT       = []
        self.c        = []                 # * geschiedenis waarde van mogelijke c piek
        self.cT       = []
        self.status   = []                 # * geschiedenis van de statussen van de corse 
        self.child    = None               # * lijst van bull_corses met een hoger minima
        self.stopped  = False              # * Geeft aan of corse nog actief is, gestopte
                                           #   corses kunnen verwijdert worden

    def summary(self):
        '''return the important values from this corse as ABCCorrection'''
        return ABCCorrection(self.level, 
                             self.a[-1], self.aT[-1],
                             self.b[-1], self.bT[-1],
                             self.c[-1], self.cT[-1],
                             self.minimum[-1], self.minimumT[-1],
                             self.maximum, self.time)

    def insert(self, red_data):
        #######
        # bereken de fase waarin de correctie zit aan de hand van de meest
        # recente reducer data
        #######
        def _make_descendant():
            #if self.child and self.child.maximum < red_data.value:
            #    vprint('level {}:{} child levels removed, create new child'.format(self.level,
            #                                                                       self.time,
            #                                                                       self.minimum))
            if not self.child or self.child.maximum < red_data.value:
                self.child = bear_corse(self.level+1) 

        def _initialise():
            #####
            # start een nieuwe bear corse, stel het minimum in
            #####
            self.time    = red_data.time
            self.maximum = red_data.value
            self.status.append(INITIALISING)
            #vprint('level {}:{} initialise new bear_corse, max: {}'.format(self.level,
            #                                                               self.time,
            #                                                               self.maximum))

        def _set_minimum():
            #####
            # stel (nieuw) minimum van de bear corse in
            #####
            self.minimum.append(red_data.value)
            self.minimumT.append(red_data.time)
            self.a.append(None)
            self.b.append(None)
            self.c.append(None)
            self.aT.append(None)
            self.bT.append(None)
            self.cT.append(None)
            self.status.append(WAITING_FOR_A)
            #vprint('level {}:{} (new) min: {}'.format(self.level,
            #                                          self.time,
            #                                          self.minimum[-1]))

        def _stop_engine():
            #####
            # Engine buiten dienst stellen
            #####
            self.stopped  = True
            self.child    = None
            self.status.append(STOPPED)
            #vprint('level {}:{} engine_stopped'.format(self.level,
            #                                           self.time))  

        def _set_a():
            #####
            # a instellen en nieuwe bull corse opstarten
            #####            
            self.a.append(red_data.value)
            self.b.append(None)
            self.c.append(None)            
            self.aT.append(red_data.time)
            self.bT.append(None)
            self.cT.append(None)
            self.status.append(WAITING_FOR_B)
            #vprint('level {}:{} A-waarde ingesteld op: {}'.format(self.level,
            #                                                      self.time,
            #                                                      self.a[-1]))

        def _set_b():
            #####
            # b instellen
            #####
            self.b.append(red_data.value)
            self.c.append(None)
            self.bT.append(red_data.time)
            self.cT.append(None)
            self.status.append(WAITING_FOR_C)
            #vprint('level {}:{} B-waarde ingesteld op: {}'.format(self.level,
            #                                                      self.time,
            #                                                      self.b[-1]))

        def _set_c():
            #####
            # c instellen
            #####
            self.c.append(red_data.value)
            self.cT.append(red_data.time)
            self.status.append(VALIDATE_C)
            #vprint('level {}:{} C-waarde ingesteld op: {}'.format(self.level,
            #                                                      self.time,
            #                                                      self.c[-1]))

        def _new_max_or_to_c():
            #####
            # grafiek heeft A B zone nog niet verlaten , verander status om te blijven zoeken
            #####
            self.status.append(IN_DOUBT)
            #vprint('level {}:{} engine twijfelt, A niet doorbroken, wacht op niewe data'
            #       .format(self.level, self.time))

        def _reset_ABC():
            #####
            # B is doorbroken voor een C werd ingesteld, herbegin zoektocht naar A
            #####
            # versie !
            ###
            #self.status.append(WAITING_FOR_A)           
            #self.a.append(None)
            #self.b.append(None)
            #self.c.append(None)
            #vprint('level {}:{} B is doorbroken, zoekt nieuwe A'
            #       .format(self.level, self.time))
            ###
            # versie 2: de b wordt gewoon bijgesteld
            ###
            #vprint('level {}:{} B is doorbroken voor C werd bereikt'
            #       .format(self.level, self.time))
            _set_b()

        def _is_next_c():
            #####
            # piek blijft tussen A en B, verander status om te blijven zoeken
            #####
            self.status.append(WAITING_FOR_C)
            #vprint('level {}:{} engine blijft twijfelen,  B niet doorbroken, zoek naar C'
            #       .format(self.level, self.time))

        def _corr_complete_new_min():
            #####
            # Correctie is afgelopen, nieuw maximum is gezet
            #####
            #self.a.append(None) now in _set_minimum()
            #self.b.append(None)
            #self.c.append(None)
            #vprint('level {}:{} corretie is beïndigd, min doorbroken.'
            #       .format(self.level, self.time))
            #vprint('level {}:{} ***GAIN***'
            #       .format(self.level, self.time))
            _set_minimum()

        def _corr_complete_no_new_min():
            #####
            # Correctie is theoretisch afgelopen, beschouw dit punt als nieuwe B
            # Vorige correctie heeft nog potentieel voor nieuwe max
            #####
            #self.c.append(None) now in _set_c()
            #vprint('level {}:{} corretie is beïndigd, mogelijk nog verdere daling voorbij min.'
            #       .format(self.level, self.time))
            #vprint('level {}:{} ***GAIN***'
            #       .format(self.level, self.time))
            _set_b()

        def _c_confirmed():
            #####
            # overlap is een feit, officieel een correctie. data verder opvolgen
            # potentieel tot onder min
            #####
            self.status.append(OVERLAP_MIN)
            #vprint('level {}:{} correctie in overlap, data opvolgen.'
            #       .format(self.level, self.time))

        def _c_not_confirmed():
            #####
            # Correctie nog niet bevestigd want a is niet doorbroken
            #####
            self.status.append(C_AT_RISC)
            #vprint('level {}:{} correctie nog niet in overlap, C wordt mogelijk doorbroken?.'
            #       .format(self.level, self.time))

        def _correction_failed_on_c():
            #####
            # Correctie is vals, laatste waarden lager dan C
            #####
            #vprint('level {}:{} C is doorbroken, correctie uitgediept, c instellen en valideren.'
            #       .format(self.level, self.time))
            #vprint('level {}:{} ***LOSS***'
            #       .format(self.level, self.time))
            _set_c()

        def _corr_to_new_high():
            #####
            # Correctie verder opvolgen
            #####
            self.status.append(OVERLAP_HIGH)
            #vprint('level {}:{} correctie verder opvolgen.'
            #       .format(self.level, self.time))
        
        def _validate_c():
            #####
            # C nog niet gevalideerd, zoek bevestiging
            #####
            self.status.append(VALIDATE_C)
            #vprint('level {}:{} blijven wachten op validatie.'
            #       .format(self.level, self.time))
        
        ###
        # START insert
        ###         
        if not self.status:
            _initialise()
        else:
            if self.status[-1] == INITIALISING:
                _set_minimum()
            elif self.status[-1] == WAITING_FOR_A:
                if red_data.value > self.maximum:
                    _stop_engine()
                else:
                    _make_descendant()                              # elk maximum leidt mogelijk naar een
                                                                    # een nieuwe bear
                    _set_a()
            elif self.status[-1] == WAITING_FOR_B:
                if red_data.value < self.minimum[-1]:
                    _set_minimum()
                else:
                    _set_b()
            elif self.status[-1] == WAITING_FOR_C:
                if red_data.value > self.maximum:       # bodem is uit de engine geslagen
                    _stop_engine()
                else:
                    _make_descendant()                             # elk minimum leidt mogelijk naar een
                                                                    # een nieuwe bull
                    if red_data.value > self.a[-1]:
                        _set_c()
                    else:
                        _new_max_or_to_c()
            elif self.status[-1] == IN_DOUBT:
                if red_data.value < self.minimum[-1]:   # Kan ik hier ook groter of gelijk aan van maken
                    _set_minimum()                      # misschien wel eens interessant om te testen welk
                elif red_data.value < self.b[-1]:       # verschil dat eventueel kan maken
                    _reset_ABC()
                else:
                    _is_next_c()
            elif ((self.status[-1] == VALIDATE_C) or
                  (self.status[-1] == OVERLAP_HIGH)):
                if red_data.value < self.minimum[-1]:
                    _corr_complete_new_min()
                elif red_data.value < self.b[-1]:
                    _corr_complete_no_new_min()
                elif ((red_data.value < self.a[-1]) or
                      (self.status[-1] == OVERLAP_HIGH)):
                    _c_confirmed()
                else:
                    _c_not_confirmed()
            elif ((self.status[-1] == OVERLAP_MIN) or
                  (self.status[-1] == C_AT_RISC)):
                if red_data.value > self.maximum:       # bodem is uit de engine geslagen
                    _stop_engine()
                else:
                    _make_descendant()                               # elk minimum leidt mogelijk naar een
                                                                     # een nieuwe bull                  
                    if red_data.value > self.c[-1]:
                        if self.status[-1] == OVERLAP_MIN:
                            _correction_failed_on_c()
                        else:
                            _set_c()
                    elif self.status[-1] == OVERLAP_MIN:
                        _corr_to_new_high()
                    else:
                        _validate_c()       
            else:
                print('level {}:{} What am i doing here???'.format(self.level, self.time))
                self.status = 'bear_not yet defined'
        if type(self.status) == list:    # kleine hack om te kunnen testen, verwijder voorwaarde
            self._atomise_values()       # als alles in gedefinieerd
        if self.child:
            self.child.insert(red_data)
        self._remove_stopped_children()


    def reverse(self, number_of_signals):
        #####
        # verwijder de laatste 'number of signals' signalen uit de
        # corse lijsten
        #####
        if number_of_signals >= len(self.status):
            self.stopped = True
            self.child   = None
            #vprint('level {}:{} Stopped'.format(self.level,
            #                                    self.time))
        else:
            self.minimum = self.minimum[:-number_of_signals]
            self.a       = self.a[:-number_of_signals]
            self.b       = self.b[:-number_of_signals]
            self.c       = self.c[:-number_of_signals]
            self.minimumT = self.minimumT[:-number_of_signals]
            self.aT       = self.aT[:-number_of_signals]
            self.bT       = self.bT[:-number_of_signals]
            self.cT       = self.cT[:-number_of_signals]
            self.status  = self.status[:-number_of_signals]
            if self.child:
                self.child.reverse(number_of_signals)
            self._remove_stopped_children()

    def get_signals(self, subset=HOTLIST, lastMin=-1):
        #print('in bear get_getsignals')        
        if (self.status[-1] in subset) and (self.minimum[-1] != lastMin):
            signals_list = [self.summary()]
        else:
            signals_list = []
        if self.child:
            return signals_list + self.child.get_signals(subset,
                                                         self.minimum[-1])
        else:
            return signals_list


    def print_set(self, subset, content, reverse = False):
        def printData(engine, subset, content, reverse, lastMin=-1):
            engineData = {'l': engine.level,
                          't': str(engine.time),
                          'T': str(engine.minimumT[-1]) if (engine.minimumT and
                                                            engine.minimumT[-1]) else '#',
                          'm': engine.minimum[-1] if (engine.minimum and
                                                      engine.minimum[-1]) else 0,
                          'M': engine.maximum,
                          'a': engine.a[-1] if (engine.a and engine.a[-1]) else 0,
                          'A': str(engine.aT[-1]) if (engine.aT and engine.aT[-1]) else '#',
                          'b': engine.b[-1] if (engine.b and engine.b[-1]) else 0,
                          'B': str(engine.bT[-1]) if (engine.bT and engine.bT[-1]) else '#',
                          'c': engine.c[-1] if (engine.c and engine.c[-1]) else 0,
                          'C': str(engine.cT[-1]) if (engine.cT and engine.cT[-1]) else '#',
                          's': engine.status[-1] if engine.status else None}
            def printContent(engine, content):
                for code, x, size, typeOfData in FIELDS:
                    if code in content:
                        if typeOfData == 'd':
                            fstr = '{{:{:d}d}}'
                        elif typeOfData == 'f':
                            fstr = '{{:{:d}.2f}}'
                        else:
                            fstr = '{{:{:d}}}'
                        fstr = fstr.format(size)
                        print(fstr.format(engineData[code]), end=' | ')
                print()
            if reverse and engine.child:
                printData(engine.child, subset, content, reverse, engine.minimum[-1])
            if engine.status[-1] in subset:
                if engine.minimum[-1] != lastMin:
                    printContent(engine, content)
            if not reverse and engine.child:
                printData(engine.child, subset, content, reverse, engine.minimum[-1])
            
        ### print header
        header_len = 0
        for code, fullname, size, x in FIELDS:
            #print (code, fullname, size)
            if code in content:
                header_len += size + 3
                fstr = '{{:{:d}}}'.format(size)
                print(fstr.format(fullname), end=' | ')
        print()
        print('=' * header_len)
        ### start printing
        if self:
            printData(self, subset, content, reverse)
            print('-' * header_len)
            printn('\n')
