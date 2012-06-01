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
import functools

from collections import namedtuple
from itertools import izip
from datetime import datetime

from ._types import *


def not_implemented(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        raise NotImplementedError(fn.__name__)
    return wrapper


def untested(logger):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            logger.warning("%s: has not been tested.  Use at your own risk", fn.__name__)
            return fn(*args, **kwargs)
    return decorator


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



class DecompressPrice(object):

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
        return Price(*L)


class DecompressRunnerPrice(object):

    tokenise = staticmethod(lambda data: data.split("~"))
    decoders = (
        as_int,   # selectionId
        as_int,   # sortOrder
        as_float, # totalAmountMatched
        as_float, # lastPriceMatched
        as_float, # handicap
        as_float, # reductionFactor
        as_bool,  # vacant
        as_float, # farBSP
        as_float, # nearBSP
        as_float, # actualBSP
    )

    def __call__(self, data, lay_prices, back_prices):
        data = self.tokenise(data)
        data = [decode(fld) for fld, decode in izip(data, self.decoders)]
        # Extend with asianLineId, which is not available from compressed
        # market prices.
        data += [ lay_prices, back_prices, None ]
        data = RunnerPrice(*data)
        return data


class DecompressRunners(object):

    tokenise = lambda self, data: data.split("|")
    decode_runner_price = DecompressRunnerPrice()
    decode_price = DecompressPrice()

    def __call__(self, data):
        data = self.tokenise(data)
        prices = [ self.decode_price(fld) for fld in data[1:] if fld ]
        # Prices that are available to Lay are made up of unmatched "Back" bets whereas
        # prices that are available to Back are made up of unmatched "Lay" bets
        lay_prices = [p for p in prices if p.betType == "B"]
        back_prices = [p for p in prices if p.betType == "L"]
        rp = self.decode_runner_price(data[0], lay_prices, back_prices)
        return rp


class DecompressRemovedRunners(object):

    tokenise = re.compile(r"(?<!\\);").split

    def __call__(self, data):
        return self.tokenise(data)


class DecompressMarketPricesInfo(object):

    tokenise = re.compile(r"(?<!\\)~").split
    decoders = (
        as_int,      # marketId
        None,        # currency
        None,        # marketStatus
        as_int,      # delay
        as_int,      # numberOfWinners
        as_string,   # marketInfo
        as_bool,     # discountAllowed
        as_float,    # marketBaseRate
        as_datetime, # lastRefresh
        None,        # removedRunners
        as_bool,     # bspMarket
    )

    def __call__(self, data):
        data = self.tokenise(data)
        data = [decode(fld) if decode else fld 
                for fld, decode in izip(data, self.decoders)]
        return data


class DecompressMarketPrices(object):

    tokenize = re.compile(r"(?<!\\):").split
    decode_info = DecompressMarketPricesInfo()
    decode_prices = DecompressRunners()

    def __call__(self, data):
        data = self.tokenize(data.strip())
        mp = self.decode_info(data[0])
        mp.append([ self.decode_prices(fld) for fld in data[1:] ])
        return MarketPrices(*mp)


class DecompressOneMarket(object):

    #tokenise = re.compile(r"(?<!\\)~").split
    tokenise = staticmethod(lambda s: s.split("~"))
    decoders = (
        as_int,      # marketId
        None,        # name
        None,        # marketType
        None,        # marketStatus
        as_datetime, # marketTime
        None,        # menuPath
        lambda s: [as_int(f) for f in s.split("/")], # eventHierarchy
        as_int,      # betDelay
        as_int,      # exchangeId
        None,        # countryISO3
        as_datetime, # lastRefresh
        as_int,      # numberOfRunners
        as_int,      # numberOfWinners
        as_float,    # matchedSize
        as_bool,     # bspMarket
        as_bool,     # turningInPlay
    )
    
    def __call__(self, data):
        L = [decode(f) if decode else f
             for f, decode in izip(self.tokenise(data), self.decoders)]
        return Market(*L)


class DecompressMarkets(object):

    tokenise = re.compile(r"(?<!\\):").split
    decode = DecompressOneMarket()

    def __call__(self, data):
        return [self.decode(f) for f in DecompressMarkets.tokenise(data.strip()) if f]


uncompress_markets = DecompressMarkets()
uncompress_market_prices = DecompressMarketPrices()
