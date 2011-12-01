import pytest

from bfair.session import ServiceError


def test_logout_and_keepalive(session):
    session.logout()
    session.logout()
    with pytest.raises(ServiceError):
        session.keep_alive()
    session.login()
    session.login()
    session.keep_alive()


def test_get_events(session):
    all_event_types = session.get_event_types()
    assert len(all_event_types) > 0

    active_event_types = session.get_event_types(active=True)
    assert len(active_event_types) > 0
    assert len(active_event_types) <= len(all_event_types)

    events = session.get_events(active_event_types[0].id)
    assert len(events) > 0


def test_get_markets(session):
    all_markets = session.get_markets()
    assert len(all_markets) > 0

    countries = set(m.countryISO3 for m in all_markets)

    has_international = "" in countries

    # Remove empty country code (international markets) because
    # the API does not accept it as input.
    countries ^= set([""])

    markets = session.get_markets(countries=countries)
    if has_international:
        assert len(markets) < len(all_markets)
    else:
        assert len(markets) == len(all_markets)


def test_get_inplay_markets(session):
    with pytest.raises(ServiceError):
        markets = session.get_inplay_markets()


def test_get_silks(session):
    with pytest.raises(ServiceError):
        silks = session.get_silks()


def test_cancel_bets_by_market(session):
    with pytest.raises(ServiceError):
        silks = session.cancel_bets_by_market()


def test_cancel_bets_by_market(session):
    with pytest.raises(ServiceError):
        silks = session.cancel_bets_by_market()

