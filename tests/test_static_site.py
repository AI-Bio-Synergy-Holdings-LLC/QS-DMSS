from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = REPO_ROOT / "site"
GITHUB_SOCIAL_PREVIEW_SIZE = (1280, 640)
SITE_SOCIAL_PREVIEW_SIZE = (1200, 630)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


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
        "What researchers can find here.",
        "QuantumScalar dark matter simulation workflows",
        "Live demo coming next at app.qs-dmss.studio.",
        "not peer-reviewed scientific validation",
        'name="twitter:card" content="summary_large_image"',
    ]

    for fragment in required_fragments:
        assert fragment in rendered_text


def test_static_site_cname_matches_public_domain() -> None:
    assert (SITE_ROOT / "CNAME").read_text(encoding="utf-8").strip() == "qs-dmss.studio"


def test_google_search_console_verification_file_is_preserved() -> None:
    verification_file = SITE_ROOT / "google67df4bb4cd1d4c1e.html"

    assert verification_file.read_text(encoding="utf-8").strip() == (
        "google-site-verification: google67df4bb4cd1d4c1e.html"
    )


def test_static_site_metadata_hardening() -> None:
    index = (SITE_ROOT / "index.html").read_text(encoding="utf-8")
    robots = (SITE_ROOT / "robots.txt").read_text(encoding="utf-8")
    sitemap = (SITE_ROOT / "sitemap.xml").read_text(encoding="utf-8")
    llms = (SITE_ROOT / "llms.txt").read_text(encoding="utf-8")

    required_fragments = [
        'content="index, follow, max-image-preview:large"',
        'name="keywords"',
        'content="QS-DMSS, QuantumScalar dark matter',
        'rel="sitemap" type="application/xml" href="https://qs-dmss.studio/sitemap.xml"',
        'property="og:site_name" content="QS-DMSS Studio"',
        'property="og:locale" content="en_US"',
        'property="og:image" content="https://qs-dmss.studio/assets/social-preview.png"',
        'property="og:image:width" content="1200"',
        'property="og:image:height" content="630"',
        'name="twitter:card" content="summary_large_image"',
        'name="twitter:image" content="https://qs-dmss.studio/assets/social-preview.png"',
        'rel="icon" href="favicon.svg" type="image/svg+xml"',
    ]

    for fragment in required_fragments:
        assert fragment in index

    assert "Sitemap: https://qs-dmss.studio/sitemap.xml" in robots
    assert "Allow: /llms.txt" in robots
    assert "<loc>https://qs-dmss.studio/</loc>" in sitemap
    assert "<lastmod>2026-07-09</lastmod>" in sitemap
    assert "<image:loc>https://qs-dmss.studio/assets/social-preview.png</image:loc>" in sitemap
    assert "Latest archived release DOI: https://doi.org/10.5281/zenodo.21270512" in llms

    json_ld_match = re.search(
        r'<script type="application/ld\+json">\s*(.*?)\s*</script>',
        index,
        flags=re.DOTALL,
    )
    assert json_ld_match
    structured_data = json.loads(json_ld_match.group(1))
    graph_types = {item["@type"] for item in structured_data["@graph"]}
    assert {"Organization", "WebSite", "WebPage", "SoftwareSourceCode", "SoftwareApplication"} <= graph_types


def test_static_site_favicon_matches_studio_mark() -> None:
    favicon = (SITE_ROOT / "favicon.svg").read_text(encoding="utf-8")

    assert 'aria-label="QS-DMSS Studio"' in favicon
    assert 'rx="17" fill="#101a18"' in favicon
    assert 'stroke="#e0b85d"' in favicon
    assert 'fill="#e0b85d"' in favicon
    assert 'text-anchor="middle">QS</text>' in favicon
    assert "#4aa3a0" not in favicon


def test_static_site_social_preview_dimensions() -> None:
    assert _png_dimensions(SITE_ROOT / "assets" / "social-preview.png") == SITE_SOCIAL_PREVIEW_SIZE


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


def test_social_preview_assets_are_publishable() -> None:
    docs_asset = REPO_ROOT / "docs" / "assets" / "social-preview.png"
    site_asset = SITE_ROOT / "assets" / "social-preview.png"

    assert _png_dimensions(docs_asset) == GITHUB_SOCIAL_PREVIEW_SIZE
    assert _png_dimensions(site_asset) == SITE_SOCIAL_PREVIEW_SIZE
    assert docs_asset.stat().st_size > 10_000
    assert site_asset.stat().st_size > 10_000
