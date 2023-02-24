#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import random

import roc_input as r_in

random.seed()

def main():
    size_of_1_run = r_in.get_integer(
            message= 'nr of guesses in 1 run : ',
            default=100,
    )
    nr_of_runs = nr_o_r = r_in.get_integer(
            message='number of runs: ',
            default=1,
    )
    total = 0
    def base_algo(a_01_list):
        total = 0
        last_good = True
        nr_of_ctr = 1
        serie_good = 0
        for c in a_01_list:
            if c == 0:
                serie_good = 0
                total -= 6 * nr_of_ctr
                nr_of_ctr = 1
            else:
                serie_good += 1
                total += nr_of_ctr
                nr_of_ctr = serie_good if serie_good < 4 else 1
        return total
    
    while nr_of_runs > 0:
        run_total = base_algo(random_01_list(size_of_1_run))
        print(run_total)
        total += run_total
        nr_of_runs -= 1
    print('avg: ', total/nr_o_r)

def random_01_list(elements):
    return [random.randrange(7) for x in range(elements)]

if __name__ == '__main__':
    main()
    
