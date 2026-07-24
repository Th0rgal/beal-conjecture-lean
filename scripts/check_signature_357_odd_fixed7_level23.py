#!/usr/bin/env python3
"""Compose the retained level-(2,3) fixed-7 artifact with the odd CM filter."""
from __future__ import annotations
import argparse,copy,hashlib,json,pathlib,tempfile
from typing import Any
import check_signature_357_fixed7_level23 as fixed7
ROOT=pathlib.Path(__file__).resolve().parents[1];DEFAULT=ROOT/'Research'/'Signature357'/'odd_fixed7_level23_frontier.json'
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

def validate(d):
 keys={'schema_version','status','equation','branch','level_exponents','artifact','packet_count','fixed7_survivors','superspecial_survivors','superspecial_removed','persistent_cm_packets','odd_branch_noncm_superspecial_survivors','compression','imported_dependencies','conclusion','nonclaim','certificate_sha256'}
 if set(d)!=keys:raise CertificateError('keys differ')
 if d['schema_version']!=1 or d['status']!='retained-public-Magma-plus-imported-CM-filter':raise CertificateError('schema/status mismatch')
 if d['equation']!='A^3+B^5=C^7' or d['level_exponents']!=[2,3]:raise CertificateError('scope mismatch')
 artifact_meta=d['artifact'];path=ROOT/artifact_meta['path']
 try:artifact_digest=fixed7.validate(fixed7.load_json(path))
 except fixed7.CertificateError as e:raise CertificateError(f'fixed7 subcertificate failed: {e}') from e
 if artifact_digest!=artifact_meta['certificate_sha256']:raise CertificateError('fixed7 artifact digest binding mismatch')
 artifact=fixed7.load_json(path)
 if d['packet_count']!=artifact['packet_count'] or d['packet_count']!=35:raise CertificateError('packet count mismatch')
 if d['fixed7_survivors']!=artifact['fixed7_survivors']:raise CertificateError('fixed7 survivor set mismatch')
 if d['superspecial_survivors']!=artifact['superspecial_survivors']:raise CertificateError('superspecial set mismatch')
 removed=sorted(set(d['fixed7_survivors'])-set(d['superspecial_survivors']))
 if removed!=[5,17] or d['superspecial_removed']!=removed:raise CertificateError('superspecial removal mismatch')
 cm=d['persistent_cm_packets']
 if cm!=[1,7,11,12,13,16,21] or not set(cm)<=set(d['superspecial_survivors']):raise CertificateError('persistent CM set mismatch')
 final=sorted(set(d['superspecial_survivors'])-set(cm))
 if final!=[24,28] or d['odd_branch_noncm_superspecial_survivors']!=final:raise CertificateError('final level-(2,3) frontier mismatch')
 if d['compression']!=['35 packets','11 fixed-7 survivors','9 superspecial survivors','2 non-CM superspecial survivors']:raise CertificateError('compression summary mismatch')
 if len(d['imported_dependencies'])!=3 or 'not yet eliminated' not in d['nonclaim']:raise CertificateError('trust boundary missing')
 if d['conclusion']!='the odd fixed-7 level-(2,3) frontier consists of packets 24 and 28':raise CertificateError('conclusion mismatch')
 h=sha(d)
 if h!=d['certificate_sha256']:raise CertificateError(f'digest mismatch: {h}')
 return h

def reject(d,desc):
 try:validate(d)
 except CertificateError:return
 raise RuntimeError(f'accepted {desc}')

def self_test():
 x=load_json(DEFAULT);validate(x)
 y=copy.deepcopy(x);y['odd_branch_noncm_superspecial_survivors']=[24];y['certificate_sha256']=sha(y);reject(y,'weakened frontier')
 y=copy.deepcopy(x);y['persistent_cm_packets'].append(24);y['certificate_sha256']=sha(y);reject(y,'false CM packet')
 with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:f.write('{"schema_version":1,"schema_version":1}');p=pathlib.Path(f.name)
 try:
  try:load_json(p)
  except CertificateError:pass
  else:raise RuntimeError('accepted duplicate keys')
 finally:p.unlink(missing_ok=True)
 print('signature-357 odd fixed7 level23 negative fixtures rejected')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=pathlib.Path,default=DEFAULT);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
 if a.self_test:self_test();return 0
 h=validate(load_json(a.manifest));print('signature-357 odd fixed-7 level-(2,3) frontier valid');print('  35 -> 11 -> 9 -> packets 24,28');print(f'  certificate sha256: {h}');return 0
if __name__=='__main__':raise SystemExit(main())
