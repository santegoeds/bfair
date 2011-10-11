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

from _types import CurrencyV2, EventType
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


class ServiceError(Exception):
    pass


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

    def __init__(self, username, password, product_id = 82, vendor_id = 0):
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
        req = BFGlobalFactory.create("ns1:KeepAliveRequest")
        rsp = self._soapcall(BFGlobalService.keepAlive, req)
        if rsp.header.errorCode != APIErrorEnum.OK:
            raise ServiceError(rsp.header.errorCode)

    def get_events(self, active=True, locale=None):
        """
        Returns a list of events that are available to bet on.
        """
        req = BFGlobalFactory.create("ns1:GetEventTypesReq")
        if locale: req.locale = locale
        func = BFGlobalService.getActiveEventTypes \
                if active else BFGlobalService.getAllEventTypes
        rsp = self._soapcall(func, req)
        if rsp.errorCode == GetEventsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode not in (GetEventsErrorEnum.OK,
                                 GetEventsErrorEnum.NO_RESULTS):
            raise ServiceError(rsp.errorCode)
        return [EventType(*[n[1] for n in e]) for e in rsp.eventTypeItems[0]]

    def get_currencies(self):
        req = BFGlobalFactory.create("ns1:GetCurrenciesV2Req")
        rsp = self._soapcall(BFGlobalService.getAllCurrenciesV2, req)
        if rsp.header.errorCode != APIErrorEnum.OK:
            raise ServiceError(rsp.header.errorCode)
        return [CurrencyV2(*c) for c in rsp.currencyItems]

    def convert_currency(self, amount, from_currency, to_currency):
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

    def get_bet(self, id, lite=False):
        req = BFGlobalFactory.create("ns1:GetBetLiteReq") \
                if lite else BFGlobalFactory.create("ns1:GetBetReq")
        req.betId = id
        func = BFExchangeService.getBetLite \
                if lite else BFExchangeService.getBet
        rsp = self._soapcall(func, req)
        if rsp.errorCode != GetBetErrorEnum.OK:
            raise ServiceError(rsp.header.errorCode)
        return rsp.betlite if lite else rsp.bet

    def get_in_play_markets(self, locale=None):
        req = BFExchangeFactory.create("ns1:GetInPlayMarketsReq")
        if locale: req.locale = locale
        rsp = self._soapcall(BFExchangeService.getInPlayMarkets, req)
        if rsp.errorCode == GetInPlayMarketsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetInPlayMarketsErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        return uncompress_markets(rsp.marketData)

    def get_markets(self, event_type_ids=None, countries=None, date_range=None):
        req = BFExchangeFactory.create("ns1:GetAllMarketsReq")
        if event_type_ids:
            req.eventTypeIds = event_ids
        if countries:
            req.countries = countries
        if date_range:
            try:
                req.fromDate = date_range.start
            except AttributeError:
                pass
            try:
                req.toDate = date_range.end
            except AttributeError:
                pass
        rsp = self._soapcall(BFExchangeService.getAllMarkets, req)
        if rsp.errorCode == GetAllMarketsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetAllMarketsErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        markets = uncompress_markets(rsp.marketData)
        return markets

    def get_complete_market_prices(self, market_id, currency=None):
        req = BFExchangeFactory.create("ns1:GetCompleteMarketPricesCompressedReq")
        req.marketId = market_id
        if currency:
            req.currencyCode = currency
        rsp = self._soapcall(BFExchangeService.getCompleteMarketPricesCompressed, req)
        if rsp.errorCode == GetCompleteMarketPricesErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetCompleteMarketPricesErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        return uncompress_complete_market_prices(rsp.completeMarketPrices)

    def get_detail_available_mkt_depth(self, market_id, selection_id, currency,
                                       asian_line_id=None, locale=None):
        req = BFExchangeFactory.create("ns1:GetDetailedAvailMktDepthReq")
        req.marketId = market_id
        req.selectionId = selection_id
        req.currencyCode = currency
        if asian_line_id is not None:
            req.asian_line_id = asian_line_id
        if locale is not None:
            req.locale = locale
        rsp = self._soapcall(BFExchangeService.getDetailedAvailableMktDepth, req)
        if rsp.errorCode == GetDetailedAvailMktDepthErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetDetailAvailMktDepthErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        return rsp.priceItems

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

