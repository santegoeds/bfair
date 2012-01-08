import pytest

from datetime import datetime
from itertools import izip
from bfair.session import ServiceError


def test_logout_and_keepalive(session):
    session.logout()
    session.logout()
    session.keep_alive()
    session.login()
    session.login()
    session.keep_alive()


def test_get_event_types(session):
    # Active event types
    types = session.get_event_types()
    assert len(types) > 0
    for type in types:
        assert_type(type)

    # All event types
    all_types = session.get_event_types(active=False)
    assert len(all_types) > 0
    assert len(types) <= len(all_types)
    for type in all_types:
        assert_type(type)


def test_get_event_info(session):
    # Get Active event types
    types = session.get_event_types()

    event_info = session.get_event_info(types[0].id)

    assert isinstance(event_info.eventParentId, int)
    assert isinstance(event_info.eventItems, list)
    assert isinstance(event_info.marketItems, list)
    assert isinstance(event_info.couponLinks, list)
    assert event_info.eventItems or event_info.marketItems


def test_get_market_info(session):
    def event_infos(ids):
        for id in ids:
            info = session.get_event_info(id)
            yield info
            for info in event_infos(e.eventId for e in info.eventItems):
                yield info
                
    # Navigate to an available market
    type_ids = (type.id for type in session.get_event_types())
    infos = event_infos(type_ids)
    summaries = (m for info in infos for m in info.marketItems)

    market_summary = summaries.next()

    assert isinstance(market_summary.eventTypeId, int)
    assert isinstance(market_summary.marketId, int)
    assert isinstance(market_summary.marketName, basestring)
    assert isinstance(market_summary.marketType, basestring)
    assert isinstance(market_summary.marketTypeVariant, basestring)
    assert isinstance(market_summary.menuLevel, int)
    assert isinstance(market_summary.orderIndex, int)
    assert isinstance(market_summary.startTime, datetime)
    assert isinstance(market_summary.timezone, basestring)
    assert isinstance(market_summary.venue, (basestring, type(None)))
    assert isinstance(market_summary.betDelay, int)
    assert isinstance(market_summary.numberOfWinners, int)
    assert isinstance(market_summary.eventParentId, int)
    assert isinstance(market_summary.exchangeId, int)
    
    market_id = market_summary.marketId

    lite = session.get_market_info_lite(market_id)
    assert isinstance(lite.marketStatus, basestring)
    assert isinstance(lite.marketSuspendTime, datetime)
    assert isinstance(lite.marketTime, datetime)
    assert isinstance(lite.numberOfRunners, int)
    assert isinstance(lite.delay, int)
    assert isinstance(lite.reconciled, bool)
    assert isinstance(lite.openForBspBetting, bool)

    info = session.get_market_info(market_id)
    assert_market_info(info)
    assert len(info.couponLinks) == 0

    info = session.get_market_info(market_id, coupon_links=True)
    assert_market_info(info)


def test_get_markets(session):
    all_markets = session.get_markets()
    assert len(all_markets) > 0

    countries = set(m.countryISO3 for m in all_markets)

    has_international = "" in countries

    # Remove empty country code (international markets) because
    # the API does not accept it as input.
    countries &= (countries ^ set([""]))

    markets = session.get_markets(countries=countries)
    if has_international:
        assert len(markets) < len(all_markets)
    else:
        assert len(markets) == len(all_markets)


@pytest.mark.xfail
def test_get_bet_info(session):
    info = sesison.get_bet_info()

@pytest.mark.xfail
def test_get_inplay_markets(session):
    markets = session.get_inplay_markets()


@pytest.mark.xfail
def test_cancel_bets(session):
    session.cancel_bets()


@pytest.mark.xfail
def test_place_bets(session):
    session.place_bets()


@pytest.mark.xfail
def test_update_bets(session):
    session.update_bets()


@pytest.mark.xfail
def test_get_bet_history(session):
    session.get_bet_history()


@pytest.mark.xfail
def test_get_bet_matches_lite(session):
    session.get_bet_matches_lite()


@pytest.mark.xfail
def test_get_current_bets(session):
    session.get_current_bets()
    session.get_current_bets_lite()


@pytest.mark.xfail
def test_get_matched_and_unmatched_bets(session):
    session.get_matched_and_unmatched_bets()


@pytest.mark.xfail
def test_get_market_profit_loss(session):
    session.get_market_profit_loss()

@pytest.mark.xfail
def test_get_market_traded_volume(session):
    session.get_market_traded_volume()


@pytest.mark.xfail
def test_get_market_traded_volume_compressed(session):
    session.get_market_traded_volume_compressed()


@pytest.mark.xfail
def test_get_private_markets(session):
    session.get_private_markets()


@pytest.mark.xfail
def test_get_silks(session):
    silks = session.get_silks()
    #session.get_sliks_v2()


@pytest.mark.xfail
def test_get_market_prices(session):
    session.get_market_prices()


@pytest.mark.xfail
def test_get_market_depth(session):
    session.get_market_depth()


@pytest.mark.xfail
def test_add_payment_card(session):
    session.add_payment_card()


@pytest.mark.xfail
def test_delete_payment_card(session):
    session.delete_payment_card()


@pytest.mark.xfail
def test_deposit_from_payment_card(session):
    session.deposit_from_payment_card()


@pytest.mark.xfail
def test_forgot_password(session):
    session.forgot_password()


@pytest.mark.xfail
def test_get_account_funds(session):
    session.get_account_funds()


@pytest.mark.xfail
def test_get_account_statement(session):
    session.get_account_statement()


@pytest.mark.xfail
def test_get_payment_card(session):
    session.get_payment_card()


@pytest.mark.xfail
def test_get_subscription_info(session):
    session.get_subscription_info()


@pytest.mark.xfail
def test_modify_password(session):
    session.modify_password()


@pytest.mark.xfail
def test_modify_profile(session):
    session.modify_profile()


@pytest.mark.xfail
def test_retrieve_limb_message(session):
    session.retrieve_limb_message()


@pytest.mark.xfail
def test_self_exclude(session):
    session.self_exclude()


@pytest.mark.xfail
def test_set_chat_name(session):
    session.set_chat_name()


@pytest.mark.xfail
def test_submit_limb_message(session):
    session.submit_limb_message()


@pytest.mark.xfail
def test_transfer_funds(session):
    session.transfer_funds()


@pytest.mark.xfail
def test_update_payment_card(session):
    session.update_payment_card()


@pytest.mark.xfail
def test_view_profile(session):
    session.view_profile()
    session.view_profile_v2()


@pytest.mark.xfail
def test_view_refer_and_earn(session):
    session.view_refer_and_earn()


@pytest.mark.xfail
def test_withdraw_to_payment_card(session):
    session.withdraw_to_payment_card()


@pytest.mark.xfail
def test_cancel_bets_by_market(session):
    session.cancel_bets_by_market()


def assert_type(type_):
    assert isinstance(type_.id, int)
    assert isinstance(type_.name, basestring)
    assert isinstance(type_.nextMarketId, int)
    assert isinstance(type_.exchangeId, int)


def assert_market_info(mi):
    assert isinstance(mi.marketStatus, basestring)
    assert isinstance(mi.marketSuspendTime, datetime)
    assert isinstance(mi.marketTime, datetime)
    assert isinstance(mi.bspMarket, bool)
    assert isinstance(mi.countryISO3, basestring)
    assert isinstance(mi.couponLinks, list)
    assert isinstance(mi.discountAllowed, bool)
    assert isinstance(mi.eventHierarchy, list)
    assert isinstance(mi.eventTypeId, int)
    assert isinstance(mi.interval, float)
    assert isinstance(mi.licenceId, int)
    assert isinstance(mi.marketBaseRate, float)
    assert isinstance(mi.marketDescription, basestring)
    assert isinstance(mi.marketDescriptionHasDate, bool)
    assert isinstance(mi.marketDisplayTime, datetime)
    assert isinstance(mi.marketId, int)
    assert isinstance(mi.marketType, basestring)
    assert isinstance(mi.marketTypeVariant, basestring)
    assert isinstance(mi.maxUnitValue, float)
    assert isinstance(mi.menuPath, basestring)
    assert isinstance(mi.minUnitValue, float)
    assert isinstance(mi.name, basestring)
    assert isinstance(mi.numberOfWinners, int)
    assert isinstance(mi.parentEventId, int)
    assert isinstance(mi.runners, list)
    assert isinstance(mi.runnersMayBeAdded, bool)
    assert isinstance(mi.timezone, basestring)
    assert mi.unit is None or isinstance(mi.unit, int)

    for evt in mi.eventHierarchy:
        assert isinstance(evt, int)

    for runner in mi.runners:
        assert isinstance(runner.asianLineId, int)
        assert isinstance(runner.handicap, float)
        assert isinstance(runner.name, basestring)
        assert isinstance(runner.selectionId, int)

    for cl in mi.couponLinks:
        assert isinstance(cl.couponId, int)
        assert isinstance(cl.couponName, basestring)

