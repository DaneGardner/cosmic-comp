#!/usr/bin/env python3
"""Resolve the cosmic-comp source Pop!_OS currently ships, and whether a patched build is due.

Prints GitHub Actions outputs (key=value lines) on stdout:
  pop_version  version of Pop's cosmic-comp source package
  commit       full upstream commit Pop built it from
  version      version our patched package gets
  build        "true" when the published repo does not already hold `version`
"""

import argparse
import gzip
import sys
import urllib.error
import urllib.request

POP_SOURCES = "http://apt.pop-os.org/release/dists/noble/main/source/Sources.gz"
SUFFIX = "+edgetiling1"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def stanza(text: str, package: str) -> dict[str, str]:
    for block in text.split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if line and not line[0].isspace() and ":" in line:
                key, _, value = line.partition(":")
                fields[key] = value.strip()
        if fields.get("Package") == package:
            return fields
    raise SystemExit(f"{package} not found in index")


def published_version(repo_url: str) -> str | None:
    try:
        text = fetch(repo_url.rstrip("/") + "/Packages").decode()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return stanza(text, "cosmic-comp")["Version"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-url", required=True, help="base URL of the published apt repo")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    src = stanza(gzip.decompress(fetch(POP_SOURCES)).decode(), "cosmic-comp")
    pop_version = src["Version"]
    # Directory: pool/noble/cosmic-comp/<full upstream sha>
    commit = src["Directory"].rsplit("/", 1)[1]
    if len(commit) != 40 or not commit.startswith(pop_version.rsplit("~", 1)[1]):
        raise SystemExit(f"cannot derive commit: version={pop_version} directory={src['Directory']}")

    version = pop_version + SUFFIX
    current = published_version(args.repo_url)
    build = args.force or current != version
    print(f"published={current} target={version} build={build}", file=sys.stderr)
    for k, v in (("pop_version", pop_version), ("commit", commit), ("version", version),
                 ("build", str(build).lower())):
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
