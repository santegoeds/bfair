#!/usr/bin/env python 

from os import path
from pprint import pprint
from nose.tools import *

from BFService import _util


def test_uncompress_market_prices():
    data_dir = path.join(path.dirname(__file__), "data")
    prices = open("tests/data/compressed_prices").read()
    pprint(_util.uncompress_market_prices(prices))

