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

from itertools import izip
from datetime import datetime


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
    return s in ["true", "Y"]


RE_FIELDS = re.compile(r"(?<!\\)~")
RE_REMOVED_RUNNERS = re.compile(r"(?<!\\);")
RE_REMOVED_RUNNER_FIELDS = re.compile(r"(?<!\\),")
RE_RUNNERS = re.compile(r"(?<!\\):")
RE_RUNNER = re.compile(r"(?<!\\)|")


def uncompress_one_removed_runner(data):
    return RE_REMOVED_RUNNER_FIELDS.split(data)


def uncompress_removed_runners(data):
    return [ uncompress_one_removed_runner(r)
             for r in RE_REMOVED_RUNNERS.split(data) ]


def uncompress_one_runner(data):
    T = ("selectionId", "sortOrder", "totalAmountBacked", "lastPriceMatched",
         "handicap", "reductionFactor", "vacant", "farBSP", "nearBSP",
         "actualBSP", "backPrices", "layPrices")
    D = dict(izip(T, RE_RUNNER.split(data)))
    return D


def uncompress_runners(data):
    return [ uncompress_one_runner(r) for r in RE_RUNNERS.split(data) ]


def uncompress_market_prices(data):
    decoders = {
        "marketId": as_int,
        "currency": None,
        "marketStatus": None,
        "delay": as_int,
        "numberOfWinners": as_int,
        "marketInfo": None,
        "discountAllowed": as_bool,
        "marketBaseRate" as_float,
        "lastRefresh" None,
        "removedRunners": uncompress_removed_runners,
        "bspMarket": None,
        "runnerPrices": None,
    }
    D = dict( (name, decode(field) if decode else field)
              for (name, decode), field in zip(decoders.iteritems(),
                                               RE_FIELDS.split(data)))
    return D


def _xxx_uncompress_market_prices(data):
    regex = r"(?P<rectype>[|:;]?)(?P<field>(?:[^~|:;]|(?<=\\)[~|:;])*)~"
    tokens = [ m.groupdict() for m in re.finditer(regex, data) ]
    def pop(sz=1):
        t = tokens[:sz]
        del tokens[:sz]
        return t
    def peek():
        return tokens[0]
    def empty():
        return not bool(tokens)
    market_prices = {}
    for k, m in zip(("marketId", "delay"), pop(2)):
        market_prices[k] = int(m["field"])
    removed_runners = []
    while not empty() and peek()["rectype"] == ';':
        m = pop()
        L = re.split(r"(?<!\\),", m["field"])
        removed_runners.append({"selection_name": L[0],
                                "removed_date": as_datetime(L[1]),
                                "adjustment_factor": L[2]})
    market_prices["removedRunners"] = removed_runners
    runners = []
    while not empty() and peek()["rectype"] == ':':
        L = [ m["field"] for m in pop(11) ]
        runners.append({"selectionId": int(L[0]),
                        "sortOrder": int(L[1]),
                        "totalAmountMatched": as_float(L[2]),
                        "lastPriceMatched": as_float(L[3]),
                        "handicap": as_float(L[4]),
                        "reductionFactor": as_float(L[5]),
                        "vacant": L[6] == "true",
                        "asianLineId": int(L[7]),
                        "farBSP": as_float(L[8]),
                        "nearBSP": as_float(L[9]),
                        "actualBSP": as_float(L[10])})
        prices = []
        if peek()["rectype"] == "|":
            while not empty():
                L = [ m["field"] for m in pop(5) ]
                price = {"odds": float(L[0]),
                         "totalAvailableBackAmount": float(L[1]),
                         "totalAvailableLayAmount": float(L[2]),
                         "totalBspLayAmount": float(L[3]),
                         "totalBspBackAmount": as_float(L[4])}
                prices.append(price)
                if not empty() and peek()["rectype"] != "":
                    break
        runners[-1]["prices"] = prices
    market_prices["runners"] = runners
    return market_prices


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

