#!/usr/bin/env python3
"""Site content validator for sportsbettingprime (run by .github/workflows/content-validator.yml).

The workflow has called this script since 2026-07-30, but the file was never
committed: .gitignore ignores *.py, so it lived only on the machine that wrote
the workflow, and every run since failed with "No such file or directory".

Checks, per the workflow's own description of what has gone wrong on this site:
  1. fabricated-stat fingerprints  - percentages / rates quoted to 3+ decimals,
                                     the shape random.uniform() output takes
  2. randomness in generators      - any scripts/*.py that imports or calls random
  3. guaranteed-win language        - "guaranteed win", "lock of the day", "can't
                                     lose", "risk-free" stated as a promise (a
                                     sentence that disclaims them is fine)
  4. misuse of "verified"           - "verified record/picks/results/handicapper"
                                     stated without TrustMyRecord, the only place
                                     such verification exists
  5. noindex directives             - a robots meta carrying noindex
  6. broken internal links          - href/src to a site path that is not in the repo
  7. fact-manifest integrity        - every facts/*.json parses, names its article,
                                     and that article exists
  8. capability overclaims          - "live odds", "real-time odds/data", "updated
                                     hourly / multiple times daily" stated as fact

Exit 0 when clean, 1 with a listing otherwise. Stdlib only.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

NEGATION = re.compile(
    r"\b(no|not|never|without|nor|neither|zero|isn'?t|aren'?t|don'?t|doesn'?t|won'?t|"
    r"avoid|free of|instead of|rather than)\b", re.I)



def long_path(path):
    """On Windows use the extended-length path form so the site's 200-character
    article filenames are reachable from any checkout depth."""
    if sys.platform == "win32":
        return chr(92) * 2 + "?" + chr(92) + os.path.abspath(path)
    return path


def read_text(path):
    with open(long_path(path), encoding="utf-8", errors="replace") as fh:
        return fh.read()


def exists(path):
    return os.path.exists(long_path(path))

def text_of(html):
    html = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b[^>]*>.*?</style>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    text = text.replace("&#39;", "'").replace("&rsquo;", "'").replace("&amp;", "&")
    return re.sub(r"[ \t]+", " ", text)


def negated(text, start):
    """True when the sentence before the match carries a negation, i.e. the
    page is disclaiming the phrase rather than making the claim."""
    window = text[max(0, start - 300):start]
    window = re.split(r"[.!?]\s", window)[-1]
    return bool(NEGATION.search(window))


def snippet(text, start, end):
    return re.sub(r"\s+", " ", text[max(0, start - 40):end + 20]).strip()


def check_page(path, html):
    problems = []
    text = text_of(html)

    # 5. noindex: only a real robots directive, never prose about noindex.
    for m in re.finditer(r"<meta[^>]+name=[\"']robots[\"'][^>]*>", html, re.I):
        if re.search(r"noindex", m.group(0), re.I):
            problems.append("noindex directive: %s" % m.group(0)[:100])

    # 1. fabricated-stat fingerprints: a percentage or per-game rate quoted with
    # three or more decimals is not something a sportsbook or a box score prints.
    for m in re.finditer(r"\b\d{1,3}\.\d{3,}\s*(%|percent|per game|per nine|K/9|BB/9)", text, re.I):
        problems.append("fabricated-stat fingerprint: %s" % m.group(0))

    # 3. guaranteed-win language stated as a promise.
    # Promises about picks. "Guaranteed profit" and "risk-free" are left out on
    # purpose: the strategy pages use them correctly for hedging, arbitrage and
    # the vig, which is education, not a pick promise.
    pat = (r"\b(guaranteed (win|winner|lock)s?|lock of the (day|week|night)|"
           r"can'?t (lose|miss)|sure thing|can'?t-miss)\b")
    for m in re.finditer(pat, text, re.I):
        if not negated(text, m.start()):
            problems.append("guaranteed-win language: ...%s..." % snippet(text, m.start(), m.end()))

    # 4. "verified" claims that are not TrustMyRecord's.
    pat = r"\bverified (record|records|results|picks|handicapper|handicappers|track record)\b"
    # Every page's nav carries "Find Verified Handicappers" pointing at
    # trustmyrecord.com; the claim is supported when the page links there.
    backed = "trustmyrecord" in html.lower().replace(" ", "")
    for m in re.finditer(pat, text, re.I):
        if not backed and not negated(text, m.start()):
            problems.append("unsupported 'verified' claim: ...%s..." % snippet(text, m.start(), m.end()))

    # 8. capability overclaims stated as fact.
    pat = (r"\b(live odds|real[- ]time (odds|lines|data)|"
           r"updated (hourly|every hour|multiple times (a |per )?day|multiple times daily))\b")
    for m in re.finditer(pat, text, re.I):
        # A claim about THIS site: a sentence with "we", "our", "here", "this site"
        # or the site name. Describing what Covers or a sportsbook does is not one.
        sentence = re.split(r"[.!?]\s", text[max(0, m.start() - 200):m.start()])[-1] + text[m.start():m.end() + 120].split(". ")[0]
        first_person = re.search(r"(we|our|us|here|this (site|page)|sportsbettingprime)", sentence, re.I)
        if first_person and not negated(text, m.start()):
            problems.append("capability overclaim: ...%s..." % snippet(text, m.start(), m.end()))

    # 6. broken internal links.
    for m in re.finditer(r"\b(?:href|src)=[\"']([^\"'#?]+)", html, re.I):
        target = m.group(1).strip()
        if not target or re.match(r"^(https?:|//|mailto:|tel:|data:|javascript:)", target, re.I):
            continue
        if target.startswith("/"):
            local = target.lstrip("/")
        else:
            local = os.path.normpath(os.path.join(os.path.dirname(path), target)).replace("\\", "/")
        if local == "" or local.endswith("/"):
            local = local + "index.html"
        if not exists(local):
            problems.append("broken internal link: %s" % target)
    return problems


def main():
    failures = {}

    # 2. randomness in generators
    for script in sorted(glob.glob("scripts/*.py")):
        if os.path.basename(script) == os.path.basename(__file__):
            continue
        src = read_text(script)
        code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
        if re.search(r"\bimport random\b|\bfrom random import\b|"
                     r"\brandom\.(uniform|randint|choice|random|gauss|shuffle|sample)\b", code):
            failures.setdefault(script, []).append("randomness in a content generator")

    # 7. fact manifests
    for manifest in sorted(glob.glob("facts/*.json")):
        try:
            data = json.loads(read_text(manifest))
        except Exception as exc:  # noqa: BLE001 - any parse failure is the finding
            failures.setdefault(manifest, []).append("manifest does not parse: %s" % exc)
            continue
        if not isinstance(data, dict) or not data.get("article"):
            failures.setdefault(manifest, []).append("manifest names no article")
            continue
        article = str(data["article"]).lstrip("/")
        if not exists(article):
            failures.setdefault(manifest, []).append("manifest article missing: %s" % article)

    pages = sorted(p.replace("\\", "/") for p in glob.glob("**/*.html", recursive=True)
                   if not p.replace("\\", "/").startswith(("node_modules", ".git", "consensus_library/archive")))
    for page in pages:
        html = read_text(page)
        found = check_page(page, html)
        if found:
            failures[page] = found

    total = sum(len(v) for v in failures.values())
    print("validate_site: %d page(s) checked, %d problem(s)" % (len(pages), total))
    for path, items in failures.items():
        print("  [FAIL] %s" % path)
        for item in items:
            print("     - %s" % item)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
