from bfair._types import Currency

def test_currency():
    c = Currency("GBP", 1.0)
    assert c.currencyCode == "GBP"
    assert c.rateGBP == 1.0
    assert len(c) == 2
    for r, e in zip(c, ["GBP", 1.0]):
        assert r == e

