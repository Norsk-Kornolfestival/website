#!/usr/bin/env python3
"""Scaffold English news posts from Norwegian originals.

For each NB post, create an EN counterpart:
- English/bilingual posts: extract the English content
- Norwegian-only posts: copy front matter + TODO placeholder
"""

import os
import re

NB_DIR = "content/nb/nyheter"
EN_DIR = "content/en/news"


def extract_front_matter(content):
    """Return (front_matter_str, body) splitting on --- delimiters."""
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[1].strip(), parts[2].strip()
    return "", content.strip()


def extract_english_from_bilingual(body):
    """Try to extract the English portion from a bilingual post."""
    # Common patterns for English sections
    patterns = [
        r"(?i)\*+\s*english[:\s]*\*+\s*\n(.*)",
        r"(?i)english(?:\s+below[^.]*)?[.:]\s*\n\n(.*)",
        r"(?i)\*english[^*]*\*\s*\n(.*)",
        r"(?i)---+\s*\n\s*(?:english|in english)[:\s]*\n(.*)",
        r"(?i)english version[:\s]*\n(.*)",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.DOTALL)
        if m:
            english_part = m.group(1).strip()
            if len(english_part) > 20:
                return english_part
    return None


def detect_language(title, body):
    """Classify post as 'en', 'bilingual', or 'nb'."""
    english_words = len(
        re.findall(
            r"\b(?:the|and|for|with|from|this|that|will|has|have|are|was|our|beer|brewing|festival|traditional)\b",
            body,
            re.I,
        )
    )
    norwegian_words = len(
        re.findall(
            r"\b(?:og|for|med|fra|som|har|vil|var|det|den|til|på|av|er|blir|kan|også|ble|alle|disse|skal|under|sine)\b",
            body,
            re.I,
        )
    )

    has_english_marker = bool(re.search(r"(?i)english below|english:", body))

    english_title_words = [
        "speaker", "talk", "brew", "the ", "festival board", "welcome",
        "about the", "sold out", "tickets", "easy travel", "hotel rooms",
        "results", "streaming", "demo brewer", "guided", "women", "viking",
        "slides from", "digital festival on",
    ]
    title_is_english = any(w in title.lower() for w in english_title_words)

    total_words = len(body.split())
    if total_words < 5:
        return "nb"
    if has_english_marker:
        return "bilingual"
    if english_words > norwegian_words * 1.5 or (
        title_is_english and english_words > norwegian_words
    ):
        return "en"
    return "nb"


def process_post(fname):
    """Process a single NB post and create EN counterpart."""
    nb_path = os.path.join(NB_DIR, fname)
    with open(nb_path, encoding="utf-8") as f:
        content = f.read()

    fm_str, body = extract_front_matter(content)

    # Extract title
    title_match = re.search(r"^title:\s*(.+)$", fm_str, re.MULTILINE)
    title = title_match.group(1).strip().strip('"') if title_match else fname

    lang = detect_language(title, body)

    if lang == "en":
        # Already English — copy as-is
        en_content = content
    elif lang == "bilingual":
        # Extract English portion
        english_body = extract_english_from_bilingual(body)
        if english_body:
            en_content = f"---\n{fm_str}\n---\n\n{english_body}\n"
        else:
            # Could not extract cleanly — copy full content with note
            en_content = content
    else:
        # Norwegian only — placeholder
        en_content = f"---\n{fm_str}\n---\n\n<!-- TODO: Translate from Norwegian -->\n"

    # Write EN file with same filename
    en_path = os.path.join(EN_DIR, fname)
    with open(en_path, "w", encoding="utf-8") as f:
        f.write(en_content)

    return lang


def main():
    os.makedirs(EN_DIR, exist_ok=True)

    stats = {"en": 0, "bilingual": 0, "nb": 0}

    for fname in sorted(os.listdir(NB_DIR)):
        if fname == "_index.md" or not fname.endswith(".md"):
            continue
        lang = process_post(fname)
        stats[lang] += 1

    print(f"Scaffolded {sum(stats.values())} English news posts:")
    print(f"  English (copied as-is): {stats['en']}")
    print(f"  Bilingual (extracted EN portion): {stats['bilingual']}")
    print(f"  Norwegian (TODO placeholder): {stats['nb']}")


if __name__ == "__main__":
    main()
