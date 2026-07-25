#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

CERTIFICATE = (
    Path(__file__).resolve().parents[1]
    / "Research"
    / "GlobalBeal"
    / "repeated_exponent_d1_audit.json"
)


class CheckError(RuntimeError):
    pass


def digest(value: dict[str, Any]) -> str:
    body = copy.deepcopy(value)
    body.pop("certificate_sha256", None)
    return hashlib.sha256(
        json.dumps(
            body,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()
    ).hexdigest()


def fueter_vector(p: int, n: int) -> tuple[int, ...]:
    return tuple(
        ((n + 1) * c) // p - (n * c) // p
        for c in range(1, p)
    )


def sigma_action(
    p: int, vector: tuple[int, ...], multiplier: int
) -> tuple[int, ...]:
    inverse = pow(multiplier, -1, p)
    result = [0] * (p - 1)
    for c, coefficient in enumerate(vector, start=1):
        d = c * inverse % p
        result[d - 1] += coefficient
    return tuple(result)


def conjugates(p: int) -> list[tuple[int, ...]]:
    result: list[tuple[int, ...]] = []
    for n in range(1, (p - 1) // 2 + 1):
        base = fueter_vector(p, n)
        for multiplier in range(1, p):
            value = sigma_action(p, base, multiplier)
            if value not in result:
                result.append(value)
    return result


def phi(p: int, vector: tuple[int, ...]) -> int:
    return sum(
        coefficient * pow(c, -1, p)
        for c, coefficient in enumerate(vector, start=1)
    ) % p


def verify(value: dict[str, Any]) -> None:
    if value.get("schema_version") != 1:
        raise CheckError("schema")
    if value.get("certificate_sha256") != digest(value):
        raise CheckError("digest")
    if value.get("status") != (
        "unconditional-finite-audit-of-the-D-equals-one-proof"
    ):
        raise CheckError("status")
    if "not a counterexample" not in value.get("nonclaim", ""):
        raise CheckError("nonclaim")
    if value.get("logical_gap", {}).get("missing_hypothesis") == "none":
        raise CheckError("missing-hypothesis marker")

    c5 = conjugates(5)
    expected_c5 = [
        tuple(row)
        for row in value["p5_exact_audit"]["conjugate_fueter_vectors"]
    ]
    if c5 != expected_c5:
        raise CheckError("p5 conjugates")
    if [phi(5, row) for row in c5] != [1, 2, 3, 4]:
        raise CheckError("p5 phi values")

    sums5 = {
        tuple(a + b for a, b in zip(left, right))
        for left in c5
        for right in c5
        if phi(
            5, tuple(a + b for a, b in zip(left, right))
        ) == 0
    }
    if sums5 != {(1, 1, 1, 1)}:
        raise CheckError("p5 J1 inventory")
    if value["p5_exact_audit"]["unique_element"] != [1, 1, 1, 1]:
        raise CheckError("p5 recorded unique element")

    c7 = conjugates(7)
    zero7 = [row for row in c7 if phi(7, row) == 0]
    expected_zero7 = [
        tuple(row)
        for row in value["p7_exact_audit"]["phi_zero_fueter_vectors"]
    ]
    if zero7 != expected_zero7:
        raise CheckError("p7 zero Fueter inventory")

    for psi in zero7:
        target = tuple(2 * coefficient for coefficient in psi)
        decompositions = [
            (i, j)
            for i, left in enumerate(c7)
            for j, right in enumerate(c7)
            if tuple(a + b for a, b in zip(left, right)) == target
        ]
        index = c7.index(psi)
        if decompositions != [(index, index)]:
            raise CheckError("p7 unique repeated decomposition")


def self_test(value: dict[str, Any]) -> None:
    verify(value)
    mutations = []

    bad = copy.deepcopy(value)
    bad["p5_exact_audit"]["unique_element"][0] = 2
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["logical_gap"]["missing_hypothesis"] = "none"
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    bad = copy.deepcopy(value)
    bad["nonclaim"] = "This proves the family."
    bad["certificate_sha256"] = digest(bad)
    mutations.append(bad)

    for index, mutation in enumerate(mutations):
        try:
            verify(mutation)
        except CheckError:
            continue
        raise CheckError(f"negative fixture {index} accepted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, default=CERTIFICATE)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    value = json.loads(args.certificate.read_text(encoding="utf-8"))
    if args.self_test:
        self_test(value)
    else:
        verify(value)
    print(json.dumps({
        "status": "ok",
        "self_test": args.self_test,
        "certificate_sha256": value["certificate_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
