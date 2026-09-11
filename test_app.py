# test_app.py

from app import hello


def test_hello():
    assert hello() == "Hello CI/CD!"