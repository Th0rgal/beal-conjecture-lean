#!/usr/bin/env python3
"""Test the corrected universal fixed-7 trace set at the norm-4 prime.

Exact point counts on the two parity reductions over F_4 and F_16 give RM
traces 0 and -1.  Thus every odd-C specialization is killed by the polynomial
T_P*(T_P+1) modulo 7.  A zero kernel on level (3,3) closes the final fixed-7
block; a positive kernel is only necessary and a failed request is explicit.
"""
from __future__ import annotations

import hashlib, html, http.cookiejar, json, re, urllib.parse, urllib.request
from typing import Any

CALCULATOR_URL="https://magma.maths.usyd.edu.au/calc/"
USER_AGENT="Mozilla/5.0 beal-conjecture-lean-research/1.0"
class ResearchError(RuntimeError): pass

def digest(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def metadata(page:str)->tuple[str,dict[str,str]]:
    form=re.search(r'<form\b([^>]*)>(.*?)</form>',page,flags=re.I|re.S)
    if not form:raise ResearchError('calculator page contains no form')
    attrs,body=form.groups();m=re.search(r'\baction=["\']([^"\']*)',attrs,flags=re.I)
    action=CALCULATOR_URL if not m else urllib.parse.urljoin(CALCULATOR_URL,html.unescape(m.group(1)));hidden={}
    for tag in re.findall(r'<input\b[^>]*>',body,flags=re.I):
        tm=re.search(r'\btype=["\']([^"\']*)',tag,flags=re.I);nm=re.search(r'\bname=["\']([^"\']*)',tag,flags=re.I);vm=re.search(r'\bvalue=["\']([^"\']*)',tag,flags=re.I)
        if tm and tm.group(1).lower()=='hidden' and nm:hidden[html.unescape(nm.group(1))]='' if not vm else html.unescape(vm.group(1))
    return action,hidden
def submit(code:str)->str:
    jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(urllib.request.Request(CALCULATOR_URL,headers={'User-Agent':USER_AGENT}),timeout=120) as r:landing=r.read().decode(errors='replace');landing_url=r.geturl()
    action,hidden=metadata(landing);hidden['input']=code;parsed=urllib.parse.urlparse(action)
    req=urllib.request.Request(action,data=urllib.parse.urlencode(hidden).encode(),headers={'User-Agent':USER_AGENT,'Content-Type':'application/x-www-form-urlencoded','Referer':landing_url,'Origin':f'{parsed.scheme}://{parsed.netloc}'})
    with opener.open(req,timeout=300) as r:return html.unescape(re.sub(r'<[^>]+>','',r.read().decode(errors='replace')))
def code()->str:return r'''
_<x>:=PolynomialRing(Rationals()); K<z>:=NumberField(x^2-5); OK:=Integers(K);
I5:=Factorisation(5*OK)[1][1]; I2:=Factorisation(2*OK)[1][1]; F7:=GF(7);
printf "PHASE=space-start\n"; M0:=HilbertCuspForms(K,3^3*I5^3); M:=NewSubspace(M0); n:=Dimension(M); printf "NEW_DIM=%o\n",n;
O:=QuaternionOrder(M); DeleteHeckePrecomputation(O); printf "PHASE=T2-start\n";
TQ:=HeckeOperator(M,I2 : LowMemory:=true,UseLLL:=false,ThetaPrec:=0); T:=Matrix(F7,TQ); delete TQ; DeleteHeckePrecomputation(O,I2);
I:=IdentityMatrix(F7,n); S:=Kernel(T*(T+I)); printf "TRACE_UNION_DIM=%o\n",Dimension(S); printf "FINAL_DIM=%o\n",Dimension(S);
'''
def parse(s:str,k:str)->int:
    m=re.search(rf'{k}=(\d+)',s)
    if not m:raise ResearchError(f'output lacked {k}')
    return int(m.group(1))
def main()->int:
    source=code();body={'schema_version':3,'status':'fixed-7 level-(3,3) exact odd-C trace-union-at-2 probe','calculator':CALCULATOR_URL,'level_exponents':[3,3],'level_norm':91125,'prime_ideal_norm':4,'allowed_integer_traces':[0,-1],'allowed_traces_mod7':[0,6],'annihilating_polynomial':'T*(T+1)','input_bytes':len(source.encode()),'soundness':'final dimension zero eliminates the complete fixed-7 level-(3,3) odd branch; positive dimension is only necessary','nonclaim':'the point-count trace theorem, modularity and level lowering are imported inputs; failure leaves the level unresolved'};out=''
    try:
        out=submit(source);body.update({'request_status':'completed','new_dimension':parse(out,'NEW_DIM'),'trace_union_dimension':parse(out,'TRACE_UNION_DIM'),'final_dimension':parse(out,'FINAL_DIM'),'output_tail':out[-6000:]})
    except Exception as exc:body.update({'request_status':'failed','error':f'{type(exc).__name__}: {exc}','output_tail':out[-9000:]})
    result=dict(body);result['certificate_sha256']=digest(body);print(json.dumps(result,sort_keys=True,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
