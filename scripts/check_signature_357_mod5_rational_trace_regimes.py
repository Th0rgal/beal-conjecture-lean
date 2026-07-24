#!/usr/bin/env python3
"""Replay rational residual trace regimes from a complete local HGM artifact."""
from __future__ import annotations
import argparse, copy, hashlib, json, pathlib, tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/mod5_rational_trace_regimes.json'
class CertificateError(ValueError): pass

def reject(pairs:list[tuple[str,Any]])->dict[str,Any]:
    out={}
    for key,value in pairs:
        if key in out: raise CertificateError(f'duplicate JSON key: {key}')
        out[key]=value
    return out

def load(path:pathlib.Path)->dict[str,Any]:
    try: value=json.loads(path.read_text(),object_pairs_hook=reject)
    except (OSError,json.JSONDecodeError) as exc: raise CertificateError(str(exc)) from exc
    if not isinstance(value,dict): raise CertificateError('JSON root must be an object')
    return value

def digest(value:dict[str,Any])->str:
    value=copy.deepcopy(value); value.pop('certificate_sha256',None)
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def terms(poly:str)->dict[int,int]:
    compact=poly.replace(' ','').replace('-','+-').removeprefix('+-'); out={}
    for term in compact.split('+'):
        if not term: continue
        if 'x' not in term: degree,coefficient=0,int(term)
        else:
            before,after=term.split('x',1); before=before.removesuffix('*')
            coefficient=-1 if before=='-' else (1 if before=='' else int(before))
            degree=int(after[1:]) if after.startswith('^') else 1
        out[degree]=out.get(degree,0)+coefficient
    return out

def evaluate(poly:str,value:int)->int:
    return sum(c*pow(value,d,5) for d,c in terms(poly).items())%5

def rows(producer:dict[str,Any],prime:int,regime:str)->list[str]:
    return [r['trace_polynomial'] for r in producer[f'{regime}_rows'] if r['prime']==prime]

def validate(manifest:dict[str,Any],producer:dict[str,Any])->str:
    if manifest.get('schema_version')!=1 or digest(manifest)!=manifest.get('certificate_sha256'):
        raise CertificateError('manifest schema or digest mismatch')
    source=manifest['source']
    if digest(producer)!=producer.get('certificate_sha256') or producer.get('certificate_sha256')!=source['producer_output_sha256'] or producer.get('primes')!=source['primes']:
        raise CertificateError('producer identity mismatch')
    for prime in source['primes']:
        expected=manifest['primes'][str(prime)]
        ratio=producer['residue_metadata'][str(prime)]['extension_residue_degree']
        if ratio!=expected['extension_residue_degree'] or ratio not in {1,2}:
            raise CertificateError(f'residue-degree mismatch at {prime}')
        for regime in ('generic','zero','infinity'):
            polynomials=rows(producer,prime,regime)
            full=sorted(v for v in range(5) if any(evaluate(poly,v)==0 for poly in polynomials))
            base=full if ratio==1 else sorted(v for v in range(5) if (v*v-2*prime)%5 in full)
            record=expected['regimes'][regime]
            if len(polynomials)!=record['candidate_count'] or full!=record['full_trace_roots_mod5'] or base!=record['base_trace_roots_mod5']:
                raise CertificateError(f'{prime}/{regime} root-set mismatch')
        multiplicative=sorted({(prime+1)%5,(-(prime+1))%5})
        if multiplicative!=expected['regimes']['multiplicative']['base_trace_roots_mod5']:
            raise CertificateError(f'{prime}/multiplicative mismatch')
    if manifest['primes']['29']['regimes']['generic']['base_trace_roots_mod5']:
        raise CertificateError('generic rational trace survives at 29')
    if manifest['primes']['43']['regimes']['generic']['base_trace_roots_mod5'] or manifest['primes']['43']['regimes']['infinity']['base_trace_roots_mod5']:
        raise CertificateError('forbidden rational regime survives at 43')
    return manifest['certificate_sha256']

def expect_rejection(manifest,producer,label):
    manifest['certificate_sha256']=digest(manifest)
    try: validate(manifest,producer)
    except CertificateError: return
    raise RuntimeError(f'checker accepted {label}')

def self_test(producer:dict[str,Any])->None:
    manifest=load(MANIFEST); validate(manifest,producer)
    bad_producer=copy.deepcopy(producer); bad_producer['unhashed_edit']=True
    try: validate(manifest,bad_producer)
    except CertificateError: pass
    else: raise RuntimeError('checker accepted producer data not bound to its digest')
    bad=copy.deepcopy(manifest); bad['primes']['29']['regimes']['generic']['base_trace_roots_mod5']=[0]
    expect_rejection(bad,producer,'a generic rational trace at 29')
    bad=copy.deepcopy(manifest); bad['primes']['43']['regimes']['infinity']['base_trace_roots_mod5']=[3]
    expect_rejection(bad,producer,'an infinity rational trace at 43')
    with tempfile.NamedTemporaryFile('w',delete=False) as fixture:
        fixture.write('{"x":1,"x":2}'); path=pathlib.Path(fixture.name)
    try:
        try: load(path)
        except CertificateError: pass
        else: raise RuntimeError('duplicate keys accepted')
    finally: path.unlink(missing_ok=True)
    print('mod-5 rational trace regime negative fixtures rejected')

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument('--producer',type=pathlib.Path,required=True); parser.add_argument('--self-test',action='store_true'); args=parser.parse_args()
    producer=load(args.producer)
    if args.self_test: self_test(producer); return 0
    value=validate(load(MANIFEST),producer)
    print('mod-5 rational Hecke trace regimes valid')
    print('  prime 29: generic rational trace impossible')
    print('  prime 43: generic and infinity rational traces impossible')
    print(f'  certificate sha256: {value}')
    return 0
if __name__=='__main__': raise SystemExit(main())
