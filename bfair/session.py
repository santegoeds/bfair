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
from itertools import izip

from bfair._types import *
from bfair._soap import *
from bfair._util import (
    uncompress_market_prices,
    uncompress_markets,
    not_implemented, untested,
)


__all__ = (
    "ServiceError", "Session", "FREE_API"
)

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    pass


FREE_API = 82


class HeartBeat(threading.Thread):

    def __init__(self, keepalive_func, interval=19):
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


class Session(object):
    """
    """

    def __init__(self, username, password, product_id=FREE_API, vendor_id=0):
        """Constructor.

        Parameters
        ----------
        username : `str`
            Betfair username.
        password : `str`
            Betfair password
        product_id : `int`
            Product id that is used to establish a session.  Default is
            FREE_API.
            Note that the free API does not support the full Betfair API and
            limits the rate at which certain functions can be called.
            See the Betfair documentation for further information.
        vendor_id : `int`
            Vendor id that is used to establish a session.  Default is 0 for
            personal usages.
        """
        super(Session, self).__init__()
        self._request_header = BFGlobalFactory.create("ns1:APIRequestHeader")
        self._request_header.clientStamp = 0
        self._heartbeat = None
        self.username = username
        self.password = password
        self.product_id = product_id
        self.vendor_id = vendor_id

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, type, value, traceback):
        if self._request_header.sessionToken is not None:
            self.logout();

    def login(self):
        """Establishes a secure session with the Betfair server.
        """
        req = BFGlobalFactory.create("ns1:LoginReq")
        req.username = self.username
        req.password = self.password
        req.productId = self.product_id
        req.vendorSoftwareId = self.vendor_id
        req.ipAddress = 0
        req.locationId = 0
        self._heartbeat = HeartBeat(self.keep_alive)
        rsp = self._soapcall(BFGlobalService.login, req)
        try:
            if rsp.errorCode != APIErrorEnum.OK:
                error_code = rsp.errorCode
                if error_code == LoginErrorEnum.API_ERROR:
                    error_code = rsp.header.errorCode
                logger.error("{login} failed with error {%s}", error_code)
                raise ServiceError(error_code)
        except:
            self._heartbeat = None
            raise
        self._heartbeat.start()

    def logout(self):
        """Terminates the session by logging out of the account.
        """
        if self._heartbeat:
            self._heartbeat.stop()
            self._heartbeat.join()
        self._heartbeat = None
        BFGlobalService.logout(self._request_header)
        self._request_header.sessionToken = None

    @property
    def is_active(self):
        return self._heartbeat is not None

    def keep_alive(self):
        """Sends a 'keepalive' message to prevent that the established session
        is timed out.
        """
        req = BFGlobalFactory.create("ns1:KeepAliveReq")
        rsp = self._soapcall(BFGlobalService.keepAlive, req)
        if rsp.header.errorCode != APIErrorEnum.OK:
            logger.error("{keepAlive} failed with error {%s}",
                         rsp.header.errorCode)

    def get_event_types(self, active=True, locale=None):
        """Returns a list that is the root all categories of sporting events.

        Parameters
        ----------
        active : `bool`
            If `True` then only events that have at least one market available
            to bet on are returned.
        locale : `str` or `None`
            Language for the response.  If None then the default language for
            the account will be used

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
        if rsp.errorCode not in (GetEventsErrorEnum.OK,
                                 GetEventsErrorEnum.NO_RESULTS):
            error_code = rsp.errorCode
            if error_code == GetEventsErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{%s} failed with error {%s}" % func.__name__,
                         errorcode)
            raise ServiceError(errorcode)
        if rsp.eventTypeItems:
            rsp = [EventType(*[T[1] for T in e])
                   for e in rsp.eventTypeItems[0]]
        else:
            rsp = []
        return rsp

    def get_event_info(self, event_id, locale=None):
        """Allows navigating of the event hierarchy.

        Where markets are available details of line and range markets are
        included in the result.

        Parameters
        ----------
        event_id : `int`
            Event id or Event Type id.
        locale : `str` or `None`
            Language of the response.  If None the default language for the
            account will be used.

        Returns
        -------
        An EventInfo object or None if there are no results for the
        requested event_id.
        """
        req = BFGlobalFactory.create("ns1:GetEventsReq")
        req.eventParentId = event_id
        if locale:
            req.locale = locale
        rsp = self._soapcall(BFGlobalService.getEvents, req)
        if rsp.errorCode not in (GetEventsErrorEnum.OK,
                                 GetEventsErrorEnum.NO_RESULTS):
            error_code = rsp.errorCode
            if error_code == GetEventsErrorEnum.API_ERROR:
                error_code = rps.header.errorCode
            logger.error("{getEvents} failed with error {%s}", error_code)
            raise ServiceError(error_code)
        event_items = rsp.eventItems[0] if rsp.eventItems else []
        event_items = [BFEvent(**{k: v for k, v in evt})
                       for evt in event_items if evt]
        market_items = rsp.marketItems[0] if rsp.marketItems else []
        market_items = [MarketSummary(**{k: v for k, v in mi})
                        for mi in market_items if mi]
        coupon_links = rsp.couponLinks[0] if rsp.couponLinks else []
        coupon_links = [CouponLink(**{k: v for k, v in cl})
                        for cl in coupon_links if cl]
        rsp = EventInfo(event_items, rsp.eventParentId, market_items,
                        coupon_links)
        return rsp

    @untested(logger)
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
            logger.error("{%s} failed with error {%s}", srv.__name__,
                         rsp.hearder.errorCode)
            raise ServiceError(rsp.header.errorCode)
        return [Currency(*c) for c in rsp.currencyItems[0]]

    @untested(logger)
    def convert_currency(self, amount, from_currency, to_currency):
        if self.product_id == FREE_API:
            raise ServiceError("Free API does not support convert_currency")
        req = BFGlobalFactory.create("ns1:ConvertCurrencyReq")
        req.amount = amount
        req.fromCurrency = from_currency
        req.toCurrency = to_currency
        rsp = self._soapcall(BFGlobalService.convertCurrency, req)
        if rsp.errorCode != ConvertCurrencyErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == ConvertCurrencyErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{convertCurrency} failed with error {%s}",
                         error_code)
            raise ServiceError(error_code)
        return rsp.convertedAmount

    @untested(logger)
    def get_bet_info(self, bet_id, lite=True, locale=None):
        """Returns bet information.

        Parameters
        ----------
        bet_id : `int`
            Bet id.
        lite : `bool`
            If True (the default) only limited information is returned.

        Returns
        -------
        An instance of BetInfo or None.
        """
        if lite:
            if locale:
                raise ServiceError("Locale is not supported when lite=True")
            return self._get_bet_info_lite(bet_id)
        req = BFGlobalFactory.create("ns1:GetBetReq")
        req.betId = bet_id
        if locale:
            req.locale = locale
        rsp = self._soapcall(BFExchangeService.getBet, req)
        if rsp.errorCode != GetBetErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == GetBetErrorEnum.NO_RESULTS:
                return None
            if error_code == GetBetErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            if error_code == GetBetErrorEnum.INVALID_LOCALE_DEFAULTING_TO_ENGLISH:
                logger.warn("Invalid locale. Defaulting to English.")
            else:
                logger.error("{%s} failed with error {%s}", getBet, error_code)
                raise ServiceError(error_code)
        rsp = BetInfo(**{k: v for k, v in rsp.bet})
        return rsp

    def get_market_info(self, market_id, lite=True, coupon_links=False,
                        locale=None):
        """Returns static market information for a single market.

        Parameters
        ----------
        market_id : `int`
            Id of the market for which market information is returned.
        coupon_links : `bool`
            Include coupon data (default is False).
        locale : `str`
            Language for the reply.  Default is None in which case the default
            language of the account is used.

        Returns
        -------
        An instance of MarketInfo.
        """
        req = BFExchangeFactory.create("ns1:GetMarketReq")
        req.marketId = market_id
        req.includeCouponLinks = coupon_links
        if locale:
            req.locale = locale
        rsp = self._soapcall(BFExchangeService.getMarket, req)
        if rsp.errorCode != GetMarketErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == GetMarketErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getMarket} failed with error {%s}", error_code)
            raise ServiceError(error_code)
        market = rsp.market
        coupons = market.couponLinks[0] if market.couponLinks else []
        coupons = [CouponLink(**{k: v for k, v in coupon})
                   for coupon in coupons if coupon]
        runners = market.runners[0] if market.runners else []
        runners = [Runner(**{k: v for k, v in runner})
                   for runner in runners if runner]
        hierarchies = market.eventHierarchy[0] if market.eventHierarchy else []
        hierarchies = [evt for evt in hierarchies]
        rsp = MarketInfo(**{k: v for k, v in market})
        info.eventHierarchy = hierarchies
        rsp.couponLinks = coupons
        rsp.runners = runners
        return rsp

    def get_market_info_lite(self, market_id):
        """Returns market information for a single market.

        Parameters
        ----------
        market_id : `int`
            Id of the market for which market information is returned.

        Returns
        -------
        An instance of MarketInfoLite.
        """
        req = BFExchangeFactory.create("ns1:GetMarketInfoReq")
        req.marketId = market_id
        rsp = self._soapcall(BFExchangeService.getMarketInfo, req)
        if rsp.errorCode != GetMarketErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code != GetMarketErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getMarketInfo} failed with error {%s}", error_code)
            raise ServiceError(error_code)
        info = MarketInfoLite(**{k: v for k, v in rsp.marketLite})
        return info

    def get_market_traded_volume(self, market_id, selection_id,
                                 asian_line_id=None, currency=None):
        req = BFExchangeFactory.create("ns1:GetMarketTradedVolumeReq")
        req.marketId = market_id
        req.selectionId = selection_id
        if asian_line_id is not None:
            req.asianLineId = asian_line_id
        if currency:
            req.currencyCode = currency
        rsp = self._soapcall(BFExchangeService.getMarketTradedVolume, req)
        if rsp.errorCode != GetMarketTradedVolumeErrorEnum.OK:
            error_code == rsp.errorCode
            if error_code == GetMarketTradedVolumeErrorEnum.NO_RESULTS:
                return None
            if error_code == GetMarketErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getMarketTradedVolume} failed with error {%s}",
                         error_code)
            raise ServiceError(error_code)
        volume_infos = rsp.priceItems[0] if rsp.priceItems else []
        volume_infos = [VolumeInfo(**{k: v for k, v in vi})
                        for vi in volume_infos if vi]
        volume = MarketTradedVolume(actualBSP=rsp.actualBSP)
        volume.priceItems = volume_infos
        return volume

    @not_implemented
    def get_market_traded_volume_compressed(self):
        pass

    @not_implemented
    def cancel_bets(self):
        pass

    @not_implemented
    def cancel_bets_by_market(self):
        pass

    @untested
    def place_bets(self, bets):
        req = BFExchangeFactory.create("ns1:PlaceBetsReq")
        req.bets[0].extend(bets)
        rsp = self._soapcall(BFExchangeService.placeBets)
        if rsp.errorCode != PlaceBetsErrorEnum.OK:
            error_code == rsp.errorCode
            if error_code == PlaceBetsErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{placeBets} failed with error {%s}",
                         error_code)
            raise ServiceError(error_code)
        results = rsp.betResults[0] if rsp.betResults else []
        results = [PlaceBetResult(**{k: v for k, v in res})
                   for res in results]
        return results


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
        if rsp.errorCode != GetInPlayMarketsErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == GetInPlayMarketsErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getInPlayMarkets} failed with error {%s}",
                         error_code)
            raise ServiceError(error_code)
        return uncompress_markets(rsp.marketData)

    def get_markets(self, event_ids=None, countries=None, date_range=None):
        req = BFExchangeFactory.create("ns1:GetAllMarketsReq")
        if event_ids:
            req.eventTypeIds[0].extend(list(iter(event_ids)))
        if countries:
            req.countries[0].extend(list(iter(countries)))
        if date_range:
            date_range = list(iter(date_range))
            req.fromDate = date_range[0]
            if len(date_range) > 1:
                req.toDate = date_range.end[-1]
        rsp = self._soapcall(BFExchangeService.getAllMarkets, req)
        if rsp.errorCode != GetAllMarketsErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == GetAllMarketsErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getAllMarkets} failed with error {%s}", error_code)
            raise ServiceError(error_code)
        markets = uncompress_markets(rsp.marketData)
        return markets

    def get_market_prices(self, market_id, currency=None):
        req = BFExchangeFactory.create("ns1:GetMarketPricesCompressedReq")
        req.marketId = market_id
        if currency:
            req.currencyCode = currency
        rsp = self._soapcall(BFExchangeService.getMarketPricesCompressed, req)
        if rsp.errorCode != GetMarketPricesErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == GetMarketPricesErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getMarketPricesCompressed} failed with error {%s}",
                         error_code)
            raise ServiceError(error_code)
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
        if rsp.errorCode != GetCompleteMarketPricesErrorEnum.OK:
            error_code = rsp.errorCode
            if rsp.errorCode == GetCompleteMarketPricesErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getCompleteMarketPricesCompressed} failed with "
                         "error {%s}", error_code)
            raise ServiceError(error_code)
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

    def _get_bet_info_lite(self, bet_id):
        req = BFGlobalFactory.create("ns1:GetBetLiteReq")
        req.betId = bet_id
        self._soapcall(BFExchangeService.getBetLite, req)
        if rsp.errorCode != GetBetErrorEnum.OK:
            error_code = rsp.errorCode
            if error_code == GetBetErrorEnum.NO_RESULTS:
                return None
            if error_code == GetBetErrorEnum.API_ERROR:
                error_code = rsp.header.errorCode
            logger.error("{getBetLite} failed with error {%s}", error_code)
            raise ServiceError(error_code)
        rsp = BetInfo(**{k: v for k, v in rsp.betlite})
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
