
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
