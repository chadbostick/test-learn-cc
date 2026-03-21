from src.utils import hello


def test_hello_default():
    assert hello() == "Hello, world!"


def test_hello_name():
    assert hello("Claude") == "Hello, Claude!"
