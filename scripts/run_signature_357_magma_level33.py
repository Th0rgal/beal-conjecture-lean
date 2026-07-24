#!/usr/bin/env python3
"""Run a fixed-7 and superspecial replay at conductor exponents (3,3).

The 112-packet space is split both by auxiliary-prime rows and by packet ranges.
Every calculator request still reconstructs the full Hilbert space, but tests only
one packet range against one row batch.  Failed requests remain explicit.
"""
from __future__ import annotations
import hashlib, html, http.cookiejar, json, re, urllib.parse, urllib.request
from typing import Any
DATA_URL=("https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/" "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Outputs/Data.txt")
CALCULATOR_URL="https://magma.maths.usyd.edu.au/calc/"
EXPECTED_DATA_BLOB="9c96357834f2298b4d91ab97812c38e84b8ef7a2"
MAX_INPUT=49000
FORM_RANGES=[(1,32),(33,64),(65,88),(89,112)]
USER_AGENT="Mozilla/5.0 beal-conjecture-lean-research/1.0"
class ResearchError(RuntimeError): pass

def blob(data:bytes)->str: return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()
def digest(value:Any)->str: return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def fetch()->bytes:
    with urllib.request.urlopen(urllib.request.Request(DATA_URL,headers={'User-Agent':USER_AGENT}),timeout=120) as response: return response.read()
def split_rows(data:bytes)->list[tuple[int,str]]:
    if blob(data)!=EXPECTED_DATA_BLOB: raise ResearchError('candidate-data blob mismatch')
    text=data.decode().strip(); inside=text[len('Data:=['):-2]; rows=[]; depth=0; start=0
    for index,char in enumerate(inside):
        if char in '[<': depth+=1
        elif char in ']>': depth-=1
        elif char==',' and depth==0: rows.append(inside[start:index].strip()); start=index+1
    rows.append(inside[start:].strip()); result=[]
    for row in rows:
        match=re.match(r'<(\d+),',row)
        if not match: raise ResearchError('unidentified row')
        result.append((int(match.group(1)),row))
    if len(result)!=37: raise ResearchError(f'expected 37 rows, got {len(result)}')
    return result
PREFIX=r'''
_<x>:=PolynomialRing(Rationals()); K<z>:=NumberField(x^2-5); OK:=Integers(K); I5:=Factorisation(5*OK)[1][1];
F7:=GF(7); R7<X>:=PolynomialRing(F7);
Red:=function(P) return R7![F7!Coefficient(P,i):i in [0..Degree(P)]]; end function;
Common:=function(P,Q) return Degree(GreatestCommonDivisor(Red(P),Red(Q))) gt 0; end function;
AnyCommon:=function(P,L) for Q in L do if Common(P,Q) then return true; end if; end for; return false; end function;
Possible:=function(form,row)
 l:=row[1]; if l eq 7 then return true; end if; I:=Factorisation(l*OK)[1][1]; Eig:=HeckeEigenvalue(form,I); P:=MinimalPolynomial(Eig);
 if AnyCommon(P,row[2]) then return true; end if;
 F:=NumberField(CyclotomicPolynomial(15)); OF:=Integers(F); f1:=InertiaDegree(Factorisation(l*OF)[1][1]); f2:=InertiaDegree(I); E2:=Eig;
 if f1/f2 eq 2 then E2:=Eig^2-2*l^f2; end if; P2:=MinimalPolynomial(E2);
 if AnyCommon(P2,row[3]) or AnyCommon(P2,row[4]) then return true; end if;
 q:=Integers()!Norm(I); if Common(P,x-(q+1)) or Common(P,x+(q+1)) then return true; end if;
 return false;
end function;
'''
def make_code(rows:list[tuple[int,str]],lo:int,hi:int)->str:
    data='Data:=['+','.join(row for _,row in rows)+'];\n'
    return PREFIX+data+rf'''
M:=HilbertCuspForms(K,3^3*I5^3); decomp:=NewformDecomposition(NewSubspace(M)); S:=[];
for i in [{lo}..{hi}] do form:=Eigenform(decomp[i]); alive:=true; for row in Data do if not Possible(form,row) then alive:=false; break; end if; end for; if alive then Append(~S,i); end if; end for;
I7:=Factorisation(7*OK)[1][1]; Ssup:=[]; for i in S do P7:=MinimalPolynomial(HeckeEigenvalue(Eigenform(decomp[i]),I7)); if Common(P7,x) then Append(~Ssup,i); end if; end for;
printf "RANGE=[{lo},{hi}]\n"; printf "PACKET_COUNT=%o\n",#decomp; printf "FIXED7_SURVIVORS=%o\n",S; printf "SUPERSPECIAL_SURVIVORS=%o\n",Ssup;
'''
def batches(rows:list[tuple[int,str]])->list[list[tuple[int,str]]]:
    out=[]; current=[]
    for item in rows:
        proposed=current+[item]
        if len(make_code(proposed,1,1).encode())>MAX_INPUT:
            if not current: raise ResearchError('single candidate row exceeds input limit')
            out.append(current); current=[item]
        else: current=proposed
    if current: out.append(current)
    return out
def form_metadata(page:str)->tuple[str,dict[str,str]]:
    form=re.search(r'<form\b([^>]*)>(.*?)</form>',page,flags=re.I|re.S)
    if not form: raise ResearchError('no calculator form')
    attrs,body=form.groups(); am=re.search(r'\baction=["\']([^"\']*)',attrs,flags=re.I); action=CALCULATOR_URL if not am else urllib.parse.urljoin(CALCULATOR_URL,html.unescape(am.group(1))); hidden={}
    for tag in re.findall(r'<input\b[^>]*>',body,flags=re.I):
        tm=re.search(r'\btype=["\']([^"\']*)',tag,flags=re.I); nm=re.search(r'\bname=["\']([^"\']*)',tag,flags=re.I); vm=re.search(r'\bvalue=["\']([^"\']*)',tag,flags=re.I)
        if tm and tm.group(1).lower()=='hidden' and nm: hidden[html.unescape(nm.group(1))]='' if not vm else html.unescape(vm.group(1))
    return action,hidden
def submit(code:str)->str:
    jar=http.cookiejar.CookieJar(); opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(urllib.request.Request(CALCULATOR_URL,headers={'User-Agent':USER_AGENT}),timeout=120) as response: landing=response.read().decode(errors='replace'); landing_url=response.geturl()
    action,hidden=form_metadata(landing); hidden['input']=code; parsed=urllib.parse.urlparse(action)
    request=urllib.request.Request(action,data=urllib.parse.urlencode(hidden).encode(),headers={'User-Agent':USER_AGENT,'Content-Type':'application/x-www-form-urlencoded','Referer':landing_url,'Origin':f'{parsed.scheme}://{parsed.netloc}'})
    with opener.open(request,timeout=210) as response: page=response.read().decode(errors='replace')
    return html.unescape(re.sub(r'<[^>]+>','',page))
def parse_list(text:str,marker:str)->list[int]:
    match=re.search(rf'{marker}=\[\s*([^\]]*)\]',text)
    if not match: raise ResearchError(f'output lacked {marker}')
    body=match.group(1).strip(); return [] if not body else [int(v.strip()) for v in body.split(',')]
def parse_int(text:str,marker:str)->int:
    match=re.search(rf'{marker}=(\d+)',text)
    if not match: raise ResearchError(f'output lacked {marker}')
    return int(match.group(1))
def main()->int:
    rows=split_rows(fetch()); row_batches=batches(rows); records=[]; completed={}
    for lo,hi in FORM_RANGES:
        completed[(lo,hi)]=[]
        for batch_number,batch in enumerate(row_batches,1):
            code=make_code(batch,lo,hi); record={'form_range':[lo,hi],'batch':batch_number,'auxiliary_primes':[p for p,_ in batch],'input_bytes':len(code.encode())}
            try:
                text=submit(code); count=parse_int(text,'PACKET_COUNT'); survivors=parse_list(text,'FIXED7_SURVIVORS'); superspecial=parse_list(text,'SUPERSPECIAL_SURVIVORS')
                if count!=112: raise ResearchError(f'expected 112 packets, got {count}')
                record.update({'status':'completed','survivors':survivors,'superspecial_survivors':superspecial,'output_tail':text[-800:]}); completed[(lo,hi)].append((set(survivors),set(superspecial)))
            except Exception as exc: record.update({'status':'failed','error':f'{type(exc).__name__}: {exc}'})
            records.append(record)
    fixed=[]; superfixed=[]; complete=True
    for key in FORM_RANGES:
        results=completed[key]
        if len(results)!=len(row_batches): complete=False; continue
        fixed.extend(sorted(set.intersection(*(a for a,_ in results)))); superfixed.extend(sorted(set.intersection(*(b for _,b in results))))
    body={'schema_version':1,'status':'complete' if complete else 'partial','source':{'calculator':CALCULATOR_URL,'candidate_blob':EXPECTED_DATA_BLOB},'level_exponents':[3,3],'packet_count':112,'row_batch_count':len(row_batches),'form_ranges':[list(r) for r in FORM_RANGES],'requests':records,'fixed7_survivors':sorted(fixed),'superspecial_survivors':sorted(superfixed),'nonclaim':'failed requests leave their packet range unresolved'}
    result=dict(body); result['certificate_sha256']=digest(body); print(json.dumps(result,sort_keys=True,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
