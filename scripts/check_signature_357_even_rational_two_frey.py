#!/usr/bin/env python3
"""Replay the even-branch rational two-Frey sieve at 13, 29 and 41."""
from __future__ import annotations
import argparse, copy, hashlib, json, pathlib, tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/even_rational_two_frey_sieve.json'
MOD5=ROOT/'Research/Signature357/mod5_rational_trace_regimes.json'
RAY=ROOT/'Research/Signature357/fixed7_ray_character_control.json'
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

def evaluate(poly:str,value:int,modulus:int=7)->int:
    return sum(c*pow(value,d,modulus) for d,c in terms(poly).items())%modulus

def validate(data:dict[str,Any],mod5:dict[str,Any],ray:dict[str,Any])->str:
    if data.get('schema_version')!=1 or digest(data)!=data.get('certificate_sha256'):
        raise CertificateError('manifest schema or digest mismatch')
    sources=data['sources']
    if digest(mod5)!=mod5.get('certificate_sha256') or mod5['certificate_sha256']!=sources['mod5_trace_regimes_sha256']:
        raise CertificateError('mod-5 trace certificate mismatch')
    if digest(ray)!=ray.get('certificate_sha256') or ray['certificate_sha256']!=sources['fixed7_ray_sha256']:
        raise CertificateError('ray-character certificate mismatch')
    if data['parameters']['identity']!='u+t7=1': raise CertificateError('parameter identity mismatch')
    u_to_t={'generic':'generic','zero':'multiplicative','infinity':'infinity','multiplicative':'zero'}
    computed={}; forced_traces={}
    for prime in (13,29,41):
        entry=data['primes'][str(prime)]; norm=entry['fixed7_norm_mod7']
        base=sorted({(norm*psi+psi)%7 for psi in (1,-1)})
        full=sorted({(value*value-2*norm)%7 for value in base})
        if base!=entry['fixed7_base_targets_mod7'] or full!=entry['fixed7_full_targets_mod7']:
            raise CertificateError(f'fixed-7 target mismatch at {prime}')
        fixed=entry['fixed7_regimes']
        for regime in ('generic','zero','infinity'):
            targets=base if regime=='generic' else full
            matches={str(value):[p for p in fixed[regime]['candidate_polynomials'] if evaluate(p,value)==0] for value in targets}
            if matches!=fixed[regime]['compatible_targets']:
                raise CertificateError(f'fixed-7 polynomial replay mismatch at {prime}/{regime}')
        allowed=[]; trace_union=set()
        for ureg,treg in u_to_t.items():
            roots=mod5['primes'][str(prime)]['regimes'][ureg]['base_trace_roots_mod5']
            compatible=True if treg=='multiplicative' else any(fixed[treg]['compatible_targets'][str(v)] for v in fixed[treg]['target_traces_mod7'])
            expected=entry['coupled_u_regimes'][ureg]
            if roots!=expected['mod5_rational_trace_roots'] or treg!=expected['fixed7_regime'] or compatible!=expected['fixed7_compatible']:
                raise CertificateError(f'coupled regime mismatch at {prime}/{ureg}')
            if roots and compatible:
                allowed.append(ureg); trace_union.update(roots)
        if allowed!=entry['allowed_u_regimes']:
            raise CertificateError(f'allowed regime mismatch at {prime}')
        computed[str(prime)]=allowed; forced_traces[str(prime)]=sorted(trace_union)
    conclusion=data['conclusion']
    if computed!=conclusion['allowed_u_regimes'] or forced_traces!=conclusion['forced_residual_traces']:
        raise CertificateError('conclusion does not replay')
    if conclusion['forced_divisibility']!='13*29 divides C' or conclusion['excluded_divisibility']!='41 does not divide B':
        raise CertificateError('divisibility conclusion mismatch')
    return data['certificate_sha256']

def expect_rejection(data,mod5,ray,label):
    data['certificate_sha256']=digest(data)
    try: validate(data,mod5,ray)
    except CertificateError: return
    raise RuntimeError(f'checker accepted {label}')

def self_test()->None:
    data,mod5,ray=load(MANIFEST),load(MOD5),load(RAY); validate(data,mod5,ray)
    bad=copy.deepcopy(data); bad['primes']['13']['allowed_u_regimes'].append('generic')
    expect_rejection(bad,mod5,ray,'a generic prime-13 branch')
    bad=copy.deepcopy(data); bad['conclusion']['forced_divisibility']='13 divides C'
    expect_rejection(bad,mod5,ray,'the weakened divisibility conclusion')
    with tempfile.NamedTemporaryFile('w',delete=False) as f: f.write('{"x":1,"x":2}'); path=pathlib.Path(f.name)
    try:
        try: load(path)
        except CertificateError: pass
        else: raise RuntimeError('duplicate keys accepted')
    finally: path.unlink(missing_ok=True)
    print('even rational two-Frey negative fixtures rejected')

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument('--self-test',action='store_true'); args=parser.parse_args()
    if args.self_test: self_test(); return 0
    value=validate(load(MANIFEST),load(MOD5),load(RAY))
    print('even-branch rational two-Frey sieve valid')
    print('  13 and 29 divide C')
    print('  41 does not divide B')
    print(f'  certificate sha256: {value}')
    return 0
if __name__=='__main__': raise SystemExit(main())
