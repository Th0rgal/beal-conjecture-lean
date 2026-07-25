#!/usr/bin/env python3
"""Replay the ray-character-robust low-level (3,5,7) closure."""
from __future__ import annotations
import argparse, copy, hashlib, json, pathlib, tempfile
from typing import Any
import check_signature_357_fixed7_ray_characters as ray
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/low_level_complete_closure.json'
LOW=ROOT/'Research/Signature357/lmfdb_low_level_filter.json'
class CertificateError(ValueError): pass

def reject(pairs:list[tuple[str,Any]])->dict[str,Any]:
    out={}
    for k,v in pairs:
        if k in out: raise CertificateError(f'duplicate JSON key: {k}')
        out[k]=v
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
    poly=poly.replace(' ','').replace('-','+-').removeprefix('+-'); out={}
    for term in poly.split('+'):
        if not term: continue
        if 'x' not in term: degree,coef=0,int(term)
        else:
            before,after=term.split('x',1); before=before.removesuffix('*')
            coef=-1 if before=='-' else (1 if before=='' else int(before))
            degree=int(after[1:]) if after.startswith('^') else 1
        out[degree]=out.get(degree,0)+coef
    return out

def evaluate(poly:str,value:int,modulus:int)->int:
    return sum(c*pow(value,d,modulus) for d,c in terms(poly).items())%modulus

def product(values:list[int],modulus:int)->int:
    out=1
    for value in values: out=out*value%modulus
    return out

def validate(manifest:dict[str,Any],low:dict[str,Any])->str:
    if manifest.get('schema_version')!=3 or digest(manifest)!=manifest.get('certificate_sha256'):
        raise CertificateError('closure schema or digest mismatch')
    scope=manifest['scope']
    if digest(low)!=low.get('certificate_sha256') or low['certificate_sha256']!=scope['low_level_filter_sha256']:
        raise CertificateError('low-level filter digest mismatch')
    branches=low['branch_filters']
    if branches['odd_branch']['low_level_survivors'] or branches['even_branch_7_unit']['low_level_survivors']:
        raise CertificateError('a previously closed branch reopened')
    if branches['even_branch_7_divides_C']['low_level_survivors']!=[scope['only_preclosure_packet']]:
        raise CertificateError('preclosure packet changed')
    try: ray_digest=ray.validate(ray.load(ROOT/scope['fixed7_ray_character_path']))
    except ray.CertificateError as exc: raise CertificateError(f'ray certificate failed: {exc}') from exc
    if ray_digest!=scope['fixed7_ray_character_sha256']: raise CertificateError('ray digest mismatch')
    mod5=manifest['mod5_prime41_filter']; prime=mod5['rational_prime']
    full=mod5['packet_trace_base']**2-2*prime
    if full!=mod5['packet_trace_full'] or full%5!=mod5['packet_trace_full_mod5']:
        raise CertificateError('mod-5 trace transformation mismatch')
    for name,count in [('generic',39),('zero',7),('infinity',3)]:
        polys=mod5[f'{name}_candidate_polynomials']; vals=[evaluate(p,full,5) for p in polys]
        if len(polys)!=count or 0 in vals or product(vals,5)!=mod5[f'{name}_evaluation_product_mod5']:
            raise CertificateError(f'{name} mod-5 regime survives')
    targets=sorted({(prime+1)%5,(-(prime+1))%5})
    if targets!=mod5['multiplicative_targets_mod5'] or mod5['packet_trace_base']%5 not in targets or mod5['only_surviving_reduction_regime']!='u=1':
        raise CertificateError('multiplicative regime mismatch')
    fixed=manifest['fixed7_prime41_obstruction']; ray41=ray.load(ROOT/scope['fixed7_ray_character_path'])['quadratic_trace_at41']
    if fixed['ray_character_control_sha256']!=ray_digest: raise CertificateError('fixed-7 target is not ray-bound')
    target=ray41['full_trace_mod7_for_both_values']
    if fixed['reducible_trace_base_mod7']!=ray41['base_trace_mod7_for_both_values'] or fixed['reducible_trace_full_mod7']!=target:
        raise CertificateError('ray-aware target mismatch')
    vals=[evaluate(p,target,7) for p in fixed['zero_candidate_polynomials']]
    if vals!=fixed['evaluations_mod7'] or 0 in vals or product(vals,7)!=fixed['evaluation_product_mod7']:
        raise CertificateError('fixed-7 t=0 obstruction mismatch')
    if len(manifest['imported_implications'])!=5: raise CertificateError('imported implication count changed')
    return manifest['certificate_sha256']

def reject_mutation(manifest,low,label):
    manifest['certificate_sha256']=digest(manifest)
    try: validate(manifest,low)
    except CertificateError: return
    raise RuntimeError(f'checker accepted {label}')

def self_test()->None:
    manifest,low=load(MANIFEST),load(LOW); validate(manifest,low)
    bad=copy.deepcopy(manifest); bad['fixed7_prime41_obstruction']['ray_character_control_sha256']='0'*64
    reject_mutation(bad,low,'an unbound trivial-character target')
    bad=copy.deepcopy(manifest); bad['mod5_prime41_filter']['generic_candidate_polynomials'][0]='x-2'
    reject_mutation(bad,low,'an extra generic regime')
    with tempfile.NamedTemporaryFile('w',delete=False) as f: f.write('{"x":1,"x":2}'); path=pathlib.Path(f.name)
    try:
        try: load(path)
        except CertificateError: pass
        else: raise RuntimeError('duplicate keys accepted')
    finally: path.unlink(missing_ok=True)
    print('ray-character-robust low-level closure negative fixtures passed')

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument('--self-test',action='store_true'); args=parser.parse_args()
    if args.self_test: self_test(); return 0
    value=validate(load(MANIFEST),load(LOW))
    print('complete LMFDB low-level mod-5 frontier is empty')
    print('prime 17 removes order-4 ray twists; both quadratic twists give target 2 at 41')
    print(f'certificate sha256: {value}')
    return 0
if __name__=='__main__': raise SystemExit(main())
