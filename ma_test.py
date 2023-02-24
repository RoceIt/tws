#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#
import os.path
from datetime import timedelta

import mypy
import moving_avgs
from barData import ochlBar, ochl

ma_s = moving_avgs.MovingAverage(120)
ma_f = moving_avgs.MovingAverage(10)
inf = open('/home/rolcam/roce/Data/bigdata/AEX', 'r')
exp = open('/home/rolcam/roce/tmp/mass', 'w')
#inf = open('/home/rolcam/roce/Data/bigdata/AEX_FUT', 'r')
inf.readline()
for line_of_data in inf:
  try:        
    d, t, o, h, l, c, v = line_of_data.strip().split(',')
    #if t < "09:00:00" or t > "17:30:00":
    #continue
    dt = ' '.join([d, t])
    dati = mypy.py_date_time(dt,'%d/%m/%Y %H:%M:%S') - timedelta(
      minutes=1)
    #dati = mypy.py_date_time(dt,'%m/%d/%Y %H:%M:%S') - timedelta(
    #minutes=1)
    #mypy.get_bool("{}|{}".format(dt, dati))
    curr_ochl = ochlBar(dati, float(o), float(c), float(h) , 
                        float(l))
  except Exception as err:
    print(line_of_data)
    print(err)
    if True: #mypy.get_bool('cont? (y)', default=True):
      continue
    break
  print("{},{},{},{}".format(curr_ochl.time, curr_ochl.close,
                             ma_s.append(curr_ochl.close), ma_f.append(curr_ochl.close)),
        file=exp)