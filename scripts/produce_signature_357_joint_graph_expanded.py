#!/usr/bin/env python3
"""Produce an expanded, parameter-labelled two-Frey HGM graph.

The PARI/GP coordinate used by the pinned source satisfies

    (z5-1)*(z7-1)=1.

For every generic z5 this producer records the matching z7 and both generic
trace polynomials.  It also records the three special graph pairs
(0,0), (1,infinity), and (infinity,1) through the complete Jacobi-sum candidate
sets used by the source elimination.
"""
from __future__ import annotations

import hashlib,json,pathlib,re,subprocess,sys,tempfile,urllib.request
from typing import Any

SOURCE_URL=("https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/" "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Codes/GPcode.gp")
EXPECTED_BLOB="d829dbdfd5b710b2164f74ee5e1c1f92adae58d2"
PRIMES=[11,13,17,19,23,29,31,41,43,59,61,71]
class ProducerError(RuntimeError):pass

def blob(data:bytes)->str:return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def digest(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fetch()->str:
    with urllib.request.urlopen(urllib.request.Request(SOURCE_URL,headers={'User-Agent':'beal-conjecture-lean-research/1.0'}),timeout=90) as response:data=response.read()
    if blob(data)!=EXPECTED_BLOB:raise ProducerError('GP source blob mismatch')
    return data.decode()
def driver()->str:
    primes=','.join(map(str,PRIMES))
    return rf'''
default(parisizemax,3000000000);
K7=nfinit(x^3-x^2-2*x+1); K5=nfinit(x^2-5); F21=nfinit(polcyclo(21)); F15=nfinit(polcyclo(15)); P=[{primes}];
NormPoly(A)=A/content(A);
Emit(p0)=
{{
 local(f5,f7,ff21,ff15,z5,z7,A5,A7,g,i);
 f5=idealprimedec(K7,p0)[1][4]; f7=idealprimedec(K5,p0)[1][4]; ff21=idealprimedec(F21,p0)[1][4]; ff15=idealprimedec(F15,p0)[1][4];
 print("META|",p0,"|",f5,"|",ff21,"|",f7,"|",ff15);
 for(z5=2,p0-1,
   z7=lift(Mod(1+1/Mod(z5-1,p0),p0));
   A5=NormPoly(algdep(p0^f5*hgm(z5,[1/7,-1/7],[1/3,-1/3],p0,f5),3));
   A7=NormPoly(algdep(p0^f7*hgm(z7,[1/5,-1/5],[1/3,-1/3],p0,f7),2));
   print("GENERIC|",p0,"|",z5,"|",z7,"|",A5,"|",A7)
 );
 g=lift(znprimroot(p0));
 for(i=1,7,A5=NormPoly(algdep(Jacobi2(1/3,-1/3,1/7,-1/7,g^i,p0,ff21),3));print("ZERO5|",p0,"|",i,"|",A5));
 for(i=1,3,A5=NormPoly(algdep(Jacobi3(1/3,-1/3,1/7,-1/7,g^i,p0,ff21),3));print("INF5|",p0,"|",i,"|",A5));
 for(i=1,5,A7=NormPoly(algdep(Jacobi2(1/3,-1/3,1/5,-1/5,g^i,p0,ff15),2));print("ZERO7|",p0,"|",i,"|",A7));
 for(i=1,3,A7=NormPoly(algdep(Jacobi3(1/3,-1/3,1/5,-1/5,g^i,p0,ff15),2));print("INF7|",p0,"|",i,"|",A7));
}};
for(ii=1,#P,Emit(P[ii]));quit;
'''
def main()->int:
    with tempfile.TemporaryDirectory() as directory:
        path=pathlib.Path(directory)/'joint-expanded.gp';path.write_text(fetch()+'\n'+driver())
        process=subprocess.run(['gp','-q',str(path)],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=3600,check=False)
    if process.returncode:raise ProducerError(process.stderr[-10000:])
    metadata={};generic=[];special={'zero5':[],'infinity5':[],'zero7':[],'infinity7':[]}
    meta=re.compile(r'^META\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)$');gen=re.compile(r'^GENERIC\|(\d+)\|(\d+)\|(\d+)\|([^|]+)\|(.+)$');sp=re.compile(r'^(ZERO5|INF5|ZERO7|INF7)\|(\d+)\|(\d+)\|(.+)$')
    names={'ZERO5':'zero5','INF5':'infinity5','ZERO7':'zero7','INF7':'infinity7'}
    for raw in process.stdout.splitlines():
        line=raw.strip();m=meta.match(line)
        if m:
            p,f5,ff21,f7,ff15=map(int,m.groups());metadata[str(p)]={'residue_degree_K7':f5,'residue_degree_F21':ff21,'residue_degree_K5':f7,'residue_degree_F15':ff15};continue
        m=gen.match(line)
        if m:
            p,z5,z7=map(int,m.groups()[:3]);generic.append({'prime':p,'z5':z5,'z7':z7,'mod5_trace_polynomial':m.group(4).replace(' ',''),'fixed7_trace_polynomial':m.group(5).replace(' ','')});continue
        m=sp.match(line)
        if m:
            kind,p,index,poly=m.groups();special[names[kind]].append({'prime':int(p),'character_index':int(index),'trace_polynomial':poly.replace(' ','')})
    if sorted(map(int,metadata))!=PRIMES:raise ProducerError(f'missing metadata: {metadata}')
    if len(generic)!=sum(p-2 for p in PRIMES):raise ProducerError('generic row count mismatch')
    expected={'zero5':7,'infinity5':3,'zero7':5,'infinity7':3}
    for kind,count in expected.items():
        if len(special[kind])!=count*len(PRIMES):raise ProducerError(f'{kind} row count mismatch')
    body={'schema_version':1,'status':'expanded parameter-labelled two-Frey HGM graph producer output','source':{'repository':'lucasvillagra/GFE-5p3','commit':'e88f914c577ab6cf9a45e5cdd82c1993477fb423','path':'Codes/GPcode.gp','git_blob_sha1':EXPECTED_BLOB,'pari_version':subprocess.run(['gp','--version-short'],text=True,stdout=subprocess.PIPE).stdout.strip()},'gp_parameter_relation':'(z5-1)*(z7-1)=1','generic_relation':'z7=1+1/(z5-1)','special_pairs':[['zero','zero'],['multiplicative','infinity'],['infinity','multiplicative']],'primes':PRIMES,'residue_metadata':metadata,'generic_rows':generic,**special}
    result=dict(body);result['certificate_sha256']=digest(body);json.dump(result,sys.stdout,sort_keys=True,indent=2);print();return 0
if __name__=='__main__':raise SystemExit(main())
