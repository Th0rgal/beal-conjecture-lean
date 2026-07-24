#!/usr/bin/env python3
"""Validate the expanded exact two-Frey graph frontier."""
from __future__ import annotations
import argparse,copy,hashlib,json,pathlib,tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/odd_e3_2_expanded_joint_graph.json'
PRIMES=[11,13,17,19,23,29,31,41,43,59,61,71]
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

def validate(data:dict[str,Any])->tuple[str,list[list[int]]]:
    if data.get('schema_version')!=1 or digest(data)!=data.get('certificate_sha256'):raise CertificateError('schema or digest mismatch')
    if data.get('status')!='complete':raise CertificateError('expanded graph run is incomplete')
    if data.get('level_pairs')!={'mod5':[2,1],'fixed7':[2,3]} or data.get('mod5_packet')!=1 or data.get('fixed7_packets')!=[24,28]:raise CertificateError('modular-pair metadata mismatch')
    primes=data.get('primes');records=data.get('records')
    if primes!=PRIMES or not isinstance(records,list) or len(records)!=len(PRIMES):raise CertificateError('prime schedule mismatch')
    seen=[];compatibility={24:True,28:True}
    for record in records:
        if record.get('request_status')!='completed':raise CertificateError('a prime request is incomplete')
        prime=record.get('prime');seen.append(prime);rows=record.get('pairs')
        if not isinstance(rows,list) or sorted(row.get('packet') for row in rows)!=[24,28]:raise CertificateError('packet rows are incomplete')
        for row in rows:
            expected=bool(row.get('generic_parameter_count')) or bool(row.get('zero_zero')) or bool(row.get('multiplicative_infinity')) or bool(row.get('infinity_multiplicative'))
            if expected!=row.get('compatible'):raise CertificateError('pair compatibility does not replay')
            compatibility[row['packet']]=compatibility[row['packet']] and expected
    if seen!=primes or len(set(primes))!=len(primes):raise CertificateError('prime schedule mismatch')
    survivors=[[1,packet] for packet in (24,28) if compatibility[packet]]
    if survivors!=data.get('surviving_modular_pairs'):raise CertificateError('surviving-pair list mismatch')
    expected='the odd e3=2 modular-pair frontier is empty' if not survivors else 'some modular pairs survive every tested prime'
    if data.get('conclusion')!=expected:raise CertificateError('conclusion mismatch')
    if 'imported research inputs' not in data.get('nonclaim',''):raise CertificateError('trust boundary missing')
    return data['certificate_sha256'],survivors

def self_test()->None:
    with tempfile.NamedTemporaryFile('w',delete=False) as f:f.write('{"x":1,"x":2}');path=pathlib.Path(f.name)
    try:
        try:load(path)
        except CertificateError:pass
        else:raise RuntimeError('duplicate keys accepted')
    finally:path.unlink(missing_ok=True)
    if not MANIFEST.exists():
        print('expanded graph result absent; manifest-dependent fixtures skipped')
        print('duplicate-key fixture rejected')
        return
    base=load(MANIFEST);validate(base)
    bad=copy.deepcopy(base);bad['records'][0]['pairs'][0]['compatible']=not bad['records'][0]['pairs'][0]['compatible'];bad['certificate_sha256']=digest(bad)
    try:validate(bad)
    except CertificateError:pass
    else:raise RuntimeError('checker accepted a forged compatibility flag')
    bad=copy.deepcopy(base);bad['primes']=bad['primes'][:1];bad['records']=bad['records'][:1];bad['certificate_sha256']=digest(bad)
    try:validate(bad)
    except CertificateError:pass
    else:raise RuntimeError('checker accepted a truncated prime schedule')
    print('expanded two-Frey graph negative fixtures rejected')

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    if not MANIFEST.exists():
        print('expanded two-Frey graph unresolved: no verified result artifact is present')
        print('  nonclaim: no modular pair is eliminated by this optional replay')
        return 0
    certificate,survivors=validate(load(MANIFEST));print('expanded two-Frey graph valid');print('  surviving modular pairs:',survivors);print('  certificate sha256:',certificate);return 0
if __name__=='__main__':raise SystemExit(main())
