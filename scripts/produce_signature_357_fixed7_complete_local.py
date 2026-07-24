#!/usr/bin/env python3
"""Produce complete local fixed-7 HGM trace data at new auxiliary primes."""
from __future__ import annotations
import hashlib, json, pathlib, re, subprocess, sys, tempfile, urllib.request
from typing import Any
SOURCE_URL=("https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/" "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Codes/GPcode.gp")
EXPECTED_GIT_BLOB="d829dbdfd5b710b2164f74ee5e1c1f92adae58d2"
PRIMES=[43]
class ProducerError(RuntimeError): pass

def blob(data:bytes)->str: return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def digest(value:Any)->str: return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def source()->str:
    with urllib.request.urlopen(urllib.request.Request(SOURCE_URL,headers={'User-Agent':'beal-conjecture-lean-research/1.0'}),timeout=90) as response: data=response.read()
    if blob(data)!=EXPECTED_GIT_BLOB: raise ProducerError('GP source blob mismatch')
    return data.decode()
def driver()->str:
    primes=','.join(map(str,PRIMES))
    return rf'''
default(parisizemax,2000000000);
K5=nfinit(x^2-5); F15=nfinit(polcyclo(15)); P=[{primes}];
NormPoly(A)=A/content(A);
EmitPrime(p0)=
{{
  local(fK,fF,g,u,A,i);
  fK=idealprimedec(K5,p0)[1][4]; fF=idealprimedec(F15,p0)[1][4];
  print("META|",p0,"|",fK,"|",fF);
  for(u=2,p0-1,A=NormPoly(algdep(p0^fK*hgm(u,[1/5,-1/5],[1/3,-1/3],p0,fK),2));print("GENERIC|",p0,"|",u,"|",A));
  g=lift(znprimroot(p0));
  for(i=1,5,A=NormPoly(algdep(Jacobi2(1/3,-1/3,1/5,-1/5,g^i,p0,fF),2));print("ZERO|",p0,"|",i,"|",A));
  for(i=1,3,A=NormPoly(algdep(Jacobi3(1/3,-1/3,1/5,-1/5,g^i,p0,fF),2));print("INFINITY|",p0,"|",i,"|",A));
}};
for(ii=1,#P,EmitPrime(P[ii])); quit;
'''
def main()->int:
    with tempfile.TemporaryDirectory() as directory:
        path=pathlib.Path(directory)/'fixed7-complete.gp'; path.write_text(source()+'\n'+driver())
        process=subprocess.run(['gp','-q',str(path)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=1200,check=False)
    if process.returncode: raise ProducerError(process.stderr[-8000:])
    metadata={}; rows={'generic':[],'zero':[],'infinity':[]}
    meta=re.compile(r'^META\|(\d+)\|(\d+)\|(\d+)$'); row=re.compile(r'^(GENERIC|ZERO|INFINITY)\|(\d+)\|(\d+)\|(.+)$')
    for raw in process.stdout.splitlines():
        line=raw.strip(); match=meta.match(line)
        if match:
            prime,fk,ff=map(int,match.groups()); metadata[str(prime)]={'residue_degree_K5':fk,'residue_degree_F15':ff,'extension_residue_degree':ff//fk}; continue
        match=row.match(line)
        if match:
            kind,prime,index,poly=match.groups(); rows[kind.lower()].append({'prime':int(prime),'parameter_index':int(index),'trace_polynomial':poly.replace(' ','')})
    if sorted(map(int,metadata))!=PRIMES: raise ProducerError(f'missing metadata: {metadata}')
    if len(rows['generic'])!=sum(p-2 for p in PRIMES) or len(rows['zero'])!=5*len(PRIMES) or len(rows['infinity'])!=3*len(PRIMES): raise ProducerError('unexpected row counts')
    body={'schema_version':1,'status':'complete local fixed-7 HGM trace-polynomial producer output','source':{'repository':'lucasvillagra/GFE-5p3','commit':'e88f914c577ab6cf9a45e5cdd82c1993477fb423','path':'Codes/GPcode.gp','git_blob_sha1':EXPECTED_GIT_BLOB,'pari_version':subprocess.run(['gp','--version-short'],text=True,stdout=subprocess.PIPE).stdout.strip()},'motive':'H((1/5,-1/5),(1/3,-1/3)|t7)','parameter':'t7=-B^5/A^3','base_field':'K5=Q(sqrt(5))','full_cyclotomic_field':'F15=Q(zeta_15)','primes':PRIMES,'residue_metadata':metadata,'generic_rows':rows['generic'],'zero_rows':rows['zero'],'infinity_rows':rows['infinity'],'multiplicative_rule':'at t7=1 use the ray-character reducible base trace'}
    result=dict(body); result['certificate_sha256']=digest(body); json.dump(result,sys.stdout,sort_keys=True,indent=2); print(); return 0
if __name__=='__main__': raise SystemExit(main())
