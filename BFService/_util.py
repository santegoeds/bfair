#!/usr/bin/env python

import re

from datetime import datetime
from decimal import Decimal


def from_timestamp(s):
    s = int(s)
    s, ms = s / 1000, s % 1000
    s = datetime.utcfromtimestamp(s)
    s = s.replace(microsecond=ms * 1000)
    return s


def as_decimal(s):
    """Returns a Decimal from a string
    """
    return Decimal("0.0" if not s else s)


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
                                "removed_date": from_timestamp(L[1]),
                                "adjustment_factor": L[2]})
    market_prices["removedRunners"] = removed_runners
    runners = []
    while not empty() and peek()["rectype"] == ':':
        L = [ m["field"] for m in pop(11) ]
        runners.append({"selectionId": int(L[0]),
                        "sortOrder": int(L[1]),
                        "totalAmountMatched": as_decimal(L[2]),
                        "lastPriceMatched": as_decimal(L[3]),
                        "handicap": as_decimal(L[4]),
                        "reductionFactor": as_decimal(L[5]),
                        "vacant": L[6] == "true",
                        "asianLineId": int(L[7]),
                        "farBSP": as_decimal(L[8]),
                        "nearBSP": as_decimal(L[9]),
                        "actualBSP": as_decimal(L[10])})
        prices = []
        if peek()["rectype"] == "|":
            while not empty():
                L = [ m["field"] for m in pop(5) ]
                available = float(L[2]) # To back
                price = {"price": float(L[0]),
                         "amountAvailable": float(L[1]),
                         "bsp_lay_liability": float(L[3]),
                         "bsp_backer_stake_volume": as_decimal(L[4])}
                         "available_to_lay": float(L[2]),
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
        mkt = dict(id = int(fields[0]),
                   name = fields[1],
                   type = fields[2],
                   status = fields[3],
                   date = from_timestamp(fields[4]),
                   path = fields[5],
                   hierarchy = fields[6],
                   delay = fields[7],
                   exchange_id = int(fields[8]),
                   country = fields[9],
                   last_refresh = from_timestamp(fields[10]),
                   no_runners = int(fields[11]),
                   no_winners = int(fields[12]),
                   amount_matched = as_decimal(fields[13]),
                   is_bsp = fields[14] == "Y",
                   is_turning_in_play = fields[15] == "Y")
        markets.append(mkt)
    return markets
