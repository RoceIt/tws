#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

from mypy import CodeAndMessage

error = CodeAndMessage

NO_VALID_ID = -1
ALREADY_CONNECTED = error(501, 'Already connected.')
CONNECT_FAIL = error(502, 'Couldn\'t connect to TWS.  Confirm that '
                     '"Enable ActiveX and Socket Clients" is enabled '
                     'on the TWS "Configure->API" menu.')
UPDATE_TWS = error(503, 'The TWS is out of date and must be upgraded.')
NOT_CONNECTED = error(504, 'Not connected')
UNKNOWN_ID = error(505, 'Fatal Error: Unknown message id.')
FAIL_SEND_REQMKT = error(510, 'Request Market Data Sending Error - ')
FAIL_SEND_CANMKT = error(511, 'Cancel Market Data Sending Error - ')
FAIL_SEND_ORDER = error(512, 'Order Sending Error - ')
FAIL_SEND_ACCT = error(513, 'Account Update Request Sending Error -')
FAIL_SEND_EXEC = error(514, 'Request For Executions Sending Error -')
FAIL_SEND_CORDER = error(515, 'Cancel Order Sending Error -')
FAIL_SEND_OORDER = error(516, 'Request Open Order Sending Error -')
UNKNOWN_CONTRACT = error(517, 'Unknown contract. Verify the contract '
                         'details supplied.')
FAIL_SEND_REQCONTRACT = error(518, 'Request Contract Data Sending Error - ')
FAIL_SEND_REQMKTDEPTH = error(519, 'Request Market Depth Sending Error - ')
FAIL_SEND_CANMKTDEPTH = error(520, 'Cancel Market Depth Sending Error - ')
FAIL_SEND_SERVER_LOG_LEVEL = error(521, 'Set Server Log Level Sending '
                                   'Error - ')
FAIL_SEND_FA_REQUEST = error(522, 'FA Information Request Sending Error - ')
FAIL_SEND_FA_REPLACE = error(523, 'FA Information Replace Sending Error - ')
FAIL_SEND_REQSCANNER = error(524, 'Request Scanner Subscription Sending '
                             'Error - ')
FAIL_SEND_CANSCANNER = error(525, 'Cancel Scanner Subscription Sending '
                             'Error - ')
FAIL_SEND_REQSCANNERPARAMETERS = error(526, 'Request Scanner Parameter '
                                       'Sending Error - ')
FAIL_SEND_REQHISTDATA = error(527, 'Request Historical Data Sending '
                              'Error - ')
FAIL_SEND_CANHISTDATA = error(528, 'Request Historical Data Sending '
                              'Error - ')
FAIL_SEND_REQRTBARS = error(529, 'Request Real-time Bar Data Sending '
                            'Error - ')
FAIL_SEND_CANRTBARS = error(530, 'Cancel Real-time Bar Data Sending '
                            'Error - ')
FAIL_SEND_REQCURRTIME = error(531, 'Request Current Time Sending Error - ')
FAIL_SEND_REQFUNDDATA = error(532, 'Request Fundamental Data Sending '
                              'Error - ')
FAIL_SEND_CANFUNDDATA = error(533, 'Cancel Fundamental Data Sending '
                              'Error - ')
FAIL_SEND_REQCALCIMPLIEDVOLAT = error(534, 'Request Calculate Implied '
                                      'Volatility Sending Error - ')
FAIL_SEND_REQCALCOPTIONPRICE = error(535, 'Request Calculate Option Price '
                                     'Sending Error - ')
FAIL_SEND_CANCALCIMPLIEDVOLAT = error(536, 'Cancel Calculate Implied '
                                      'Volatility Sending Error - ')
FAIL_SEND_CANCALCOPTIONPRICE = error(537, 'Cancel Calculate Option Price '
                                     'Sending Error - ');

