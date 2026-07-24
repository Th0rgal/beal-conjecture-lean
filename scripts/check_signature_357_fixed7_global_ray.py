#!/usr/bin/env python3
"""Replay the global ray-character sieve for a reducible fixed-7 representation."""
from __future__ import annotations
import argparse, copy, hashlib, json, math, pathlib, tempfile
from typing import Any
import check_signature_357_fixed7_ray_characters as base
ROOT=pathlib.Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'Research/Signature357/fixed7_global_reducibility_sieve.json'
RAY=ROOT/'Research/Signature357/fixed7_ray_character_control.json'
EXTRA=ROOT/'Research/Signature357/fixed7_forced_c_candidates.json'
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

def polys(text:str)->list[str]: return [piece.strip() for piece in text.split(',') if piece.strip()]
CANDIDATES={
11:(1,polys('x+5,x-2,x^2-5,x^2+4*x-1,x^2+3*x+1,x^2-x-1,x^2+x-11,x^2+2*x-19,x^2+5*x-5'),polys('x^2-4*x-316,x^2+x-101,x^2-19*x-61,x^2-19*x+59,x^2+41*x+419'),polys('x+22')),
13:(2,polys('x-7,x+14,x-10,x+15,x-20,x+10,x,x+3,x+8,x+10,x-11'),polys('x+338'),polys('x-338,x+169')),
17:(2,polys('x+31,x+10,x+17,x+7,x+15,x+2,x-20,x+6,x+11,x-23,x-18,x+20,x-28,x+20,x-20'),polys('x+578'),polys('x+382')),
19:(1,polys('x^2+7*x+1,x^2+4*x-16,x^2+11*x+29,x^2+6*x+4,x^2-6*x-11,x^2+7*x+11,x^2+9*x+9,x^2-4*x-1,x^2-2*x-4,x^2-x-1,x^2+2*x-19,x^2+9*x+19,x^2-5*x-25,x^2+4*x-1,x^2+3*x+1,x-5,x^2+2*x-19'),polys('x+38'),polys('x+22,x^2-22*x-599')),
71:(1,polys('x^2-9*x-131,x^2+25*x+155,x^2-11*x+19,x^2+13*x+31,x^2+6*x+4,x^2+3*x-99,x^2-8*x+11,x^2+10*x-100,x^2-8*x-29,x^2-14*x+29,x^2+20*x+95,x^2-15*x+55,x-6,x-2,x^2-245,x^2+5*x-5,x^2-26*x+164,x^2+7*x-49,x^2+9*x-81,x^2-45,x^2+15*x+25,x^2+6*x-71,x+1,x^2+16*x+59,x^2-x-61,x^2-6*x-11,x-4,x^2-12*x+31,x^2+15*x+25,x^2-5*x-5,x^2-4*x-41,x^2+10*x-55,x^2-4*x-1,x^2-20*x+95,x+7,x^2-18*x+76,x^2+11*x-1,x^2+3*x-29,x+11,x+7,x^2-x-31,x^2-8*x-4,x^2-7*x+1,x-1,x^2+3*x+1,x^2+4*x-76,x+4,x^2+6*x-36,x^2-14*x+44,x^2-2*x-4,x^2-9*x-81,x^2+18*x+76,x^2+15*x+45,x^2-x-11,x^2+19*x+59,x^2+6*x+4,x^2+13*x-19,x^2+25*x+145,x^2-5*x-95,x^2+15*x+45,x^2-18*x+76,x^2-80,x^2-10*x+5,x^2+2*x-179,x^2+24*x+139,x^2+4*x-121,x^2+7*x+1,x^2-3*x-29,x^2+10*x-55'),polys('x^2-59*x-11381,x^2+41*x-10861,x^2-19*x-61,x^2-199*x+8699,x^2+236*x+13604'),polys('x+142'))}

def extend_candidates(extra:dict[str,Any])->None:
    if extra.get('schema_version')!=1 or digest(extra)!=extra.get('certificate_sha256'):
        raise CertificateError('extra candidate fixture schema or digest mismatch')
    if extra.get('primes')!=[79,89,131]:
        raise CertificateError('extra candidate prime list mismatch')
    source=extra.get('source',{})
    if source.get('git_blob_sha1')!='9c96357834f2298b4d91ab97812c38e84b8ef7a2':
        raise CertificateError('extra candidate source blob mismatch')
    degrees={79:1,89:1,131:1}
    for prime in extra['primes']:
        record=extra['records'].get(str(prime))
        if not isinstance(record,dict) or set(record)!={'generic','zero','infinity'}:
            raise CertificateError(f'extra candidate record mismatch at {prime}')
        CANDIDATES[prime]=(degrees[prime],record['generic'],record['zero'],record['infinity'])

def certificate(prime:int,psi:base.F49)->list[list[int]]:
    degree,generic,zero,infinity=CANDIDATES[prime]; norm=base.F49(prime**degree); z=norm*psi+psi.inverse(); w=z*z-2*norm
    values=[base.product_at(generic,z),base.product_at(zero,w),base.product_at(infinity,w),(z-(norm+1))*(z+(norm+1))]
    return [value.pair() for value in values]

def mul(left:tuple[int,int],right:tuple[int,int],modulus:int)->tuple[int,int]:
    a,b=left;c,d=right; return ((a*c+b*d)%modulus,(a*d+b*c+b*d)%modulus)
def dlog(value,generator,modulus,order):
    current=(1,0); target=(value[0]%modulus,value[1]%modulus)
    for exponent in range(order):
        if current==target:return exponent
        current=mul(current,generator,modulus)
    raise CertificateError('ray discrete log failed')
def ray_coordinate(a:int,b:int)->list[int]:
    r=dlog((a,b),(0,1),3,8); residue=(a+3*b)%5; s=next(e for e in range(4) if pow(3,e,5)==residue)
    root=math.sqrt(5); e1=int(a+b*(1+root)/2<0); e2=int(a+b*(1-root)/2<0)
    return [(3*r+s+2*e1)%4,(r+e1+e2)%2]
def f49_power(value:base.F49,exponent:int)->base.F49:
    result=base.F49(1); factor=value
    while exponent:
        if exponent&1: result=result*factor
        factor=factor*factor; exponent//=2
    return result
def character(a:int,b:int,coordinate:list[int])->base.F49:
    return f49_power(base.I,a*coordinate[0])*((-1)**(b*coordinate[1]))
def nonsquare(value:int,prime:int)->bool: return pow(value%prime,(prime-1)//2,prime)==prime-1

def validate(data:dict[str,Any],ray:dict[str,Any],extra:dict[str,Any])->str:
    extend_candidates(extra)
    if data.get('schema_version')!=2 or digest(data)!=data.get('certificate_sha256'): raise CertificateError('schema or digest mismatch')
    if digest(ray)!=ray.get('certificate_sha256') or ray['certificate_sha256']!=data['source']['ray_control_sha256']: raise CertificateError('base ray certificate mismatch')
    generators={'11a':(3,1),'11b':(3,2),'13':(13,0),'17':(17,0),'19a':(4,1),'19b':(4,3),'71a':(8,1),'71b':(8,7)}
    for label,generator in generators.items():
        if ray_coordinate(*generator)!=data['ray_coordinates'][label]['coordinate']: raise CertificateError(f'ray coordinate mismatch at {label}')
    tests={'17_i':(17,base.I),'17_minus_i':(17,-base.I),'19_plus':(19,base.F49(1)),'19_minus':(19,base.F49(-1)),'11_plus':(11,base.F49(1)),'71_minus':(71,base.F49(-1)),'79_minus':(79,base.F49(-1)),'89_plus':(89,base.F49(1)),'131_minus':(131,base.F49(-1)),'13_minus':(13,base.F49(-1))}
    for label,(prime,psi) in tests.items():
        if certificate(prime,psi)!=data['candidate_products_mod7'][label]['products_G_0_inf_1']: raise CertificateError(f'candidate product mismatch at {label}')
    split=data['nodal_splitting_character']
    if split['norm']!=45: raise CertificateError('nodal norm mismatch')
    nonsquare_sets=((11,split['prime11_residues_nonsquare']),(19,split['prime19_residues_nonsquare']),(79,split['prime79_residues_nonsquare']),(131,split['prime131_residues_nonsquare']))
    if not all(nonsquare(v,p) for p,values in nonsquare_sets for v in values): raise CertificateError('nodal nonsquare-class mismatch')
    if not all(not nonsquare(v,89) for v in split['prime89_residues_square']): raise CertificateError('nodal square-class mismatch at 89')
    candidates=[(a,b) for a in range(4) for b in range(2)]
    candidates=[pair for pair in candidates if pair[0]%2==0]
    if candidates!=[(0,0),(0,1),(2,0),(2,1)]: raise CertificateError('prime-17 character reduction failed')
    coord19=data['ray_coordinates']['19a']['coordinate']; candidates=[pair for pair in candidates if character(*pair,coord19)==base.F49(-1)]
    if candidates!=[(2,0),(2,1)]: raise CertificateError('prime-19 sign did not force a=2')
    coords11=[data['ray_coordinates']['11a']['coordinate'],data['ray_coordinates']['11b']['coordinate']]
    candidates=[pair for pair in candidates if all(character(*pair,c)==base.F49(-1) for c in coords11)]
    if candidates!=[(2,0)]: raise CertificateError('prime-11 sign did not force b=0')
    conclusion=data['conclusion']
    if conclusion['unique_reducibility_character']!='psi_(2,0)' or conclusion['forced_divisibility']!='19*71*79*89*131 divides C' or conclusion['forced_divisor']!=19*71*79*89*131 or conclusion['additional_divisibility']!='13 divides A*C': raise CertificateError('global conclusion mismatch')
    for label in ('71_minus','79_minus','89_plus','131_minus'):
        if data['candidate_products_mod7'][label]['products_G_0_inf_1'][3]!=[0,0] or any(value==[0,0] for value in data['candidate_products_mod7'][label]['products_G_0_inf_1'][:3]):
            raise CertificateError(f'{label} does not force t7=1')
    return data['certificate_sha256']

def expect_rejection(data,ray,extra,label):
    data['certificate_sha256']=digest(data)
    try: validate(data,ray,extra)
    except CertificateError:return
    raise RuntimeError(f'checker accepted {label}')
def self_test():
    data,ray,extra=load(MANIFEST),load(RAY),load(EXTRA);validate(data,ray,extra)
    bad=copy.deepcopy(data);bad['ray_coordinates']['19a']['coordinate']=[3,0];expect_rejection(bad,ray,extra,'a mutated ray coordinate')
    bad=copy.deepcopy(data);bad['nodal_splitting_character']['prime11_residues_nonsquare'][0]=1;expect_rejection(bad,ray,extra,'a square nodal residue')
    bad=copy.deepcopy(data);bad['conclusion']['forced_divisor']=19*71;expect_rejection(bad,ray,extra,'a weakened forced divisor')
    with tempfile.NamedTemporaryFile('w',delete=False) as f:f.write('{"x":1,"x":2}');path=pathlib.Path(f.name)
    try:
        try:load(path)
        except CertificateError:pass
        else:raise RuntimeError('duplicate keys accepted')
    finally:path.unlink(missing_ok=True)
    print('global fixed-7 ray sieve negative fixtures rejected')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return 0
    value=validate(load(MANIFEST),load(RAY),load(EXTRA));print('global fixed-7 reducibility sieve valid');print('  unique ray character: psi_(2,0)');print('  19*71*79*89*131 divides C and 13 divides A*C');print(f'  certificate sha256: {value}');return 0
if __name__=='__main__':raise SystemExit(main())
