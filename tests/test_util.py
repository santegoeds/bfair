#!/usr/bin/env python 
import pytest

from os import path
from bfair._util import (
    uncompress_market_prices,
    uncompress_markets,
#   uncompress_market_depth,
)

not_implemented = pytest.mark.xfail

DATA_DIR = path.join(path.dirname(__file__), "data")


def test_uncompress_market_prices():
    with open(path.join(DATA_DIR, "market_prices.dump")) as f:
        for line in f:
            uncompress_market_prices(line)


def test_uncompress_markets():
    with open(path.join(DATA_DIR, "markets.dump")) as f:
        for line in f:
            uncompress_markets(line)
        
@not_implemented
def test_uncompress_market_depth():
    with open(path.join(DATA_DIR, "complete_market_prices.dump")) as f:
        for line in f:
            uncompress_market_depth(line)

