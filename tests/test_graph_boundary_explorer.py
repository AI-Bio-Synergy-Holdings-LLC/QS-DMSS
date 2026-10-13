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


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


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


@pytest.mark.skipif(
    not SOURCE_CHECKOUT and not (PAGE / "boundary-explanation-v2.mp4").is_file(),
    reason="Portal-only MP4 is intentionally excluded from Python distributions",
)
def test_optional_video_keeps_identity_rights_and_accessible_fallbacks():
    provenance = json.loads((PAGE / "media-provenance.json").read_bytes())
    video = PAGE / provenance["video"]
    assert video.stat().st_size == provenance["video_bytes"] == 15981923
    assert hashlib.sha256(video.read_bytes()).hexdigest() == provenance["video_sha256"]
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
    assert "continuous screen recording" in html and "No spoken narration" in html
    assert (
        (PAGE / "explanations.vtt").read_text(encoding="utf-8").startswith("WEBVTT\n")
    )
    assert "00:00:53.000 --> 00:01:00.000" in (PAGE / "explanations.vtt").read_text(
        encoding="utf-8"
    )
    assert "NOT_ESTABLISHED" in (PAGE / "transcript.txt").read_text(encoding="utf-8")


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
