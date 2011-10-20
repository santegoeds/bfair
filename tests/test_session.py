import pytest

needs_session = pytest.mark.needs_session

@needs_session
def test_login_logout(session):
    session.logout()
    session.login()
    session.logout()
    
@needs_session
def test_get_events(session):
    with session as s:
        all_events = s.get_events()
        assert len(all_events) > 0

        active_events = s.get_events(active=True)
        assert len(active_events) > 0
        assert len(active_events) <= len(all_events)

