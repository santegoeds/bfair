import pytest

from bfair.session import Session


def pytest_addoption(parser):
    parser.addoption("--user", action="store")
    parser.addoption("--password", action="store")


def setup_session(request):
    if not request.config.option.user or not request.config.option.password:
        pytest.skip("needs --user and --password")
    user = request.config.option.user
    password = request.config.option.password
    session = Session(user, password)
    session.login()
    return session


def teardown_session(session):
    session.logout()
                      

def pytest_funcarg__session(request):
    return request.cached_setup(setup = lambda: setup_session(request),
                                teardown = teardown_session,
                                scope = "session")


