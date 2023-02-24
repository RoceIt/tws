#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import roc_input as r_in
import tws
import marketdata
import last_min_max


def main():
    
    base_export_header_str = 'time, vwap, last_min, last_max'
    
    ##quick selection for testing, menufy it
    ##
    print('algo contract: ', end='')
    contract, db_name, dataset_ib, dataset_db, foo = get_contract_info()
    is_index = r_in.get_bool(
        message='index data {}: ', 
        default=True,
    )
    start = r_in.get_datetime(
        message='start date ({default}): ',
        time_format='%y/%m/%d',
        default='13/09/23',
    ).date()
    end = r_in.get_datetime(
        message='end date ({default}): ',
        time_format='%y/%m/%d',
        #default='13/10/14',
        empty=True,
    )
    end = end.date() if end else None        
    feeder = marketdata.data_bar_feeder(
                db_name, 
                is_index=is_index, 
                start=start, 
                stop=end,
                update=False,
                contract=contract, #only usefull for update True
    )
    new_bars = marketdata.ComposingDatabarFeeder(
            feeder=feeder,
            seconds=5,
    )
    indicators = []
    while True:
        moderator = r_in.get_integer(
            "volwap moderater (enter or 0 to stop): ",
            default=0,
        )
        if moderator == 0:
            break
        normaliser = r_in.get_integer(
            "use normaliser (1): ",
            default=1,
        )
        indicators.append(
            VolWapIndicator1(moderator, normaliser))
        base_export_header_str += ',{}'.format(moderator)
    min_max_keeper = last_min_max.LastMinMax()
    base_export_filename = r_in.get_string(
        'base filename: ',
    )
    tot_f = '.'.join([base_export_filename, 'tot'])
    vw_f = '.'.join([base_export_filename, 'vw'])
    rat_f = '.'.join([base_export_filename, 'rat'])
    with open(vw_f, 'w') as vw_fh, open(rat_f, 'w') as rat_fh:
        with open(tot_f, 'w') as tot_fh:
            print(base_export_header_str.format(type='total'), file=tot_fh)
            print(base_export_header_str.format(type='volwap'), file=vw_fh)
            print(base_export_header_str.format(type='ratio'), file=rat_fh) 
            for announced, curr_base_bar, composing_bar, new_bar in new_bars:
                if new_bar:
                    min_max_keeper.insert_next_bar(new_bar)
                    totals, vws, rats = [], [], []
                    for indicator in indicators:
                        (time_, vwap, total,
                         moderated_volwap,
                         vw_d_ratio) = indicator.new_bar(new_bar)
                        totals.append(total)
                        vws.append(moderated_volwap)
                        rats.append(vw_d_ratio)
                    print(time_, ',', vwap, ',',
                          min_max_keeper.last_min, ',',
                          min_max_keeper.last_max,
                          end='', file=vw_fh)
                    for v in vws:
                        print(',', v, end='', file=vw_fh)
                    print('', file=vw_fh)
                        #print(time_, ',', vwap, ',', total, ',', 
                              #moderated_volwap, ',', vw_d_ratio)
        
class VolWapIndicator1():
    
    def __init__(self, volwap_moderator=1, normaliser=1):
        self.volwap_moderator = volwap_moderator
        self.total_list = []
        self.diff_list = []
        self.total = 0
        self.prev_bar = None
        self.prev_total = 0
        self.normaliser = normaliser
        self.prev_volwap_ratio = None
        
    def new_bar(self, bar):
        
        real_volwap = 0
        vw_d_ratio = 0
        if self.prev_bar:
            gap = bar.vwap - self.prev_bar.vwap
            self.total += gap * bar.volume
            if self.prev_total:
                self.diff_list.append(self.total - self.prev_total)
                if len(self.diff_list) > self.volwap_moderator:
                    self.diff_list.pop(0)
                    real_volwap = sum(self.diff_list) / self.volwap_moderator
                    real_volwap /= bar.vwap / 1000
                    try:
                        vw_d_ratio = (real_volwap / self.prev_volwap) - 1
                    except ZeroDivisionError:
                        vw_d_ratio = 0
                else:
                    real_volwap = 0
                #print(bar.time, ',', bar.vwap, ',', self.total, ',', 
                      #real_volwap, ',', vw_d_ratio)
        self.prev_bar = bar
        self.prev_total = self.total
        self.prev_volwap = real_volwap
        mod_vw = real_volwap / self.normaliser
        return bar.time, bar.vwap, self.total, mod_vw, vw_d_ratio
    
def get_contract_info():
    menu = r_in.SelectionMenu(auto_number=True)
    menu.add_menu_item(
        'AEX', 
        return_value=(
            tws.contract_data("AEX-index"),
            "/home/rolcam/roce/Data/db/EOE IND EUR AEX@FTA.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.01",
        ),
    )
    menu.add_menu_item(
        'AEX FUTURE november 2013', 
        return_value=(
            tws.contract_data('AEX_FUT1311'),
            "/home/rolcam/roce/Data/db/EOE FUT X200 20131115 EUR FTIX3@FTA.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.05",
        ),
    )
    menu.add_menu_item(
        "DAX", 
        return_value=(
            tws.contract_data("DAX-30"),
            "/home/rolcam/roce/Data/db/DAX IND EUR DAX@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.01",
        ),
    )
    menu.add_menu_item(
        "DAX FUTURE december 2013", 
        return_value=(
            tws.contract_data("DAX-30_FUT1312"),
            "/home/rolcam/roce/Data/db/DAX FUT X25 20131220 EUR FDAX DEC 13@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.5",
        ),
    )
    menu.add_menu_item(
        "EUR.USD", 
        return_value=(
            tws.contract_data("euro-dollar"),
            "/home/rolcam/roce/Data/db/EUR CASH USD EUR.USD@IDEALPRO.db",
            "MIDPOINT", 
            "MIDPOINT_5_secs",
            "0.000001",
        ),
    )
    menu.add_menu_item(
        "Eurostoxx", 
        return_value=(
            tws.contract_data("DJ_Eurostoxx50"),
            "ESTX50 IND EUR ESTX50@DTB.db",
            "TRADES", 
            "TRADES_5_secs",
            "None",
        ),
    )
    menu.add_menu_item(
        'FTSE 100', 
        return_value=(
            tws.contract_data("FTSE-100"),
            "/home/rolcam/roce/Data/db/Z IND GBP Z@LIFFE.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.01",
        ),
    )
    menu.add_menu_item(
        'ZFTSE 100 FUTURE december 2013', 
        return_value=(
            tws.contract_data('FTSE_FUT1312'),
            "/home/rolcam/roce/Data/db/Z FUT X1000 20131220 GBP ZZ3@LIFFE.db",
            "TRADES", 
            "TRADES_5_secs",
            "0.5",
        ),
    )
    
    return menu.get_users_choice()

if __name__ == '__main__':
    main()