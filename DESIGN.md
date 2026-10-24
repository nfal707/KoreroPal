# KōreroPal design notes

The design keeps the original olive identity and gives the content more room. Display headings use Georgia, with system fonts for readable body text and controls. There are no external font requests.

## Shared design

`assets/style.css` contains the reusable palette and component rules:

- Warm paper `#f8f7f2` for the page and `#fdfcf8` for forms.
- Forest `#294035` for headings and important sections.
- Olive `#56694a` for primary actions.
- Sage `#e7ecdf`, sand `#efe9df` and lilac `#eee9ed` for restrained accents.
- Ink `#2d3b32`, muted text `#5d685c`, and borders `#d9ded1`.
- Visible focus outlines, 44px action buttons, reduced-motion rules, and a narrower border on small screens.

`core/ui.py` owns the shared header, notice, page introductions, links and footer. `core/website.py` holds the public pages and everyday practices. The existing Python chat, ratings and database modules remain in use. Page URLs and titles describe their contents.

## Asset provenance

`assets/koreropal-logo.png` is the user's original supplied logo screenshot. `scripts/prepare_logo.py` removes its pale paper/grid with a deterministic mask and edge correction; it does not generate or redraw the artwork. `static/logo.png` is a 700px RGBA PNG with real alpha transparency, reused at smaller sizes in the header, navigation, footer and About page.

`static/weave.svg` is a small original vector pattern made in code. Its alternating strips suggest the structure of harakeke weaving. It is decorative, fades into the paper background and scrolls with the main content using a local background attachment. Its repeating tile is seamless, and it does not intercept input. It does not reproduce the supplied watermarked painting or claim a named iwi pattern, cultural endorsement or partnership. The About page links to Te Papa's explanation of raranga. Seek local cultural review before making more specific cultural claims or using named traditional designs.

There are no AI-generated photos, illustrations, logos or other generated media in the site. The interface uses the original brand asset, code-native patterns, typography and functional controls.

## Content and behaviour

The directory links directly to Just a Thought courses, The Wellbeing Space, and Depression.org.nz, including stress, sleep and rangatahi resources. Cards identify each provider and account requirements. There are no KōreroPal-written guide articles; old article URLs redirect to the resource directory. Short descriptions help students choose where to go without reproducing provider content or implying affiliation.

Breathing, grounding, resource search, journal download and clearing, daily habit choices, chat and rating forms have real behaviour. A feedback form prepares a validated GitHub issue draft and says clearly that it has not sent it. Newsletter signup remains hidden unless a real HTTPS subscription page is configured.

## Hosting limits

Streamlit provides application navigation, page titles, semantic routes and a skip link. It is not a server-rendered publishing system with per-article metadata and canonical tags. No public host has been guessed, so there is no fabricated sitemap or structured data. If search indexing becomes a requirement, place public editorial pages on a publishing layer with verified canonical URLs and keep the private reflection application separate.

The layout is responsive and includes visible keyboard focus and reduced-motion support. These are practical improvements, not an independent WCAG certification. The app remains a portfolio wellbeing tool with the privacy and provider limits described in `PRIVACY.md` and `DEPLOYMENT.md`.
