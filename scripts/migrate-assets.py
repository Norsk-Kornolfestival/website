#!/usr/bin/env python3
"""Download WP upload assets referenced in content and rewrite URLs to local paths."""

import os
import re
import subprocess
import sys
from urllib.parse import unquote

CONTENT_DIR = "content"
STATIC_DIR = "static/images/wp"

# Match WP upload URLs (both http and https, with or without usercontent.one proxy)
WP_URL_RE = re.compile(
    r'https?://(?:usercontent\.one/wp/)?(?:www\.)?norskkornolfestival\.no/wp-content/uploads/([^\s\)\]"\']+)'
)


def find_all_urls():
    """Scan all markdown files for WP upload URLs."""
    urls = {}  # url -> set of files referencing it
    for root, _, files in os.walk(CONTENT_DIR):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
            for m in WP_URL_RE.finditer(content):
                full_url = m.group(0)
                urls.setdefault(full_url, set()).add(fpath)
    return urls


def url_to_local_path(url):
    """Convert WP upload URL to local static path."""
    m = WP_URL_RE.match(url)
    if not m:
        return None
    rel_path = unquote(m.group(1))
    # Determine subdirectory by file extension
    ext = rel_path.rsplit(".", 1)[-1].lower() if "." in rel_path else ""
    if ext == "pdf":
        local_dir = "static/files/wp"
    else:
        local_dir = STATIC_DIR
    local_path = os.path.join(local_dir, rel_path)
    return local_path


def url_to_hugo_path(url):
    """Convert WP upload URL to Hugo-relative path (for use in markdown)."""
    m = WP_URL_RE.match(url)
    if not m:
        return None
    rel_path = unquote(m.group(1))
    ext = rel_path.rsplit(".", 1)[-1].lower() if "." in rel_path else ""
    if ext == "pdf":
        return f"/files/wp/{rel_path}"
    return f"/images/wp/{rel_path}"


def download_file(url, local_path):
    """Download a file using curl."""
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    # Try the direct URL first
    result = subprocess.run(
        ["curl", "-fL", "--max-time", "15", "-o", local_path, url],
        capture_output=True,
    )
    if result.returncode == 0 and os.path.getsize(local_path) > 0:
        return True

    # If http, also try https
    if url.startswith("http://"):
        https_url = "https://" + url[7:]
        result = subprocess.run(
            ["curl", "-fL", "--max-time", "15", "-o", local_path, https_url],
            capture_output=True,
        )
        if result.returncode == 0 and os.path.getsize(local_path) > 0:
            return True

    # Try via usercontent.one proxy
    proxy_url = url.replace(
        "://www.norskkornolfestival.no/",
        "://usercontent.one/wp/www.norskkornolfestival.no/",
    ).replace(
        "://norskkornolfestival.no/",
        "://usercontent.one/wp/www.norskkornolfestival.no/",
    )
    if not proxy_url.startswith("https"):
        proxy_url = "https" + proxy_url[4:]
    result = subprocess.run(
        ["curl", "-fL", "--max-time", "15", "-o", local_path, proxy_url],
        capture_output=True,
    )
    if result.returncode == 0 and os.path.getsize(local_path) > 0:
        return True

    # Clean up empty file
    if os.path.exists(local_path):
        os.remove(local_path)
    return False


def rewrite_urls(file_path, url_map):
    """Rewrite WP URLs to local paths in a markdown file."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    changed = False
    for old_url, new_path in url_map.items():
        if old_url in content:
            content = content.replace(old_url, new_path)
            changed = True

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    return changed


def main():
    print("Scanning content for WP upload URLs...")
    urls = find_all_urls()
    print(f"Found {len(urls)} unique URLs across {len(set(f for fs in urls.values() for f in fs))} files")

    # Download all files
    downloaded = {}
    failed = []
    for i, (url, files) in enumerate(sorted(urls.items()), 1):
        local_path = url_to_local_path(url)
        hugo_path = url_to_hugo_path(url)
        if not local_path:
            continue

        # Skip if already downloaded
        if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
            downloaded[url] = hugo_path
            print(f"  [{i}/{len(urls)}] EXISTS {local_path}")
            continue

        print(f"  [{i}/{len(urls)}] Downloading {url[:80]}...")
        if download_file(url, local_path):
            size = os.path.getsize(local_path)
            downloaded[url] = hugo_path
            print(f"           -> {local_path} ({size // 1024}KB)")
        else:
            failed.append(url)
            print(f"           -> FAILED")

    print(f"\nDownloaded: {len(downloaded)}, Failed: {len(failed)}")

    # Rewrite URLs in content files
    print("\nRewriting URLs in content files...")
    all_files = set()
    for files in urls.values():
        all_files.update(files)

    rewritten = 0
    for fpath in sorted(all_files):
        if rewrite_urls(fpath, downloaded):
            rewritten += 1

    print(f"Rewrote URLs in {rewritten} files")

    if failed:
        print(f"\n=== Failed downloads ({len(failed)}) ===")
        for url in sorted(failed):
            print(f"  {url}")


if __name__ == "__main__":
    main()
