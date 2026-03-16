#!/usr/bin/env python3
"""Convert WordPress WXR export to Hugo markdown files."""

import xml.etree.ElementTree as ET
import html
import os
import re
import sys
from datetime import datetime

NS = {
    "wp": "http://wordpress.org/export/1.2/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}

# WP image base → Hugo static path
WP_UPLOAD_RE = re.compile(
    r'https?://(?:usercontent\.one/wp/)?www\.norskkornolfestival\.no/wp-content/uploads/'
)


def html_to_markdown(html_str):
    """Simple HTML→Markdown conversion for WP post content."""
    if not html_str:
        return ""

    s = html_str

    # Decode HTML entities
    s = html.unescape(s)

    # Preserve line breaks
    s = s.replace("\r\n", "\n").replace("\r", "\n")

    # Convert common block elements
    # Headings
    for i in range(6, 0, -1):
        s = re.sub(
            rf"<h{i}[^>]*>(.*?)</h{i}>",
            lambda m, lvl=i: "\n" + "#" * lvl + " " + m.group(1).strip() + "\n",
            s,
            flags=re.DOTALL | re.IGNORECASE,
        )

    # Bold / italic
    s = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", s, flags=re.DOTALL)
    s = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", s, flags=re.DOTALL)
    s = re.sub(r"<i[^>]*>(.*?)</i>", r"*\1*", s, flags=re.DOTALL)

    # Links
    s = re.sub(
        r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
        r"[\2](\1)",
        s,
        flags=re.DOTALL,
    )

    # Images — convert WP URLs to relative paths
    def img_replace(m):
        attrs = m.group(1)
        src_match = re.search(r'src="([^"]*)"', attrs)
        alt_match = re.search(r'alt="([^"]*)"', attrs)
        if not src_match:
            return ""
        src = src_match.group(1)
        alt = alt_match.group(1) if alt_match else ""
        return f"![{alt}]({src})"

    s = re.sub(r"<img([^>]*)/?>" , img_replace, s, flags=re.IGNORECASE)

    # Figures with captions
    s = re.sub(r"<figure[^>]*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</figure>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<figcaption[^>]*>(.*?)</figcaption>", r"*\1*", s, flags=re.DOTALL)

    # Lists
    s = re.sub(r"<ul[^>]*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</ul>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<ol[^>]*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</ol>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", s, flags=re.DOTALL)

    # Blockquotes
    s = re.sub(
        r"<blockquote[^>]*>(.*?)</blockquote>",
        lambda m: "\n"
        + "\n".join("> " + line for line in m.group(1).strip().split("\n"))
        + "\n",
        s,
        flags=re.DOTALL,
    )

    # Paragraphs and breaks
    s = re.sub(r"<p[^>]*>", "\n\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</p>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)

    # Divs
    s = re.sub(r"<div[^>]*>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</div>", "\n", s, flags=re.IGNORECASE)

    # WordPress blocks / comments
    s = re.sub(r"<!--.*?-->", "", s, flags=re.DOTALL)

    # Iframes (YouTube embeds etc) — keep as raw HTML
    # Already will pass through

    # Strip remaining tags (but keep iframes)
    s = re.sub(r"<(?!iframe)(?!/iframe)[^>]+>", "", s)

    # Clean up whitespace
    s = re.sub(r"\n{3,}", "\n\n", s)
    s = s.strip()

    return s


def slugify(text):
    """Create a URL-safe slug."""
    s = text.lower()
    s = re.sub(r"[æ]", "ae", s)
    s = re.sub(r"[ø]", "o", s)
    s = re.sub(r"[å]", "a", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s


def escape_yaml(text):
    """Escape a string for YAML front matter."""
    if not text:
        return '""'
    # If it contains quotes, colons, or special chars, wrap in quotes
    if any(c in text for c in ':"\'#[]{}|>&*!?,\n'):
        escaped = text.replace('"', '\\"')
        return f'"{escaped}"'
    return text


def convert(wxr_path, output_dir):
    tree = ET.parse(wxr_path)
    root = tree.getroot()

    os.makedirs(output_dir, exist_ok=True)

    # Build author map
    authors = {}
    for a in root.iter("{http://wordpress.org/export/1.2/}author"):
        login = a.find("{http://wordpress.org/export/1.2/}author_login").text
        display = a.find("{http://wordpress.org/export/1.2/}author_display_name").text
        authors[login] = display

    count = 0
    slugs_seen = set()

    for item in root.iter("item"):
        post_type = item.find("wp:post_type", NS)
        status = item.find("wp:status", NS)

        if post_type is None or post_type.text != "post":
            continue
        if status is None or status.text != "publish":
            continue

        title = item.find("title").text or "Untitled"
        date_str = item.find("wp:post_date", NS).text  # e.g. "2018-01-23 11:12:33"
        slug = item.find("wp:post_name", NS).text or slugify(title)
        author_login = item.find("dc:creator", NS).text or ""
        author = authors.get(author_login, author_login)
        content_html = item.find("content:encoded", NS).text or ""
        link = item.find("link").text or ""

        # Categories and tags
        categories = []
        tags = []
        for cat in item.findall("category"):
            domain = cat.get("domain")
            if domain == "category" and cat.text:
                categories.append(cat.text)
            elif domain == "post_tag" and cat.text:
                tags.append(cat.text)

        # Parse date
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            dt = datetime.now()

        # Build unique slug with date prefix
        date_prefix = dt.strftime("%Y-%m-%d")
        full_slug = f"{date_prefix}-{slug}"

        if full_slug in slugs_seen:
            i = 2
            while f"{full_slug}-{i}" in slugs_seen:
                i += 1
            full_slug = f"{full_slug}-{i}"
        slugs_seen.add(full_slug)

        # Convert content
        content_md = html_to_markdown(content_html)

        # Build old URL path for alias
        # WP format: /2018/01/23/slug/ or /slug/
        old_path = ""
        if link:
            old_path = link.replace("https://www.norskkornolfestival.no", "").replace(
                "http://www.norskkornolfestival.no", ""
            )

        # Front matter
        fm_lines = [
            "---",
            f"title: {escape_yaml(title)}",
            f"date: {dt.strftime('%Y-%m-%dT%H:%M:%S+01:00')}",
            f"author: {escape_yaml(author)}",
        ]

        if old_path and old_path != f"/nyheter/{full_slug}/":
            fm_lines.append(f"aliases:")
            fm_lines.append(f"  - {escape_yaml(old_path)}")

        if tags:
            fm_lines.append(f"tags: [{', '.join(escape_yaml(t) for t in tags)}]")

        fm_lines.append("---")

        # Write file
        filename = f"{full_slug}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(fm_lines))
            f.write("\n\n")
            f.write(content_md)
            f.write("\n")

        count += 1

    print(f"Converted {count} posts to {output_dir}/")


if __name__ == "__main__":
    wxr = sys.argv[1] if len(sys.argv) > 1 else "/Users/eirikhm/Downloads/norskkornlfestival2026.WordPress.2026-03-16.xml"
    out = sys.argv[2] if len(sys.argv) > 2 else "content/nb/nyheter"
    convert(wxr, out)
