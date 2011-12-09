#!/usr/bin/env python
#
#  Copyright 2011 Tjerk Santegoeds
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import threading

from datetime import datetime

from ._types import Currency, EventType, BFEvent, MarketSummary, CouponLink, Event
from ._util import uncompress_market_prices, uncompress_markets, not_implemented
from ._soap import *


__all__ = [
    "ServiceError", "Session", "FREE_API"
]


class ServiceError(Exception):
    pass


FREE_API = 82


class HeartBeat(threading.Thread):

    def __init__(self, keepalive_func, interval = 19):
        super(HeartBeat, self).__init__()
        self.daemon = True
        self.event = threading.Event()
        self.interval = interval
        self.keepalive_func = keepalive_func
        self.tstamp = None

    def run(self):
        self.tstamp = datetime.now()
        while True:
            time_out = float(self.interval - self.elapsed_mins())
            self.event.wait(time_out)
            if self.event.is_set(): break
            if self.elapsed_mins() > self.interval:
                self.keepalive_func()
                self.reset()

    def elapsed_mins(self):
        return (datetime.now() - self.tstamp).seconds / 60

    def reset(self):
        self.tstamp = datetime.now()

    def stop(self):
        self.event.set()
        self.join()


class Session(object):
    """
    """

    def __init__(self, username, password, product_id=FREE_API, vendor_id=0):
        super(Session, self).__init__()
        self._request_header = BFGlobalFactory.create("ns1:APIRequestHeader")
        self._request_header.clientStamp = 0
        self._heartbeat = None
        self.username = username
        self.password = password
        self.product_id = product_id
        self.vendor_id = 0

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, type, value, traceback):
        if self._request_header.sessionToken is not None:
            self.logout();

    def login(self):
        """Login and establish a secure session.
        """
        req = BFGlobalFactory.create("ns1:LoginReq")
        req.username = self.username
        req.password = self.password
        req.productId = self.product_id
        req.vendorSoftwareId = self.vendor_id
        req.ipAddress = 0
        req.locationId = 0
        rsp = self._soapcall(BFGlobalService.login, req)
        if rsp.errorCode != APIErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == APIErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            raise ServiceError(error_code)
        self._heartbeat = HeartBeat(self.keep_alive)
        self._heartbeat.start()

    def logout(self):
        if self._heartbeat:
            self._heartbeat.stop()
        self._heartbeat = None
        BFGlobalService.logout(self._request_header)
        self._request_header.sessionToken = None

    def is_active(self):
        return self._heartbeat is not None

    def keep_alive(self):
        req = BFGlobalFactory.create("ns1:KeepAliveReq")
        rsp = self._soapcall(BFGlobalService.keepAlive, req)
        if rsp.header.errorCode != APIErrorEnum.OK:
            raise ServiceError(rsp.header.errorCode)

    def get_event_types(self, active=True, locale=None):
        """
        Returns a list of all categories of sporting events.

        active : `bool`
            If `True` then only events that have at least one
            market available to bet on are returned.
        """
        req = BFGlobalFactory.create("ns1:GetEventTypesReq")
        if locale: req.locale = locale
        func = BFGlobalService.getActiveEventTypes \
                if active else BFGlobalService.getAllEventTypes
        rsp = self._soapcall(func, req)
        if rsp.errorCode == GetEventsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode not in (GetEventsErrorEnum.OK, GetEventsErrorEnum.NO_RESULTS):
            raise ServiceError(rsp.errorCode)
        event_types = [EventType(*[T[1] for T in e]) for e in rsp.eventTypeItems[0]]
        return event_types

    def get_events(self, parent_id, locale=None):
        req = BFGlobalFactory.create("ns1:GetEventsReq")
        req.eventParentId = int(parent_id)
        if locale:
            req.locale = locale
        rsp = self._soapcall(BFGlobalService.getEvents, req)
        if rsp.errorCode == GetEventsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode not in (GetEventsErrorEnum.OK, GetEventsErrorEnum.NO_RESULTS):
            raise ServiceError(rsp.errorCode)
        rsp = [
            [BFEvent(*[T[1] for T in e]) for e in rsp.eventItems[0]] if rsp.eventItems else [],
            rsp.eventParentId,
            [MarketSummary(*[T[1] for T in s]) for s in rsp.marketItems[0]] if rsp.marketItems else [],
            [CouponLink(*[T[1] for T in l]) for l in rsp.couponLinks[0]] if rsp.couponLinks else [],
        ]
        return Event(*rsp)

    def get_currencies(self, v2=True):
        if self.product_id == FREE_API:
            raise ServiceError("Free API does not support get_currencies")
        if v2:
            req = BFGlobalFactory.create("ns1:GetCurrenciesV2Req")
            srv = BFGlobalService.getAllCurrenciesV2
        else:
            req = BFGlobalFactory.create("ns1:GetCurrenciesReq")
            srv = BFGlobalService.getAllCurrencies
        rsp = self._soapcall(srv, req)
        if rsp.header.errorCode != APIErrorEnum.OK:
            raise ServiceError(rsp.header.errorCode)
        return [Currency(*c) for c in rsp.currencyItems[0]]

    def convert_currency(self, amount, from_currency, to_currency):
        if self.product_id == FREE_API:
            raise ServiceError("Free API does not support convert_currency")
        req = BFGlobalFactory.create("ns1:ConvertCurrencyReq")
        req.amount = amount
        req.fromCurrency = from_currency
        req.toCurrency = to_currency
        rsp = self._soapcall(BFGlobalService.convertCurrency, req)
        if rsp.errorCode == ConvertCurrencyErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        elif rsp.errorCode != ConvertCurrencyErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        return rsp.convertedAmount

    def get_bet(self, id, lite=True):
        req = BFGlobalFactory.create("ns1:GetBetLiteReq") \
                if lite else BFGlobalFactory.create("ns1:GetBetReq")
        req.betId = id
        func = BFExchangeService.getBetLite \
                if lite else BFExchangeService.getBet
        rsp = self._soapcall(func, req)
        if rsp.errorCode != GetBetErrorEnum.OK:
            raise ServiceError(rsp.header.errorCode)
        if lite:
            attrs = ["betCategoryType", "betId", "betPersistencType", "betStatus",
                     "bspLiability", "marketId", "matchedSize", "remainingSize"]
            bet = Bet(**{k: v for k, v in izip(attrs, rsp.betlite)})
        else:
            bet = Bet(*rsp.bet)
        return bet

    @not_implemented
    def cancel_bets(self):
        pass

    @not_implemented
    def cancel_bets_by_market(self):
        pass

    @not_implemented
    def place_bets(self):
        pass

    @not_implemented
    def update_bets(self):
        pass

    @not_implemented
    def get_bet_history(self):
        pass

    @not_implemented
    def get_bet_matches_lite(self):
        pass

    @not_implemented
    def get_current_bets(self):
        pass

    @not_implemented
    def get_current_bets_lite(self):
        pass

    @not_implemented
    def get_matched_and_unmatched_bets(self):
        pass

    @not_implemented
    def get_market_profit_loss(self):
        pass

    @not_implemented
    def get_market_traded_volume(self):
        pass

    @not_implemented
    def get_market_traded_volume_compressed(self):
        pass

    @not_implemented
    def get_private_markets(self):
        pass

    @not_implemented
    def get_silks(self):
        pass

    @not_implemented
    def get_sliks_v2(self):
        pass

    def get_inplay_markets(self, locale=None):
        if self.product_id == FREE_API:
            raise ServiceError("Free API does not support get_inplay_markets")
        req = BFExchangeFactory.create("ns1:GetInPlayMarketsReq")
        if locale: req.locale = locale
        rsp = self._soapcall(BFExchangeService.getInPlayMarkets, req)
        if rsp.errorCode == GetInPlayMarketsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetInPlayMarketsErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        return uncompress_markets(rsp.marketData)

    def get_markets(self, event_ids=None, countries=None, date_range=None):
        req = BFExchangeFactory.create("ns1:GetAllMarketsReq")
        if event_ids:
            req.eventTypeIds[0].extend(list(iter(event_ids)))
        if countries:
            req.countries[0].extend(list(iter(countries)))
        if date_range:
            req.fromDate = date_range[0]
            if len(date_range) > 1:
                req.toDate = date_range.end[-1]
        rsp = self._soapcall(BFExchangeService.getAllMarkets, req)
        if rsp.errorCode == GetAllMarketsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetAllMarketsErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        markets = uncompress_markets(rsp.marketData)
        return markets

    @not_implemented
    def get_market_info(self):
        pass

    def get_market_prices(self, market_id, currency=None):
        req = BFExchangeFactory.create("ns1:GetMarketPricesCompressedReq")
        req.marketId = market_id
        if currency:
            req.currencyCode = currency
        rsp = self._soapcall(BFExchangeService.getMarketPricesCompressed, req)
        if rsp.errorCode == GetMarketPricesErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetMarketPricesErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        prices = uncompress_market_prices(rsp.marketPrices)
        return prices

    # Betfair recommend to use getCompleteMarketPricesCompressed instead
    #def get_market_depth(self, market_id, selection_id, currency=None,
    #                     asian_line_id=None, locale=None):
    #    req = BFExchangeFactory.create("ns1:GetDetailedAvailMktDepthReq")
    #    req.marketId = market_id
    #    req.selectionId = selection_id
    #    if currency:
    #        req.currencyCode = currency
    #    if asian_line_id is not None:
    #        req.asian_line_id = asian_line_id
    #    if locale:
    #        req.locale = locale
    #    rsp = self._soapcall(BFExchangeService.getDetailedAvailableMktDepth, req)
    #    if rsp.errorCode == GetDetailedAvailMktDepthErrorEnum.API_ERROR:
    #        raise ServiceError(rsp.header.errorCode)
    #    if rsp.errorCode != GetDetailAvailMktDepthErrorEnum.OK:
    #        raise ServiceError(rsp.errorCode)
    #    return [AvailabilityInfo(*p) for p in rsp.priceItems[0]]

    def get_market_depth(self, market_id, currency):
        req = BFExchangeFactory.create("ns1:GetCompleteMarketPricesCompressedReq")
        req.marketId = market_id
        req.currencyCode = currency
        rsp = self._soapcall(BFExchangeService.getCompleteMarketPricesCompressed, req)
        if rsp.errorCode == GetCompleteMarketPricesErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetCompleteMarketPricesErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        return uncompress_complete_market_depth(rsp.completeMarketPrices)

    @not_implemented
    def add_payment_card(self):
        pass

    @not_implemented
    def delete_payment_card(self):
        pass

    @not_implemented
    def deposit_from_payment_card(self):
        pass

    @not_implemented
    def forgot_password(self):
        pass

    @not_implemented
    def get_account_funds(self):
        pass

    @not_implemented
    def get_account_statement(self):
        pass

    @not_implemented
    def get_payment_card(self):
        pass

    @not_implemented
    def get_subscription_info(self):
        pass

    @not_implemented
    def modify_password(self):
        pass

    @not_implemented
    def modify_profile(self):
        pass

    @not_implemented
    def retrieve_limb_message(self):
        pass

    @not_implemented
    def self_exclude(self):
        pass

    @not_implemented
    def set_chat_name(self):
        pass

    @not_implemented
    def submit_limb_message(self):
        pass

    @not_implemented
    def transfer_funds(self):
        pass

    @not_implemented
    def update_payment_card(self):
        pass

    @not_implemented
    def view_profile(self):
        pass

    @not_implemented
    def view_profile_v2(self):
        pass

    @not_implemented
    def view_refer_and_earn(self):
        pass

    @not_implemented
    def withdraw_to_payment_card(self):
        pass

    def _soapcall(self, soapfunc, req):
        if hasattr(req, 'header'):
            req.header = self._request_header
        if self._heartbeat:
            self._heartbeat.reset()
        rsp = soapfunc(req)
        try:
            token = rsp.header.sessionToken
            if token:
                self._request_header.sessionToken = token
        except AttributeError:
            pass
        return rsp

