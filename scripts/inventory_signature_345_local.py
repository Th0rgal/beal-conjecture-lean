#!/usr/bin/env python3
"""Emit the raw local-obstruction inventory for reconstructed Edwards IDs.

This diagnostic is intentionally separate from the proof checker. It computes
local profiles using the same exact arithmetic, but does not attach paper C_i
labels to reconstructed Table-1 IDs. The output is used to construct and audit
the missing source-index permutation.
"""

from __future__ import annotations

import json

import check_signature_345_local as local


def main() -> int:
    triples = local.reconstruct_triples()
    q2_powers: dict[int, int] = {}
    q3_powers: dict[int, int] = {}
    mod256_empty: list[int] = []

    for form_id, (f, _g, _h) in triples.items():
        q2 = local.first_obstructing_power(f, 2, 14)
        if q2 is not None:
            q2_powers[form_id] = q2
        q3 = local.first_obstructing_power(f, 3, 9)
        if q3 is not None:
            q3_powers[form_id] = q3
        if not local.primitive_modulus_set_nonempty(triples[form_id], 256):
            mod256_empty.append(form_id)

    payload = {
        "raw_reconstructed_ids": {
            "first_obstructing_power_2": q2_powers,
            "first_obstructing_power_3": q3_powers,
            "primitive_mod_256_empty": mod256_empty,
        },
        "paper_labels": {
            "no_Q2": [1, 4, 9, 10, 11, 13, 14, 18, 25, 26, 33, 35, 39, 45, 46, 48],
            "no_Q3_after_Q2": [20, 42],
            "primitive_mod_256_empty_after_local": [7, 8, 12, 19, 21, 22, 30, 34],
            "survivors": [2, 3, 5, 6, 15, 16, 17, 23, 24, 27, 28, 29, 31, 32, 36, 37, 38, 40, 41, 43, 44, 47, 49],
        },
        "known_anchors": {
            "paper_2": 28,
            "paper_3": 2,
            "paper_5": 3,
        },
    }
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
