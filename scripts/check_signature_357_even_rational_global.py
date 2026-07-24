#!/usr/bin/env python3
"""Compose the global ray and rational two-Frey even-branch certificates."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, pathlib, tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/even_rational_global_divisibility.json'
class CertificateError(ValueError):pass

def reject(pairs:list[tuple[str,Any]])->dict[str,Any]:
    out={}
    for k,v in pairs:
        if k in out:raise CertificateError(f'duplicate JSON key: {k}')
        out[k]=v
    return out
def load(path:pathlib.Path)->dict[str,Any]:
    try:value=json.loads(path.read_text(),object_pairs_hook=reject)
    except (OSError,json.JSONDecodeError) as exc:raise CertificateError(str(exc)) from exc
    if not isinstance(value,dict):raise CertificateError('JSON root must be an object')
    return value
def digest(value:dict[str,Any])->str:
    value=copy.deepcopy(value);value.pop('certificate_sha256',None)
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def validate(data:dict[str,Any])->str:
    if data.get('schema_version')!=1 or digest(data)!=data.get('certificate_sha256'):raise CertificateError('schema or digest mismatch')
    inputs=data['inputs'];global_ray=load(ROOT/inputs['global_fixed7_path']);rational=load(ROOT/inputs['rational_two_frey_path'])
    if digest(global_ray)!=global_ray.get('certificate_sha256') or global_ray['certificate_sha256']!=inputs['global_fixed7_sha256']:raise CertificateError('global ray input mismatch')
    if digest(rational)!=rational.get('certificate_sha256') or rational['certificate_sha256']!=inputs['rational_two_frey_sha256']:raise CertificateError('rational two-Frey input mismatch')
    if global_ray['conclusion']['forced_divisibility']!='19*71 divides C' or rational['conclusion']['forced_divisibility']!='13*29 divides C':raise CertificateError('input divisibilities changed')
    primes=data['prime_factors_for_C']
    if primes!=[2,3,5,13,19,29,71] or math.prod(primes)!=data['forced_divisor_of_C'] or data['forced_divisor_of_C']!=15257190:raise CertificateError('composed divisor mismatch')
    if data['additional_conclusions']!=['the fixed-7 reducibility character is psi_(2,0)','41 does not divide B']:raise CertificateError('additional conclusions changed')
    return data['certificate_sha256']
def expect_rejection(data,label):
    data['certificate_sha256']=digest(data)
    try:validate(data)
    except CertificateError:return
    raise RuntimeError(f'checker accepted {label}')
def self_test():
    data=load(MANIFEST);validate(data)
    bad=copy.deepcopy(data);bad['prime_factors_for_C'].remove(71);bad['forced_divisor_of_C']//=71;expect_rejection(bad,'a weakened divisor')
    with tempfile.NamedTemporaryFile('w',delete=False) as f:f.write('{"x":1,"x":2}');path=pathlib.Path(f.name)
    try:
        try:load(path)
        except CertificateError:pass
        else:raise RuntimeError('duplicate keys accepted')
    finally:path.unlink(missing_ok=True)
    print('even rational global divisibility negative fixtures rejected')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    value=validate(load(MANIFEST));print('even rational global divisibility certificate valid');print('  15,257,190 divides C');print('  41 does not divide B');print(f'  certificate sha256: {value}');return 0
if __name__=='__main__':raise SystemExit(main())
