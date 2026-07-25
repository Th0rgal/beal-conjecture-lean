#!/usr/bin/env python3
"""Replay the exceptional-q localization in the cross-side mask descent."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CERTIFICATE = (
    ROOT / "Research" / "GlobalBeal" / "cross_side_square_mask_descent.json"
)


class CheckError(RuntimeError):
    pass


def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
    )
    if not isinstance(value, dict):
        raise CheckError("certificate root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            body, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
    ).hexdigest()


def verify(value: dict[str, Any]) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("schema mismatch")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("certificate digest mismatch")

    localization = value["odd_Y_branch"].get("exceptional_localization", {})
    if "if and only if q divides X" not in localization.get("minus", ""):
        raise CheckError("minus localization missing")
    if "if and only if q divides Z" not in localization.get("plus", ""):
        raise CheckError("plus localization missing")
    if "at most one" not in localization.get("coprime_consequence", ""):
        raise CheckError("coprime consequence missing")

    for q in (3, 5, 7, 11, 13):
        for u in range(1, 45, 2):
            for v in range(u + 2, 70, 2):
                if math.gcd(u, v) != 1:
                    continue
                if (v**q - u**q) % q != (v - u) % q:
                    raise CheckError("minus Fermat congruence failed")
                if (v**q + u**q) % q != (v + u) % q:
                    raise CheckError("plus Fermat congruence failed")
                if (v - u) % q == 0 and (v + u) % q == 0:
                    raise CheckError("both signs became q-exceptional")


def expect_rejection(value: dict[str, Any]) -> None:
    bad = copy.deepcopy(value)
    bad["odd_Y_branch"]["exceptional_localization"]["minus"] = "none"
    bad["certificate_sha256"] = digest(bad)
    try:
        verify(bad)
    except CheckError:
        return
    raise CheckError("mutated localization accepted")


def main() -> int:
    value = load(CERTIFICATE)
    verify(value)
    expect_rejection(value)

    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        handle.write('{"x":1,"x":2}')
        path = pathlib.Path(handle.name)
    try:
        try:
            load(path)
        except CheckError:
            pass
        else:
            raise CheckError("duplicate JSON keys accepted")
    finally:
        path.unlink(missing_ok=True)

    print(json.dumps({
        "status": "ok",
        "certificate_sha256": value["certificate_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
