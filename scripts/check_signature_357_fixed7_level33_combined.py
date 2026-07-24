#!/usr/bin/env python3
"""Validate the combined fixed-7 level-(3,3) residual manifest."""
from __future__ import annotations
import argparse,copy,hashlib,json,pathlib,tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/fixed7_level33_combined_residual.json'
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
    if not isinstance(value,dict):raise CertificateError('root must be an object')
    return value

def digest(value:dict[str,Any])->str:
    value=copy.deepcopy(value);value.pop('certificate_sha256',None)
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def validate(data:dict[str,Any])->tuple[str,int]:
    if data.get('schema_version')!=1 or digest(data)!=data.get('certificate_sha256'):raise CertificateError('schema or digest mismatch')
    if data.get('level_exponents')!=[3,3] or data.get('level_norm')!=91125:raise CertificateError('level mismatch')
    if data.get('request_status')!='completed':raise CertificateError('producer request is incomplete')
    primes=data.get('auxiliary_primes');dims=data.get('dimensions_after_primes')
    if primes!=[13,43,11,29,41] or not isinstance(dims,dict):raise CertificateError('prime schedule mismatch')
    previous=data.get('superspecial_dimension')
    if not isinstance(previous,int) or previous<0:raise CertificateError('bad superspecial dimension')
    for prime in primes:
        current=dims.get(str(prime))
        if not isinstance(current,int) or current<0 or current>previous:raise CertificateError('residual dimensions are not monotone')
        previous=current
    if data.get('final_dimension')!=previous:raise CertificateError('final dimension mismatch')
    if 'positive dimension is only necessary' not in data.get('soundness',''):raise CertificateError('soundness boundary missing')
    return data['certificate_sha256'],previous

def self_test()->None:
    if not MANIFEST.exists():print('combined result not present yet');return
    base=load(MANIFEST);validate(base)
    bad=copy.deepcopy(base);bad['final_dimension']=bad['final_dimension']+1;bad['certificate_sha256']=digest(bad)
    try:validate(bad)
    except CertificateError:pass
    else:raise RuntimeError('checker accepted a forged final dimension')
    with tempfile.NamedTemporaryFile('w',delete=False) as f:f.write('{"x":1,"x":2}');path=pathlib.Path(f.name)
    try:
        try:load(path)
        except CertificateError:pass
        else:raise RuntimeError('duplicate keys accepted')
    finally:path.unlink(missing_ok=True)
    print('fixed-7 combined level33 negative fixtures rejected')

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    certificate,dimension=validate(load(MANIFEST));print('fixed-7 level33 combined residual result valid');print('  final dimension:',dimension);print('  certificate sha256:',certificate);return 0
if __name__=='__main__':raise SystemExit(main())
