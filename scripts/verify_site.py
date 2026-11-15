#!/usr/bin/env python3
"""Check the generated static site without requiring browser tooling."""

from __future__ import annotations

import argparse
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        values = dict(attrs)
        for name in ("href", "src"):
            if values.get(name):
                self.references.append(str(values[name]))


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"Missing generated file: {path}")
    return path.read_text(encoding="utf-8")


def route_target(output: Path, route: str) -> Path:
    clean = route.split("?", 1)[0].split("#", 1)[0]
    if not clean or clean == "/":
        return output / "index.html"
    relative = clean.lstrip("/")
    candidate = output / relative
    if candidate.suffix:
        return candidate
    return candidate / "index.html"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    project = Path(__file__).resolve().parents[1]

    pages = {
        "home": output / "index.html",
        "about": output / "about/index.html",
        "legal": output / "legal/index.html",
        "blog": output / "blog/index.html",
        "article": output / "blog/positive-reinforcement-in-aba-therapy/index.html",
        "not_found": output / "404.html",
    }
    html = {name: read(path) for name, path in pages.items()}

    assert "Thoughtful ABA support for children" in html["home"]
    assert re.search(r"\bid=['\"]?contact(?:['\"]|\s|>)", html["home"])
    assert "mailto:info@aba-therapist.com" in html["home"]
    assert "signal.me/#p/+995598568368" in html["home"]
    assert "wa.me/995598568368" in html["home"]
    assert "Individual therapy" in html["home"]
    assert "Parent and caregiver coaching" in html["home"]
    assert "School and kindergarten consultation" in html["home"]
    assert "child’s assent matters too" in html["home"]
    assert "Sessions are usually under one hour" in html["home"]
    assert "fictional layout placeholders" not in html["home"]
    assert "Composite design example" not in html["home"]
    assert "testimonial-section" not in html["home"]
    assert "<form" not in html["home"].lower()

    assert "I’m a clinical psychologist" in html["about"]
    assert "Caucasus University" in html["about"]
    assert "International Behavior Analysis Organization" in html["about"]
    assert "Awarded July 2022" in html["about"]
    assert "Sulkhan-Saba Orbeliani University" in html["about"]
    assert "Awaiting verified details" not in html["about"]
    assert "Example article" in html["blog"]
    assert "It has not yet been reviewed or approved by Keti" in html["article"]
    assert 'content="noindex, nofollow"' in html["legal"]
    assert "Draft placeholder" in html["legal"]
    sitemap = read(output / "sitemap.xml")
    assert "/legal/" not in sitemap

    assert "positive-reinforcement-in-aba-therapy" in html["blog"]
    assert re.search(r"\bid=['\"]?TableOfContents(?:['\"]|\s|>)", html["article"])
    assert "Please contact us if anything is unclear" in html["article"]
    assert "This blog post was translated" not in html["article"]
    assert html["article"].count("<h2") >= 7

    # Non-English sources and output remain intentionally absent until copy approval.
    assert not (project / "i18n/de.json").exists()
    assert not (project / "content/_index.de.md").exists()
    assert not (output / "de").exists()
    assert (project / "scripts/generate_locales.py").is_file()

    internal_links = 0
    css_assets = 0
    rendered_css_files: set[Path] = set()
    for page_path in output.rglob("*.html"):
        document = read(page_path)
        assert not re.search(r"\bautistic\b", document, re.I), f"Unwanted wording in {page_path}"
        assert "info@aba-therapy.com" not in document
        assert "ketti.petriashvili@gmail.com" not in document
        assert re.search(r"<html\s+lang=['\"]?en-GB(?:['\"]|\s)", document)
        assert re.search(r"<html\s+lang=['\"]?en-GB(?:['\"]|\s)[^>]*\bdir=['\"]?ltr(?:['\"]|\s|>)", document)
        parsed = AssetParser()
        parsed.feed(document)
        assert "form" not in parsed.tags
        for reference in parsed.references:
            split = urlsplit(reference)
            if split.scheme in {"mailto", "tel"}:
                continue
            if split.scheme in {"http", "https"}:
                if split.netloc != "aba-therapist.com":
                    continue
                reference = split.path
            if not reference.startswith("/"):
                continue
            internal_links += 1
            target = route_target(output, reference)
            if not target.exists():
                raise AssertionError(f"Broken reference in {page_path}: {reference} -> {target}")
            if re.search(r"/css/[^/]+\.css$", reference.split("?", 1)[0]):
                css_assets += 1
                rendered_css_files.add(target)

    assert internal_links > 20
    assert css_assets >= len(list(output.rglob("*.html")))
    assert rendered_css_files
    for css_file in rendered_css_files:
        css = read(css_file)
        assert re.search(r"\.site-header\{[^}]*position:sticky[^}]*top:0", css)
        assert "height:calc(100svh - 196px)" in css
        assert re.search(r"\.signal-strip,.signal-grid\{height:112px", css)
    assert (output / "images/logo-mark.webp").is_file()
    assert (output / "images/hero-therapy.webp").is_file()
    assert (output / "images/hero-therapy-mobile.webp").is_file()
    assert (output / "images/about-keti.webp").is_file()
    assert (output / "images/social-card.webp").is_file()

    served_image_suffixes = {".jpg", ".jpeg", ".png", ".svg", ".gif", ".avif", ".webp"}
    served_images = [
        path for path in (output / "images").rglob("*")
        if path.is_file() and path.suffix.lower() in served_image_suffixes
    ]
    non_webp_images = [path for path in served_images if path.suffix.lower() != ".webp"]
    assert not non_webp_images, f"Non-WebP served images: {non_webp_images}"

    for name, document in html.items():
        parsed_headings = re.findall(r"<h[1-3][^>]*>(.*?)</h[1-3]>", document, re.S | re.I)
        for raw_heading in parsed_headings:
            heading = re.sub(r"<[^>]+>", "", raw_heading).strip()
            assert not heading.endswith("."), f"Heading ends with a period on {name}: {heading}"

    print(
        f"PASS: {len(pages)} required pages, {internal_links} internal references, "
        f"updated source-backed copy, draft safeguards, article TOC, and English-only boundary verified."
    )


if __name__ == "__main__":
    main()
