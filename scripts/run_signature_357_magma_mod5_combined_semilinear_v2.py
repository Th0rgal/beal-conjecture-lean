#!/usr/bin/env python3
"""Combined odd mod-5 residual sieve, including the removed-prime-7 trace.

This version adds the necessary trace condition a_p7=+/-(7+1) mod 5 whenever
the cyclotomic untwist removes p7 from the residual conductor (e7=0).
"""
from __future__ import annotations

import argparse, hashlib, html, http.cookiejar, json, pathlib, re, urllib.parse, urllib.request
from typing import Any

CALCULATOR_URL="https://magma.maths.usyd.edu.au/calc/"
LEVEL_PAIRS=[(2,1),(3,0),(3,1)]
INERT_PRIMES=[11,23]
SPLIT_PRIMES=[13,29,41,43]
PRIMES=INERT_PRIMES+SPLIT_PRIMES
MAX_INPUT=49000
USER_AGENT="Mozilla/5.0 beal-conjecture-lean-research/1.0"
class ResearchError(RuntimeError): pass

def digest(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def form_metadata(page:str)->tuple[str,dict[str,str]]:
    form=re.search(r"<form\b([^>]*)>(.*?)</form>",page,flags=re.I|re.S)
    if form is None: raise ResearchError('calculator page contains no form')
    attributes,body=form.groups(); am=re.search(r"\baction=[\"']([^\"']*)",attributes,flags=re.I)
    action=CALCULATOR_URL if am is None else urllib.parse.urljoin(CALCULATOR_URL,html.unescape(am.group(1))); hidden={}
    for tag in re.findall(r"<input\b[^>]*>",body,flags=re.I):
        tm=re.search(r"\btype=[\"']([^\"']*)",tag,flags=re.I); nm=re.search(r"\bname=[\"']([^\"']*)",tag,flags=re.I); vm=re.search(r"\bvalue=[\"']([^\"']*)",tag,flags=re.I)
        if tm and tm.group(1).lower()=='hidden' and nm: hidden[html.unescape(nm.group(1))]='' if vm is None else html.unescape(vm.group(1))
    return action,hidden

def submit(code:str)->str:
    if len(code.encode())>MAX_INPUT: raise ResearchError(f'generated input has {len(code.encode())} bytes')
    jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(urllib.request.Request(CALCULATOR_URL,headers={'User-Agent':USER_AGENT}),timeout=120) as response: landing=response.read().decode(errors='replace'); landing_url=response.geturl()
    action,hidden=form_metadata(landing); hidden['input']=code; parsed=urllib.parse.urlparse(action)
    request=urllib.request.Request(action,data=urllib.parse.urlencode(hidden).encode(),headers={'User-Agent':USER_AGENT,'Content-Type':'application/x-www-form-urlencoded','Referer':landing_url,'Origin':f'{parsed.scheme}://{parsed.netloc}'})
    with opener.open(request,timeout=210) as response: page=response.read().decode(errors='replace')
    return html.unescape(re.sub(r'<[^>]+>','',page))

def rows_from(data:dict[str,Any],wanted:list[int])->dict[int,tuple[Any,...]]:
    result={}
    for prime in wanted:
        if prime not in data.get('primes',[]): raise ResearchError(f'local data lacks prime {prime}')
        meta=data['residue_metadata'][str(prime)]; kinds={kind:[row['trace_polynomial'] for row in data[f'{kind}_rows'] if row['prime']==prime] for kind in ('generic','zero','infinity')}
        result[prime]=(prime,kinds['generic'],kinds['zero'],kinds['infinity'],meta['residue_degree_K7'],meta['residue_degree_F21'])
    return result

def ml(values:list[str])->str:return '['+','.join(values)+']'
def encode(row:tuple[Any,...])->str:
    p,g,z,i,fk,ff=row; return f'<{p},{ml(g)},{ml(z)},{ml(i)},{fk},{ff}>'

def code(e3:int,e7:int,rows:dict[int,tuple[Any,...]])->str:
    encoded=','.join(encode(rows[p]) for p in PRIMES)
    removed='true' if e7==0 else 'false'
    return rf'''
_<x>:=PolynomialRing(Rationals()); K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
I3:=Factorisation(3*OK)[1][1]; I7:=Factorisation(7*OK)[1][1]; I2:=Factorisation(2*OK)[1][1];
F5:=GF(5); R5<X>:=PolynomialRing(F5); Rows:=[{encoded}];
Red:=function(P) return R5![F5!Coefficient(P,j):j in [0..Degree(P)]]; end function;
Eval:=function(P,T) n:=Nrows(T); A:=ZeroMatrix(F5,n,n); Q:=IdentityMatrix(F5,n); for j in [0..Degree(P)] do A+:=F5!Coefficient(P,j)*Q; Q:=Q*T; end for; return A; end function;
Union:=function(T,row)
 n:=Nrows(T); Id:=IdentityMatrix(F5,n); U:=T; if row[6]/row[5] eq 2 then U:=T*T-F5!(2*row[1]^row[5])*Id; end if; A:=Id;
 for P in row[2] do A:=A*Eval(Red(P),U); end for; for P in row[3] do A:=A*Eval(Red(P),U); end for; for P in row[4] do A:=A*Eval(Red(P),U); end for;
 q:=Integers()!Norm(Factorisation(row[1]*OK)[1][1]); return A*(T-F5!(q+1)*Id)*(T+F5!(q+1)*Id);
end function;
M0:=HilbertCuspForms(K,I3^{e3}*I7^{e7}); M:=NewSubspace(M0); SetRationalBasis(M); n:=Dimension(M); V:=VectorSpace(F5,n);
printf "NEW_DIM=%o\n",n; T2:=Matrix(F5,HeckeOperator(M,I2)); S:=V meet Kernel(T2); printf "NORM8_DIM=%o\n",Dimension(S);
if {removed} then T7:=Matrix(F5,HeckeOperator(M,I7)); Id:=IdentityMatrix(F5,n); S:=S meet Kernel((T7-F5!8*Id)*(T7+F5!8*Id)); end if;
printf "AFTER_REMOVED7_DIM=%o\n",Dimension(S);
for row in Rows do
 l:=row[1]; fac:=Factorisation(l*OK); T1:=Matrix(F5,HeckeOperator(M,fac[1][1])); S:=S meet Kernel(Union(T1,row));
 if #fac eq 1 then S:=S meet Kernel(T1^5-T1); elif #fac eq 3 then T2c:=Matrix(F5,HeckeOperator(M,fac[2][1])); T3c:=Matrix(F5,HeckeOperator(M,fac[3][1])); S:=S meet Kernel(T2c+T3c-T1^5-T1^25); S:=S meet Kernel(T2c*T3c-T1^30); S:=S meet Kernel(T1^125-T1); end if;
 printf "DIM_AFTER_%o=%o\n",l,Dimension(S);
end for; printf "FINAL_DIM=%o\n",Dimension(S);
'''

def pair(raw:str)->tuple[int,int]:
    try:value=tuple(int(x) for x in raw.split(','))
    except ValueError as exc:raise argparse.ArgumentTypeError('pair must be e3,e7') from exc
    if len(value)!=2 or value not in LEVEL_PAIRS:raise argparse.ArgumentTypeError(f'unsupported pair {raw}')
    return value

def integer(text:str,marker:str)->int:
    m=re.search(rf'{marker}=(\d+)',text)
    if m is None:raise ResearchError(f'output lacked {marker}')
    return int(m.group(1))

def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--split-data',type=pathlib.Path,required=True);parser.add_argument('--inert-data',type=pathlib.Path,required=True);parser.add_argument('--pair',type=pair,required=True);args=parser.parse_args()
    split=json.loads(args.split_data.read_text());inert=json.loads(args.inert_data.read_text());rows=rows_from(inert,INERT_PRIMES);rows.update(rows_from(split,SPLIT_PRIMES));e3,e7=args.pair;source=code(e3,e7,rows)
    body={'schema_version':2,'status':'combined odd mod-5 residual HGM, semilinear and removed-prime sieve','calculator':CALCULATOR_URL,'level_exponents':[e3,e7],'level_norm':27**e3*7**e7,'removed_prime7_trace_applied':e7==0,'removed_prime7_targets_mod5':[2,3] if e7==0 else [],'inert_primes':INERT_PRIMES,'split_primes':SPLIT_PRIMES,'split_local_sha256':split.get('certificate_sha256'),'inert_local_sha256':inert.get('certificate_sha256'),'input_bytes':len(source.encode()),'soundness':'zero final dimension is a fail-closed residual elimination; positive dimension is only necessary'}
    try:
        output=submit(source);body.update({'request_status':'completed','new_dimension':integer(output,'NEW_DIM'),'norm8_dimension':integer(output,'NORM8_DIM'),'after_removed7_dimension':integer(output,'AFTER_REMOVED7_DIM'),'dimensions_after_primes':{str(p):integer(output,f'DIM_AFTER_{p}') for p in PRIMES},'final_dimension':integer(output,'FINAL_DIM'),'output_tail':output[-2200:]})
    except Exception as exc:body.update({'request_status':'failed','error':f'{type(exc).__name__}: {exc}'})
    result=dict(body);result['certificate_sha256']=digest(body);print(json.dumps(result,sort_keys=True,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
