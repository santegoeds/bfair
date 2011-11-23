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
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

from os import path
from datetime import datetime
from suds.client import Client

from _types import Currency, EventType, BFEvent, MarketSummary, CouponLink, Event
from _util import uncompress_market_prices, uncompress_markets


__all__ = ("ServiceError", "Session")


BFGlobalServiceUrl = "file://" + path.abspath(path.join(path.dirname(__file__), "wsdl/BFGlobalService.wsdl"))
BFGlobalServiceUrl = "https://api.betfair.com/global/v3/BFGlobalService.wsdl"
BFGlobalServiceClient = Client(BFGlobalServiceUrl)
BFGlobalService = BFGlobalServiceClient.service
BFGlobalFactory = BFGlobalServiceClient.factory

BFExchangeServiceUrl = "file://" + path.abspath(path.join(path.dirname(__file__), "wsdl/BFExchangeService.wsdl"))
BFExchangeServiceUrl = "https://api.betfair.com/exchange/v5/BFExchangeService.wsdl"
BFExchangeServiceClient = Client(BFExchangeServiceUrl)
BFExchangeService = BFExchangeServiceClient.service
BFExchangeFactory = BFExchangeServiceClient.factory

# Error enumerations
APIErrorEnum = BFGlobalFactory.create("ns1:APIErrorEnum")
GetEventsErrorEnum = BFGlobalFactory.create("ns1:GetEventsErrorEnum")
ConvertCurrencyErrorEnum = BFGlobalFactory.create("ns1:ConvertCurrencyErrorEnum")
GetBetErrorEnum = BFExchangeFactory.create("ns1:GetBetErrorEnum")
GetAllMarketsErrorEnum = BFExchangeFactory.create("ns1:GetAllMarketsErrorEnum")
GetCompleteMarketPricesErrorEnum = BFExchangeFactory.create("ns1:GetCompleteMarketPricesErrorEnum")
GetInPlayMarketsErrorEnum = BFExchangeFactory.create("ns1:GetInPlayMarketsErrorEnum")
GetMarketPricesErrorEnum = BFExchangeFactory.create("ns1:GetMarketPricesErrorEnum")


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

    def get_market_depth(self, market_id, selection_id=None, currency=None,
                         asian_line_id=None, locale=None):
        if selection_id is None:
            return self._get_complete_market_depth(market_id, currency)
        req = BFExchangeFactory.create("ns1:GetDetailedAvailMktDepthReq")
        req.marketId = market_id
        req.selectionId = selection_id
        if currency:
            req.currencyCode = currency
        if asian_line_id is not None:
            req.asian_line_id = asian_line_id
        if locale:
            req.locale = locale
        rsp = self._soapcall(BFExchangeService.getDetailedAvailableMktDepth, req)
        if rsp.errorCode == GetDetailedAvailMktDepthErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetDetailAvailMktDepthErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        # TODO: Convert into our own types
        return rsp.priceItems[0]

    def _get_complete_market_depth(self, market_id, currency=None):
        req = BFExchangeFactory.create("ns1:GetCompleteMarketPricesCompressedReq")
        req.marketId = market_id
        if currency:
            req.currencyCode = currency
        rsp = self._soapcall(BFExchangeService.getCompleteMarketPricesCompressed, req)
        if rsp.errorCode == GetCompleteMarketPricesErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetCompleteMarketPricesErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        return uncompress_complete_market_depth(rsp.completeMarketPrices)


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

