#!/usr/bin/env python3
"""Audit packets 24 and 28 against the exact odd-C trace set {0,-1}."""
from __future__ import annotations
import hashlib,html,http.cookiejar,json,re,urllib.parse,urllib.request
from typing import Any
CALCULATOR_URL='https://magma.maths.usyd.edu.au/calc/';USER_AGENT='Mozilla/5.0 beal-conjecture-lean-research/1.0';PACKETS=[24,28]
class ResearchError(RuntimeError):pass
def digest(v:Any)->str:return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def metadata(page:str)->tuple[str,dict[str,str]]:
    f=re.search(r'<form\b([^>]*)>(.*?)</form>',page,flags=re.I|re.S)
    if not f:raise ResearchError('calculator page contains no form')
    attrs,body=f.groups();m=re.search(r'\baction=["\']([^"\']*)',attrs,flags=re.I);action=CALCULATOR_URL if not m else urllib.parse.urljoin(CALCULATOR_URL,html.unescape(m.group(1)));hidden={}
    for tag in re.findall(r'<input\b[^>]*>',body,flags=re.I):
        tm=re.search(r'\btype=["\']([^"\']*)',tag,flags=re.I);nm=re.search(r'\bname=["\']([^"\']*)',tag,flags=re.I);vm=re.search(r'\bvalue=["\']([^"\']*)',tag,flags=re.I)
        if tm and tm.group(1).lower()=='hidden' and nm:hidden[html.unescape(nm.group(1))]='' if not vm else html.unescape(vm.group(1))
    return action,hidden
def submit(code:str)->str:
    jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(urllib.request.Request(CALCULATOR_URL,headers={'User-Agent':USER_AGENT}),timeout=120) as r:landing=r.read().decode(errors='replace');landing_url=r.geturl()
    action,hidden=metadata(landing);hidden['input']=code;parsed=urllib.parse.urlparse(action);req=urllib.request.Request(action,data=urllib.parse.urlencode(hidden).encode(),headers={'User-Agent':USER_AGENT,'Content-Type':'application/x-www-form-urlencoded','Referer':landing_url,'Origin':f'{parsed.scheme}://{parsed.netloc}'})
    with opener.open(req,timeout=240) as r:return html.unescape(re.sub(r'<[^>]+>','',r.read().decode(errors='replace')))
def code()->str:return r'''
_<x>:=PolynomialRing(Rationals());K<z>:=NumberField(x^2-5);OK:=Integers(K);I5:=Factorisation(5*OK)[1][1];I2:=Factorisation(2*OK)[1][1];F7:=GF(7);R7<X>:=PolynomialRing(F7);
M:=HilbertCuspForms(K,3^2*I5^3);D:=NewformDecomposition(NewSubspace(M));printf "PACKET_COUNT=%o\n",#D;
for i in [24,28] do f:=Eigenform(D[i]);a:=HeckeEigenvalue(f,I2);P:=MinimalPolynomial(a);P7:=R7![F7!Coefficient(P,j):j in [0..Degree(P)]];G:=GreatestCommonDivisor(P7,X*(X+1));printf "ROW|%o|%o|",i,Degree(P);for c in Eltseq(P) do printf "%o,",c;end for;printf "|%o\n",Degree(G);end for;
'''
def main()->int:
    source=code();body={'schema_version':3,'status':'fixed-7 packet-24/28 exact odd-C trace-union-at-2 audit','level_exponents':[2,3],'level_norm':10125,'packets':PACKETS,'prime_ideal_norm':4,'allowed_integer_traces':[0,-1],'allowed_traces_mod7':[0,6],'annihilating_polynomial':'X*(X+1)','rows':[],'soundness':'a packet survives only when its Hecke polynomial shares a root with X*(X+1) modulo 7'};out=''
    try:
        out=submit(source);m=re.search(r'PACKET_COUNT=(\d+)',out)
        if not m or int(m.group(1))!=35:raise ResearchError('unexpected packet count')
        rows=[]
        for m in re.finditer(r'ROW\|(24|28)\|(\d+)\|([^|\n]*)\|(\d+)',out):
            packet,degree=map(int,m.groups()[:2]);coeffs=[int(v) for v in m.group(3).split(',') if v]
            if len(coeffs)!=degree+1:raise ResearchError('coefficient count mismatch')
            rows.append({'packet':packet,'trace_polynomial_degree':degree,'trace_coefficients_low_to_high':coeffs,'gcd_with_trace_union_degree_mod7':int(m.group(4)),'survives':int(m.group(4))>0})
        if [r['packet'] for r in rows]!=PACKETS:raise ResearchError('incomplete packet rows')
        body.update({'request_status':'completed','rows':rows,'surviving_packets':[r['packet'] for r in rows if r['survives']],'output_tail':out[-5000:]})
    except Exception as exc:body.update({'request_status':'failed','error':f'{type(exc).__name__}: {exc}','output_tail':out[-8000:]})
    result=dict(body);result['certificate_sha256']=digest(body);print(json.dumps(result,sort_keys=True,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
