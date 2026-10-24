from datetime import date, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from streamlit.testing.v1 import AppTest

import core.ai as ai
import core.content as content
import core.database as database
import core.website as website


@pytest.fixture
def site(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    for module in (database, ai, website):
        monkeypatch.setattr(module, "get_secret", lambda name, default=None: default)
    # Test navigation through the registered pages without changing production routes.
    return AppTest.from_string('''
import app
import streamlit as st
app.main()
with st.expander("Test navigation"):
    page = st.selectbox("Test destination", list(st.session_state.pages))
    if st.button("Open test page"):
        st.switch_page(st.session_state.pages[page])
''', default_timeout=15).run()


def button(site, label):
    return next(item for item in site.button if item.label == label)


def visit(site, page):
    next(item for item in site.selectbox if item.label == "Test destination").set_value(page)
    button(site, "Open test page").click().run()
    assert not site.exception
    return site


def test_all_registered_pages_render(site):
    for page in list(site.session_state.pages):
        visit(site, page)
        assert not site.error, page


def test_resource_search_and_empty_state(site):
    visit(site, "guides")
    search = next(item for item in site.text_input if item.label == "Search resources")
    search.set_value("insomnia").run()
    assert [heading.value for heading in site.subheader] == ["Managing Insomnia"]
    search.set_value("not-a-topic").run()
    assert not site.subheader
    assert "No resources match" in site.info[0].value


def test_journal_survives_navigation_and_clears(site):
    visit(site, "journal")
    site.text_area(key="journal_input").set_value("A test-only journal draft").run()
    visit(site, "home")
    visit(site, "journal")
    assert site.text_area(key="journal_input").value == "A test-only journal draft"
    button(site, "Clear my writing").click().run()
    assert site.text_area(key="journal_input").value == ""
    assert site.session_state.journal_draft == ""


def test_identity_switch_removes_journal_and_habits(site):
    visit(site, "journal")
    site.text_area(key="journal_input").set_value("Private test draft").run()
    visit(site, "goals")
    site.checkbox(key="habit_check_0").check().run()
    button(site, "Start with a new code").click().run()
    assert site.session_state.habit_values == {}
    visit(site, "journal")
    assert site.text_area(key="journal_input").value == ""


def test_habits_survive_navigation_and_reset_next_day(site, monkeypatch):
    today = date(2026, 10, 24)
    monkeypatch.setattr(website, "local_day", lambda: today)
    visit(site, "goals")
    site.checkbox(key="habit_check_1").check().run()
    visit(site, "home")
    visit(site, "goals")
    assert site.checkbox(key="habit_check_1").value is True
    monkeypatch.setattr(website, "local_day", lambda: today + timedelta(days=1))
    site.run()
    assert not any(item.value for item in site.checkbox if item.key.startswith("habit_check_"))


def test_grounding_advances_and_restarts(site):
    visit(site, "practices")
    site.button_group(key="practice_choice").set_value("Notice your senses").run()
    assert button(site, "Previous").disabled
    for step in range(4):
        button(site, "Next step").click().run()
        assert site.session_state.grounding_step == step + 1
    button(site, "Begin again").click().run()
    assert site.session_state.grounding_step == 0


def test_feedback_validates_without_sending(site):
    visit(site, "contact")
    button(site, "Prepare my report").click().run()
    assert site.error
    next(item for item in site.text_input if item.label == "Short subject").set_value("Test-only report")
    site.text_area[0].set_value("This is a local test of the report draft form.")
    site.checkbox[0].check()
    button(site, "Prepare my report").click().run()
    assert not site.error
    assert "Nothing has been sent" in site.success[0].value


def test_search_combines_query_and_topic():
    assert len(content.filter_resources("  INSOMNIA  ", "Sleep")) == 1
    assert not content.filter_resources("insomnia", "Anxiety")
    assert len(content.filter_resources()) == 6


def test_daily_prompts_rotate_and_repeat(monkeypatch):
    monkeypatch.setattr(content, "local_day", lambda: date(2026, 10, 24))
    prompts = [content.daily_prompt(i) for i in range(7)]
    assert len(set(prompts)) == 7
    assert content.daily_prompt(7) == prompts[0]


@pytest.mark.parametrize("subject,message,consent,trap", [
    ("bad", "A valid description with enough detail.", True, ""),
    ("A valid subject", "short", True, ""),
    ("A valid subject", "A valid description with enough detail.", False, ""),
    ("A valid subject", "A valid description with enough detail.", True, "bot"),
    ("x" * 101, "A valid description with enough detail.", True, ""),
    ("A valid subject", "x" * 1501, True, ""),
])
def test_invalid_feedback_rejected(subject, message, consent, trap):
    with pytest.raises(ValueError):
        website.build_feedback_link("Suggestion", subject, message, consent, trap)


def test_feedback_is_encoded_to_the_fixed_issue_destination():
    subject = "A button & its label? #mobile"
    message = "A multiline report\nwith https://example.com/?a=b&c=d"
    parsed = urlparse(website.build_feedback_link("Suggestion", subject, message, True))
    assert parsed.scheme == "https"
    assert parsed.netloc == "github.com"
    assert parsed.path == "/nfal707/KoreroPal/issues/new"
    assert parse_qs(parsed.query) == {"title": [subject], "body": [f"Topic: Suggestion\n\n{message}"]}


def test_daily_reflection_button_opens_journal(site):
    button(site, "Open your journal").click().run()
    assert not site.exception
    assert site.text_area(key="journal_input").value == ""


def test_resources_link_to_providers_and_legacy_guides_redirect(site):
    visit(site, "guides")
    links = [item.proto.url for item in site.get("link_button")]
    assert set(links) == {resource["url"] for resource in content.RESOURCES}
    for path in content.LEGACY_GUIDE_PATHS:
        visit(site, path)
        assert any(item.label == "Search resources" for item in site.text_input)
        assert not any("editorial notes" in item.value for item in site.caption)
