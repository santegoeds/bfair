#!/usr/bin/env python 

from nose.tools import *
from pprint import pprint

from BFService import _util


def test_uncompress_market_prices():
    prices = open("tests/data/compressed_prices").read()
    pprint(_util.uncompress_market_prices(prices))


