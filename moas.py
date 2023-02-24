#!/usr/bin/env python3
#  Copyright (c) 2014, Rolf Camps (rolf.camps@scarlet.be)

import roc_input as r_in

expected_average_day_gain = 10
max_loss_per_day = 60                 # percentage of exp dayly gain
force_profit_if_loss_bigger_then = 5  # times max loss per day
forced_profit_percentge = 50          # stop trading after this percentage of
                                      # loss is gained
max_gain_to_lose = 50                 # max to lose is this percentage of your
                                      # max gain of the day or max loss per day
                                      # if bigger

def main():
    print('start')
    day_count = r_in.get_integer('Day count: ')
    current_ballans = r_in.get_float('current ballans: ')
    target = day_count * expected_average_day_gain
    max_loss_today = max_loss_per_day *expected_average_day_gain / 100
    max_profit_today = None
    if current_ballans > target:
        max_loss_today = max(max_loss_today,
                             (current_ballans - target) * max_gain_to_lose / 100)
    elif current_ballans < (
        target - force_profit_if_loss_bigger_then * max_loss_today):
        max_profit_today = forced_profit_percentge * (target - force_profit_if_loss_bigger_then * max_loss_today) / 100
    result_today = max_today = 0
    while r_in.get_bool('show my limits {}:', default=True):
        print('curr total: {}'.format(current_ballans + result_today))
        if max_profit_today and result_today >= max_profit_today:
            print('Take a break, come back tomorrow, max gain reached')
            break
        if result_today <= max_today - max_loss_today:
            print('Take a break, come back tomorrow')
            break
        last_result = r_in.get_float('Max stop {}, result: '.format(
            max_loss_today + result_today - max_today))
        result_today += last_result
        max_today = max(max_today, result_today)
        if current_ballans + result_today > target:            
            max_loss_today = max(max_loss_today,
                                 (current_ballans + result_today - target) * max_gain_to_lose / 100)
    print('rapport day {}'.format(day_count))
    print('total: {}'.format(current_ballans + result_today))
    
if __name__ == '__main__':
    main()