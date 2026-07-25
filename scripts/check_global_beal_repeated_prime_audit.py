#!/usr/bin/env python3
"""Replay the finite group theory in the repeated-prime decomposition-group audit."""
from __future__ import annotations
import argparse,copy,hashlib,json,math
from pathlib import Path
from typing import Any
CERT=Path(__file__).resolve().parents[1]/'Research'/'GlobalBeal'/'repeated_prime_decomposition_group_audit.json'
class CheckError(RuntimeError):pass

def digest(v:dict[str,Any])->str:
 b=dict(v);b.pop('certificate_sha256',None)
 return hashlib.sha256(json.dumps(b,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def prime(n:int)->bool:
 if n<2:return False
 if n%2==0:return n==2
 d=3
 while d*d<=n:
  if n%d==0:return False
  d+=2
 return True

def order(a:int,p:int)->int:
 if math.gcd(a,p)!=1:raise ValueError('unit required')
 x=1
 for n in range(1,p):
  x=x*a%p
  if x==1:return n
 raise CheckError('order not found')

def intersection_trivial(p:int,q:int,r:int)->bool:
 m=order(r%p,p);n=order(r%q,q);L=math.lcm(m,n)
 # D=< (a,b)>; H is the second factor. A nonidentity intersection element
 # is a k with a^k=1 and b^k!=1.
 for k in range(1,L):
  if pow(r,k,p)==1 and pow(r,k,q)!=1:return False
 return True

def verify(v:dict[str,Any],bound:int=100)->None:
 if v.get('schema_version')!=1:raise CheckError('schema')
 if v.get('certificate_sha256')!=digest(v):raise CheckError('digest')
 if v.get('correct_group_theorem',{}).get('equivalence') != 'D_r intersect H_prime is trivial iff ord_q(r) divides ord_p(r)':
  raise CheckError('group-theorem statement mismatch')
 ex=v['invalid_inference']['explicit_counterexample']
 p,q,r=ex['p'],ex['q'],ex['r']
 if not intersection_trivial(p,q,r):raise CheckError('counterexample intersection')
 if r%q==1:raise CheckError('counterexample projection accidentally trivial')
 if order(r,p)!=ex['ord_p_r'] or order(r,q)!=ex['ord_q_r']:raise CheckError('counterexample orders')
 ps=[x for x in range(3,bound+1,2) if prime(x)]
 rs=[x for x in range(2,bound+1) if prime(x)]
 for p in ps:
  for q in ps:
   if p==q:continue
   for r in rs:
    if r in (p,q):continue
    lhs=intersection_trivial(p,q,r)
    rhs=order(r,p)%order(r,q)==0
    if lhs!=rhs:raise CheckError(f'equivalence failed p={p},q={q},r={r}')
 # If n|m, then n|gcd(p-1,q-1), hence q|2^g-1 for r=2.
 for p in ps:
  for q in ps:
   if p==q or p==2 or q==2:continue
   if order(2,p)%order(2,q)==0:
    g=math.gcd(p-1,q-1)
    if pow(2,g,q)!=1:raise CheckError(f'Mersenne consequence p={p},q={q}')
   if math.gcd(p-1,q-1)==2 and q>3 and order(2,p)%order(2,q)==0:
    raise CheckError('gcd-2 pair unexpectedly survived the order condition')
 s=v['conditional_repeated_exponent_sieve']['surviving_example']
 if order(2,s['p'])!=s['ord_p_2'] or order(2,s['q'])!=s['ord_q_2']:raise CheckError('survivor orders')
 if pow(2,s['gcd_p_minus_1_q_minus_1'],s['q'])!=1:raise CheckError('survivor Mersenne')

def self_test(v:dict[str,Any])->None:
 verify(v,80)
 b=copy.deepcopy(v);b['correct_group_theorem']['equivalence']='intersection trivial iff r=1 mod q';b['certificate_sha256']=digest(b)
 try:verify(b,30)
 except CheckError:return
 raise CheckError('negative fixture accepted')

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--certificate',type=Path,default=CERT);ap.add_argument('--self-test',action='store_true');ap.add_argument('--bound',type=int,default=100);a=ap.parse_args();v=json.loads(a.certificate.read_text())
 if a.self_test:self_test(v)
 else:verify(v,a.bound)
 print(json.dumps({'status':'ok','certificate_sha256':v['certificate_sha256'],'bound':80 if a.self_test else a.bound,'self_test':a.self_test},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
