"""Check presentation-copy fidelity, not new scientific calculations."""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "site/challenges/sc-graph-001"
PACKET_SHA = "17e568bf7944972c57eda3f275ec7a1126f1cd3d92a4fa04308063425ef02ba4"
DATA_SHA = "ed955ee0de108dddfd652a5cf0f847bbfc10332a9292623a5cf644ba5bfaf1ec"
URL = "https://qs-dmss.studio/challenges/sc-graph-001/"
SOURCE_CHECKOUT = (ROOT / ".git").exists()
WEB_VIDEO = "boundary-explanation-web-v1.mp4"
WEB_VIDEO_SHA = "e88cc89d77a3989c725a67fbbd411d2e35134ccad6fac96e5a6dba037c4840e6"
ORIGINAL_VIDEO_SHA = "0e49295279b8698655fe896415adc7873bd3bfa2d2222960d86517427d2b2404"
MAX_GIT_BLOB_BYTES = 10 * 1024 * 1024


class PageParser(HTMLParser):
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self):
        super().__init__()
        self.nodes = []
        self.contexts = []
        self.stack = []

    def handle_starttag(self, tag, attrs):
        node = (tag, dict(attrs))
        self.nodes.append(node)
        self.contexts.append((*node, tuple(self.stack)))
        if tag not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def test_transcript_link_is_outside_video_fallback_and_keyboard_reachable():
    parser = PageParser()
    parser.feed((PAGE / "index.html").read_text(encoding="utf-8"))
    links = [
        (attrs, ancestors)
        for tag, attrs, ancestors in parser.contexts
        if tag == "a" and attrs.get("id") == "video-transcript"
    ]
    assert len(links) == 1
    attrs, ancestors = links[0]
    assert attrs["href"] == "transcript.txt"
    assert not any(tag == "video" for tag, _ in ancestors)
    assert any("demonstration" in a.get("class", "").split() for _, a in ancestors)
    assert not any("hidden" in a or "inert" in a for _, a in ancestors)
    assert attrs.get("tabindex") is None
    assert (PAGE / attrs["href"]).is_file()


def test_explorer_source_order_matches_responsive_region_order():
    parser = PageParser()
    parser.feed((PAGE / "index.html").read_text(encoding="utf-8"))
    regions = [
        attrs.get("class")
        for _, attrs, ancestors in parser.contexts
        if ancestors and "workbench" in ancestors[-1][1].get("class", "").split()
    ]
    assert regions == ["graph-panel", "controls", "evidence-panel"]
    for _, attrs in parser.nodes:
        if "tabindex" in attrs:
            assert int(attrs["tabindex"]) <= 0
    css = (PAGE / "styles.css").read_text(encoding="utf-8")
    assert not re.search(r"(?m)^\s*order\s*:", css)
    assert "display: contents" not in css
    normalized = re.sub(r"\s+", " ", css)
    assert 'grid-template-areas: "graph controls" "graph evidence";' in normalized
    assert 'grid-template-areas: "graph" "controls" "evidence";' in normalized


def test_exact_presentation_bytes_and_manifest():
    raw = (PAGE / "data.json").read_bytes()
    manifest = json.loads((PAGE / "manifest.json").read_bytes())
    assert len(raw) == 39979
    assert hashlib.sha256(raw).hexdigest() == DATA_SHA == manifest["data_sha256"]
    assert manifest["data_bytes"] == len(raw)
    assert manifest["source_packet_sha256"] == PACKET_SHA
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "site/challenges/sc-graph-001/* text eol=lf" in attributes


def test_every_displayed_array_record_and_pointer_is_retained():
    raw = (ROOT / "docs/review-evidence/falsification-pilot-v1.zip").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == PACKET_SHA
    display = json.loads((PAGE / "data.json").read_bytes())
    with zipfile.ZipFile(io.BytesIO(raw)) as packet:
        hashes = json.loads(packet.read("manifest.sha256.json"))
        for name, digest in hashes.items():
            assert hashlib.sha256(packet.read(name)).hexdigest() == digest
        report = json.loads(packet.read("results.json"))
        records = report["exercises"]["graph"]
        assert len(records) == display["full_registered_graph_cases"] == 15
        assert display["source_recorded_at"] == report["created_utc"]
        assert display["measurement_member_sha256"] == hashes["measurements.npz"]
        with np.load(
            io.BytesIO(packet.read("measurements.npz")), allow_pickle=False
        ) as arrays:
            for case in display["cases"]:
                record_index = next(
                    i
                    for i, r in enumerate(records)
                    if r["artifact_prefix"] == case["id"]
                )
                assert case["record"] == records[record_index]
                assert (
                    case["pointers"]["record"]
                    == f"results.json#/exercises/graph/{record_index}"
                )
                for source in ("candidate", "reference"):
                    for field, values in case[source].items():
                        key = f"{case['id']}_{source}_{field}"
                        assert values == arrays[key].tolist()
                        assert (
                            case["pointers"][f"{source}.{field}"]
                            == f"measurements.npz#{key}"
                        )


def test_scientific_status_and_acceptance_scope_match_registry():
    display = json.loads((PAGE / "data.json").read_bytes())
    registry = json.loads((ROOT / "research/challenges/registry-v1.json").read_bytes())
    challenge = next(c for c in registry["challenges"] if c["id"] == "SC-GRAPH-001")
    assert display["source_commit"] == registry["candidate"]["source_commit"]
    assert display["scientific_assessment"] == challenge["scientific_assessment"]
    assert display["acceptance_limits"] == challenge["acceptance_limits"]
    assert display["scientific_assessment"]["status"] == "NOT_ESTABLISHED"
    assert display["scientific_assessment"]["independent_review"] == "PENDING"
    assert display["scientific_assessment"]["human_disposition"] == "PENDING"


def test_metadata_is_static_canonical_and_different_from_homepage():
    parser = PageParser()
    html = (PAGE / "index.html").read_text(encoding="utf-8")
    parser.feed(html)
    metadata = {
        a.get("property", a.get("name")): a.get("content")
        for t, a in parser.nodes
        if t == "meta"
    }
    assert metadata["og:url"] == URL
    assert metadata["og:image"] == URL + "social-card-v1.png"
    assert metadata["og:image:width"] == "1200"
    assert metadata["og:image:height"] == "630"
    assert metadata["twitter:image"] == metadata["og:image"]
    assert metadata["twitter:card"] == "summary_large_image"
    assert "pending" in metadata["og:description"]
    assert "frozen" in metadata["twitter:description"].lower()
    assert any(
        t == "link" and a.get("rel") == "canonical" and a.get("href") == URL
        for t, a in parser.nodes
    )
    assert "social-preview-v0132.png" not in html
    assert 'href="challenges/sc-graph-001/"' in (ROOT / "site/index.html").read_text(
        encoding="utf-8"
    )
    ET.parse(ROOT / "site/sitemap.xml")
    assert URL in (ROOT / "site/sitemap.xml").read_text(encoding="utf-8")


def test_current_csp_needs_no_new_inline_exception_or_remote_runtime():
    parser = PageParser()
    parser.feed((PAGE / "index.html").read_text(encoding="utf-8"))
    for tag, attrs in parser.nodes:
        assert "style" not in attrs
        assert not any(k.startswith("on") for k in attrs)
        if tag in ("script", "source", "video", "track", "img"):
            for key in ("src", "poster"):
                if value := attrs.get(key):
                    assert not value.startswith(("http:", "https:", "//", "data:"))
                    # Sdists retain small test fixtures, not the portal-only MP4.
                    # A source checkout must contain every deployment asset.
                    if not value.endswith(".mp4") or SOURCE_CHECKOUT:
                        assert (PAGE / value).is_file()
        if tag == "script":
            assert attrs.get("src") == "app.mjs"
        assert tag not in ("iframe", "form", "object", "embed", "style")
    code = (PAGE / "app.mjs").read_text(encoding="utf-8")
    assert "innerHTML" not in code and "insertAdjacentHTML" not in code
    assert "textContent" in code
    assert "AbortController" in code and "15000" in code
    assert "readBoundedBytes(response,MAX_DATA_BYTES)" in re.sub(r"\s", "", code)
    for filename in ("data.json", "manifest.json"):
        assert re.search(r"fetch\(\s*['\"]\./" + re.escape(filename) + r"['\"]", code)
    assert "/api/" not in code and "localStorage" not in code


def test_media_provenance_preserves_approved_original_and_delivery_contract():
    provenance = json.loads((PAGE / "media-provenance.json").read_bytes())
    assert provenance["schema_version"] == 2
    assert provenance["video"] == WEB_VIDEO
    assert provenance["video_sha256"] == WEB_VIDEO_SHA
    assert provenance["video_bytes"] == 1986425 <= MAX_GIT_BLOB_BYTES
    original = provenance["approved_original"]
    assert original["sha256"] == ORIGINAL_VIDEO_SHA
    assert original["bytes"] == 15981923
    assert original["git_commit"] == "5e094782dd0926475350533a54e0e6150ceb2494"
    assert original["git_path"] == (
        "site/challenges/sc-graph-001/boundary-explanation-v2.mp4"
    )
    assert not (PAGE / original["filename"]).exists()
    derivative = provenance["delivery_derivation"]
    assert derivative["source_sha256"] == original["sha256"]
    assert derivative["maximum_git_blob_bytes"] == MAX_GIT_BLOB_BYTES
    assert derivative["verification"]["decoded_frames"] == 1800
    assert derivative["verification"]["audio_compressed_payload_identical"] is True
    assert derivative["verification"]["approved_original_sha256_rechecked"] is True
    assert derivative["verification"]["global_metadata_copied_from_approved"] is True
    assert derivative["verification"]["fast_start"] is True
    assert derivative["verification"]["fps"] == 30
    assert provenance["dimensions"] == [1080, 1350]
    assert provenance["scientific_status"] == "NOT_ESTABLISHED"
    assert provenance["independent_review"] == "PENDING"
    assert provenance["candidate_source"] == (
        "48d7ab5d10da189caddbcad1dd6622e58d204940"
    )
    for filename, key in (
        ("video-poster.png", "poster_sha256"),
        ("explanations.vtt", "explanations_vtt_sha256"),
        ("transcript.txt", "transcript_sha256"),
    ):
        assert (
            hashlib.sha256((PAGE / filename).read_bytes()).hexdigest()
            == provenance[key]
        )
    assert provenance["duration_seconds"] == 60
    assert provenance["music"]["recording_license"] == "CC0-1.0"
    html = (PAGE / "index.html").read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    videos = [a for t, a in parser.nodes if t == "video"]
    assert len(videos) == 1
    assert "controls" in videos[0] and "playsinline" in videos[0]
    assert videos[0]["preload"] == "none" and "autoplay" not in videos[0]
    sources = [a for t, a in parser.nodes if t == "source"]
    assert sources == [{"src": WEB_VIDEO, "type": "video/mp4"}]
    assert "continuous screen recording" in html and "No spoken narration" in html
    assert (
        (PAGE / "explanations.vtt").read_text(encoding="utf-8").startswith("WEBVTT\n")
    )
    assert "00:00:53.000 --> 00:01:00.000" in (PAGE / "explanations.vtt").read_text(
        encoding="utf-8"
    )
    assert "NOT_ESTABLISHED" in (PAGE / "transcript.txt").read_text(encoding="utf-8")


@pytest.mark.skipif(
    not SOURCE_CHECKOUT and not (PAGE / WEB_VIDEO).is_file(),
    reason="Portal-only MP4 is intentionally excluded from Python distributions",
)
def test_web_delivery_has_exact_identity_and_obeys_unchanged_size_policy():
    provenance = json.loads((PAGE / "media-provenance.json").read_bytes())
    video = PAGE / WEB_VIDEO
    assert video.stat().st_size == provenance["video_bytes"] == 1986425
    assert hashlib.sha256(video.read_bytes()).hexdigest() == WEB_VIDEO_SHA
    assert video.stat().st_size <= MAX_GIT_BLOB_BYTES
    # Prevent another oversized asset from returning to the deployed route.
    for asset in PAGE.iterdir():
        if asset.is_file():
            assert asset.stat().st_size <= MAX_GIT_BLOB_BYTES, asset.name


def test_social_card_dimensions_claim_and_source():
    png = (PAGE / "social-card-v1.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert int.from_bytes(png[16:20], "big") == 1200
    assert int.from_bytes(png[20:24], "big") == 630
    assert len(png) < 5_000_000
    svg = ET.parse(PAGE / "social-card-v1.svg")
    labels = " ".join(svg.getroot().itertext())
    assert "Independent scientific review pending" in labels
    assert "Frozen candidate 48d7ab5" in labels
    assert "not physical distance" in labels
    receipt = json.loads((PAGE / "social-card-provenance.json").read_bytes())
    assert receipt["image_sha256"] == hashlib.sha256(png).hexdigest()
    assert receipt["image_bytes"] == len(png)
    assert (
        receipt["svg_sha256"]
        == hashlib.sha256((PAGE / receipt["svg"]).read_bytes()).hexdigest()
    )
    assert receipt["data_sha256"] == DATA_SHA


@pytest.mark.parametrize("name", ["core.mjs", "loader.mjs", "app.mjs"])
def test_js_syntax_when_node_is_available(name):
    import shutil

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is separately required by the remote JavaScript gate")
    subprocess.run(
        [node, "--check", str(PAGE / name)], check=True, capture_output=True, text=True
    )
