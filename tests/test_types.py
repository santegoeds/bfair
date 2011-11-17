from itertools import chain, repeat
from bfair._types import Currency


def test_construct_currency_args():
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

    # Check repr
    assert repr(c) == "<Currency(currencyCode='GBP', rateGBP=1.0, minimumStake=1.0, " \
                                "minimumStakeRange=1.0, minimumBSPLayLiability=1.0)>"

    L = ["GBP", 1.0]
    c = Currency(*L)

    assert c.currencyCode == "GBP"
    assert c.rateGBP == 1.0
    assert c.minimumStake is None
    assert c.minimumStakeRange is None
    assert c.minimumBSPLayLiability is None
    assert len(c) == 5

    # Verify that the attributes are iterable in the
    # correct sequence
    for r, e in zip(c, chain(L, repeat(None))):
        assert r == e

    # Check repr
    assert repr(c) == "<Currency(currencyCode='GBP', rateGBP=1.0, minimumStake=None, " \
                                "minimumStakeRange=None, minimumBSPLayLiability=None)>"


def test_construct_currency_kwargs():
    D = {
        "currencyCode": "GBP",
        "rateGBP": 1.0,
        "minimumStake": 1.0,
        "minimumStakeRange": 1.0,
        "minimumBSPLayLiability": 1.0
    }
    c = Currency(**D)

    # Verify that the right attributes are set
    assert c.currencyCode == "GBP"
    assert c.rateGBP == 1.0
    assert c.minimumStake == 1.0
    assert c.minimumStakeRange == 1.0
    assert c.minimumBSPLayLiability == 1.0
    assert len(c) == 5

    # Verify that the attributes are iterable in the
    # correct sequence
    for r, e in zip(c, ("GBP", 1., 1., 1., 1.)):
        assert r == e

    # Check repr
    assert repr(c) == "<Currency(currencyCode='GBP', rateGBP=1.0, minimumStake=1.0, " \
                                "minimumStakeRange=1.0, minimumBSPLayLiability=1.0)>"

    D = {"currencyCode": "GBP", "rateGBP": 1.0}
    c = Currency(**D)

    assert c.currencyCode == "GBP"
    assert c.rateGBP == 1.0
    assert c.minimumStake is None
    assert c.minimumStakeRange is None
    assert c.minimumBSPLayLiability is None
    assert len(c) == 5

    # Verify that the attributes are iterable in the
    # correct sequence
    for r, e in zip(c, chain(("GBP", 1.), repeat(None))):
        assert r == e

    # Check repr
    assert repr(c) == "<Currency(currencyCode='GBP', rateGBP=1.0, minimumStake=None, " \
                                "minimumStakeRange=None, minimumBSPLayLiability=None)>"
