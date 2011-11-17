
import pytest

from bfair.session import Session

def setup_session(request):
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

def pytest_addoption(parser):
    parser.addoption("--user", action="store")
    parser.addoption("--password", action="store")

def pytest_runtest_setup(item):
    if "needs_session" not in item.keywords:
        return
    option = item.config.option
    if not option.user or not option.password:
        pytest.skip("needs --user and --password")

