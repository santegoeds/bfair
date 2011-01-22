#!/usr/bin/env python

from datetime import datetime
from itertools import islice
import re
import logging

logging.basicConfig(level=logging.INFO)
#logging.getLogger('suds.client').setLevel(logging.DEBUG)

from suds.client import Client

from _util import as_decimal, uncompress_market_prices, from_timestamp


BFGlobalServiceUrl = "https://api.betfair.com/global/v3/BFGlobalService.wsdl"
BFGlobalServiceClient = Client(BFGlobalServiceUrl)
BFGlobalService = BFGlobalServiceClient.service
BFGlobalFactory = BFGlobalServiceClient.factory

BFExchangeServiceUrl = "https://api.betfair.com/exchange/v5/BFExchangeService.wsdl"
BFExchangeServiceClient = Client(BFExchangeServiceUrl)
BFExchangeService = BFExchangeServiceClient.service
BFExchangeFactory = BFExchangeServiceClient.factory

# Error enumerations
APIErrorEnum = BFGlobalFactory.create("ns1:APIErrorEnum")
GetEventsErrorEnum = BFGlobalFactory.create("ns1:GetEventsErrorEnum")
GetBetErrorEnum = BFExchangeFactory.create("ns1:GetBetErrorEnum")
GetAllMarketsErrorEnum = BFExchangeFactory.create("ns1:GetAllMarketsErrorEnum")
GetCompleteMarketPricesErrorEnum = BFExchangeFactory.create("ns1:GetCompleteMarketPricesErrorEnum")
ConvertCurrencyErrorEnum = BFExchangeFactory.create("ns1:ConvertCurrencyErrorEnum")


class BFServiceError(Exception):
    pass


class Session(object):

    request_header = BFGlobalFactory.create("ns1:APIRequestHeader")
    request_header.clientStamp = 0

    def __init__(self, username, password, product_id = 82):
        super(Session, self).__init__()
        self.username = username
        self.password = password
        self.product_id = product_id

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, type, value, traceback):
        if self.request_header.sessionToken is not None:
            self.logout();

    def login(self):
        req = BFGlobalFactory.create("ns1:LoginReq")
        req.username = self.username
        req.password = self.password
        req.productId = self.product_id
        req.ipAddress = 0
        req.locationId = 0
        req.vendorSoftwareId = 0
        rsp = self._soapcall(BFGlobalService.login, req)
        if rsp.errorCode != APIErrorEnum.OK:
            raise BFServiceError(rsp.errorCode)

    def logout(self):
        BFGlobalService.logout(self.request_header)

    def keep_alive(self):
        req = BFGlobalFactory.create("ns1:KeepAliveRequest")
        rsp = self._soapcall(BFGlobalService.keepAlive, req)
        if rsp.header.errorCode != APIErrorEnum.OK:
            raise BFServiceError(rsp.header.errorCode)

    def get_events(self, active=True, locale=None):
        req = BFGlobalFactory.create("ns1:GetEventTypesReq")
        if locale: req.locale = locale
        func = BFGlobalService.getActiveEventTypes \
                if active else BFGlobalService.getAllEventTypes
        rsp = self._soapcall(func, req)
        if rsp.errorCode == GetEventsErrorEnum.API_ERROR:
            raise BFServiceError(rsp.header.errorCode)
        if rsp.errorCode not in (GetEventsErrorEnum.OK,
                                 GetEventsErrorEnum.NO_RESULTS):
            raise BFServiceError(rsp.errorCode)
        return rsp.eventTypeItems

    def get_currencies(self):
        req = BFGlobalFactory.create("ns1:GetCurrenciesV2Req")
        rsp = self._soapcall(BFGlobalService.getAllCurrenciesV2, req)
        if rsp.header.errorCode != self.APIError.OK:
            raise BFServiceError(rsp.header.errorCode)
        return rsp.currencyItems

    def convert_currency(self, amount, from_currency, to_currency):
        req = BFGlobalFactory.create("ns1:ConvertCurrencyReq")
        req.amount = amount
        req.fromCurrency = from_currency
        req.toCurrency = to_currency
        rsp = self._soapcall(BFGlobalService.convertCurrency, req)
        if rsp.errorCode == ConvertCurrencyErrorEnum.API_ERROR:
            raise BFServiceError(rsp.header.errorCode)
        elif rsp.errorCode != ConvertCurrencyErrorEnum.OK:
            raise BFServiceError(rsp.errorCode)
        return rsp.convertedAmount

    def get_bet(self, id, lite=False):
        req = BFGlobalFactory.create("ns1:GetBetLiteReq") \
                if lite else BFGlobalFactory.create("ns1:GetBetReq")
        req.betId = id
        func = BFExchangeService.getBetLite \
                if lite else BFExchangeService.getBet
        rsp = self._soapcall(func, req)
        if rsp.errorCode != GetBetErrorEnum.OK:
            raise BFServiceError(rsp.header.errorCode)
        return rsp.betlite if lite else rsp.bet

    def get_in_play_markets(self, locale=None):
        req = BFExchangeService.create("ns1:GetInPlayMarkets")
        if locale: req.locale = locale
        rsp = self._soapcall(BFExchangeService.getInPlayMarkets, req)
        if rsp.errorCode == GetInPlayMarketsErrorEnum.API_ERROR:
            raise BFServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetInPlayMarketsErrorEnum.OK:
            raise BFServiceError(rsp.errorCode)
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
            raise BFServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetAllMarketsErrorEnum.OK:
            raise BFServiceError(rsp.errorCode)
        markets = uncompress_markets(rsp.marketData)
        return markets

    def get_complete_market_prices(self, market_id, currency):
        req = BFExchangeFactory.create("ns1:GetCompleteMarketPricesCompressedReq")
        req.marketId = market_id
        req.currencyCode = currency
        rsp = self._soapcall(BFExchangeService.getCompleteMarketPricesCompressed, req)
        if rsp.errorCode == GetCompleteMarketPricesErrorEnum.API_ERROR:
            raise BFServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetCompleteMarketPricesErrorEnum.OK:
            raise BFServiceError(rsp.errorCode)
        return uncompress_market_prices(rsp.completeMarketPrices)

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
            raise BFServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetDetailAvailMktDepthErrorEnum.OK:
            raise BFServiceError(rsp.errorCode)
        return rsp.priceItems

    def _soapcall(self, soapfunc, req):
        if hasattr(req, 'header'):
            req.header = self.request_header
        rsp = soapfunc(req)
        try:
            token = rsp.header.sessionToken
            if token:
                self.request_header.sessionToken = token
        except AttributeError:
            pass
        return rsp

