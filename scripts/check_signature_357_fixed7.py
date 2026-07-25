#!/usr/bin/env python3
"""Validate and optionally replay the fixed-p=7 elimination frontier for (5,p,3).

The manifest records what can be extracted from the public Pacetti--Villagra
Magma transcript at the pinned commit. Two Hilbert levels are currently complete
for p=7:

* level exponents (2,2): 3 survivors among 14 newforms;
* level exponents (3,2): 9 survivors among 111 newforms.

The other two public runs were not emitted with `flag := true`, so their exact
fixed-7 survivor sets are intentionally marked incomplete.

When `--transcript` is supplied, this checker parses a TheoremA transcript and
recomputes the survivor sets. Without it, the checker validates the pinned
machine-readable frontier and its internal logic. This is research evidence,
not a proof of signature (3,5,7).
"""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import re
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Research" / "Signature357" / "fixed7_frontier.json"
RESIDUAL_PRIME = 7


class FrontierError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise FrontierError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        data = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise FrontierError(str(exc)) from exc
    if not isinstance(data, dict):
        raise FrontierError("manifest root must be an object")
    return data


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise FrontierError(
            f"{context} keys differ: expected {sorted(expected)}, got {sorted(value)}"
        )


def integer_list(value: Any, context: str) -> list[int]:
    if (
        not isinstance(value, list)
        or any(type(item) is not int or item <= 0 for item in value)
        or value != sorted(set(value))
    ):
        raise FrontierError(f"{context} must be a sorted list of distinct positive integers")
    return value


def level_key(level: list[int]) -> str:
    return f"{level[0]},{level[1]}"


def validate_data(data: dict[str, Any]) -> dict[str, list[int] | None]:
    exact_keys(
        data, {"schema_version", "residual_prime", "source", "levels", "summary"},
        "manifest",
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise FrontierError("schema_version must be the integer 1")
    if data["residual_prime"] != RESIDUAL_PRIME:
        raise FrontierError("this manifest must target residual prime 7")

    source = data["source"]
    if not isinstance(source, dict):
        raise FrontierError("source must be an object")
    exact_keys(
        source,
        {"paper_arxiv", "repository", "commit", "path", "blob_sha", "magma_version"},
        "source",
    )
    if (
        source["paper_arxiv"] != "2512.17845"
        or source["repository"] != "lucasvillagra/GFE-5p3"
        or source["commit"] != "e88f914c577ab6cf9a45e5cdd82c1993477fb423"
        or source["path"] != "Outputs/TheoremA.txt"
        or source["blob_sha"] != "890802467458f79b468738a90be4bf8e57f255ff"
    ):
        raise FrontierError("unexpected or unpinned upstream source")

    levels = data["levels"]
    if not isinstance(levels, list) or len(levels) != 4:
        raise FrontierError("levels must contain exactly four entries")

    expected_metadata = {
        "2,2": (45, 14, 4),
        "3,2": (405, 111, 11),
        "2,3": (225, 35, 21),
        "3,3": (2025, 112, 44),
    }
    seen: set[str] = set()
    computed: dict[str, list[int] | None] = {}

    for entry in levels:
        if not isinstance(entry, dict):
            raise FrontierError("level entry must be an object")
        common = {
            "level_exponents",
            "dimension",
            "newform_count",
            "coefficient_field_equals_base_count",
            "transcript_mode",
            "fixed7_complete",
        }
        level = entry.get("level_exponents")
        if (
            not isinstance(level, list)
            or len(level) != 2
            or any(type(x) is not int for x in level)
        ):
            raise FrontierError("level_exponents must be a two-integer array")
        key = level_key(level)
        if key in seen or key not in expected_metadata:
            raise FrontierError(f"unexpected or duplicate level {key}")
        seen.add(key)
        metadata = (
            entry.get("dimension"),
            entry.get("newform_count"),
            entry.get("coefficient_field_equals_base_count"),
        )
        if metadata != expected_metadata[key]:
            raise FrontierError(f"metadata mismatch for level {key}")

        complete = entry.get("fixed7_complete")
        if type(complete) is not bool:
            raise FrontierError(f"fixed7_complete must be boolean at level {key}")

        if entry.get("transcript_mode") == "summary":
            expected = common | {
                "persistent_forms",
                "other_forms_exceptional_residual_primes",
            }
            expected |= (
                {"fixed7_survivors", "reason"}
                if complete
                else {"fixed7_survivors_lower_bound", "required_rerun"}
            )
            exact_keys(entry, expected, f"level {key}")
            persistent = integer_list(entry["persistent_forms"], f"{key} persistent_forms")
            exceptions = integer_list(
                entry["other_forms_exceptional_residual_primes"],
                f"{key} exceptional residual primes",
            )
            if any(form > entry["newform_count"] for form in persistent):
                raise FrontierError(f"persistent form outside level {key}")
            if complete:
                if RESIDUAL_PRIME in exceptions:
                    raise FrontierError(
                        f"summary level {key} cannot be complete while 7 remains exceptional"
                    )
                survivors = integer_list(
                    entry["fixed7_survivors"], f"{key} fixed7_survivors"
                )
                if survivors != persistent:
                    raise FrontierError(
                        f"complete summary level {key} must retain exactly persistent forms"
                    )
                computed[key] = survivors
            else:
                if RESIDUAL_PRIME not in exceptions:
                    raise FrontierError(
                        f"incomplete summary level {key} must explain why 7 is unresolved"
                    )
                lower = integer_list(
                    entry["fixed7_survivors_lower_bound"],
                    f"{key} fixed7_survivors_lower_bound",
                )
                if lower != persistent:
                    raise FrontierError(
                        f"summary lower bound must equal persistent forms at level {key}"
                    )
                if (
                    not isinstance(entry["required_rerun"], str)
                    or "flag := true" not in entry["required_rerun"]
                ):
                    raise FrontierError(f"level {key} lacks a flagged rerun command")
                computed[key] = None
        elif entry.get("transcript_mode") == "flagged_per_form":
            if not complete:
                raise FrontierError("flagged_per_form entries must be complete")
            exact_keys(
                entry,
                common
                | {
                    "forms_with_explicit_7",
                    "failed_forms",
                    "fixed7_survivors",
                    "reason",
                },
                f"level {key}",
            )
            explicit = integer_list(
                entry["forms_with_explicit_7"], f"{key} forms_with_explicit_7"
            )
            failed = integer_list(entry["failed_forms"], f"{key} failed_forms")
            if set(explicit) & set(failed):
                raise FrontierError(f"explicit and failed forms overlap at level {key}")
            survivors = integer_list(
                entry["fixed7_survivors"], f"{key} fixed7_survivors"
            )
            if survivors != sorted(explicit + failed):
                raise FrontierError(
                    f"fixed7 survivors must be explicit-7 union failed forms at level {key}"
                )
            if any(form > entry["newform_count"] for form in survivors):
                raise FrontierError(f"survivor outside level {key}")
            computed[key] = survivors
        else:
            raise FrontierError(f"unknown transcript_mode at level {key}")

    if seen != set(expected_metadata):
        raise FrontierError("missing Hilbert level")

    summary = data["summary"]
    if not isinstance(summary, dict):
        raise FrontierError("summary must be an object")
    exact_keys(
        summary,
        {
            "complete_levels",
            "known_fixed7_survivor_counts",
            "incomplete_levels",
            "total_newforms_in_complete_levels",
            "total_fixed7_survivors_in_complete_levels",
        },
        "summary",
    )
    complete_keys = [level_key(level) for level in summary["complete_levels"]]
    incomplete_keys = [level_key(level) for level in summary["incomplete_levels"]]
    if complete_keys != ["2,2", "3,2"] or incomplete_keys != ["2,3", "3,3"]:
        raise FrontierError("summary level partition mismatch")
    counts = summary["known_fixed7_survivor_counts"]
    if counts != {"2,2": 3, "3,2": 9}:
        raise FrontierError("fixed-7 survivor count mismatch")
    if summary["total_newforms_in_complete_levels"] != 125:
        raise FrontierError("complete-level newform total must be 125")
    if summary["total_fixed7_survivors_in_complete_levels"] != 12:
        raise FrontierError("complete-level survivor total must be 12")
    for key, count in counts.items():
        survivors = computed[key]
        if survivors is None or len(survivors) != count:
            raise FrontierError(f"summary count disagrees at level {key}")
    return computed


RUN_RE = re.compile(
    r">\s*time\s+TheoremA\((\d),(\d),Data(?::flag\s*:=\s*true)?\);"
)
PERSISTENT_RE = re.compile(
    r"The newforms\s*\[\s*([^\]]*?)\s*\]\s*cannot be discarded", re.S
)
EXCEPTIONS_RE = re.compile(
    r"The rest of the newforms can be discarded for p outside\s*\[\s*([^\]]*?)\s*\]",
    re.S,
)
SMALL_RE = re.compile(
    r"i\s*=\s*(\d+)\s+of\s+(\d+),\s*small exponents after elimination\s*=\s*"
    r"\[\s*([^\]]*?)\s*\]",
    re.S,
)
FAILED_RE = re.compile(
    r"i\s*=\s*(\d+)\s+of\s+(\d+)\s+failed using\s*\[\s*([^\]]*?)\s*\]",
    re.S,
)


def parse_ints(text: str) -> list[int]:
    return sorted({int(token) for token in re.findall(r"\d+", text)})


def parse_transcript(text: str) -> dict[str, dict[str, Any]]:
    matches = list(RUN_RE.finditer(text))
    if not matches:
        raise FrontierError("no TheoremA runs found in transcript")
    out: dict[str, dict[str, Any]] = {}
    for index, match in enumerate(matches):
        key = f"{match.group(1)},{match.group(2)}"
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[start:end]
        persistent_match = PERSISTENT_RE.search(block)
        exceptions_match = EXCEPTIONS_RE.search(block)
        persistent = parse_ints(persistent_match.group(1)) if persistent_match else []
        exceptions = parse_ints(exceptions_match.group(1)) if exceptions_match else []

        small: dict[int, list[int]] = {}
        totals: set[int] = set()
        for form, total, primes in SMALL_RE.findall(block):
            form_id, total_count = int(form), int(total)
            small[form_id] = parse_ints(primes)
            totals.add(total_count)
        failed: set[int] = set()
        for form, total, _primes in FAILED_RE.findall(block):
            failed.add(int(form))
            totals.add(int(total))
        if len(totals) > 1:
            raise FrontierError(f"inconsistent form totals in transcript level {key}")

        if small or failed:
            if not totals:
                raise FrontierError(f"flagged transcript level {key} lacks a total")
            total = next(iter(totals))
            if set(small) | failed != set(range(1, total + 1)):
                raise FrontierError(
                    f"flagged transcript for level {key} does not cover every form"
                )
            survivors = sorted(
                [form for form, primes in small.items() if RESIDUAL_PRIME in primes]
                + list(failed)
            )
            complete = True
        elif persistent_match and exceptions_match:
            complete = RESIDUAL_PRIME not in exceptions
            survivors = persistent if complete else None
        else:
            raise FrontierError(f"could not classify transcript block for level {key}")

        out[key] = {
            "persistent_forms": persistent,
            "exceptional_primes": exceptions,
            "failed_forms": sorted(failed),
            "forms_with_explicit_7": sorted(
                form for form, primes in small.items() if RESIDUAL_PRIME in primes
            ),
            "complete": complete,
            "survivors": survivors,
        }
    return out


def compare_transcript(
    manifest_results: dict[str, list[int] | None],
    transcript_results: dict[str, dict[str, Any]],
) -> None:
    for key, expected in manifest_results.items():
        if key not in transcript_results:
            raise FrontierError(f"transcript is missing level {key}")
        actual = transcript_results[key]["survivors"]
        if expected is not None and actual != expected:
            raise FrontierError(
                f"transcript survivor mismatch at level {key}: "
                f"expected {expected}, got {actual}"
            )
        if expected is None and transcript_results[key]["complete"]:
            raise FrontierError(
                f"manifest marks level {key} incomplete but transcript is complete; "
                "update the frontier manifest"
            )


def self_test(path: pathlib.Path) -> None:
    data = load_json(path)

    mutated = copy.deepcopy(data)
    mutated["levels"][1]["fixed7_survivors"].remove(98)
    try:
        validate_data(mutated)
    except FrontierError:
        pass
    else:
        raise RuntimeError("mutated survivor set was accepted")

    mutated = copy.deepcopy(data)
    mutated["levels"][2]["fixed7_complete"] = True
    try:
        validate_data(mutated)
    except FrontierError:
        pass
    else:
        raise RuntimeError("unsupported completeness claim was accepted")

    synthetic = """
> time TheoremA(9,9,Data:flag := true);
i = 1 of 3, small exponents after elimination = [2, 3]
i = 2 of 3, small exponents after elimination = [2, 7]
i = 3 of 3 failed using [11, 13]
The newforms [3] cannot be discarded using primes in [11,13].
The rest of the newforms can be discarded for p outside [2,3,7].
"""
    parsed = parse_transcript(synthetic)
    if parsed["9,9"]["survivors"] != [2, 3]:
        raise RuntimeError("transcript parser produced an incorrect survivor set")

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
        fixture_path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(fixture_path)
        except FrontierError:
            pass
        else:
            raise RuntimeError("duplicate JSON key was accepted")
    finally:
        fixture_path.unlink(missing_ok=True)

    print("signature (3,5,7) fixed-7 negative fixtures rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        nargs="?",
        type=pathlib.Path,
        default=DEFAULT_MANIFEST,
    )
    parser.add_argument(
        "--transcript",
        type=pathlib.Path,
        help="optional pinned Outputs/TheoremA.txt transcript to replay",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test(args.manifest)
    manifest_results = validate_data(load_json(args.manifest))
    if args.transcript:
        transcript_results = parse_transcript(
            args.transcript.read_text(encoding="utf-8")
        )
        compare_transcript(manifest_results, transcript_results)
        print("fixed-7 transcript agrees with the manifest")
    print(
        "fixed-7 frontier: complete levels (2,2)=3/14 survivors, "
        "(3,2)=9/111 survivors; levels (2,3) and (3,3) need flagged reruns"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
