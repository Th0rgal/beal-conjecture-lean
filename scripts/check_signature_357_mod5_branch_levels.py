#!/usr/bin/env python3
"""Validate the branch-specific eleven-level mod-5 automorphic frontier."""
from __future__ import annotations
import argparse, copy, hashlib, json, pathlib, tempfile
from typing import Any
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'Research'/'Signature357'/'mod5_branch_level_frontier.json'
class CertificateError(ValueError): pass

def reject_duplicate_keys(pairs:list[tuple[str,Any]])->dict[str,Any]:
 out={}
 for k,v in pairs:
  if k in out: raise CertificateError(f'duplicate JSON key: {k}')
  out[k]=v
 return out

def load_json(path:pathlib.Path)->dict[str,Any]:
 try: value=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=reject_duplicate_keys)
 except (OSError,json.JSONDecodeError) as exc: raise CertificateError(str(exc)) from exc
 if not isinstance(value,dict): raise CertificateError('manifest root must be an object')
 return value

def digest(data:dict[str,Any])->str:
 x=copy.deepcopy(data);x.pop('certificate_sha256',None)
 return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def validate(data:dict[str,Any])->str:
 expected={'schema_version','status','equation','field','source_dependencies','branches','levels','summary','nonclaim','certificate_sha256'}
 if set(data)!=expected: raise CertificateError('manifest keys differ')
 if data['schema_version']!=1 or data['status']!='literature-assisted-branch-valid-mod5-level-frontier': raise CertificateError('schema/status mismatch')
 if data['equation']!='A^3+B^5=C^7': raise CertificateError('equation mismatch')
 if data['field']!={'name':'K7=Q(zeta_7)^+','prime_norms':{'p3':27,'p7':7}}: raise CertificateError('field metadata mismatch')
 branches=data['branches']
 if set(branches)!={'even','odd'}: raise CertificateError('branch keys differ')
 even=branches['even']; odd=branches['odd']
 if even['possible_e3']!=[0,1,2] or even['possible_e7']!=[2,3]: raise CertificateError('even exponent ranges differ')
 if odd['possible_e3']!=[2,3] or odd['possible_e7']!=[0,1,2]: raise CertificateError('odd exponent ranges differ')
 even_pairs={(a,b) for a in even['possible_e3'] for b in even['possible_e7']}
 odd_pairs={(a,b) for a in odd['possible_e3'] for b in odd['possible_e7']}
 union=sorted(even_pairs|odd_pairs)
 levels=data['levels']
 if not isinstance(levels,list) or len(levels)!=len(union): raise CertificateError('level count differs')
 actual=[]
 for row,pair in zip(levels,union):
  if set(row)!={'exponent_pair','level_norm','branches'}: raise CertificateError('level row keys differ')
  if row['exponent_pair']!=list(pair): raise CertificateError('level order differs')
  norm=27**pair[0]*7**pair[1]
  if row['level_norm']!=norm: raise CertificateError('level norm mismatch')
  names=sorted(name for name,values in [('even',even_pairs),('odd',odd_pairs)] if pair in values)
  if row['branches']!=names: raise CertificateError('level branch membership mismatch')
  actual.append(norm)
 summary=data['summary']
 if summary['level_count']!=11 or len(union)!=11: raise CertificateError('frontier must contain eleven levels')
 if summary['level_norms']!=sorted(actual): raise CertificateError('level norm summary differs')
 if summary['maximum_level_norm']!=964467 or max(actual)!=964467: raise CertificateError('maximum norm differs')
 if summary['previous_global_level_count']!=16 or summary['previous_global_maximum_norm']!=6751269: raise CertificateError('previous frontier metadata differs')
 if summary['older_coarse_level_count']!=24 or summary['older_coarse_maximum_norm']!=4921675101: raise CertificateError('older coarse frontier differs')
 if '(0,2)' not in summary['unproved_nine_level_refinement'] or '(0,3)' not in summary['unproved_nine_level_refinement']: raise CertificateError('conservative refinement warning missing')
 if 'literature inputs' not in data['nonclaim'] or 'does not' not in data['nonclaim']: raise CertificateError('nonclaim missing')
 d=digest(data)
 if d!=data['certificate_sha256']: raise CertificateError(f'digest mismatch: {d}')
 return d

def reject(data,desc):
 try: validate(data)
 except CertificateError:return
 raise RuntimeError(f'accepted {desc}')

def self_test():
 x=load_json(DEFAULT);validate(x)
 y=copy.deepcopy(x);y['branches']['even']['possible_e3']=[1,2];y['certificate_sha256']=digest(y);reject(y,'unsupported nine-level refinement')
 y=copy.deepcopy(x);y['levels'][0]['level_norm']+=1;y['certificate_sha256']=digest(y);reject(y,'wrong level norm')
 y=copy.deepcopy(x);y['summary']['maximum_level_norm']=6751269;y['certificate_sha256']=digest(y);reject(y,'obsolete maximum')
 with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:f.write('{"schema_version":1,"schema_version":1}');p=pathlib.Path(f.name)
 try:
  try:load_json(p)
  except CertificateError:pass
  else:raise RuntimeError('accepted duplicate keys')
 finally:p.unlink(missing_ok=True)
 print('signature-357 branch-level frontier negative fixtures rejected')

def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=pathlib.Path,default=DEFAULT);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 if a.self_test:self_test();return 0
 d=validate(load_json(a.manifest));print('signature-357 branch-valid mod-5 level frontier valid');print('  11 levels; maximum norm 964467');print(f'  certificate sha256: {d}');return 0
if __name__=='__main__':raise SystemExit(main())
