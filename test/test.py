#!/usr/bin/env python 

from nose.tools import *
from pprint import pprint

from BFService import util

prices = open("test/compressed_prices").read()

pprint(util.uncompress_market_prices(prices))


