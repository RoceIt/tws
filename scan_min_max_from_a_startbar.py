#!/usr/bin/env python3
#
#  Copyright (c) 2012, 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import marketdata

def main():
  profit = .5
  _feeder = marketdata.data_bar_feeder(
    '/home/rolcam/roce/Data/daxfut_2013.txt', 
    is_index='False', 
  )
  feeder = marketdata.ComposingDatabarFeeder(
    feeder=_feeder,
    only_finished_bars=True,
    seconds=60
  )
  curr_date = None
  for bar in feeder:
    if not bar.time.date() == curr_date:
      if not curr_date is None:
        export_results(results_up, work_list_up, curr_date, 'up', prev_bar.time ,prev_bar.close)
        export_results(results_down, work_list_down, curr_date, 'down', prev_bar.time, prev_bar.close)
      curr_date = bar.time.date()
      print('*****',curr_date)
      results_up, results_down = [], []
      work_list_up, work_list_down = [], []
    curr_time = bar.time.time()
    if curr_time.minute == curr_time.second == 0:
      print(curr_time, len(results_down), len(work_list_down), len(results_up)
            , len(work_list_up))
    work_list_up.append([curr_time, bar.high, bar.high, bar.low, bar.open_])
    work_list_down.append([curr_time, bar.low, bar.low, bar.high, bar.open_])
    for info in work_list_up:
      info[2] = max(info[2], bar.high)
      info[3] = min(info[3], bar.low)
      if info[2] - info[1] >= profit:
        a = info[:]
        a.extend([curr_time, profit, (2*profit + info[1] - info[4]) / 2])
        results_up.append(a)
    for info in work_list_down:
      info[2] = min(info[2], bar.low)
      info[3] = max(info[3], bar.high)
      if info[1] - info[2] >= profit:
        a = info[:]
        a.extend([curr_time, profit, (2*profit + info[4] - info[1]) / 2])
        results_down.append(a)
    work_list_up = [x for x in work_list_up if not x[2] - x[1] >= profit]
    work_list_down = [x for x in work_list_down if not x[1] - x[2] >= profit]
    prev_bar = bar
    
    
def export_results(results, work_list, curr_date, direction, last_time, last_close):
  print("{}|{} {}".format(direction, len(results), len(work_list)))
  #if direction == 'up':
    #last
  filename = '/tmp/mima_{}_{}'.format(direction, curr_date)
  exit = last_close #results[-1][3]
  exit_time = last_time #results[-1][0]
  if direction == "up":
    work_list = [
      [x[0], x[1], exit, exit, x[4], exit_time, exit - x[1], exit - x[1]]
      for x in work_list]
  else:
    work_list = [
      [x[0], x[1], exit, exit, x[4], exit_time, x[1] - exit, x[1] - exit]
      for x in work_list]    
  results.extend(work_list)
  print(len(results))
  with open(filename, 'w') as of_h:
    print("time, worst_open, out, biggest dd"
          ", 'real'_open, exit, worst_result, medium_result",
          file=of_h)
    for r in sorted(results):
      print("{}, {}, {}, {}, {}, {}, {}, {}".format(*r), file=of_h)
    
if __name__ == '__main__':
  main()
    
    