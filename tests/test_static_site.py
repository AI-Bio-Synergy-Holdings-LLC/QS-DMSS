from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = REPO_ROOT / "site"


class _AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.anchor_hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_map = dict(attrs)
        if element_id := attrs_map.get("id"):
            self.ids.add(element_id)
        if tag == "a" and (href := attrs_map.get("href")):
            self.anchor_hrefs.append(href)


def test_static_site_front_door_contract() -> None:
    index = (SITE_ROOT / "index.html").read_text(encoding="utf-8")
    rendered_text = " ".join(index.split())

    required_fragments = [
        "Run simulations. Inspect evidence. Compare campaigns. Publish reproducible artifacts.",
        "Install from PyPI",
        "View GitHub",
        "Run local cockpit",
        "Read DOI",
        "Support on Open Collective",
        "Lab Mode",
        "Campaign Studio",
        "Evidence Bundles",
        "Publication Export",
        "Dry-Run Slurm Review",
        "Scientific Boundaries",
        "Live demo coming next at app.qs-dmss.studio.",
        "not peer-reviewed scientific validation",
    ]

    for fragment in required_fragments:
        assert fragment in rendered_text


def test_static_site_cname_matches_public_domain() -> None:
    assert (SITE_ROOT / "CNAME").read_text(encoding="utf-8").strip() == "qs-dmss.studio"


def test_static_site_local_anchor_links_resolve() -> None:
    index = (SITE_ROOT / "index.html").read_text(encoding="utf-8")
    parser = _AnchorParser()
    parser.feed(index)

    local_anchor_targets = [
        href.removeprefix("#")
        for href in parser.anchor_hrefs
        if href.startswith("#") and href != "#"
    ]

    assert local_anchor_targets
    for target in local_anchor_targets:
        assert target in parser.ids
