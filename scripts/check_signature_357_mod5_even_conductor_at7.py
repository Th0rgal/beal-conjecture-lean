#!/usr/bin/env python3
"""Replay the even-branch mod-5 conductor bookkeeping at the prime above 7.

The finite checker validates the Beal-to-paper orientation and the branch
arithmetic q∤b*c.  The exact Table 3.5 conductor rows remain an explicit
literature input.  In particular, exponent 1 is not available in the even
branch; the only possibilities are 2 and 3.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import tempfile
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'Research' / 'Signature357' / 'mod5_even_conductor_at7.json'


class CertificateError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CertificateError(f'duplicate JSON key: {key}')
        out[key] = value
    return out


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=reject_duplicate_keys)
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificateError(str(exc)) from exc
    if not isinstance(value, dict):
        raise CertificateError('manifest root must be an object')
    return value


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(f'{context} keys differ: expected {sorted(expected)}, got {sorted(value)}')


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop('certificate_sha256', None)
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate(data: dict[str, Any]) -> str:
    exact_keys(data, {
        'schema_version','status','equation','orientation','branch','table_3_5_input',
        'complete_lmfdb_effect','nonclaim','certificate_sha256'
    }, 'manifest')
    if data['schema_version'] != 1:
        raise CertificateError('schema_version must equal 1')
    if data['status'] != 'literature-assisted-even-branch-conductor-at-7-correction':
        raise CertificateError('unexpected status')
    if data['equation'] != 'A^3+B^5=C^7':
        raise CertificateError('unexpected equation')

    orientation = data['orientation']
    if orientation != {
        'paper_equation':'a^7+b^5+c^3=0',
        'paper_variables':['a=-C','b=B','c=A','q=7','p=5','r=3'],
        'parameter':'u=C^7/A^3',
    }:
        raise CertificateError('paper orientation mismatch')

    branch = data['branch']
    if branch != {
        'name':'Dahmen--Siksek even branch',
        'conditions':['30 divides C','7 does not divide A*B','gcd(A,B,C)=1'],
        'paper_consequence':'q does not divide b*c',
    }:
        raise CertificateError('even-branch metadata mismatch')
    # In the orientation b=B,c=A,q=7, the branch hypothesis 7∤A*B is exactly q∤b*c.
    if orientation['paper_variables'][1:3] != ['b=B','c=A']:
        raise CertificateError('q∤b*c was attached to the wrong variables')

    table = data['table_3_5_input']
    exact_keys(table, {
        'source','condition','reducible_degree_q_polynomial_exponent',
        'irreducible_degree_q_polynomial_exponent','possible_exponents','excluded_exponent'
    }, 'table_3_5_input')
    if 'Table 3.5' not in table['source'] or table['condition'] != 'q does not divide b*c':
        raise CertificateError('Table 3.5 source/condition mismatch')
    if table['reducible_degree_q_polynomial_exponent'] != 2:
        raise CertificateError('reducible-polynomial exponent must be 2')
    if table['irreducible_degree_q_polynomial_exponent'] != 3:
        raise CertificateError('irreducible-polynomial exponent must be 3')
    if table['possible_exponents'] != [2,3] or table['excluded_exponent'] != 1:
        raise CertificateError('even-branch exponent set must be exactly {2,3}')

    effect = data['complete_lmfdb_effect']
    exact_keys(effect, {
        'packet_excluded_by_conductor','excluded_packet_exponent_pair',
        'packet_remaining_before_existing_local_type_filter','remaining_packet_exponent_pair',
        'existing_local_type_certificate','conclusion'
    }, 'complete_lmfdb_effect')
    if effect['packet_excluded_by_conductor'] != '3.3.49.1-189.1-a':
        raise CertificateError('unexpected conductor-excluded packet')
    if effect['excluded_packet_exponent_pair'] != [1,1]:
        raise CertificateError('packet 189.1-a must have exponent pair (1,1)')
    if effect['excluded_packet_exponent_pair'][1] in table['possible_exponents']:
        raise CertificateError('the supposedly excluded packet has an allowed e7')
    if effect['packet_remaining_before_existing_local_type_filter'] != '3.3.49.1-1323.1-a':
        raise CertificateError('unexpected remaining packet')
    if effect['remaining_packet_exponent_pair'] != [1,2]:
        raise CertificateError('packet 1323.1-a must have exponent pair (1,2)')
    if effect['remaining_packet_exponent_pair'][1] not in table['possible_exponents']:
        raise CertificateError('the remaining packet does not have an allowed e7')
    if effect['existing_local_type_certificate'] != 'Research/Signature357/mod5_even_7unit_local_type.json':
        raise CertificateError('existing local-type subcertificate path mismatch')
    if effect['conclusion'] != 'the complete LMFDB low-level even branch is empty after the existing local-type filter':
        raise CertificateError('low-level conclusion mismatch')
    if 'literature inputs' not in data['nonclaim'] or 'does not' not in data['nonclaim']:
        raise CertificateError('trust-boundary nonclaim missing')

    digest = canonical_sha256(data)
    if digest != data['certificate_sha256']:
        raise CertificateError(f"certificate digest mismatch: expected {data['certificate_sha256']}, got {digest}")
    return digest


def expect_rejection(data: dict[str, Any], description: str) -> None:
    try:
        validate(data)
    except CertificateError:
        return
    raise RuntimeError(f'checker accepted {description}')


def self_test() -> None:
    source = load_json(DEFAULT_MANIFEST)
    validate(source)

    mutated = copy.deepcopy(source)
    mutated['table_3_5_input']['possible_exponents'] = [1,2,3]
    mutated['certificate_sha256'] = canonical_sha256(mutated)
    expect_rejection(mutated, 'an obsolete exponent-1 branch')

    mutated = copy.deepcopy(source)
    mutated['orientation']['paper_variables'][1] = 'b=-C'
    mutated['certificate_sha256'] = canonical_sha256(mutated)
    expect_rejection(mutated, 'the wrong variable orientation')

    mutated = copy.deepcopy(source)
    mutated['complete_lmfdb_effect']['packet_excluded_by_conductor'] = '3.3.49.1-1323.1-a'
    mutated['certificate_sha256'] = canonical_sha256(mutated)
    expect_rejection(mutated, 'elimination of the wrong packet')

    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fixture:
        fixture.write('{"schema_version":1,"schema_version":1}')
        path = pathlib.Path(fixture.name)
    try:
        try:
            load_json(path)
        except CertificateError:
            pass
        else:
            raise RuntimeError('checker accepted duplicate JSON keys')
    finally:
        path.unlink(missing_ok=True)
    print('signature-357 even conductor-at-7 negative fixtures rejected')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=pathlib.Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    digest = validate(load_json(args.manifest))
    print('signature-357 even-branch conductor-at-7 correction valid')
    print('  q does not divide b*c, so e7 is 2 or 3; e7=1 is excluded')
    print('  packet 189.1-a is removed by conductor support')
    print(f'  certificate sha256: {digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
