#!/usr/bin/env python3
"""Replay the complete LMFDB low-level mod-5 filter for signature (3,5,7).

The checker uses numeric HMF-label ordering, validates the complete degree-three
inventory through level norm 2059, composes the global non-CM certificate, the
corrected even-branch conductor-at-7 certificate, and the existing local-type
certificate.  The complete low-level range is empty in both Dahmen--Siksek
branches.  Levels above the documented completeness bound remain open.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import tempfile
from typing import Any

import check_signature_357_mod5_even_7unit as even7
import check_signature_357_mod5_even_conductor_at7 as even_conductor
import check_signature_357_mod5_noncm as noncm

ROOT = pathlib.Path(__file__).resolve().parents[1]
INVENTORY = ROOT / 'Research' / 'Signature357' / 'lmfdb_low_levels.json'
FILTER = ROOT / 'Research' / 'Signature357' / 'lmfdb_low_level_filter.json'
EXPECTED_LEVELS = [1,7,27,49,189,343,729,1323]
LABEL_RE = re.compile(r'^3\.3\.49\.1-(\d+)\.1-([a-z]+)$')


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
        raise CertificateError(f'{path} root must be an object')
    return value


def exact_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    if set(value) != expected:
        raise CertificateError(f'{context} keys differ: expected {sorted(expected)}, got {sorted(value)}')


def canonical_sha256(data: dict[str, Any]) -> str:
    payload = copy.deepcopy(data)
    payload.pop('certificate_sha256', None)
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def packet_key(label: str) -> tuple[int, str]:
    match = LABEL_RE.fullmatch(label)
    if match is None:
        raise CertificateError(f'malformed HMF label: {label!r}')
    return int(match.group(1)), match.group(2)


def packet_sorted(labels: Any, context: str) -> list[str]:
    if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels):
        raise CertificateError(f'{context} must be a list of labels')
    if len(labels) != len(set(labels)):
        raise CertificateError(f'{context} contains duplicates')
    return sorted(labels, key=packet_key)


def polynomial_constant(polynomial: str) -> int:
    if polynomial == 'x':
        return 0
    compact = polynomial.replace(' ', '')
    match = re.search(r'([+-]?\d+)$', compact)
    if match is None:
        raise CertificateError(f'cannot parse polynomial constant: {polynomial!r}')
    return int(match.group(1))


def has_prime_above_five_with_zero_trace(record: dict[str, Any]) -> bool:
    value = record['hecke_eigenvalue_norm8']
    if type(value) is int:
        return value % 5 == 0
    if value == 'e':
        return polynomial_constant(record['hecke_polynomial']) % 5 == 0
    raise CertificateError(f"unsupported norm-8 eigenvalue for {record.get('label')}: {value!r}")


def validate_inventory(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    exact_keys(data, {
        'candidate_levels_within_bound','certificate_sha256','level_count','levels',
        'prime_ordering','schema_version','source','status',
        'total_coefficient_field_dimension','total_record_count'
    }, 'inventory')
    if data['schema_version'] != 2 or canonical_sha256(data) != data['certificate_sha256']:
        raise CertificateError('inventory schema or digest mismatch')
    if data['candidate_levels_within_bound'] != EXPECTED_LEVELS or data['level_count'] != 8:
        raise CertificateError('complete-range level list mismatch')
    if data['total_record_count'] != 14 or data['total_coefficient_field_dimension'] != 26:
        raise CertificateError('inventory aggregate mismatch')
    if data['prime_ordering'] != {'norm8_index_zero_based':1,'norm8_prime':'[8, 2, 2]'}:
        raise CertificateError('norm-8 prime ordering mismatch')

    records: dict[str, dict[str, Any]] = {}
    total_records = total_dimension = 0
    for expected_norm, level in zip(EXPECTED_LEVELS, data['levels']):
        exact_keys(level, {'exponent_pair','level_norm','record_count','records','total_coefficient_field_dimension'}, f'level {expected_norm}')
        if level['level_norm'] != expected_norm:
            raise CertificateError('level order mismatch')
        pair = level['exponent_pair']
        if not isinstance(pair,list) or len(pair)!=2 or any(type(x) is not int for x in pair):
            raise CertificateError('invalid exponent pair')
        if 27**pair[0] * 7**pair[1] != expected_norm:
            raise CertificateError('level norm does not match exponent pair')
        if level['record_count'] != len(level['records']):
            raise CertificateError('level record count mismatch')
        local_dimension = 0
        for record in level['records']:
            exact_keys(record, {
                'dimension','hecke_eigenvalue_norm8','hecke_polynomial','is_CM',
                'is_base_change','label','level_ideal','level_norm','parallel_weight'
            }, 'packet record')
            label = record['label']; packet_key(label)
            if label in records or record['level_norm'] != expected_norm or record['parallel_weight'] != 2:
                raise CertificateError(f'packet metadata mismatch for {label}')
            if record['is_CM'] not in {'yes','no'} or record['is_base_change'] not in {'yes','no'}:
                raise CertificateError(f'packet flags malformed for {label}')
            if type(record['dimension']) is not int or record['dimension'] < 1:
                raise CertificateError(f'packet dimension malformed for {label}')
            records[label] = dict(record, exponent_pair=list(pair))
            local_dimension += record['dimension']
        if local_dimension != level['total_coefficient_field_dimension']:
            raise CertificateError('level coefficient-field dimension mismatch')
        total_records += len(level['records']); total_dimension += local_dimension
    if total_records != 14 or total_dimension != 26 or len(records) != 14:
        raise CertificateError('replayed inventory totals differ')
    return records


def validate_filter(manifest: dict[str, Any], inventory: dict[str, Any], records: dict[str, dict[str, Any]]) -> tuple[list[str],list[str],list[str]]:
    exact_keys(manifest, {
        'schema_version','status','scope','residual_filter','global_noncm_filter',
        'even_conductor_at7_filter','even_7unit_local_type_filter','branch_filters',
        'source_dependencies','certificate_sha256'
    }, 'filter')
    if manifest['schema_version'] != 4 or manifest['status'] != 'literature-assisted-complete-LMFDB-low-level-filter':
        raise CertificateError('filter schema/status mismatch')
    if canonical_sha256(manifest) != manifest['certificate_sha256']:
        raise CertificateError('filter digest mismatch')
    scope = manifest['scope']
    if scope['inventory_sha256'] != inventory['certificate_sha256'] or scope['candidate_level_norms'] != EXPECTED_LEVELS:
        raise CertificateError('filter is not bound to the inventory')

    try:
        noncm_digest = noncm.validate(noncm.load_json(ROOT / scope['global_noncm_path']))
        conductor_digest = even_conductor.validate(even_conductor.load_json(ROOT / scope['even_conductor_at7_path']))
        even7_digest = even7.validate(even7.load_json(ROOT / scope['even_7unit_local_type_path']))
    except (noncm.CertificateError, even_conductor.CertificateError, even7.CertificateError) as exc:
        raise CertificateError(f'subcertificate failed: {exc}') from exc
    if noncm_digest != scope['global_noncm_sha256']:
        raise CertificateError('global non-CM digest binding mismatch')
    if conductor_digest != scope['even_conductor_at7_sha256']:
        raise CertificateError('even conductor digest binding mismatch')
    if even7_digest != scope['even_7unit_local_type_sha256']:
        raise CertificateError('even local-type digest binding mismatch')

    residual = packet_sorted([label for label,record in records.items() if has_prime_above_five_with_zero_trace(record)], 'computed residual survivors')
    residual_manifest = manifest['residual_filter']
    if residual != packet_sorted(residual_manifest['survivors'], 'residual survivors') or residual_manifest['survivors'] != residual:
        raise CertificateError(f'residual survivors differ: {residual}')
    if residual_manifest['prime_norm'] != 8 or residual_manifest['required_hecke_eigenvalue_mod5'] != 0 or residual_manifest['total_packets'] != 14 or residual_manifest['survivor_count'] != 4:
        raise CertificateError('residual summary mismatch')
    if not all(records[label]['hecke_polynomial']=='x' and records[label]['is_base_change']=='yes' for label in residual):
        raise CertificateError('residual survivor is not rational base change')

    noncm_survivors = packet_sorted([label for label in residual if records[label]['is_CM']=='no'], 'non-CM survivors')
    removed_cm = packet_sorted(list(set(residual)-set(noncm_survivors)), 'removed CM')
    noncm_manifest = manifest['global_noncm_filter']
    if removed_cm != noncm_manifest['cm_packets_removed'] or noncm_survivors != noncm_manifest['survivors'] or noncm_manifest['count'] != 2:
        raise CertificateError('global non-CM filter mismatch')

    conductor_manifest = manifest['even_conductor_at7_filter']
    allowed_e7 = conductor_manifest['allowed_e7']
    post_conductor = packet_sorted([label for label in noncm_survivors if records[label]['exponent_pair'][1] in allowed_e7], 'post-conductor survivors')
    removed_by_conductor = packet_sorted(list(set(noncm_survivors)-set(post_conductor)), 'conductor removed')
    if allowed_e7 != [2,3] or removed_by_conductor != [conductor_manifest['packet_removed']] or conductor_manifest['packet_removed'] != '3.3.49.1-189.1-a':
        raise CertificateError('even conductor filter mismatch')
    if records[conductor_manifest['packet_removed']]['exponent_pair'] != conductor_manifest['removed_packet_exponent_pair'] or conductor_manifest['removed_packet_exponent_pair'] != [1,1]:
        raise CertificateError('conductor-removed packet exponent mismatch')
    if post_conductor != conductor_manifest['survivors'] or conductor_manifest['count'] != 1:
        raise CertificateError('post-conductor survivor mismatch')

    local_manifest = manifest['even_7unit_local_type_filter']
    if local_manifest['packet_removed'] not in post_conductor or local_manifest['packet_removed'] != '3.3.49.1-1323.1-a':
        raise CertificateError('local-type packet mismatch')
    final_even = packet_sorted(list(set(post_conductor)-{local_manifest['packet_removed']}), 'final even')
    if final_even != local_manifest['survivors'] or final_even != [] or local_manifest['count'] != 0:
        raise CertificateError('local-type final set mismatch')

    branches = manifest['branch_filters']
    odd_pre = packet_sorted([label for label in residual if records[label]['exponent_pair'][0] in {2,3}], 'odd pre-nonCM')
    odd_final = packet_sorted([label for label in noncm_survivors if records[label]['exponent_pair'][0] in {2,3}], 'odd final')
    if odd_pre != branches['odd_branch']['pre_noncm_survivors'] or odd_final != [] or branches['odd_branch']['low_level_survivors'] != []:
        raise CertificateError('odd branch closure mismatch')
    even_pre = packet_sorted(noncm_survivors, 'even pre-conductor')
    if even_pre != branches['even_branch']['pre_conductor_survivors'] or post_conductor != branches['even_branch']['post_conductor_survivors'] or final_even != branches['even_branch']['low_level_survivors']:
        raise CertificateError('even branch closure mismatch')
    if branches['all_branches']['low_level_survivors'] != [] or branches['all_branches']['count'] != 0:
        raise CertificateError('global complete-range closure mismatch')
    return residual, noncm_survivors, final_even


def validate() -> tuple[list[str],list[str],list[str]]:
    inventory = load_json(INVENTORY)
    records = validate_inventory(inventory)
    return validate_filter(load_json(FILTER), inventory, records)


def expect_rejection(manifest: dict[str, Any], inventory: dict[str, Any], records: dict[str,dict[str,Any]], description: str) -> None:
    try:
        validate_filter(manifest, inventory, records)
    except CertificateError:
        return
    raise RuntimeError(f'checker accepted {description}')


def self_test() -> None:
    inventory = load_json(INVENTORY); records = validate_inventory(inventory); manifest = load_json(FILTER)
    validate_filter(manifest, inventory, records)

    mutated = copy.deepcopy(manifest)
    mutated['residual_filter']['survivors'] = sorted(mutated['residual_filter']['survivors'])
    mutated['certificate_sha256'] = canonical_sha256(mutated)
    expect_rejection(mutated, inventory, records, 'lexicographic rather than numeric label ordering')

    mutated = copy.deepcopy(manifest)
    mutated['even_conductor_at7_filter']['allowed_e7'] = [1,2,3]
    mutated['certificate_sha256'] = canonical_sha256(mutated)
    expect_rejection(mutated, inventory, records, 'the obsolete exponent-1 even branch')

    mutated = copy.deepcopy(manifest)
    mutated['branch_filters']['all_branches']['low_level_survivors'] = ['3.3.49.1-189.1-a']
    mutated['branch_filters']['all_branches']['count'] = 1
    mutated['certificate_sha256'] = canonical_sha256(mutated)
    expect_rejection(mutated, inventory, records, 'a false nonempty complete-range frontier')

    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fixture:
        fixture.write('{"schema_version":4,"schema_version":4}')
        path = pathlib.Path(fixture.name)
    try:
        try: load_json(path)
        except CertificateError: pass
        else: raise RuntimeError('checker accepted duplicate JSON keys')
    finally:
        path.unlink(missing_ok=True)
    print('signature-357 low-level filter negative fixtures passed')


def main() -> int:
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test: self_test(); return 0
    residual, noncm_survivors, final_even = validate()
    print('LMFDB-complete levels: 8')
    print(f'packets: 14 -> {len(residual)} after a_P=0 mod 5')
    print(f'after global non-CM: {len(noncm_survivors)}')
    print('odd branch low-level frontier: empty')
    print('even branch low-level frontier: empty')
    print('complete degree-three range through norm 2059: empty')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
