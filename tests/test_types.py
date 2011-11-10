from bfair._types import Currency

def test_currency():
    L = ["GBP", 1.0, 1.0, 1.0, 1.0]
    c = Currency(*L)
    # Verify that the right attributes are set
    assert c.currencyCode == "GBP"
    assert c.rateGBP == 1.0
    assert c.minimumStake == 1.0
    assert c.minimumStakeRange == 1.0
    assert c.minimumBSPLayLiability == 1.0
    assert len(c) == 5
    # Verify that the attributes are iterable in the
    # correct sequence
    for r, e in zip(c, L):
        assert r == e

