#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''File to listen to a TWS server datastream'''


import mypy
import tws
import TWSClientServerMessages as M

not_implemented = 'work in progress'
C = tws.def_contract()
CD = tws.def_details()
O = tws.def_order(0)
EXE = tws.def_execution()

def listen(TWSConn, message_queue, logger):

    while True:
        server_mess = TWSConn.read_int()
        if server_mess in valid_messages:
            last_valid_server_mess = server_mess
            if message_handler[server_mess] is not_implemented:
                logger.warning('{} not implemented'.format(server_mess))
                continue
            answer = message_handler[server_mess](TWSConn)
            for line in answer:
                message_queue.put(line)
        else:
            logger.error('unknown message {} last handeled message {}'.
                         format(server_mess, last_valid_server_mess))


def tick_price(TWSConn):

    # tr is used to remap tick type to size tick type
    # check jave TickType file
    # eg: 2 (ask) --->  3 (ask_size)
    tr = {1: 0, 2: 3, 4: 5}
    message = []
    version = TWSConn.read_int()
    ticker_id = TWSConn.read_int()
    tick_type = TWSConn.read_int()
    price = TWSConn.read_float()
    size = TWSConn.read_int() if version >= 2 else 0
    can_auto_execute = TWSConn.read_bool() if version >= 3 else 0
    message.append(M.TickPrice(ticker_id, 
                               M.tick_type[tick_type],
                               price, 
                               can_auto_execute))
    if version >= 2 and tick_type in tr:
        message.append(M.TickSize(ticker_id,
                                  M.tick_type[tr[tick_type]], 
                                  size))
    return message


def tick_size(TWSConn):

    version = TWSConn.read_int()
    message = M.TickSize(id_=TWSConn.read_int(),
                         type_=M.tick_type[TWSConn.read_int()],
                         size=TWSConn.read_int())
    return [message]

    
def tick_option_computation(TWSConn):

    version = TWSConn.read_int()
    ticker_id = TWSConn.read_int()
    tick_type = TWSConn.read_int()
    t = TWSConn.read_float()
    implied_volume = t if t >= 0 else None
    t = TWSConn.read_float()
    delta = t if t*t <= 1 else None
    if version >= 6:
        t = TWSConn.read_float()
        opt_price = t if t >= 0 else None
        t = TWSConn.read_float()
        pv_dividend = t if t >= 0 else None
        t = TWSConn.read_float()
        gamma = t if t*t <= 1 else None
        t = TWSConn.read_float()
        vega = t if t*t <= 1 else None
        t = TWSConn.read_float()
        theta = t if t*t <= 1 else None
        t = TWSConn.read_float()
        und_price = t if t >= 0 else None
    else:
        opt_price = pvDivident = gamma = vega = theta = undPrice = None
    message = M.TickOptionComputation(ticker_id, tick_type, implier_volume,
                                      delta, opt_price, pv_dividend,
                                      gamma, vega, theta, und_price)
    return [message]

def tick_generic(TWSConn):

    version = TWSConn.read_int()
    message = M.TickGeneric(id_=TWSConn.read_int(),
                            type_=M.tick_type[TWSConn.read_int()],
                            value=TWSConn.read_float())
    return [message]


def tick_string(TWSConn):

    version = TWSConn.read_int()
    message = M.TickString(id_=TWSConn.read_int(),
                           type_=M.tick_type[TWSConn.read_int()],
                           value=TWSConn.read_str())
    return [message]


def tick_EFP(TWSConn):
    
    version = TWSConn.read_int()
    message = M.TickEFP(id_=TWSConn.read_int(),
                        type_=TWSConn.read_int(),
                        basis_points=TWSConn.read_float(),
                        formatted_basis_points=TWSConn.read_str(),
                        implied_futures_price=TWSConn.read_float(),
                        hold_days=TWSConn.read_int(),
                        future_expiry=TWSConn.read_str(),
                        dividend_impact=TWSConn.read_float(),
                        dividends_to_expiry=TWSConn.read_float())
    return [message]


def order_status(TWSConn):
    
    version = TWSConn.read_int()
    order_id = TWSConn.read_int()
    status = TWSConn.read_str()
    filled = TWSConn.read_int()
    remaining = TWSConn.read_int()
    avg_fill_price = TWSConn.read_float()
    perm_id = TWSConn.read_int() if version >= 2 else 0
    parent_id = TWSConn.read_int() if version >= 3 else 0
    last_fill_price = TWSConn.read_float() if version >= 4 else 0
    client_id = TWSConn.read_int() if version >= 5 else 0
    why_held = TWSConn.read_str() if version >= 6 else None
    message = M.OrderStatus(order_id, status, filled, remaining, 
                            avg_fill_price, perm_id, parent_id,
                            last_fill_price, client_id, why_held)
    return [message]


def account_value(TWSConn):
    
    version = TWSConn.read_int()
    key = TWSConn.read_str()
    value = TWSConn.read_str()
    currency = TWSConn.read_str()
    account_name = TWSConn.read_str() if version >= 2 else None
    message = M.UpdateAccountValue(key, value, currency, account_name)
    return [message]


def portfolio_value(TWSConn):

    version = TWSConn.read_int()
    #read contract data
    con_id = TWSConn.read_int() if version >= 6 else C.conId
    symbol = TWSConn.read_str()
    sec_type = TWSConn.read_str()
    expiry = TWSConn.read_str()
    strike = TWSConn.read_float()
    right = TWSConn.read_str()
    multiplier = TWSConn.read_str() if version >= 7 else C.multiplier
    primary_exch = TWSConn.read_str() if version >= 7 else C.primaryExch
    currency = TWSConn.read_str()
    local_symbol = TWSConn.read_str() if version >= 2 else C.localSymbol
    contract = tws.def_contract(conId=con_id, symbol=symbol,
                                secType=sec_type, expiry=expiry,
                                strike=strike, right=right,
                                multiplier=multiplier,
                                primaryExch=primary_exch,
                                currency=currency,
                                localSymbol=local_symbol)
    ###
    position = TWSConn.read_int()
    market_price = TWSConn.read_float()
    market_value = TWSConn.read_float()
    average_cost = TWSConn.read_float() if version >= 3 else 0
    unrealised_PNL = TWSConn.read_float() if version >= 3 else 0
    realised_PNL = TWSConn.read_float() if version >= 3 else 0
    account_name = TWSConn.read_str() if version >= 4 else None
    message = M.PortfolioValue(contract, position, market_price,
                               market_value, average_cost,
                               unrealised_PNL, realised_PNL,
                               account_name)
    return [message]


def update_account_time(TWSConn):

    version = TWSConn.read_int()
    time_=mypy.py_time(TWSConn.read_str(),'%H:%M')
    message = M.UpdateAccountTime(time_)
    return [message]
                  

def process_error_message(TWSConn):

    version = TWSConn.read_int()
    if version < 2:
        message = M.Error(None, None, 
                          message=socket.read_str())
    else:
        message = M.Error(id_=TWSConn.read_int(),
                          code=TWSConn.read_int(),
                          message=TWSConn.read_str())
    return [message]


def open_order(TWSConn):
    
    version = TWSConn.read_int()
    order_id = TWSConn.read_int()
    #read contract data
    con_id = TWSConn.read_int() if version >=17 else C.conId
    symbol = TWSConn.read_str()
    sec_type = TWSConn.read_str()
    expiry = TWSConn.read_str()
    strike = TWSConn.read_float()
    right = TWSConn.read_str()
    exchange = TWSConn.read_str()
    currency = TWSConn.read_str()
    local_symbol = TWSConn.read_str() if version >= 2 else C.localSymbol
    #read order data
    action = TWSConn.read_str()
    total_quantity = TWSConn.read_int()
    order_type = TWSConn.read_str()
    lmt_price = TWSConn.read_float()
    aux_price = TWSConn.read_float()
    tif = TWSConn.read_str()
    oca_group = TWSConn.read_str()
    account = TWSConn.read_str()
    open_close = TWSConn.read_str()
    origin = TWSConn.read_int()
    order_ref = TWSConn.read_str()
    client_id = TWSConn.read_int() if version >= 3 else O.clientId
    perm_id = TWSConn.read_int() if version >= 4 else O.permId
    outside_RTH = TWSConn.read_bool() if version >= 4 else O.outsideRth
    hidden = TWSConn.read_bool() if version >= 4 else O.hidden
    discretionary_AMT = TWSConn.read_float() if version >= 4 else O.discretionaryAmt
    good_after_time = TWSConn.read_str() if version >=5 else O.goodAfterTime 
    if version >= 6:
        TWSConn.read_str()
    fa_group = TWSConn.read_str() if version >=7 else O.faGroup
    fa_method = TWSConn.read_str() if version >=7 else O.faMethod
    fa_percentage = TWSConn.read_str() if version >=7 else O.faPercentage
    fa_profile = TWSConn.read_str() if version >=7 else O.faProfile
    good_till_date = TWSConn.read_str() if version >= 8 else O.goodTillDate
    rule_80A = TWSConn.read_str() if version >= 9 else O.rule80A
    percent_offset = TWSConn.read_float() if version >= 9 else O.percentOffset
    settling_firm = TWSConn.read_str() if version >= 9 else O.settlingFirm
    short_sale_slot = TWSConn.read_int() if version >= 9 else O.shortSaleSlot
    des_loc = TWSConn.read_str() if version >= 9 else O.designatedLocation
    auction_strategy = TWSConn.read_int() if version >= 9 else O.auctionStrategy
    starting_price = TWSConn.read_float() if version >= 9 else O.startPrice
    stock_ref_price = TWSConn.read_float() if version >= 9 else O.stockRefPrice
    delta = TWSConn.read_float() if version >= 9 else O.delta
    stk_rng_lower = TWSConn.read_float() if version >= 9 else O.stockRangeLower
    stk_rng_upper = TWSConn.read_float() if version >= 9 else O.stockRangeUpper
    display_size = TWSConn.read_int() if version >= 9 else O.displaySize
    block_order = TWSConn.read_bool() if version >= 9 else O.blockOrder
    sweep_to_fill = TWSConn.read_bool() if version >= 9 else O.sweepToFill
    all_or_none = TWSConn.read_bool() if version >= 9 else O.allOrNone
    min_quantity = TWSConn.read_int() if version >= 9 else O.minQty
    oca_type = TWSConn.read_int() if version >= 9 else O.ocaType
    e_trade_only = TWSConn.read_bool() if version >= 9 else O.eTradeOnly
    firm_quote_only = TWSConn.read_bool() if version >= 9 else O.firmQuoteOnly
    nbbo_price_cap = TWSConn.read_float() if version >= 9 else O.nbboPriceCap
    parent_id  = TWSConn.read_int() if version >=10 else O.parentId
    trigger_method = TWSConn.read_int() if version >= 10 else O.triggerMethod
    volatility = TWSConn.read_float()
    volatility_type = TWSConn.read_int()
    if version == 11:
        t = TWSConn.read_int()
        d_n_ot = 'NONE' if t == 0 else 'MKT'
        d_n_ap = O.deltaNeutralAuxPrice
    else:
        d_n_ot = TWSConn.read_str() if version >=11 else O.deltaNeutralOrderType
        d_n_ap = TWSConn.read_float() if version >= 11 else O.deltaNeutralAuxPrice
    continuous_update = TWSConn.read_int() if version >= 11 else O.continuousUpdate
    reference_price_type = TWSConn.read_int() if version >= 11 else O.referencePriceType
    trail_stop_price = TWSConn.read_float() if version >= 13 else O.trailStopPrice
    basis_points = TWSConn.read_float() if version >= 14 else O.basisPoints
    basis_points_type = TWSConn.read_int() if version >= 14 else O.basisPointsType
    combo_legs_descrip = TWSConn.read_str() if version >= 14 else C.comboLegsDescrip
    scale_i_l_s = TWSConn.read_int() if version >= 15 else O.scaleInitLevelSize
    scale_s_l_s = TWSConn.read_int() if version >= 20 else O.scaleSubsLelelSize
    scale_p_i = TWSConn.read_float() if version >= 15 else O.scalePriceIncrement
    clearing_account = TWSConn.read_str() if version >= 19 else O.clearingAccount
    clearing_intent = TWSConn.read_str() if version >= 19 else O.clearingIntent
    not_held = TWSConn.read_bool() if version >=22 else O.notHeld
    if version >= 20 and TWSConn.read_bool():
        uc_con_id = TWSConn.read_int()
        uc_delta = TWSConn.read_float()
        uc_price = TWSConn.read_float()
        under_comp = tws.def_under_comp(uc_con_id, uc_delta, uc_price)
    else:
        under_comp = None
    if version >= 21:
        algo_strategy = TWSConn.read_str()
        #print('algo_strategy: ',algo_strategy)
        algo_params = []
        if algo_strategy:
            for count in range(TWSConn.read_int()):
                algo_params.append(tagValue(TWSConn.read_str(),
                                            TWSConn.read_str()))
    else:
        algo_strategy = O.algoStrategy
        algo_params = O.algoParams
    what_if = TWSConn.read_bool() if version >= 16 else O.whatIf
    if version >= 16:
        order_state = tws.orderState(TWSConn.read_str(),
                                     TWSConn.read_str(),
                                     TWSConn.read_str(),
                                     TWSConn.read_str(),
                                     TWSConn.read_float(),
                                     TWSConn.read_float(),
                                     TWSConn.read_float(),
                                     TWSConn.read_str(),
                                     TWSConn.read_str())
    else:
        order_state = None
    contract = tws.def_contract(symbol=symbol, 
                                secType=sec_type,
                                expiry=expiry, 
                                strike=strike,
                                right=right,
                                exchange=exchange,
                                currency=currency,
                                localSymbol=local_symbol,
                                comboLegsDescrip=combo_legs_descrip,
                                conId=con_id,
                                underComp=under_comp)
    order = tws.def_order(orderId=order_id,
                          clientId=client_id,
                          permId=perm_id,
                          action=action,
                          totalQuantity= total_quantity,
                          orderType=order_type,
                          lmtPrice=lmt_price,
                          auxPrice=aux_price,
                          tif=tif,
                          ocaGroup=oca_group,
                          ocaType=oca_type,
                          orderRef=order_ref,
                          parentId=parent_id,
                          blockOrder=block_order,
                          sweepToFill=sweep_to_fill,
                          displaySize=display_size,
                          triggerMethod=trigger_method,
                          outsideRth=outside_RTH,
                          hidden=hidden,
                          goodAfterTime=good_after_time,
                          goodTillDate=good_till_date,
                          rule80A=rule_80A,
                          allOrNone=all_or_none,
                          minQty=min_quantity,
                          percentOffset=percent_offset,
                          trailStopPrice=trail_stop_price,
                          faGroup=fa_group,
                          faProfile=fa_profile,
                          faMethod=fa_method,
                          faPercentage=fa_percentage,
                          openClose=open_close,
                          origin=origin,
                          shortSaleSlot=short_sale_slot,
                          designatedLocation=des_loc,
                          discretionaryAmt=discretionary_AMT,
                          eTradeOnly=e_trade_only,
                          firmQuoteOnly=firm_quote_only,
                          nbboPriceCap=nbbo_price_cap,
                          auctionStrategy=auction_strategy,
                          startingPrice=starting_price,
                          stockRefPrice=stock_ref_price,
                          delta=delta,
                          stockRangeLower=stk_rng_lower,
                          stockRangeUpper=stk_rng_upper,
                          volatility=volatility,
                          volatilityType=volatility_type,
                          continuousUpdate=continuous_update,
                          referencePriceType=reference_price_type,
                          deltaNeutralOrderType=d_n_ot,
                          deltaNeutralAuxPrice=d_n_ap,
                          basisPoints=basis_points,
                          basisPointsType=basis_points_type,
                          scaleInitLevelSize=scale_i_l_s,
                          scaleSubsLevelSize=scale_s_l_s,
                          scalePriceIncrement=scale_p_i,
                          account=account,
                          settlingFirm=settling_firm,
                          clearingAccount=clearing_account,
                          clearingIntent=clearing_intent,
                          algoStrategy=algo_strategy,
                          algoParams=algo_params,
                          whatIf=what_if,
                          notHeld=not_held)
    message = M.OpenOrder(order.orderId, contract, order, order_state)
    return [message]


def next_valid_id(TWSConn):

    version = TWSConn.read_int()
    message = M.NextValidId(order_id=TWSConn.read_int())
    return [message]

def scanner_data(TWSConn):

    message = []
    version = TWSConn.read_int()
    ticker_id = TWSConn.read_int()
    number_of_ellements = TWSConn.read_int()
    for i in range(number_of_ellements):
        rank = TWSConn.read_int()
        con_id = TWSConn.read_int() if version >= 3 else C.conId
        symbol = TWSConn.read_str()
        sec_type = TWSConn.read_str()
        expiry = TWSConn.read_str()
        strike = TWSConn.read_float()
        right = TWSConn.read_str()
        exchange = TWSConn.read_str()
        currency = TWSConn.read_str()
        local_symbol = TWSConn.read_str()
        market_name = TWSConn.read_str()
        trading_class = TWSConn.read_str()
        distance = TWSConn.read_str()
        benchmark = TWSConn.read_str()
        projection = TWSConn.read_str()
        legs_str = TWSConn.read_str() if version >= 2 else None
        base_contract = tws.def_contract(conId=con_id,
                                         symbol=symbol,
                                         secType=sec_type,
                                         expiry=expiry,
                                         strike=strike,
                                         right=right,
                                         exchange=exchange,
                                         currency=currency,
                                         localSymbol=local_symbol)
        full_contract = tws.def_contract_details(summary=base_contract,
                                                 marketName=market_name,
                                                 tradingClass=trading_class)
        message.append(M.ScannerData(ticker_id, rank, full_contract, distance,
                                     benchmark, projection, legs_str))
    message.append(M.ScannerDataEnd(ticker_id))
    return message


def contract_data(TWSConn):

    version = TWSConn.read_int()
    request_id = TWSConn.read_int() if version >= 3 else -1
    symbol = TWSConn.read_str()
    sec_type = TWSConn.read_str()
    expiry = TWSConn.read_str()
    strike = TWSConn.read_float()
    right = TWSConn.read_str()
    exchange = TWSConn.read_str()
    currency = TWSConn.read_str()
    local_symbol = TWSConn.read_str()
    market_name = TWSConn.read_str()
    trading_class = TWSConn.read_str()
    con_id = TWSConn.read_int()
    min_tick = TWSConn.read_float()
    multiplier = TWSConn.read_str()
    order_types = TWSConn.read_str()
    valid_exchanges = TWSConn.read_str()
    price_magnifier = TWSConn.read_int() if version >=2 else CD.priceMagnifier
    under_con_id = TWSConn.read_int() if version >= 4 else CD.underConId
    long_name = TWSConn.read_str() if version >= 5 else CD.longName
    primary_exch = TWSConn.read_str() if version >= 5 else C.primaryExch
    contract_month = TWSConn.read_str() if version >= 6 else CD.contractMonth
    industry = TWSConn.read_str() if version >= 6 else CD.industry
    category = TWSConn.read_str() if version >= 6 else CD.category
    sub_category = TWSConn.read_str() if version >= 6 else CD.subCategory
    time_zone_id = TWSConn.read_str() if version >= 6 else CD.timeZoneId
    trading_hours = TWSConn.read_str() if version >= 6 else CD.tradingHours
    liquid_hours = TWSConn.read_str() if version >= 6 else CD.liquidHours
    base_contract = tws.def_contract(symbol=symbol,
                                     secType=sec_type,
                                     expiry=expiry,
                                     strike=strike,
                                     right=right,
                                     exchange=exchange,
                                     currency=currency,
                                     localSymbol=local_symbol,
                                     conId=con_id,
                                     multiplier=multiplier,
                                     primaryExch=primary_exch)
    full_contract = tws.def_details(summary=base_contract,
                                    marketName=market_name,
                                    tradingClass=trading_class,
                                    minTick=min_tick,
                                    orderTypes=order_types,
                                    validExchanges=valid_exchanges,
                                    priceMagnifier=price_magnifier,
                                    underConId=under_con_id,
                                    longName=long_name,
                                    contractMonth=contract_month,
                                    industry=industry,
                                    category=category,
                                    subcategory=sub_category,
                                    timeZoneId=time_zone_id,
                                    tradingHours=trading_hours,
                                    liquidHours=liquid_hours)
    message = M.ContractDetails(request_id, full_contract) 
    return [message]


def bond_contract_data(TWSConn):

    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int() if version >= 3 else -1
    symbol = TWSConn.read_str()
    sec_type = TWSConn.read_str()
    cusip = TWSConn.read_str()             
    coupon = TWSConn.read_float()         
    maturity = TWSConn.read_str()          
    issue_date  = TWSConn.read_str()        
    ratings = TWSConn.read_str()           
    bond_type = TWSConn.read_str()          
    coupon_type = TWSConn.read_str()        
    convertible = readBoolFromInt()
    callable_ = TWSConn.read_bool()
    putable = TWSConn.read_bool()
    desc_append = TWSConn.read_str()        
    exchange = TWSConn.read_str()
    currency = TWSConn.read_str()
    market_name = TWSConn.read_str()        
    trading_class = TWSConn.read_str()      
    con_id = TWSConn.read_int()   
    min_tick = TWSConn.read_float()        
    order_types = TWSConn.read_str()        
    validExchanges = TWSConn.read_str()
    next_o_d = TWSConn.read_str() if version >= 2 else CD.nextOptionDate
    next_o_t = TWSConn.read_str() if version >= 2 else CD.nextOptionType
    next_o_p = TWSConn.read_bool() if version >= 2 else CD.nextOptionPartial 
    notes = TWSConn.read_str() if version >= 2 else CD.notes
    long_name = TWSConn.read_str() if version >=4 else CD.longName
    base_contract = tws.def_contract(symbol=symbol,
                                     secType=sec_type,
                                     exchange=exchange,
                                     currency=currency,
                                     conId=con_id)
    full_contract = tws.def_details(summary=base_contract,
                                    marketName=market_name,
                                    tradingClass=trading_class,
                                    minTick=min_tick,
                                    orderTypes=order_types,
                                    validExchanges=valid_exchanges,
                                    longName=long_name,
                                    cusip=cusip,
                                    coupon=coupon,
                                    maturity=maturity,
                                    issueDate=issue_date,
                                    ratings=ratings,
                                    bondType=bond_type,
                                    couponType=couponType,
                                    convertible=convertible,
                                    callable_=callable_,
                                    putable=putable,
                                    descAppend=desc_append,
                                    nextOptionDate=next_o_d,
                                    nextOptionType=next_o_t,
                                    nextOptionPartial=naxt_o_p,
                                    notes=notes)
    message.append(M.BondContractData(request_id, full_contract))
    return message
    

def execution_data(TWSConn):
                       
    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int() if version >= 7 else -1
    order_id = TWSConn.read_int()
    con_id = TWSConn.read_int() if version >=5 else C.conId
    symbol = TWSConn.read_str()
    sec_type = TWSConn.read_str()
    expiry = TWSConn.read_str()
    strike = TWSConn.read_float()
    right = TWSConn.read_str()
    exchange = TWSConn.read_str()
    currency = TWSConn.read_str()
    local_symbol = TWSConn.read_str()
    exec_id = TWSConn.read_str()
    time_ = TWSConn.read_str()     
    acct_number = TWSConn.read_str()
    exchange = TWSConn.read_str()
    side = TWSConn.read_str()
    shares = TWSConn.read_int()
    price = TWSConn.read_float()
    perm_id = TWSConn.read_int() if version >= 2 else EXE.permId
    client_id = TWSConn.read_int() if version >= 3 else EXE.clientId
    liquidation = TWSConn.read_int() if version >= 4 else EXE.liquidation
    cum_quantity = TWSConn.read_int() if version >= 6 else EXE.cumQty
    avg_price = TWSConn.read_float() if version >= 6 else EXE.avgPrice
    contract = tws.def_contract(symbol=symbol,
                                secType=sec_type,
                                expiry=expiry,
                                strike=strike,
                                right=right,
                                exchange=exchange,
                                currency=currency,
                                localSymbol=local_symbol)
    execution = tws.def_execution(orderId=order_id,
                                  clientId=client_id,
                                  execId=exec_id,
                                  time_=time_,
                                  acctNumber=acct_number,
                                  exchange=exchange,
                                  side=side,
                                  shares=shares,
                                  price=price,
                                  permId=perm_id,
                                  liquidation=liquidation,
                                  cumQty=cum_quantity,
                                  avgPrice=avg_price)
    message.append(M.ExecDetails(request_id, contract, execution))
    return message


def market_depth(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    id_ = TWSConn.read_int()
    position = TWSConn.read_int()
    operation = TWSConn.read_int()
    side = TWSConn.read_int()
    price = TWSConn.read_float()
    size = TWSConn.read_int()
    message.append(M.UpdateMktDepth(id_, position, operation, side, 
                                    price, size))
    return message


def market_depth_l2(TWSConn):

    version = TWSConn.read_int()
    message = []
    id_ = TWSConn.read_int()
    position = TWSConn.read_int()
    market_maker = TWSConn.read_str()
    operation = TWSConn.read_int()
    side = TWSConn.read_int()
    price = TWSConn.read_float()
    size = TWSConn.read_int()
    message.append(M.UpdateMktDepth(id_, position, market_maker, operation, 
                                    side, price, size))
    return message


def news_bulletins(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    msg_id = TWSConn.read_int()
    msg_type = TWSConn.read_int()
    n_message = TWSConn.read_str()
    originating_exch = TWSConn.read_str()
    message.append(M.UpdateNewsBuletin(msg_id, msg_type, n_message, 
                                       originating_exch))
    return message
                   
    
def managed_accounts(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    account_list = TWSConn.read_str()
    message.append(M.ManagedAccounts(account_list))
    return message


def receive_fa(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    fa_data_type = TWSConn.read_int()
    xml = TWSConn.read_str()
    message.append(M.ReceiveFA(fa_data_type, xml))
    return message


def historical_data(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int()
    start_date_str = TWSConn.read_str() if version >= 2 else 'start'
    end_date_str = TWSConn.read_str() if version >= 2 else 'stop'
    completed_indicator = 'READY'
    number_of_items = TWSConn.read_int()
    for i in range(number_of_items):
        date_ = TWSConn.read_str()
        open_ = TWSConn.read_float()
        high = TWSConn.read_float()
        low = TWSConn.read_float()
        close = TWSConn.read_float()
        volume = TWSConn.read_int()
        wap = TWSConn.read_float()
        has_gaps = False if TWSConn.read_str() == 'false' else True
        bar_count = TWSConn.read_int() if version >= 3 else -1
        message.append(M.HistoricalData(request_id, date_, open_, high, low,
                                        close, volume, bar_count, wap, 
                                        has_gaps))
    message.append(M.HistoricalData(request_id, completed_indicator,
                                   open_, high, low, close, volume,
                                   bar_count, wap, has_gaps))
    return message
        

def scanner_parameters(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    xml = TWSConn.read_str()
    message.append(M.ScannerParameters(xml))
    return message

                  
def current_time(TWSConn):

    version = TWSConn.read_int()
    message = M.CurrentTime(time_=TWSConn.read_date(format='EPOCH'))
    return [message]


def real_time_bars(TWSConn):

    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int()
    time_ = mypy.epoch2date_time(TWSConn.read_int())
    open_ = TWSConn.read_float()
    high = TWSConn.read_float()
    low = TWSConn.read_float()
    close = TWSConn.read_float()
    volume = TWSConn.read_int()
    wap = TWSConn.read_float()
    count = TWSConn.read_int()
    message.append(M.RealTimeBars(request_id, time_, open_, high, low,
                                  close, volume, wap, count))
    return message


def fundamental_data(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int()
    data = TWSConn.read_str()
    message.append(M.FundamentalData(request_id, data))
    return message


def contract_data_end(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int()
    message.append(M.ContractDetailsEnd(request_id))
    return message


def acct_download_end(TWSConn):

    version = TWSConn.read_int()
    message = []
    account_name = TWSConn.read_str()
    message.append(M.AccountDownloadEnd(account_name))
    return message


def execution_data_end(TWSConn):

    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int()
    message.append(M.ExecutionDetailsEnd(request_id))
    return message


def delta_neutral_validation(TWSConn):
    
    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int()
    con_id = TWSConn.read_int()
    delta = TWSConn.read_float()
    price = TWSConn.read_float()
    under_comp = tws.def_under_comp(con_id, delta, price)
    message.append(M.DeltaNeutralValidation(request_id, under_comp))
    return message  


def tick_snapshot_end(TWSConn):

    version = TWSConn.read_int()
    message = []
    request_id = TWSConn.read_int()
    message.append(M.TickSnapshotEnd(request_id))
    return message
    

def open_order_end(TWSConn):

    version = TWSConn.read_int()
    message = [M.OpenOrderEnd()]
    return message


message_handler = {M.TICK_PRICE: tick_price, 
                   M.TICK_SIZE: tick_size, 
                   M.ORDER_STATUS: order_status, 
                   M.ERR_MSG: process_error_message, 
                   M.OPEN_ORDER: open_order, 
                   M.ACCT_VALUE: account_value, 
                   M.PORTFOLIO_VALUE: portfolio_value, 
                   M.ACCT_UPDATE_TIME: update_account_time, 
                   M.NEXT_VALID_ID: next_valid_id, 
                   M.CONTRACT_DATA: contract_data, 
                   M.EXECUTION_DATA: execution_data, 
                   M.MARKET_DEPTH: market_depth,
                   M.MARKET_DEPTH_L2: market_depth_l2,
                   M.NEWS_BULLETINS: news_bulletins, 
                   M.MANAGED_ACCTS: managed_accounts,
                   M.RECEIVE_FA: receive_fa, 
                   M.HISTORICAL_DATA: historical_data, 
                   M.BOND_CONTRACT_DATA: bond_contract_data, 
                   M.SCANNER_PARAMETERS: scanner_parameters, 
                   M.SCANNER_DATA: scanner_data, 
                   M.TICK_OPTION_COMPUTATION: tick_option_computation, 
                   M.TICK_GENERIC: tick_generic, 
                   M.TICK_STRING: tick_string, 
                   M.TICK_EFP: tick_EFP, 
                   M.CURRENT_TIME: current_time, 
                   M.REAL_TIME_BARS: real_time_bars, 
                   M.FUNDAMENTAL_DATA: fundamental_data, 
                   M.CONTRACT_DATA_END: contract_data_end, 
                   M.OPEN_ORDER_END: open_order_end, 
                   M.ACCT_DOWNLOAD_END: acct_download_end, 
                   M.EXECUTION_DATA_END: execution_data_end, 
                   M.DELTA_NEUTRAL_VALIDATION: delta_neutral_validation, 
                   M.TICK_SNAPSHOT_END: tick_snapshot_end}

valid_messages = message_handler.keys()


        
    



