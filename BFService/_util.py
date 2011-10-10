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

import re

from collections import namedtuple
from itertools import izip
from datetime import datetime, time
from pprint import pprint

def as_time(s):
    """Returns a time object from a string.
    """
    s = s.split(".")
    hour, mins = [ int(s) for s in s.split(".") ]
    return time(hour, mins)

def as_datetime(s):
    """Returns a datetime object from a string
    """
    s = int(s) if s else 0
    s, ms = s / 1000, s % 1000
    s = datetime.utcfromtimestamp(s)
    s = s.replace(microsecond=ms * 1000)
    return s

def as_float(s):
    """Returns a float from a string
    """
    if not s: return 0.0
    return float(s)

def as_int(s):
    if not s: return 0
    return int(s)

def as_bool(s):
    if not s: return False
    return s.lower() in ["true", "y", "1"]

def as_string(s):
    if not s: return ""
    return s.replace(r"\\", "")



MarketPrices = namedtuple(
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

RemovedRunner = namedtuple(
    "RemovedRunner", (
        "selection_name",
        "removed_date",
        "adjustment_factor"
    )
)

Runner = namedtuple(
    "Runner", (
        "selectionId",
        "sortOrder",
        "totalAmountMatched",
        "lastPriceMatched",
        "handicap",
        "reductionFactor",
        "vacant"
        "farBSP",
        "nearBSP",
        "actualBSP",
        "bestPricesToBack",
        "bestPricesToLay",
    )
)

MarketPrice = namedtuple(
    "MarketPrice", (
        "price",
        "amountAvailable",
        "betType",
        "depth",
    )
)

class DecompressOneMarketPrice(object):

    tokenise = lambda self, data: data.split("~")
    decoders = (
        as_float,   # price
        as_float,   # amountAvailable
        None,       # betType ("B" or "L")
        as_int,     # depth
    )

    def __call__(self, data):
        L = [
            decode(fld) if decode else fld
            for decode, fld in izip(self.decoders, self.tokenise(data))
        ]
        return MarketPrice(L)


class DecompressOneRunner(object):

    def __call__(self, data):
        pprint(data)

class DecompressMarketRunners(object):

    tokenise = lambda self, data: data.split("|")
    decode = DecompressOneRunner()

    def __call__(self, data):
        return [ self.decode(fld) for fld in self.tokenise(data) ]


class DecompressRemovedRunners(object):

    tokenise = re.compile(r"(?<!\\);")

    def __call__(self, data):
        pass


class DecompressMarketPricesInfo(object):

    tokenise = re.compile(r"(?<!\\)~").split
    decoders = (
        as_int,          # marketId
        None,            # currency
        None,            # marketStatus
        as_int,          # delay
        as_int,          # numberOfWinners
        as_string,       # marketInfo
        as_bool,         # discountAllowed
        None,            # marketBaseRate
        as_datetime,     # lastRefresh
        None,            # removedRunners
        as_bool,         # bspMarket
    )

    def __call__(self, data):
        return [
            decode(field) if decode else field
            for field, decode in izip(self.tokenise(data), self.decoders)
        ]


class DecompressMarketPrices(object):

    tokenize = re.compile(r"(?<!\\):").split
    decode_info = DecompressMarketPricesInfo()
    decode_prices = DecompressMarketRunners()

    def __call__(self, data):
        data = self.tokenize(data)
        market_prices = self.decode_info(data[0])
        market_prices.append(self.decode_prices(data[1]))
        return MarketPrices(market_prices)


uncompress_market_prices = DecompressMarketPrices()


def uncompress_markets(data):
    markets = []
    # Split data by colon, except when escaped.
    for rec in re.split(r"(?<!\\):", data):
        if not rec: continue
        # Unescape colons.
        rec = re.sub(r"\\:", ":", rec)
        fields = re.split(r"(?<!\\)~", rec)
        fields = [ re.sub(r"\\~", "~", f) for f in fields]
        mkt = dict(marketId = int(fields[0]),
                   name = fields[1],
                   marketType = fields[2],
                   marketStatus = fields[3],
                   marketTime = as_datetime(fields[4]),
                   menuPath = fields[5],
                   eventHierarchy = [ int(f) for f in fields[6].split("/") if f != ''],
                   betDelay = int(fields[7]),
                   exchangeId = int(fields[8]),
                   countryISO3 = fields[9],
                   lastRefresh = as_datetime(fields[10]),
                   numberOfRunners = int(fields[11]),
                   numberOfWinners = int(fields[12]),
                   matchedSize = as_float(fields[13]),
                   bspMarket = fields[14] == "Y",
                   turningInPlay = fields[15] == "Y")
        markets.append(mkt)
    return markets

