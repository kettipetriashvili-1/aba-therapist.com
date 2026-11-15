#!/usr/bin/env python3
"""Generate the site's reviewed-as-AI locale source files.

This is an authoring helper, not part of the Hugo build or the public website.
It uses Google Translate's public web endpoint and stores a resumable local cache
outside the repository. Every generated blog page is visibly labelled as an AI
translation by the Hugo template.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_PATH = Path.home() / ".cache/hermes/aba-therapist/translation-cache.json"
SEPARATOR = "\n__ABA_SPLIT_9F6C__\n"
MAX_CHARS = 3000

LANGUAGES = {
    "de": "de",
    "es": "es",
    "fr": "fr",
    "ru": "ru",
    "pt-br": "pt",
    "it": "it",
    "pl": "pl",
    "ja": "ja",
    "zh-cn": "zh-CN",
    "nl": "nl",
    "tr": "tr",
    "ko": "ko",
    "fa": "fa",
    "ar": "ar",
    "cs": "cs",
    "ro": "ro",
    "hu": "hu",
    "id": "id",
    "sv": "sv",
    "no": "no",
    "fi": "fi",
    "el": "el",
    "zh-tw": "zh-TW",
}

PROTECTED_TERMS = {
    "Keti Petriashvili": "__KEEP_KETI__",
    "Applied Behavior Analysis": "__KEEP_ABA_LONG__",
    "ABA": "__KEEP_ABA__",
    "WhatsApp": "__KEEP_WHATSAPP__",
    "Signal": "__KEEP_SIGNAL__",
    "Cloudflare": "__KEEP_CLOUDFLARE__",
}

PAGE_META = {
    "home_title": "Keti Petriashvili | ABA Therapy for Children",
    "home_description": "Psychological and ABA support for children and families from clinical psychologist Keti Petriashvili, with respect for assent and autonomy.",
    "about_title": "About Keti Petriashvili",
    "about_description": "Meet Keti Petriashvili: clinical psychologist, International Behavior Analyst and lecturer. My approach, qualifications and work with children and families.",
    "legal_title": "Legal Notice & Privacy",
    "legal_description": "Draft legal and privacy information for aba-therapist.com.",
    "blog_title": "ABA Therapy Blog",
    "blog_description": "Practical articles about supportive ABA practice, children, communication, learning and family collaboration.",
    "article_title": "What Positive Reinforcement Looks Like in ABA Therapy",
    "article_seo_title": "Positive Reinforcement in ABA Therapy: A Parent-Friendly Guide",
    "article_description": "A practical explanation of positive reinforcement in ABA therapy, including how reinforcers are selected, used and reviewed with children.",
    "article_summary": "Positive reinforcement is more than giving a reward. Used thoughtfully, it helps make useful skills worth practising while keeping goals clear, individual and respectful.",
}


def load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text(encoding="utf-8"))


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def protect(text: str) -> str:
    for term, token in PROTECTED_TERMS.items():
        text = text.replace(term, token)
    return text


def restore(text: str) -> str:
    for term, token in PROTECTED_TERMS.items():
        text = text.replace(token, term)
        # Some scripts add spaces around an unknown token.
        text = text.replace(token.replace("_", " _ "), term)
    return text


def request_translation(target: str, text: str) -> str:
    query = urllib.parse.urlencode(
        {"client": "gtx", "sl": "en", "tl": target, "dt": "t", "q": text}
    )
    request = urllib.request.Request(
        "https://translate.googleapis.com/translate_a/single?" + query,
        headers={"User-Agent": "Mozilla/5.0 (compatible; static-site-authoring/1.0)"},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.load(response)
            return "".join(piece[0] for piece in data[0] if piece[0])
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2**attempt)
    raise RuntimeError("Translation retry loop ended unexpectedly")


def translate_many(target: str, strings: list[str], cache: dict[str, str]) -> list[str]:
    results: list[str | None] = [None] * len(strings)
    missing: list[tuple[int, str]] = []
    for index, text in enumerate(strings):
        key = f"{target}\0{text}"
        if key in cache:
            results[index] = cache[key]
        else:
            missing.append((index, text))

    position = 0
    while position < len(missing):
        batch: list[tuple[int, str]] = []
        batch_size = 0
        while position < len(missing):
            item = missing[position]
            protected = protect(item[1])
            added = len(protected) + (len(SEPARATOR) if batch else 0)
            if batch and batch_size + added > MAX_CHARS:
                break
            batch.append(item)
            batch_size += added
            position += 1

        payload = SEPARATOR.join(protect(text) for _, text in batch)
        translated = request_translation(target, payload)
        parts = translated.split(SEPARATOR)
        if len(parts) != len(batch):
            # Preserve correctness over speed if a provider modifies the delimiter.
            parts = [request_translation(target, protect(text)) for _, text in batch]

        for (index, source), value in zip(batch, parts, strict=True):
            value = restore(value.strip())
            results[index] = value
            cache[f"{target}\0{source}"] = value
        save_cache(cache)
        time.sleep(0.15)

    return [value if value is not None else "" for value in results]


def markdown_segments(markdown: str) -> tuple[list[str], list[tuple[str, int | str]]]:
    strings: list[str] = []
    structure: list[tuple[str, int | str]] = []
    for line in markdown.splitlines():
        if not line.strip():
            structure.append(("literal", ""))
            continue
        heading = re.match(r"^(#{2,3})\s+(.+)$", line)
        bullet = re.match(r"^-\s+(.+)$", line)
        if heading:
            strings.append(heading.group(2))
            structure.append((f"heading:{heading.group(1)}", len(strings) - 1))
        elif bullet:
            strings.append(bullet.group(1))
            structure.append(("bullet", len(strings) - 1))
        else:
            strings.append(line)
            structure.append(("paragraph", len(strings) - 1))
    return strings, structure


def rebuild_markdown(translations: list[str], structure: list[tuple[str, int | str]]) -> str:
    lines: list[str] = []
    for kind, value in structure:
        if kind == "literal":
            lines.append(str(value))
        elif kind.startswith("heading:"):
            lines.append(f"{kind.split(':', 1)[1]} {translations[int(value)]}")
        elif kind == "bullet":
            lines.append(f"- {translations[int(value)]}")
        else:
            lines.append(translations[int(value)])
    return "\n".join(lines).strip() + "\n"


def frontmatter(values: list[tuple[str, object]]) -> str:
    lines = ["---"]
    for key, value in values:
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        elif isinstance(value, (int, float)):
            rendered = str(value)
        elif isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False)
        else:
            rendered = json.dumps(str(value), ensure_ascii=False)
        lines.append(f"{key}: {rendered}")
    lines.extend(["---", ""])
    return "\n".join(lines)


def write_locale_content(code: str, meta: dict[str, str], article_body: str) -> None:
    suffix = f".{code}.md"
    files = {
        ROOT / "content" / f"_index{suffix}": frontmatter(
            [("title", meta["home_title"]), ("description", meta["home_description"])]
        ),
        ROOT / "content/about" / f"_index{suffix}": frontmatter(
            [("title", meta["about_title"]), ("description", meta["about_description"])]
        ),
        ROOT / "content/legal" / f"_index{suffix}": frontmatter(
            [
                ("title", meta["legal_title"]),
                ("description", meta["legal_description"]),
                ("noindex", True),
                ("sitemap", {"disable": True}),
            ]
        ),
        ROOT / "content/blog" / f"_index{suffix}": frontmatter(
            [("title", meta["blog_title"]), ("description", meta["blog_description"])]
        ),
        ROOT / "content/blog" / f"positive-reinforcement-in-aba-therapy{suffix}": frontmatter(
            [
                ("title", meta["article_title"]),
                ("seo_title", meta["article_seo_title"]),
                ("description", meta["article_description"]),
                ("summary", meta["article_summary"]),
                ("author", "Keti Petriashvili"),
                ("date", "2026-08-20"),
                ("lastmod", "2026-08-20"),
                ("slug", "positive-reinforcement-in-aba-therapy"),
            ]
        )
        + article_body,
    }
    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def enable_generated_languages() -> None:
    """Enable locales only after every translated source file exists."""
    config_path = ROOT / "hugo.toml"
    output: list[str] = []
    current_language = ""
    for line in config_path.read_text(encoding="utf-8").splitlines():
        section = re.match(r"\s*\[languages\.([^]]+)]\s*$", line)
        if section:
            current_language = section.group(1)
        elif re.match(r"\s*\[", line):
            current_language = ""
        if current_language in LANGUAGES and line.strip() == "disabled = true":
            continue
        output.append(line)
    config_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def main() -> None:
    english_i18n = json.loads((ROOT / "i18n/en.json").read_text(encoding="utf-8"))
    keys = list(english_i18n)
    ui_strings = [english_i18n[key]["other"] for key in keys]

    english_article = (ROOT / "content/blog/positive-reinforcement-in-aba-therapy.md").read_text(
        encoding="utf-8"
    )
    _, article_body = english_article.split("---\n", 2)[1:]
    article_strings, article_structure = markdown_segments(article_body)

    meta_keys = list(PAGE_META)
    all_source_strings = ui_strings + [PAGE_META[key] for key in meta_keys] + article_strings
    cache = load_cache()

    for code, target in LANGUAGES.items():
        print(f"Generating {code} …", flush=True)
        translated = translate_many(target, all_source_strings, cache)

        ui_values = translated[: len(ui_strings)]
        meta_start = len(ui_strings)
        article_start = meta_start + len(meta_keys)

        localized_i18n = {
            key: {"other": value} for key, value in zip(keys, ui_values, strict=True)
        }
        if code == "de":
            localized_i18n["article_ai_translation_notice"]["other"] = (
                "Dieser Blogbeitrag wurde mithilfe von KI übersetzt. Die Originalversion finden Sie"
            )
            localized_i18n["ai_translation_link"]["other"] = "hier."

        (ROOT / f"i18n/{code}.json").write_text(
            json.dumps(localized_i18n, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        meta_values = translated[meta_start:article_start]
        localized_meta = dict(zip(meta_keys, meta_values, strict=True))
        localized_article = rebuild_markdown(translated[article_start:], article_structure)
        write_locale_content(code, localized_meta, localized_article)

    enable_generated_languages()
    print(f"Generated and enabled {len(LANGUAGES)} locales.")


if __name__ == "__main__":
    main()
