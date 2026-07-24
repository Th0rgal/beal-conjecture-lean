#!/usr/bin/env python3
"""Replay the finite arithmetic in the fixed-7 ray/Hasse dichotomy.

The large candidate table, arithmetic helpers, and manifest validator are kept
in adjacent modules for reviewability. The finite-flat and local-type steps are
explicit imported lemmas, not claims of this checker.
"""
from __future__ import annotations

from signature357_ray_hasse_validate import *  # noqa: F401,F403

def expect_rejection(data: dict[str, Any], description: str) -> None:
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f"checker accepted {description}")


def self_test() -> None:
    source = load_json(DEFAULT_MANIFEST)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated["candidate_product_rows"][0]["products"][0] = [0, 0]
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "a zeroed prime-17 candidate product")

    mutated = copy.deepcopy(source)
    mutated["ray_class_coordinates"]["19a=4+phi"] = [0, 0]
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "a mutated ray-class coordinate")

    mutated = copy.deepcopy(source)
    mutated["hasse_witt_mod7"]["generic_matrix"][0][1] = [[4, 5]]
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "a mutated generic Hasse-Witt matrix")

    mutated = copy.deepcopy(source)
    mutated["conditional_conclusions"][-1] = "the full signature is proved"
    mutated["certificate_sha256"] = canonical_sha256(mutated)
    expect_rejection(mutated, "an overclaimed conclusion")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
        path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError("checker accepted duplicate JSON keys")
    finally:
        path.unlink(missing_ok=True)

    print("signature-357 ray/Hasse negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.manifest))
    print("signature-357 fixed-7 ray/Hasse arithmetic certificate valid")
    print("  unique ray character: eta=(2,0)")
    print("  reducibility support before the residual-prime step: 2*19*71 | C, 13 | A*C")
    print("  Hasse-Witt matrices: generic ordinary test; zero/infinity stable rank zero")
    print("  conclusion remains conditional on the explicit finite-flat/local-type lemmas")
    print(f"  certificate sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
