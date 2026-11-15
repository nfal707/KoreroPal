from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_homepage_does_not_show_creator_attribution():
    homepage = (ROOT / "core" / "website.py").read_text(encoding="utf-8")
    homepage_intro = homepage.split("def home_page():", 1)[1].split("def newsletter_section(", 1)[0]
    assert "KōreroPal is a wellbeing reflection app for students.</p>" in homepage_intro
    assert "created by Nick Falkov." not in homepage_intro.split('with st.container(key="home_pathways")', 1)[0]


def test_site_fonts_do_not_restyle_streamlit_navigation_icons():
    css = (ROOT / "assets" / "style.css").read_text(encoding="utf-8")
    assert ".stApp button *" not in css
    assert '.stApp [data-testid="stNavigation"] *' not in css
    assert '[data-testid="stSidebarCollapsedControl"] [data-testid="stIconMaterial"]' in css


def test_breathing_timer_uses_wall_clock_and_spaced_layout():
    timer = (ROOT / "assets" / "breathing.html").read_text(encoding="utf-8")
    assert "deadline - Date.now()" in timer
    assert "setInterval(tick, 100)" in timer
    assert "min-height: 270px;" in timer
    assert "if (document.hidden) pause()" not in timer
