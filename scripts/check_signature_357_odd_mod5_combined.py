#!/usr/bin/env python3
"""Validate the aggregate combined odd mod-5 residual frontier."""
from __future__ import annotations
import argparse,copy,hashlib,json,pathlib,tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/odd_mod5_combined_residual_frontier.json'
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

def validate(data:dict[str,Any])->tuple[str,list[int]]:
    if data.get('schema_version')!=1 or digest(data)!=data.get('certificate_sha256'):raise CertificateError('schema or digest mismatch')
    if data.get('equation')!='A^3+B^5=C^7':raise CertificateError('equation mismatch')
    rows=data.get('levels')
    if not isinstance(rows,list) or sorted(row.get('level_norm') for row in rows)!=[5103,19683,137781]:raise CertificateError('level list mismatch')
    closed=[];surviving=[]
    for row in rows:
        if row.get('request_status')!='completed':raise CertificateError('an aggregate producer row is incomplete')
        primes=row.get('inert_primes',[])+row.get('split_primes',[]);dims=row.get('dimensions_after_primes')
        previous=row.get('after_removed7_dimension')
        if not isinstance(previous,int) or not isinstance(dims,dict):raise CertificateError('dimension metadata malformed')
        for prime in primes:
            current=dims.get(str(prime))
            if not isinstance(current,int) or current<0 or current>previous:raise CertificateError('dimensions are not monotone')
            previous=current
        if row.get('final_dimension')!=previous:raise CertificateError('final dimension mismatch')
        (closed if previous==0 else surviving).append(row['level_norm'])
    if sorted(closed)!=data.get('closed_levels') or sorted(surviving)!=data.get('surviving_levels'):raise CertificateError('frontier partition mismatch')
    expected='the odd mod-5 residual frontier is empty' if not surviving else 'some combined residual Hecke subspaces remain nonzero'
    if data.get('conclusion')!=expected:raise CertificateError('conclusion mismatch')
    if 'imported research inputs' not in data.get('nonclaim',''):raise CertificateError('trust boundary missing')
    return data['certificate_sha256'],sorted(surviving)

def self_test()->None:
    if not MANIFEST.exists():print('aggregate combined result not present yet');return
    base=load(MANIFEST);validate(base)
    bad=copy.deepcopy(base);bad['closed_levels']=[];bad['certificate_sha256']=digest(bad)
    try:validate(bad)
    except CertificateError:pass
    else:raise RuntimeError('checker accepted a forged closed-level list')
    with tempfile.NamedTemporaryFile('w',delete=False) as f:f.write('{"x":1,"x":2}');path=pathlib.Path(f.name)
    try:
        try:load(path)
        except CertificateError:pass
        else:raise RuntimeError('duplicate keys accepted')
    finally:path.unlink(missing_ok=True)
    print('odd mod-5 combined frontier negative fixtures rejected')

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    certificate,survivors=validate(load(MANIFEST));print('odd mod-5 combined residual frontier valid');print('  surviving levels:',survivors);print('  certificate sha256:',certificate);return 0
if __name__=='__main__':raise SystemExit(main())
