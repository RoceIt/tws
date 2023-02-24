#!/usr/bin/python3

import barData
import corse
import csv
import sql_IB_chart_time_db

data = barData.load('out.ochl')

bd     = barData.reducer()
aCorse = corse.corse
last_rg = None

IBContractName = 'AEX-index'   #####!!!!!HACK, PAS OP !!!!!

for line in data:
    st = bd.insert(line)
    #print (line,'***',st)
    if st:
        print(st)
        #if (not last_rg) or last_rg.curr_time != bd.reduced_graph[-1].curr_time:
        #    last_rg = bd.reduced_graph[-1]
        #    print(last_rg)
#for line in bd.reduced_graph:
#    print(line)

with open('out.red', 'w') as ofh:
    red_writer = csv.writer(ofh)
    red_count = 0
    for line in data:
        if line.time < bd.reduced_graph[red_count].time:
            red_writer.writerow([])
            continue
        red_writer.writerow(list(bd.reduced_graph[red_count]))
        red_count += 1
        if red_count >= len(bd.reduced_graph):
            break

with open('out.redo', 'w') as ofh:
    ctf = sql_IB_chart_time_db.chart_time_feeder(IBContractName)
    red_writer = csv.writer(ofh)
    for line in bd.reduced_graph:
        red_writer.writerow([ctf.symbol_chart_time(line.time)]+list(line))
    ctf.close()

