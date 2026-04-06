#!/usr/bin/env python3
"""Rewrite the latest-push Shields badge between README markers."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

OWNER = "Ducstii"
README = Path("README.md")
START = "<!-- LATEST_REPO_BADGE:START -->"
END = "<!-- LATEST_REPO_BADGE:END -->"


def fetch_repos() -> list[dict]:
    url = (
        f"https://api.github.com/users/{OWNER}/repos"
        "?per_page=100&sort=pushed&type=owner"
    )
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.load(resp)


def main() -> int:
    this_repo = os.environ.get("GITHUB_REPOSITORY", f"{OWNER}/{OWNER}").lower()

    try:
        repos = fetch_repos()
    except urllib.error.HTTPError as e:
        sys.stderr.write(e.read().decode(errors="replace"))
        return 1

    chosen: dict | None = None
    for r in repos:
        full = (r.get("full_name") or "").lower()
        if full == this_repo:
            continue
        chosen = r
        break

    if not chosen:
        sys.stderr.write("No public repo left to badge after excluding this repo.\n")
        return 1

    name = chosen["name"]
    full_name = chosen["full_name"]
    label = quote(f"{name} updated")
    badge = f"https://img.shields.io/github/last-commit/{full_name}?style=for-the-badge&logo=github&label={label}"
    link = f"https://github.com/{full_name}/commits"
    block = f'<a href="{link}"><img src="{badge}" alt="Last commit to {name}" /></a>'

    text = README.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        re.DOTALL,
    )
    if not pattern.search(text):
        sys.stderr.write("README markers missing.\n")
        return 1

    new_text = pattern.sub(f"{START}\n  {block}\n  {END}", text, count=1)
    if new_text == text:
        print("Latest-push badge already up to date.")
        return 0

    README.write_text(new_text, encoding="utf-8")
    print(f"Badge now tracks {full_name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
