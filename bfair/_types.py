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

from itertools import izip

def _mk_class(name, attrs):
    """Creates a class similar to a namedtuple.  These classes are compatible
    with SQLAlchemy, however.
    """
    D = dict((attr, None) for attr in attrs)
    class_ = type(name, (object,), D)

    class_.__slots__ = attrs

    def init(self, *args):
        for attr, val in izip(attrs, args):
            setattr(self, attr, val)

    def repr(self):
        s = "".join(("<%s(", ", ".join(attrs), ")>"))
        s = s % name
        return s

    def len_(self):
        return len(self.__slots__)

    def getitem(self, i):
        return getattr(self, self.__slots__[i])

    class_.__init__ = init
    class_.__repr__ = repr
    class_.__len__ = len_
    class_.__getitem__ = getitem

    return class_

    
Market = _mk_class(
    "Market", (
        "marketId",         # Integer
        "marketName",       # String
        "marketType",       # String
        "marketStatus",     # String
        "marketTime",       # Datetime
        "menuPath",
        "eventHierarchy",
        "betDelay",
        "exchangeId",
        "countryISO3",
        "lastRefresh",
        "numberOfRunners",
        "numberOfWinners",
        "matchedSize",
        "bspMarket",
        "turningInPlay",
    )
)


Currency = _mk_class(
    "Currency", (
        "currencyCode",
        "rateGBP",
    )
)
Currency.__str__ = lambda self: self.currencyCode


CurrencyV2 = _mk_class(
    "CurrencyV2", (
        "currencyCode",
        "rateGBP",
        "minimumStake",
        "minimumStakeRange",
        "minimumBSPLayLiability",
    )
)
CurrencyV2.__str__ = lambda self: self.currencyCode


MarketPrices = _mk_class(
    "MarketPrices", (
        "marketId",
        "currency",
        "marketStatus",
        "delay",
        "numberOfWinners",
        "marketInfo",
        "discountAllowed",
        "marketBaseRate",
        "lastRefresh",
        "removedRunners",
        "bspMarket",
        "runnerPrices",
    )
)


EventType = _mk_class(
    "EventType", (
        "id",
        "name",
        "nextMarketId",
        "exchangeId",
    )
)


RunnerPrice = _mk_class(
    "RunnerPrice", (
        "selectionId",
        "sortOrder",
        "totalAmountMatched",
        "lastPriceMatched",
        "handicap",
        "reductionFactor",
        "vacant",
        "farBSP",
        "nearBSP",
        "actualBSP",
        "bestPricesToLay",
        "bestPricesToBack",
        "asianLineId",
    )
)


Price = _mk_class(
    "Price", (
        "price",
        "amountAvailable",
        "betType",
        "depth",
    )
)

RemovedRunner = _mk_class(
    "RemovedRunner", (
        "selection_name",
        "removed_date",
        "adjustment_factor"
    )
)

Bet = _mk_class(
    "Bet", (
        "asianLineId",
        "avgPrice",
        "betCategoryType",
        "betId",
        "betPersistenceType",
        "bspLiability",
        "cancelledDate",
        "executedBy",
        "fullMarketName",
        "handicap",
        "lapsedDate",
        "marketId",
        "marketName",
        "marketType",
        "marketTypeVariant",
        "matchedDate",
        "matchedSize",
        "matches",
        "placedDate",
        "price",
        "profitAndLoss",
        "remainingSize",
        "requestedSize",
        "selectionId",
        "selectionName",
        "settledDate",
        "voidedDate",
    )
)

Match = _mk_class(
    "Match", (
        "betStatus",
        "matchedDate",
        "priceMatched",
        "profitLoss",
        "settledDate",
        "sizeMatched",
        "transactionId",
        "voidedDate",
    )
)

BetLite = _mk_class(
    "BetLite", (
        "betCategoryType",
        "betId",
        "betPersistencType",
        "betStatus",
        "bspLiability",
        "marketId",
        "matchedSize",
        "remainingSize",
    )
)

del _mk_class
