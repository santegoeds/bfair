

def pytest_funcarg__session(request):
    #import pdb; pdb.set_trace()
    user = request.config.inicfg.get("betfair_user")
    password = request.config.inicfg.get("betfair_password")
    return user, password


def test_example(session):
    assert session[0] == "santegoeds"
