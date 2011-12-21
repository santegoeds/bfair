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

import logging
import threading

from datetime import datetime

from bfair._types import Currency, EventType, BFEvent, MarketSummary, CouponLink, EventInfo, MarketInfo, Runner
from bfair._util import uncompress_market_prices, uncompress_markets, not_implemented
from bfair._soap import *


__all__ = [
    "ServiceError", "Session", "FREE_API"
]

logger = logging.getLogger(__name__)


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
        """Terminates the session by logging out of the account.
        """
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
            logger.error("keepAlive failed with error {%s}", rsp.header.errorCode)

    def get_event_types(self, active=True, locale=None):
        """Returns a list that is the root all categories of sporting events.

        Parameters
        ----------
        active : `bool`
            If `True` then only events that have at least one market available to
            bet on are returned.
        locale : `str` or `None`
            Language for the response.  If None then the default language for the
            account will be used

        Returns
        -------
        A list of `EventType` objects.
        """
        req = BFGlobalFactory.create("ns1:GetEventTypesReq")
        if locale:
            req.locale = locale
        if active:
            func = BFGlobalService.getActiveEventTypes
        else:
            func = BFGlobalService.getAllEventTypes
        rsp = self._soapcall(func, req)
        if rsp.errorCode == GetEventsErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode not in (GetEventsErrorEnum.OK, GetEventsErrorEnum.NO_RESULTS):
            raise ServiceError(rsp.errorCode)
        if rsp.eventTypeItems:
            rsp = [EventType(*[T[1] for T in e]) for e in rsp.eventTypeItems[0]]
        else:
            rsp = []
        return rsp

    def get_event_info(self, parent_id, locale=None):
        """Allows navigating the event hierarchy.  Where markets are available details
        of line and range markets are included in the result.

        Parameters
        ----------
        parent_id : `int`
            Event id or Event Type id.
        locale : `str` or `None`
            Language of the response.  If None the default language for the account
            will be used.

        Returns
        -------
        An `EventInfo` object.
        """
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
            [MarketSummary(*[T[1] for T in ms]) for ms in rsp.marketItems[0]] if rsp.marketItems else [],
            [CouponLink(*[T[1] for T in l]) for l in rsp.couponLinks[0]] if rsp.couponLinks else [],
        ]
        return EventInfo(*rsp)

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

    def get_bet_info(self, bet_id, lite=True):
        """Returns bet information.

        Parameters
        ----------
        bet_id : `int`
            Bet id.
        lite : `bool`
            If True (the default) only limited information is returned.

        Returns
        -------
        A BetInfo instance.
        """
        if lite:
            req = BFGlobalFactory.create("ns1:GetBetLiteReq")
            func = BFExchangeService.getBetLite
        else:
            req = BFGlobalFactory.create("ns1:GetBetReq")
            func = BFExchangeService.getBet
        req.betId = bet_id
        rsp = self._soapcall(func, req)
        if rsp.errorCode != GetBetErrorEnum.OK:
            raise ServiceError(rsp.header.errorCode)
        if lite:
            attrs = ["betCategoryType", "betId", "betPersistencType", "betStatus",
                     "bspLiability", "marketId", "matchedSize", "remainingSize"]
            bet = BetInfo(**{k: v for k, v in izip(attrs, rsp.betlite)})
        else:
            bet = BetInfo(*rsp.bet)
        return bet

    def get_market_info(self, market_id, lite=True, coupon_links=False, locale=None):
        """Returns static market information for a single market.

        market_id : `int`
            Id of the market for which market information is returned.
        lite : `bool`
            Lite information (default is True). Mutually exclusive with parameter
            "coupon_links".
        coupon_links : `bool`
            Include coupon data (default is False). Mutually exclusive with parameter
            "lite".
        locale : `str`
            Language for the reply.  Default is None in which case the default
            language of the account is used.
        """
        if lite and coupon_links:
            raise ServiceError("parameters `lite` and `coupon_links` are mutually exclusive")
        if lite:
            return self._get_market_info_lite(market_id)
        req = BFExchangeFactory.create("ns1:GetMarketReq")
        req.marketId = market_id
        req.includeCouponLinks = bool(coupon_links)
        if locale:
            req.locale = locale
        rsp = self._soapcall(BFExchangeService.getMarket, req)
        if rsp.errorCode == GetMarketErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetMarketErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        market = rsp.market
        coupon_links = [CouponLink(*lnk) for lnk in market.couponLinks[0] if lnk] if market.couponLinks else []
        runners = [Runner(*runner) for runner in market.runners[0] if runner] if market.runners else []
        rsp = MarketInfo(*market)
        rsp.couponLinks = coupon_links
        rsp.runners = runners
        return rsp

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

    # Betfair advice to use get_matched_unmatched_bets instead.
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
    #def get_detail_available_market_depth(self, market_id, selection_id, currency=None,
    #                                      asian_line_id=None, locale=None):
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

    def _get_market_info_lite(self, market_id):
        req = BFExchangeFactory.create("ns1:GetMarketInfoReq")
        req.marketId = market_id
        rsp = self._soapcall(BFExchangeService.getMarketInfo, req)
        if rsp.errorCode == GetMarketErrorEnum.API_ERROR:
            raise ServiceError(rsp.header.errorCode)
        if rsp.errorCode != GetMarketErrorEnum.OK:
            raise ServiceError(rsp.errorCode)
        attrs = ["delay", "marketStatus", "marketSuspendTime", "marketTime",
                 "numberOfRunners", "openForBspBetting"]
        rsp = MarketInfo(*zip(attrs, rsp))
        return rsp

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

