from core.safety import assess_risk


def test_crisis_risk():
    assert assess_risk("I want to die") == "crisis"


def test_high_risk():
    assert assess_risk("I feel hopeless and overwhelmed") == "high"


def test_normal_risk():
    assert assess_risk("I feel stressed about uni") == "normal"
