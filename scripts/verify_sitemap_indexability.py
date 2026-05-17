#!/usr/bin/env python3
"""Verify sitemap URLs are final, indexable, self-canonical pages."""

from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


ROOT = Path(__file__).resolve().parents[1]
PREFERRED_HOST = "sportsbettingprime.com"
BASE_URL = f"https://{PREFERRED_HOST}"

META_ROBOTS_RE = re.compile(
    r"""<meta\b(?=[^>]*\bname\s*=\s*['"]robots['"])(?=[^>]*\bcontent\s*=\s*['"]([^'"]+)['"])[^>]*>""",
    re.I | re.S,
)
CANONICAL_RE = re.compile(
    r"""<link\b(?=[^>]*\brel\s*=\s*['"]canonical['"])(?=[^>]*\bhref\s*=\s*['"]([^'"]+)['"])[^>]*>""",
    re.I | re.S,
)
META_REFRESH_RE = re.compile(r"""<meta\b(?=[^>]*http-equiv\s*=\s*['"]refresh['"])[^>]*>""", re.I | re.S)


def normalize_url(url: str) -> str:
    parsed = urlparse(html.unescape(url.strip()))
    path = parsed.path or "/"
    if path != "/" and path.endswith("/index.html"):
        path = path[: -len("index.html")]
    return f"https://{parsed.netloc.lower()}{path}"


def local_path_for(url: str) -> Path:
    path = urlparse(url).path
    if path in {"", "/"}:
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path.lstrip("/") / "index.html"
    return ROOT / path.lstrip("/")


def read_sitemap(path: Path) -> list[str]:
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    return [node.text.strip() for node in root.findall(".//{*}loc") if node.text and node.text.strip()]


def read_robots() -> RobotFileParser:
    parser = RobotFileParser()
    robots = ROOT / "robots.txt"
    if robots.exists():
        parser.parse(robots.read_text(encoding="utf-8", errors="ignore").splitlines())
    else:
        parser.parse([])
    return parser


def header_value(headers: object, name: str) -> str:
    if hasattr(headers, "items"):
        for key, value in headers.items():
            if key.lower() == name.lower():
                return str(value)
    return ""


def fetch_live(url: str) -> tuple[int | str, str, str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "SportsBettingPrime-sitemap-guard/1.0"})
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    try:
        with opener.open(request, timeout=30) as response:
            body = response.read().decode("utf-8", errors="ignore")
            return response.status, response.geturl(), header_value(response.headers, "X-Robots-Tag"), body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return exc.code, exc.geturl(), header_value(exc.headers, "X-Robots-Tag"), body
    except Exception as exc:
        return "ERR", url, "", str(exc)


def inspect_local(url: str, robots: RobotFileParser) -> list[str]:
    issues: list[str] = []
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() != PREFERRED_HOST:
        issues.append("non_preferred_host")
    if not robots.can_fetch("*", url):
        issues.append("robots_blocked")

    path = local_path_for(url)
    if not path.exists():
        issues.append("non_200_missing_local_file")
        return issues
    if path.suffix.lower() not in {".html", ".htm", ""}:
        issues.append("non_html_sitemap_url")
        return issues

    text = path.read_text(encoding="utf-8", errors="ignore")
    robots_match = META_ROBOTS_RE.search(text)
    if robots_match and "noindex" in robots_match.group(1).lower():
        issues.append("noindex")
    if META_REFRESH_RE.search(text):
        issues.append("redirect_meta_refresh")

    canonical_match = CANONICAL_RE.search(text)
    if not canonical_match:
        issues.append("missing_canonical")
    else:
        canonical = normalize_url(canonical_match.group(1))
        expected = normalize_url(url)
        if canonical != expected:
            issues.append(f"non_self_canonical:{canonical}")
    return issues


def inspect_live(url: str) -> list[str]:
    issues: list[str] = []
    status, final_url, x_robots, body = fetch_live(url)
    if status != 200:
        issues.append(f"non_200:{status}")
    if normalize_url(final_url) != normalize_url(url):
        issues.append(f"redirected_to:{final_url}")
    if "noindex" in x_robots.lower():
        issues.append("x_robots_noindex")
    robots_match = META_ROBOTS_RE.search(body)
    if robots_match and "noindex" in robots_match.group(1).lower():
        issues.append("live_meta_noindex")
    canonical_match = CANONICAL_RE.search(body)
    if canonical_match and normalize_url(canonical_match.group(1)) != normalize_url(url):
        issues.append(f"live_non_self_canonical:{canonical_match.group(1)}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sitemap", type=Path, default=ROOT / "sitemap.xml")
    parser.add_argument("--live", action="store_true", help="Also verify deployed HTTP status, redirects, X-Robots, and live canonicals.")
    args = parser.parse_args()

    urls = read_sitemap(args.sitemap)
    robots = read_robots()
    failures: list[tuple[str, list[str]]] = []
    for url in urls:
        issues = inspect_local(url, robots)
        if args.live:
            issues.extend(inspect_live(url))
        if issues:
            failures.append((url, issues))

    print(f"sitemap_urls={len(urls)}")
    print(f"failures={len(failures)}")
    for url, issues in failures[:100]:
        print(f"FAIL {url} :: {', '.join(issues)}")
    if len(failures) > 100:
        print(f"... {len(failures) - 100} additional failures omitted")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
