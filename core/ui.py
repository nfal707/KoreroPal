from html import escape
from pathlib import Path
from urllib.parse import quote
from base64 import b64encode
from functools import lru_cache

import streamlit as st


ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"


@lru_cache(maxsize=8)
def asset_url(name):
    path = STATIC / name

    if name == "logo.png":
        encoded = b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    if name == "weave.svg":
        encoded = quote(path.read_text(encoding="utf-8"), safe="")
        return f"data:image/svg+xml,{encoded}"

    raise ValueError(f"Unsupported asset: {name}")


def intro(kicker, title, description):
    st.html(
        '<div class="page-intro">'
        f'<p class="eyebrow">{escape(kicker)}</p>'
        f'<h1>{escape(title)}</h1>'
        f'<p class="intro-copy">{escape(description)}</p>'
        '</div>',
    )


def section_title(kicker, title, description=""):
    st.html(
        '<div class="section-heading">'
        f'<p class="eyebrow">{escape(kicker)}</p>'
        f'<h2>{escape(title)}</h2>'
        f'<p>{escape(description)}</p>'
        '</div>',
    )


def go(page, label, primary=False, key=None):
    if st.button(label, type="primary" if primary else "secondary", key=key):
        st.switch_page(st.session_state.pages[page])


def page_link(page, label, icon=None):
    st.page_link(st.session_state.pages[page], label=label, icon=icon)


def brand_header():
    css = (ROOT / "assets" / "style.css").read_text()
    css = css.replace("/app/static/weave.svg", asset_url("weave.svg"))
    st.html(f"<style>{css}</style>")
    st.logo(str(STATIC / "logo.png"), size="large", link=None)
    st.html(
        '<header class="brandbar">'
        f'<img src="{asset_url("logo.png")}" width="66" height="58" alt="KōreroPal logo">'
        '<div><span class="wordmark">KōreroPal</span><span class="brand-caption">Just the two of us</span></div>'
        '<span class="brand-location">MADE IN AOTEAROA</span></header>'
    )


def safety_note():
    st.html(
        '<aside class="safety-note" aria-label="Wellbeing notice">'
        '<span class="notice-mark" aria-hidden="true">i</span>'
        '<p>KōreroPal is a wellbeing reflection tool, not a therapist, doctor, or crisis service. '
        '<a href="tel:111">Call 111</a> in immediate danger in New Zealand.</p>'
        '</aside>',
    )


def footer():
    st.divider()
    with st.container(key="site_footer"):
        brand, explore, space, information = st.columns([1.7, 1, 1, 1.1], gap="large")
        with brand:
            st.html(
                '<footer>'
                f'<img class="footer-logo" src="{asset_url("logo.png")}" '
                'width="74" height="64" alt="KōreroPal">'
                '<h3>Just the two of us</h3>'
                '<p>Check in, talk things through,<br>and keep track of how you feel.</p>'
                '</footer>',
            )
        with explore:
            st.markdown("**Explore**")
            page_link("practices", "Guided practices")
            page_link("guides", "NZ wellbeing resources")
            page_link("about", "About KōreroPal")
            page_link("resources", "Find real support")
        with space:
            st.markdown("**Your space**")
            page_link("chat", "Start a reflection")
            page_link("checkin", "Daily check-in")
            page_link("journal", "Private journal")
            page_link("goals", "Small habits")
        with information:
            st.markdown("**Good to know**")
            page_link("faq", "Common questions")
            page_link("contact", "Contact & feedback")
            page_link("privacy", "Privacy")
            page_link("terms", "Terms of use")
            page_link("accessibility", "Accessibility")
        st.caption(
            "© 2026 KōreroPal · An independent student portfolio project. General wellbeing "
            "information, not clinical care.",
        )
