#!/usr/bin/env python3
"""Replay the odd-branch modulo-9 synchronization of the two Frey systems."""
from __future__ import annotations
import argparse,copy,hashlib,json,math,pathlib,tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1];DEFAULT=ROOT/'Research'/'Signature357'/'odd_e3_synchronization.json'
class CertificateError(ValueError):pass

def reject_duplicate_keys(pairs:list[tuple[str,Any]])->dict[str,Any]:
 out={}
 for k,v in pairs:
  if k in out:raise CertificateError(f'duplicate JSON key: {k}')
  out[k]=v
 return out

def load_json(p:pathlib.Path)->dict[str,Any]:
 try:v=json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=reject_duplicate_keys)
 except (OSError,json.JSONDecodeError) as e:raise CertificateError(str(e)) from e
 if not isinstance(v,dict):raise CertificateError('root must be object')
 return v

def sha(d):
 x=copy.deepcopy(d);x.pop('certificate_sha256',None);return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def enumerate_pairs()->tuple[int,list[list[int]]]:
 units=[x for x in range(9) if math.gcd(x,9)==1];count=0;pairs=set()
 for A in units:
  inv=pow(pow(A,3,9),-1,9)
  for B in units:
   for C in units:
    if (pow(A,3,9)+pow(B,5,9)-pow(C,7,9))%9:continue
    count+=1;u=pow(C,7,9)*inv%9;v=-pow(B,5,9)*inv%9;pairs.add((u,v%9))
 return count,[list(x) for x in sorted(pairs)]

def validate(d):
 keys={'schema_version','status','equation','branch','parameters','modulus','unit_solution_count','parameter_pairs','local_conductor_map','conclusion','blocks','source_dependency','nonclaim','certificate_sha256'}
 if set(d)!=keys:raise CertificateError('keys differ')
 if d['schema_version']!=1 or d['status']!='finite-arithmetic-with-imported-local-conductor-table':raise CertificateError('schema/status mismatch')
 if d['parameters']!={'mod5':'u=C^7/A^3','fixed7':'v=-B^5/A^3','identity':'u+v=1'}:raise CertificateError('parameter metadata mismatch')
 count,pairs=enumerate_pairs()
 if count!=18 or d['unit_solution_count']!=count:raise CertificateError('unit solution count mismatch')
 if pairs!=[[2,8],[5,5],[8,2]] or d['parameter_pairs']!=pairs:raise CertificateError('parameter pairs mismatch')
 if any((u+v)%9!=1 for u,v in pairs):raise CertificateError('u+v=1 failed')
 mapping=d['local_conductor_map']
 if mapping!={'2':3,'5':2,'8':3}:raise CertificateError('conductor map mismatch')
 if any(mapping[str(u)]!=mapping[str(v)] for u,v in pairs):raise CertificateError('e3 synchronization failed')
 if d['conclusion']!='e3(mod5)=e3(fixed7) for every odd-branch unit residue class':raise CertificateError('conclusion mismatch')
 if d['blocks']['e3=2']['parameter_pair']!=[5,5] or d['blocks']['e3=3']['parameter_pairs']!=[[2,8],[8,2]]:raise CertificateError('block partition mismatch')
 if 'imported' not in d['nonclaim'] or 'does not' not in d['nonclaim']:raise CertificateError('nonclaim missing')
 h=sha(d)
 if h!=d['certificate_sha256']:raise CertificateError(f'digest mismatch: {h}')
 return h

def reject(d,desc):
 try:validate(d)
 except CertificateError:return
 raise RuntimeError(f'accepted {desc}')

def self_test():
 x=load_json(DEFAULT);validate(x)
 y=copy.deepcopy(x);y['parameter_pairs']=[[2,8],[5,5]];y['certificate_sha256']=sha(y);reject(y,'incomplete pair set')
 y=copy.deepcopy(x);y['local_conductor_map']['8']=2;y['certificate_sha256']=sha(y);reject(y,'false conductor map')
 with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:f.write('{"schema_version":1,"schema_version":1}');p=pathlib.Path(f.name)
 try:
  try:load_json(p)
  except CertificateError:pass
  else:raise RuntimeError('accepted duplicate keys')
 finally:p.unlink(missing_ok=True)
 print('signature-357 odd e3 synchronization negative fixtures rejected')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=pathlib.Path,default=DEFAULT);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 if a.self_test:self_test();return 0
 h=validate(load_json(a.manifest));print('signature-357 odd e3 synchronization certificate valid');print('  (u,v) mod 9 = (2,8),(5,5),(8,2)');print(f'  certificate sha256: {h}');return 0
if __name__=='__main__':raise SystemExit(main())
