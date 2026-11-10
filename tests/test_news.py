"""The News & tips feed: what build_news.py accepts, what it refuses, and that
the bytes it writes are stable and sign/verify exactly like the manifest.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from PIL import Image

import build_news
import sign_manifest
import verify_manifest
from holdfast import news, signing, util

ROOT = util.repo_root()


def item(**overrides) -> dict:
    base = {
        "id": "2026-11-sample",
        "date": "2026-11-10",
        "kind": "news",
        "title": "A sample item",
        "summary": "One line about it.",
        "body": "First paragraph.\n\nA list:\n- one\n- two",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def write_item(root: Path, data: dict, name: str | None = None) -> Path:
    folder = root / "news" / "items"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (name or f"{data['id']}.json")
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def write_image(root: Path, name: str, size=(64, 32), fmt="PNG", noise=False) -> Path:
    folder = root / "news" / "img"
    folder.mkdir(parents=True, exist_ok=True)
    if noise:
        im = Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3))
    else:
        im = Image.new("RGB", size, (24, 72, 36))
    path = folder / name
    im.save(path, format=fmt)
    return path


def problems_of(root: Path) -> str:
    with pytest.raises(news.NewsError) as exc:
        news.build(root)
    return "\n".join(exc.value.problems)


# -- the real feed ---------------------------------------------------------


def test_the_real_news_json_is_valid():
    feed = news.load()
    assert news.validate_feed(feed) == []
    assert 1 <= len(feed["items"]) <= news.MAX_ITEMS


def test_the_real_news_json_is_exactly_what_the_sources_build():
    """publish.yml signs the committed bytes, so they must match a fresh build."""
    assert build_news.main(["--check"]) == 0
    assert news.news_path().read_bytes() == news.canonical_bytes(news.build().feed)


def test_the_real_news_json_has_signable_bytes():
    raw = news.news_path().read_bytes()
    assert b"\r\n" not in raw
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert raw.endswith(b"}\n") and not raw.endswith(b"\n\n")


def test_the_launch_items_are_there():
    ids = {i["id"]: i for i in news.load()["items"]}
    assert ids["2026-11-welcome"]["kind"] == "news"
    tips = [i for i in ids.values() if i["kind"] == "tip"]
    assert tips and any("ready.gov" in t["body"].lower() for t in tips)


def test_published_image_urls_point_at_files_in_news_img():
    for entry in news.load()["items"]:
        if "image" in entry:
            name = entry["image"]["url"].removeprefix(news.IMAGE_URL_PREFIX)
            path = ROOT / "news" / "img" / name
            assert path.is_file(), name
            assert util.size_and_sha256(path) == (entry["image"]["size"], entry["image"]["sha256"])


# -- what a good build looks like -----------------------------------------


def test_build_computes_image_fields_and_orders_fields(tmp_path):
    write_image(tmp_path, "pic.png", size=(120, 80))
    write_item(tmp_path, item(image={"file": "pic.png", "alt": "A green rectangle."}, expires="2026-12-01"))
    feed = news.build(tmp_path).feed
    entry = feed["items"][0]
    assert list(entry) == ["id", "date", "kind", "title", "summary", "body", "image", "expires"]
    image = entry["image"]
    assert image["url"] == "https://evolvlabsai.github.io/holdfast-packs/news/img/pic.png"
    assert (image["width"], image["height"]) == (120, 80)
    assert (image["size"], image["sha256"]) == util.size_and_sha256(tmp_path / "news" / "img" / "pic.png")
    assert list(image) == ["url", "sha256", "size", "width", "height", "alt"]
    assert feed["published"] == "2026-11-10T00:00:00Z"
    assert news.validate_feed(feed) == []


def test_items_are_sorted_newest_first_news_before_tips(tmp_path):
    write_item(tmp_path, item(id="b-old", date="2026-01-01"))
    write_item(tmp_path, item(id="a-tip", date="2026-11-10", kind="tip"))
    write_item(tmp_path, item(id="z-news", date="2026-11-10"))
    write_item(tmp_path, item(id="m-mid", date="2026-06-15"))
    ids = [i["id"] for i in news.build(tmp_path).feed["items"]]
    assert ids == ["z-news", "a-tip", "m-mid", "b-old"]


def test_only_the_newest_50_are_kept(tmp_path):
    for n in range(55):
        day = f"2026-{1 + n // 28:02d}-{1 + n % 28:02d}"
        write_item(tmp_path, item(id=f"item-{n:02d}", date=day))
    result = news.build(tmp_path)
    assert len(result.feed["items"]) == news.MAX_ITEMS
    assert result.dropped == ["item-04", "item-03", "item-02", "item-01", "item-00"]
    assert news.validate_feed(result.feed) == []


# -- canonical bytes -------------------------------------------------------


def test_building_twice_gives_identical_bytes(tmp_path):
    write_image(tmp_path, "pic.png")
    write_item(tmp_path, item(image={"file": "pic.png", "alt": "Alt text."}))
    write_item(tmp_path, item(id="2026-10-tip", date="2026-10-01", kind="tip", title="Tip — with an em dash"))
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    assert build_news.main(["--root", str(tmp_path), "--out", str(first)]) == 0
    assert build_news.main(["--root", str(tmp_path), "--out", str(second)]) == 0
    raw = first.read_bytes()
    assert raw == second.read_bytes()
    assert b"\r" not in raw and raw.endswith(b"}\n")
    assert "Tip — with".encode() in raw  # UTF-8, not \\u escapes
    assert raw == news.canonical_bytes(json.loads(raw))
    assert build_news.main(["--root", str(tmp_path), "--out", str(first), "--check"]) == 0


def test_source_formatting_and_key_order_do_not_change_the_output(tmp_path):
    write_item(tmp_path, item())
    before = news.canonical_bytes(news.build(tmp_path).feed)
    path = tmp_path / "news" / "items" / "2026-11-sample.json"
    shuffled = dict(reversed(list(json.loads(path.read_text(encoding="utf-8")).items())))
    path.write_text(json.dumps(shuffled, indent=4), encoding="utf-8")
    assert news.canonical_bytes(news.build(tmp_path).feed) == before


def test_check_fails_on_a_stale_or_reformatted_feed(tmp_path):
    write_item(tmp_path, item())
    out = tmp_path / "news.json"
    assert build_news.main(["--root", str(tmp_path)]) == 0
    out.write_bytes(json.dumps(json.loads(out.read_bytes()), indent=4).encode() + b"\n")
    assert build_news.main(["--root", str(tmp_path), "--check"]) == 1


def test_a_rebuild_that_changes_bytes_deletes_the_stale_signature(tmp_path):
    write_item(tmp_path, item())
    assert build_news.main(["--root", str(tmp_path)]) == 0
    sig = tmp_path / "news.json.sig"
    sig.write_text("stale\n")
    assert build_news.main(["--root", str(tmp_path)]) == 0
    assert sig.exists(), "same bytes: the signature is still good"
    write_item(tmp_path, item(title="A changed title"))
    assert build_news.main(["--root", str(tmp_path)]) == 0
    assert not sig.exists()


# -- refusals --------------------------------------------------------------


@pytest.mark.parametrize("bad_id", ["Welcome", "has_underscore", "-leading", "trailing-", "double--dash", "a b", ""])
def test_bad_ids_are_refused(tmp_path, bad_id):
    write_item(tmp_path, item(id=bad_id), name="x.json")
    assert "id" in problems_of(tmp_path)


def test_the_file_name_must_match_the_id(tmp_path):
    write_item(tmp_path, item(), name="something-else.json")
    assert "must be named 2026-11-sample.json" in problems_of(tmp_path)


def test_duplicate_ids_are_refused(tmp_path):
    write_item(tmp_path, item())
    write_item(tmp_path, item(), name="copy.json")
    assert "also used by" in problems_of(tmp_path)


@pytest.mark.parametrize("bad_date", ["2026-02-30", "2026-13-01", "26-11-10", "2026/11/10", "2026-11-10T00:00:00Z"])
def test_bad_dates_are_refused(tmp_path, bad_date):
    write_item(tmp_path, item(date=bad_date))
    assert "date" in problems_of(tmp_path)


def test_expires_before_date_is_refused(tmp_path):
    write_item(tmp_path, item(expires="2026-11-01"))
    assert "is before its date" in problems_of(tmp_path)


def test_a_published_feed_out_of_order_is_refused():
    feed = {
        "schema": 1,
        "published": "2026-11-10T00:00:00Z",
        "items": [item(id="older", date="2026-01-01"), item(id="newer", date="2026-11-10")],
    }
    assert any("newest first" in p for p in news.validate_feed(feed))


@pytest.mark.parametrize(
    ("field", "limit"), [("title", news.MAX_TITLE), ("summary", news.MAX_SUMMARY), ("body", news.MAX_BODY)]
)
def test_text_over_the_limit_is_refused(tmp_path, field, limit):
    write_item(tmp_path, item(**{field: "x" * limit}))
    news.build(tmp_path)  # exactly at the limit is fine
    write_item(tmp_path, item(**{field: "x" * (limit + 1)}))
    assert field in problems_of(tmp_path)


def test_length_is_counted_in_utf16_units_like_the_app(tmp_path):
    """An emoji is one code point but two UTF-16 units; .NET counts the latter."""
    write_item(tmp_path, item(title="x" * (news.MAX_TITLE - 1) + "\U0001f600"))
    assert "UTF-16" in problems_of(tmp_path)


@pytest.mark.parametrize(
    "body",
    [
        "# Heading\n\nText.",
        "Text.\n\n* star bullet",
        "Text.\n\n1. numbered",
        "Some **bold** text.",
        "A [link](https://example.com).",
        "An <b>html</b> tag.",
        "Too\n\n\nmany blank lines.",
        " leading space",
        "Tab\there.",
        "-no space bullet",
    ],
)
def test_bodies_that_are_not_plain_text_are_refused(tmp_path, body):
    write_item(tmp_path, item(body=body))
    assert "body" in problems_of(tmp_path)


@pytest.mark.parametrize("field", ["title", "summary"])
def test_title_and_summary_are_one_line(tmp_path, field):
    write_item(tmp_path, item(**{field: "two\nlines"}))
    assert field in problems_of(tmp_path)


def test_unknown_fields_and_kinds_are_refused(tmp_path):
    write_item(tmp_path, item(kind="promo", sumary="typo"))
    text = problems_of(tmp_path)
    assert "promo" in text and "sumary" in text


def test_hand_typed_image_hashes_are_refused_in_sources(tmp_path):
    write_image(tmp_path, "pic.png")
    write_item(tmp_path, item(image={"file": "pic.png", "alt": "Alt.", "sha256": "0" * 64}))
    assert "sha256" in problems_of(tmp_path)


def test_an_oversized_image_file_is_refused(tmp_path):
    path = write_image(tmp_path, "big.png", size=(500, 500), noise=True)
    assert path.stat().st_size > news.MAX_IMAGE_BYTES
    write_item(tmp_path, item(image={"file": "big.png", "alt": "Noise."}))
    assert f"the limit is {news.MAX_IMAGE_BYTES}" in problems_of(tmp_path)


@pytest.mark.parametrize("size", [(1601, 10), (10, 1601)])
def test_an_image_over_1600px_is_refused(tmp_path, size):
    write_image(tmp_path, "wide.png", size=size)
    write_item(tmp_path, item(image={"file": "wide.png", "alt": "Too big."}))
    assert "longest side" in problems_of(tmp_path)


def test_an_image_at_1600px_is_fine(tmp_path):
    write_image(tmp_path, "edge.jpg", size=(1600, 900), fmt="JPEG")
    write_item(tmp_path, item(image={"file": "edge.jpg", "alt": "Edge."}))
    assert news.build(tmp_path).feed["items"][0]["image"]["width"] == 1600


def test_an_image_whose_extension_lies_is_refused(tmp_path):
    write_image(tmp_path, "fake.jpg", fmt="PNG")
    write_item(tmp_path, item(image={"file": "fake.jpg", "alt": "Fake."}))
    assert "extension says JPEG" in problems_of(tmp_path)


@pytest.mark.parametrize("name", ["pic.gif", "Pic.png", "missing.png"])
def test_bad_or_missing_image_files_are_refused(tmp_path, name):
    write_image(tmp_path, "pic.png")
    write_item(tmp_path, item(image={"file": name, "alt": "Alt."}))
    with pytest.raises(news.NewsError):
        news.build(tmp_path)


def test_an_image_that_is_not_an_image_is_refused(tmp_path):
    folder = tmp_path / "news" / "img"
    folder.mkdir(parents=True)
    (folder / "junk.png").write_bytes(b"not a png")
    write_item(tmp_path, item(image={"file": "junk.png", "alt": "Junk."}))
    assert "not a readable image" in problems_of(tmp_path)


def test_a_failed_build_writes_nothing(tmp_path):
    write_item(tmp_path, item(id="BAD"), name="x.json")
    assert build_news.main(["--root", str(tmp_path)]) == 1
    assert not (tmp_path / "news.json").exists()


def test_an_empty_feed_is_refused(tmp_path):
    (tmp_path / "news" / "items").mkdir(parents=True)
    assert "no items" in problems_of(tmp_path)


# -- signing: same key, same format as the manifest ------------------------


@pytest.fixture
def built_feed(tmp_path):
    write_image(tmp_path, "pic.png")
    write_item(tmp_path, item(image={"file": "pic.png", "alt": "Alt."}))
    assert build_news.main(["--root", str(tmp_path)]) == 0
    return tmp_path / "news.json"


def test_sign_and_verify_round_trip(built_feed):
    private_b64, public_b64 = signing.generate()
    assert sign_manifest.main(["--file", str(built_feed), "--key", private_b64]) == 0
    sig = Path(str(built_feed) + ".sig")
    text = sig.read_text(encoding="utf-8")
    assert text.endswith("\n") and text.count("\n") == 1
    assert len(signing.decode_base64(text, signing.SIGNATURE_LENGTH, "signature")) == 64
    assert verify_manifest.main(["--file", str(built_feed), "--pub", public_b64]) == 0
    assert signing.verify_file(signing.load_public(public_b64), built_feed)


def test_a_tampered_feed_fails_verification(built_feed):
    private_b64, public_b64 = signing.generate()
    assert sign_manifest.main(["--file", str(built_feed), "--key", private_b64]) == 0
    feed = json.loads(built_feed.read_bytes())
    feed["items"][0]["body"] = "Something else."
    built_feed.write_bytes(news.canonical_bytes(feed))
    assert verify_manifest.main(["--file", str(built_feed), "--pub", public_b64]) == 1


def test_another_key_cannot_sign_the_feed(built_feed):
    theirs, _ = signing.generate()
    _, ours_public = signing.generate()
    assert sign_manifest.main(["--file", str(built_feed), "--key", theirs]) == 0
    assert verify_manifest.main(["--file", str(built_feed), "--pub", ours_public]) == 1


def test_signing_refuses_an_invalid_feed(tmp_path):
    bad = tmp_path / "news.json"
    bad.write_bytes(news.canonical_bytes({"schema": 1, "published": "2026-11-10T00:00:00Z", "items": [item(id="BAD")]}))
    private_b64, _ = signing.generate()
    with pytest.raises(SystemExit):
        sign_manifest.main(["--file", str(bad), "--key", private_b64])
    assert not (tmp_path / "news.json.sig").exists()


# -- publishing ------------------------------------------------------------


def test_publish_workflow_signs_verifies_and_publishes_the_feed():
    text = (ROOT / ".github" / "workflows" / "publish.yml").read_text(encoding="utf-8")
    for needle in (
        "- news.json",
        "- news/**",
        "build_news.py --check",
        "sign_manifest.py --file news.json",
        'verify_manifest.py --pub "$PUB" --file news.json',
        "cp news.json news.json.sig _site/",
        "_site/news/img/",
    ):
        assert needle in text, needle
    # The manifest flow is unchanged.
    for needle in ("python scripts/sign_manifest.py\n", 'verify_manifest.py --pub "$PUB"\n', "cp manifest.json manifest.json.sig _site/"):
        assert needle in text, needle


def test_the_feed_signature_is_never_committed():
    assert "/news.json.sig" in (ROOT / ".gitignore").read_text(encoding="utf-8")
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "news.json         -text" in attributes
