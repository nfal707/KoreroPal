from core.identity import create_anonymous_id, valid_anonymous_id


def test_new_codes_have_160_bits_and_legacy_codes_still_work():
    first = create_anonymous_id()
    assert len(first) == 43
    assert first != create_anonymous_id()
    assert valid_anonymous_id(first)
    assert valid_anonymous_id("KP-ABCDEFGHIJ")
    assert not valid_anonymous_id(None)
    assert not valid_anonymous_id("KP-ABCDEFGHIJ&other=1")
