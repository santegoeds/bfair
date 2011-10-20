
import pytest

from bfair.session import Session

def pytest_funcarg__session(request):
    user = request.config.option.user
    password = request.config.option.password
    return Session(user, password)

def pytest_addoption(parser):
    parser.addoption("--user", action="store")
    parser.addoption("--password", action="store")

def pytest_runtest_setup(item):
    if "needs_session" not in item.keywords:
        return
    option = item.config.option
    if not option.user or not option.password:
        pytest.skip("needs --user and --password")

