#!/usr/bin/env python 

from os import path
from pprint import pprint

from BFService._util import uncompress_market_prices


def test_uncompress_market_prices():
    data_dir = path.join(path.dirname(__file__), "data")
    with open("../compressed_prices") as f:
        prices = f.readline().strip()
        pprint(uncompress_market_prices(prices))
        assert False

