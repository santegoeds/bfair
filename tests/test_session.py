import pytest

from bfair.session import ServiceError

needs_session = pytest.mark.needs_session
skip = pytest.mark.skipif("True")

@needs_session
def test_logout_and_keepalive(session):
    session.logout()
    session.logout()
    with pytest.raises(ServiceError):
        session.keep_alive()
    session.login()
    session.login()
    session.keep_alive()

@needs_session
def test_get_event_types(session):
    all_events = session.get_event_types()
    assert len(all_events) > 0

    active_events = session.get_event_types(active=True)
    assert len(active_events) > 0
    assert len(active_events) <= len(all_events)


@needs_session
def test_get_markets(session):
    all_markets = session.get_markets()
    assert len(all_markets) > 0

    countries = set(m.countryISO3 for m in all_markets)

    markets = session.get_markets(countries=countries)
    assert len(markets) == len(all_markets)

    try:
        countries.remove('')
    except KeyError:
        pass

    if len(countries) > 2:
        country = countries.pop()
        markets = session.get_markets(countries=["ESP"])
        assert len(markets) < len(all_markets)


@pytest.mark.xfail
@needs_session
def test_get_inplay_markets(session):
    markets = session.get_inplay_markets()


@pytest.mark.xfail
@needs_session
def test_get_silks(session):
    silks = session.get_silks()


@pytest.mark.xfail
@needs_session
def test_cancel_bets_by_market(session):
    silks = session.cancel_bets_by_market()


@pytest.mark.xfail
@needs_session
def test_cancel_bets_by_market(session):
    silks = session.cancel_bets_by_market()

