#!/usr/bin/env python3
"""Query and filter the seven open mod-5 Hilbert spaces on public Magma.

Each level is submitted independently. A failed or timed-out level is retained as
an explicit error record and is never interpreted as an empty newform space.
"""
from __future__ import annotations
import argparse, hashlib, html, http.cookiejar, json, pathlib, re, urllib.parse, urllib.request
from typing import Any
CALCULATOR_URL="https://magma.maths.usyd.edu.au/calc/"
LEVEL_PAIRS=[(2,1),(1,3),(3,0),(2,2),(3,1),(2,3),(3,2)]
MAX_INPUT=49000
USER_AGENT="Mozilla/5.0 beal-conjecture-lean-research/1.0"
class ResearchError(RuntimeError): pass

def canonical_sha256(value:Any)->str:
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def form_metadata(page:str)->tuple[str,dict[str,str]]:
    form=re.search(r"<form\b([^>]*)>(.*?)</form>",page,flags=re.I|re.S)
    if form is None: raise ResearchError('calculator page contains no form')
    attributes,body=form.groups(); action_match=re.search(r"\baction=[\"']([^\"']*)",attributes,flags=re.I)
    action=CALCULATOR_URL if action_match is None else urllib.parse.urljoin(CALCULATOR_URL,html.unescape(action_match.group(1)))
    hidden={}
    for tag in re.findall(r"<input\b[^>]*>",body,flags=re.I):
        tm=re.search(r"\btype=[\"']([^\"']*)",tag,flags=re.I); nm=re.search(r"\bname=[\"']([^\"']*)",tag,flags=re.I); vm=re.search(r"\bvalue=[\"']([^\"']*)",tag,flags=re.I)
        if tm and tm.group(1).lower()=='hidden' and nm: hidden[html.unescape(nm.group(1))]='' if vm is None else html.unescape(vm.group(1))
    return action,hidden

def submit(code:str)->str:
    if len(code.encode())>MAX_INPUT: raise ResearchError(f'generated input has {len(code.encode())} bytes')
    jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(urllib.request.Request(CALCULATOR_URL,headers={'User-Agent':USER_AGENT}),timeout=120) as response:
        landing=response.read().decode(errors='replace'); landing_url=response.geturl()
    action,hidden=form_metadata(landing); payload=dict(hidden); payload['input']=code; parsed=urllib.parse.urlparse(action)
    request=urllib.request.Request(action,data=urllib.parse.urlencode(payload).encode(),headers={'User-Agent':USER_AGENT,'Content-Type':'application/x-www-form-urlencoded','Referer':landing_url,'Origin':f'{parsed.scheme}://{parsed.netloc}'})
    with opener.open(request,timeout=210) as response: page=response.read().decode(errors='replace')
    return html.unescape(re.sub(r'<[^>]+>','',page))

def magma_list(polynomials:list[str])->str: return '['+','.join(polynomials)+']'

def candidate_rows(local:dict[str,Any])->list[tuple[int,list[str],list[str],list[str],int,int]]:
    result=[]
    for prime in local['primes']:
        metadata=local['residue_metadata'][str(prime)]; kinds={}
        for kind in ('generic','zero','infinity'):
            kinds[kind]=[row['trace_polynomial'] for row in local[f'{kind}_rows'] if row['prime']==prime]
        result.append((prime,kinds['generic'],kinds['zero'],kinds['infinity'],metadata['residue_degree_K7'],metadata['residue_degree_F21']))
    return result
PREFIX=r'''
_<x> := PolynomialRing(Rationals());
K<w> := NumberField(x^3-x^2-2*x+1);
OK := Integers(K);
I3 := Factorisation(3*OK)[1][1]; I7 := Factorisation(7*OK)[1][1]; I2 := Factorisation(2*OK)[1][1];
F5 := GF(5); R5<X> := PolynomialRing(F5);
Red := function(P) return R5![F5!Coefficient(P,i) : i in [0..Degree(P)]]; end function;
Common := function(P,Q) return Degree(GreatestCommonDivisor(Red(P),Red(Q))) gt 0; end function;
AnyCommon := function(P,L) for Q in L do if Common(P,Q) then return true; end if; end for; return false; end function;
PossibleAt := function(form,row)
  l:=row[1]; G:=row[2]; Z:=row[3]; Inf:=row[4]; fK:=row[5]; fF:=row[6]; I:=Factorisation(l*OK)[1][1];
  Eig:=HeckeEigenvalue(form,I); Pbase:=MinimalPolynomial(Eig); Efull:=Eig;
  if fF/fK eq 2 then Efull:=Eig^2-2*l^fK; end if; Pfull:=MinimalPolynomial(Efull);
  if AnyCommon(Pfull,G) or AnyCommon(Pfull,Z) or AnyCommon(Pfull,Inf) then return true; end if;
  q:=Integers()!Norm(I); if Common(Pbase,x-(q+1)) or Common(Pbase,x+(q+1)) then return true; end if;
  return false;
end function;
'''
def make_code(e3:int,e7:int,rows)->str:
    encoded=[f'<{prime},{magma_list(generic)},{magma_list(zero)},{magma_list(infinity)},{fk},{ff}>' for prime,generic,zero,infinity,fk,ff in rows]
    data='Rows:=['+','.join(encoded)+'];\n'
    suffix=rf'''
M := HilbertCuspForms(K,I3^{e3}*I7^{e7}); decomp := NewformDecomposition(NewSubspace(M));
S8 := []; Slocal := []; Dims := [];
for i in [1..#decomp] do
  form:=Eigenform(decomp[i]); Append(~Dims,Dimension(decomp[i])); P2:=MinimalPolynomial(HeckeEigenvalue(form,I2));
  if Common(P2,x) then Append(~S8,i); alive:=true;
    for row in Rows do if not PossibleAt(form,row) then alive:=false; break; end if; end for;
    if alive then Append(~Slocal,i); end if;
  end if;
end for;
printf "LEVEL_PAIR=[{e3},{e7}]\n"; printf "LEVEL_NORM=%o\n",27^{e3}*7^{e7};
printf "SPACE_DIMENSION=%o\n",Dimension(M); printf "PACKET_COUNT=%o\n",#decomp;
printf "PACKET_DIMS=%o\n",Dims; printf "NORM8_SURVIVORS=%o\n",S8; printf "LOCAL_SURVIVORS=%o\n",Slocal;
'''
    return PREFIX+data+suffix

def parse_list(text:str,marker:str)->list[int]:
    match=re.search(rf'{marker}=\[\s*([^\]]*)\]',text)
    if match is None: raise ResearchError(f'output lacked {marker}')
    body=match.group(1).strip(); return [] if not body else [int(value.strip()) for value in body.split(',')]

def parse_int(text:str,marker:str)->int:
    match=re.search(rf'{marker}=(\d+)',text)
    if match is None: raise ResearchError(f'output lacked {marker}')
    return int(match.group(1))

def main()->int:
    parser=argparse.ArgumentParser(); parser.add_argument('--local-data',type=pathlib.Path,required=True); args=parser.parse_args()
    local=json.loads(args.local_data.read_text()); rows=candidate_rows(local); outputs=[]
    for e3,e7 in LEVEL_PAIRS:
        code=make_code(e3,e7,rows); record={'level_exponents':[e3,e7],'level_norm':27**e3*7**e7,'input_bytes':len(code.encode())}
        try:
            text=submit(code); record.update({'status':'completed','space_dimension':parse_int(text,'SPACE_DIMENSION'),'packet_count':parse_int(text,'PACKET_COUNT'),'packet_dimensions':parse_list(text,'PACKET_DIMS'),'norm8_survivors':parse_list(text,'NORM8_SURVIVORS'),'local_survivors':parse_list(text,'LOCAL_SURVIVORS'),'output_tail':text[-1000:]})
        except Exception as exc: record.update({'status':'failed','error':f'{type(exc).__name__}: {exc}'})
        outputs.append(record)
    body={'schema_version':1,'status':'public-Magma mod-5 high-level packet enumeration and marginal local filter','calculator':CALCULATOR_URL,'field':'K7=Q(zeta_7)^+','source_local_data_sha256':local['certificate_sha256'],'levels':outputs,'nonclaim':'failed levels are unresolved; the marginal local filter is necessary but not sufficient for a solution'}
    result=dict(body); result['certificate_sha256']=canonical_sha256(body); print(json.dumps(result,sort_keys=True,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
