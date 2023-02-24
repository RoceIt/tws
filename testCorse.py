#!/usr/bin/python3

import barData
import corse
import csv

data = barData.load('out.ochl')

bdred  = barData.reducer()
aCorse = corse.corse()

for line in data:
    curr_reducer_bar = bdred.insert(line)
    if curr_reducer_bar:
        print(aCorse.insert(curr_reducer_bar))

#with open('out.red', 'w') as ofh:
#    red_writer = csv.writer(ofh)
#    red_count = 0
#    for line in data:
#        if line.time < bd.reduced_graph[red_count].time:
#            red_writer.writerow([])
#            continue
#        red_writer.writerow(list(bd.reduced_graph[red_count]))
#        red_count += 1
#        if red_count >= len(bd.reduced_graph):
#            break


