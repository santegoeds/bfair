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

from os import path
from suds.client import Client


__all__ = [
    "BFGlobalService", "BFGlobalFactory", "BFExchangeService", "BFExchangeFactory",
    "APIErrorEnum", "GetEventsErrorEnum", "ConvertCurrencyErrorEnum", "GetBetErrorEnum",
    "GetAllMarketsErrorEnum", "GetCompleteMarketPricesErrorEnum", "GetInPlayMarketsErrorEnum",
    "GetMarketPricesErrorEnum",
]


BFGlobalServiceUrl = "file://" + path.abspath(path.join(path.dirname(__file__), "wsdl/BFGlobalService.wsdl"))
BFGlobalServiceUrl = "https://api.betfair.com/global/v3/BFGlobalService.wsdl"
BFGlobalServiceClient = Client(BFGlobalServiceUrl)
BFGlobalService = BFGlobalServiceClient.service
BFGlobalFactory = BFGlobalServiceClient.factory

BFExchangeServiceUrl = "file://" + path.abspath(path.join(path.dirname(__file__), "wsdl/BFExchangeService.wsdl"))
BFExchangeServiceUrl = "https://api.betfair.com/exchange/v5/BFExchangeService.wsdl"
BFExchangeServiceClient = Client(BFExchangeServiceUrl)
BFExchangeService = BFExchangeServiceClient.service
BFExchangeFactory = BFExchangeServiceClient.factory

# Error enumerations
APIErrorEnum = BFGlobalFactory.create("ns1:APIErrorEnum")
GetEventsErrorEnum = BFGlobalFactory.create("ns1:GetEventsErrorEnum")
ConvertCurrencyErrorEnum = BFGlobalFactory.create("ns1:ConvertCurrencyErrorEnum")
GetBetErrorEnum = BFExchangeFactory.create("ns1:GetBetErrorEnum")
GetAllMarketsErrorEnum = BFExchangeFactory.create("ns1:GetAllMarketsErrorEnum")
GetCompleteMarketPricesErrorEnum = BFExchangeFactory.create("ns1:GetCompleteMarketPricesErrorEnum")
GetInPlayMarketsErrorEnum = BFExchangeFactory.create("ns1:GetInPlayMarketsErrorEnum")
GetMarketPricesErrorEnum = BFExchangeFactory.create("ns1:GetMarketPricesErrorEnum")

