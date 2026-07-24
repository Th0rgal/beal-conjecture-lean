#!/usr/bin/env python3
"""One-shot LMFDB fetcher for the lowest candidate mod-5 level.

This is a research producer, not a trusted checker.  Its output must be pinned
and replayed by a separate offline checker before being used in a theorem.
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

BASE = "https://www.lmfdb.org/api/hmf_forms/"
QUERY = {
    "field_label": "s3.3.49.1",
    "level_norm": "i729",
    "parallel_weight": "i2",
    "_format": "json",
    "_fields": "label,level_norm,level_ideal,dimension,is_CM,is_base_change,parallel_weight",
}


def main() -> int:
    url = BASE + "?" + urllib.parse.urlencode(QUERY)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "beal-conjecture-lean-research/1.0 (+https://github.com/Th0rgal/beal-conjecture-lean)"
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    output = {
        "schema_version": 1,
        "source_url": url,
        "query": QUERY,
        "response": payload,
    }
    json.dump(output, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
