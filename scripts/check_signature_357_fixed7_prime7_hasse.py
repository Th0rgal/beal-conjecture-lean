#!/usr/bin/env python3
"""Replay the finite Hasse-Witt part of the fixed-7 residual-prime obstruction."""
from __future__ import annotations
import argparse, copy, hashlib, json, pathlib, tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/fixed7_prime7_hasse_obstruction.json'
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

def trim(a:list[int])->list[int]:
    while len(a)>1 and a[-1]%7==0:a.pop()
    return [v%7 for v in a]
def add(a,b):
    return trim([((a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0))%7 for i in range(max(len(a),len(b)))])
def sub(a,b):return add(a,[(-v)%7 for v in b])
def mul(a,b):
    out=[0]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]=(out[i+j]+x*y)%7
    return trim(out)
def power(a,n):
    result=[1]
    while n:
        if n&1:result=mul(result,a)
        a=mul(a,a);n//=2
    return result
def derivative(a):return trim([(i*a[i])%7 for i in range(1,len(a))] or [0])
def inverse(v):return pow(v,-1,7)
def divmod_poly(a,b):
    a=trim(a[:]);b=trim(b[:])
    if b==[0]:raise ZeroDivisionError
    q=[0]*max(1,len(a)-len(b)+1)
    while a!=[0] and len(a)>=len(b):
        degree=len(a)-len(b);coefficient=a[-1]*inverse(b[-1])%7;q[degree]=coefficient
        term=[0]*degree+[coefficient];a=sub(a,mul(term,b))
    return trim(q),trim(a)
def gcd_poly(a,b):
    a,b=trim(a),trim(b)
    while b!=[0]:_,r=divmod_poly(a,b);a,b=b,r
    if a==[0]:return a
    inv=inverse(a[-1]);return trim([(inv*v)%7 for v in a])

def validate(data:dict[str,Any])->str:
    if data.get('schema_version')!=1 or digest(data)!=data.get('certificate_sha256'):raise CertificateError('schema or digest mismatch')
    source=load(ROOT/data['reducible_character']['source_path'])
    if digest(source)!=source.get('certificate_sha256') or source['certificate_sha256']!=data['reducible_character']['source_sha256']:raise CertificateError('global ray input mismatch')
    if source['conclusion']['unique_reducibility_character']!='psi_(2,0)':raise CertificateError('unique character changed')
    behavior=data['reducible_character']['prime7_behavior']
    if data['reducible_character']['norm_d']%7!=behavior['norm_d_mod7'] or pow(behavior['norm_d_mod7'],3,7)!=6 or behavior['psi_Frobenius_value']!=-1:raise CertificateError('quadratic character at 7 mismatch')
    unit=data['unit_case'];scalars={}
    for t in unit['parameter_classes_mod7']:
        f=[t*t%7,0,0,10*t%7,0,-12%7,5]
        if gcd_poly(f,derivative(f))!=[1]:raise CertificateError(f'singular unit model at t={t}')
        cube=power(f,3);coeff=lambda i:cube[i] if i<len(cube) else 0
        expected=[(-pow(t,4,7))%7,0,0,t]
        if [coeff(5),coeff(6),coeff(12),coeff(13)]!=expected:raise CertificateError(f'Hasse-Witt coefficients mismatch at t={t}')
        determinant=t*pow(t,4,7)%7
        if determinant==0:raise CertificateError('unit case is not ordinary')
        scalars[str(t)]=(-pow(t,5,7))%7
    if scalars!=unit['q_frobenius_scalars_mod7']:raise CertificateError('iterated Hasse-Witt scalars mismatch')
    if any(pow(t,5,7)==1 for t in unit['parameter_classes_mod7']):raise CertificateError('a forbidden unit class has fifth power one')
    if unit['parameter_classes_mod7']!=[2,3,4,5,6] or data['scope']['conclusion']!='7 divides C':raise CertificateError('scope conclusion mismatch')
    if len(data['imported_implications'])!=3 or 'imported literature inputs' not in data['nonclaim']:raise CertificateError('trust boundary missing')
    return data['certificate_sha256']

def expect_rejection(data,label):
    data['certificate_sha256']=digest(data)
    try:validate(data)
    except CertificateError:return
    raise RuntimeError(f'checker accepted {label}')
def self_test():
    data=load(MANIFEST);validate(data)
    bad=copy.deepcopy(data);bad['unit_case']['q_frobenius_scalars_mod7']['2']=1;expect_rejection(bad,'a mutated Hasse-Witt scalar')
    bad=copy.deepcopy(data);bad['reducible_character']['prime7_behavior']['psi_Frobenius_value']=1;expect_rejection(bad,'the wrong ray-character value at 7')
    with tempfile.NamedTemporaryFile('w',delete=False) as f:f.write('{"x":1,"x":2}');path=pathlib.Path(f.name)
    try:
        try:load(path)
        except CertificateError:pass
        else:raise RuntimeError('duplicate keys accepted')
    finally:path.unlink(missing_ok=True)
    print('fixed-7 prime-7 Hasse negative fixtures rejected')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    value=validate(load(MANIFEST));print('fixed-7 residual-prime Hasse certificate valid');print('  reducibility and 7 not dividing A*B force 7 to divide C');print(f'  certificate sha256: {value}');return 0
if __name__=='__main__':raise SystemExit(main())
