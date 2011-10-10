#!/usr/bin/env python 

from os import path
from pprint import pprint

from BFService import _util

from nose.tools import *


def test_uncompress_market_prices():
    data_dir = path.join(path.dirname(__file__), "data")
    with open(path.join(data_dir, "compressed_prices")) as f:
        prices = f.read()
    pprint(_util.uncompress_market_prices(prices))

