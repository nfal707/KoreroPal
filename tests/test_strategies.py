from core.strategies import choose_strategy


def test_study_strategy():
    key, strategy = choose_strategy("I have an exam and cannot focus")
    assert key == "study"


def test_sleep_strategy():
    key, strategy = choose_strategy("I am tired and got no sleep")
    assert key == "sleep"
