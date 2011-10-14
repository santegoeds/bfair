
from collections import namedtuple


Market = namedtuple(
    "Market", (
        "marketId",
        "name",
        "marketType",
        "marketStatus",
        "marketTime",
        "menuPath",
        "eventHierarchy",
        "betDelay",
        "exchangeId",
        "countryISO3",
        "lastRefresh",
        "numberOfRunners",
        "numberOfWinners",
        "matchedSize",
        "bspMarket",
        "turningInPlay",
    )
)


Currency = namedtuple(
    "Currency", (
        "currencyCode",
        "rateGBP",
    )
)
Currency.__str__ = lambda self: self.currencyCode


CurrencyV2 = namedtuple(
    "CurrencyV2", (
        "currencyCode",
        "rateGBP",
        "minimumStake",
        "minimumStakeRange",
        "minimumBSPLayLiability",
    )
)
CurrencyV2.__str__ = lambda self: self.currencyCode


MarketPrices = namedtuple(
    "MarketPrices", (
        "marketId",
        "currency",
        "marketStatus",
        "delay",
        "numberOfWinners",
        "marketInfo",
        "discountAllowed",
        "marketBaseRate",
        "lastRefresh",
        "removedRunners",
        "bspMarket",
        "runnerPrices",
    )
)


EventType = namedtuple(
    "EventType", (
        "id",
        "name",
        "nextMarketId",
        "exchangeId",
    )
)


RunnerPrice = namedtuple(
    "RunnerPrice", (
        "selectionId",
        "sortOrder",
        "totalAmountMatched",
        "lastPriceMatched",
        "handicap",
        "reductionFactor",
        "vacant",
        "farBSP",
        "nearBSP",
        "actualBSP",
        "bestPricesToLay",
        "bestPricesToBack",
        "asianLineId",
    )
)


Price = namedtuple(
    "Price", (
        "price",
        "amountAvailable",
        "betType",
        "depth",
    )
)

RemovedRunner = namedtuple(
    "RemovedRunner", (
        "selection_name",
        "removed_date",
        "adjustment_factor"
    )
)

