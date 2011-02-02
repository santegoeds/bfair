#!/usr/bin/env python

import re

from datetime import datetime


def as_datetime(s):
    s = int(s)
    s, ms = s / 1000, s % 1000
    s = datetime.utcfromtimestamp(s)
    s = s.replace(microsecond=ms * 1000)
    return s


def as_float(s):
    """Returns a float from a string
    """
    return 0.0 if not s else float(s)


def uncompress_market_prices(data):
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
                available = float(L[2]) # To back
                price = {"price": float(L[0]),
                         "amountAvailable": float(L[1]),
                         "bsp_lay_liability": float(L[3]),
                         "bsp_backer_stake_volume": as_float(L[4]),
                         "available_to_lay": float(L[2])}
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

