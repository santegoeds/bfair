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
    countries &= (countries ^ set([""]))

    markets = session.get_markets(countries=countries)
    if has_international:
        assert len(markets) < len(all_markets)
    else:
        assert len(markets) == len(all_markets)


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
def test_get_market_info(session):
    session.get_market_info()


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

