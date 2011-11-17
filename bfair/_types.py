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
    class_ = type(name, (object,), {attr: None for attr in attrs})
    class_.__slots__ = attrs

    def __init__(self, *args, **kwargs):
        for attr, val in izip(self.__slots__, args):
            setattr(self, attr, val)
        for k, v in kwargs.iteritems():
            if k not in self.__slots__:
                raise ValueError("%s : Invalid attribute" % k)
            setattr(self, k, v)

    def __repr__(self):
        s = ", ".join("=".join((a, repr(getattr(self, a)))) for a in self.__slots__)
        s = "".join(("<", type(self).__name__, "(", s, ")>"))
        return s

    def __len__(self):
        return len(self.__slots__)

    def __getitem__(self, i):
        return getattr(self, self.__slots__[i])

    class_.__init__ = __init__
    class_.__repr__ = __repr__
    class_.__len__ = __len__
    class_.__getitem__ = __getitem__

    return class_

    
Market = _mk_class(
    "Market", (
        "id",               # marketId
        "name",             # marketName
        "type",             # marketType
        "status",           # marketStatus
        "time",             # marketTime
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
        "minimumStake",
        "minimumStakeRange",
        "minimumBSPLayLiability",
    )
)
Currency.__str__ = lambda self: self.currencyCode


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


del _mk_class
