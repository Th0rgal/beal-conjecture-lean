#!/usr/bin/env python3
"""Test the two remaining odd-e3=2 modular pairs on an expanded HGM graph.

For each auxiliary prime the request compares packet 1 of the mod-5 level 5103
space with fixed-7 packet 24 or 28 at level (2,3), retaining the exact generic
parameter pairing and all three special graph pairs.  One incompatible prime
eliminates the modular pair without assuming that the prime is outside A*B*C.
"""
from __future__ import annotations
import argparse,hashlib,html,http.cookiejar,json,pathlib,re,urllib.parse,urllib.request
from typing import Any
CALCULATOR_URL='https://magma.maths.usyd.edu.au/calc/'
PACKETS=[24,28]
MAX_INPUT=49000
USER_AGENT='Mozilla/5.0 beal-conjecture-lean-research/1.0'
class ResearchError(RuntimeError):pass

def digest(value:Any)->str:return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def form_metadata(page:str)->tuple[str,dict[str,str]]:
    form=re.search(r'<form\b([^>]*)>(.*?)</form>',page,flags=re.I|re.S)
    if not form:raise ResearchError('calculator page contains no form')
    attrs,body=form.groups();am=re.search(r'\baction=["\']([^"\']*)',attrs,flags=re.I);action=CALCULATOR_URL if not am else urllib.parse.urljoin(CALCULATOR_URL,html.unescape(am.group(1)));hidden={}
    for tag in re.findall(r'<input\b[^>]*>',body,flags=re.I):
        tm=re.search(r'\btype=["\']([^"\']*)',tag,flags=re.I);nm=re.search(r'\bname=["\']([^"\']*)',tag,flags=re.I);vm=re.search(r'\bvalue=["\']([^"\']*)',tag,flags=re.I)
        if tm and tm.group(1).lower()=='hidden' and nm:hidden[html.unescape(nm.group(1))]='' if not vm else html.unescape(vm.group(1))
    return action,hidden
def submit(code:str)->str:
    if len(code.encode())>MAX_INPUT:raise ResearchError(f'generated input has {len(code.encode())} bytes')
    jar=http.cookiejar.CookieJar();opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(urllib.request.Request(CALCULATOR_URL,headers={'User-Agent':USER_AGENT}),timeout=120) as response:landing=response.read().decode(errors='replace');landing_url=response.geturl()
    action,hidden=form_metadata(landing);hidden['input']=code;parsed=urllib.parse.urlparse(action)
    request=urllib.request.Request(action,data=urllib.parse.urlencode(hidden).encode(),headers={'User-Agent':USER_AGENT,'Content-Type':'application/x-www-form-urlencoded','Referer':landing_url,'Origin':f'{parsed.scheme}://{parsed.netloc}'})
    with opener.open(request,timeout=210) as response:page=response.read().decode(errors='replace')
    return html.unescape(re.sub(r'<[^>]+>','',page))
def ml(values:list[str])->str:return '['+','.join(values)+']'
def prime_data(data:dict[str,Any],prime:int)->dict[str,Any]:
    generic=[row for row in data['generic_rows'] if row['prime']==prime]
    result={'prime':prime,'generic':generic}
    for name in ('zero5','infinity5','zero7','infinity7'):result[name]=[row['trace_polynomial'] for row in data[name] if row['prime']==prime]
    if len(generic)!=prime-2:raise ResearchError(f'generic data incomplete at {prime}')
    return result
def code(entry:dict[str,Any])->str:
    prime=entry['prime'];generic='['+','.join(f'<{row["z5"]},{row["z7"]},{row["mod5_trace_polynomial"]},{row["fixed7_trace_polynomial"]}>' for row in entry['generic'])+']'
    return rf'''
_<x>:=PolynomialRing(Rationals());
K7<w>:=NumberField(x^3-x^2-2*x+1); O7:=Integers(K7); I3:=Factorisation(3*O7)[1][1]; I7:=Factorisation(7*O7)[1][1];
K5<s>:=NumberField(x^2-5); O5:=Integers(K5); J5:=Factorisation(5*O5)[1][1];
F21:=NumberField(CyclotomicPolynomial(21)); OF21:=Integers(F21); F15:=NumberField(CyclotomicPolynomial(15)); OF15:=Integers(F15);
F5:=GF(5);R5<X5>:=PolynomialRing(F5);F7:=GF(7);R7<X7>:=PolynomialRing(F7);
Red5:=function(P)return R5![F5!Coefficient(P,j):j in [0..Degree(P)]];end function;Red7:=function(P)return R7![F7!Coefficient(P,j):j in [0..Degree(P)]];end function;
Common5:=function(P,Q)return Degree(GreatestCommonDivisor(Red5(P),Red5(Q))) gt 0;end function;Common7:=function(P,Q)return Degree(GreatestCommonDivisor(Red7(P),Red7(Q))) gt 0;end function;
Any5:=function(P,L)for Q in L do if Common5(P,Q) then return true;end if;end for;return false;end function;Any7:=function(P,L)for Q in L do if Common7(P,Q) then return true;end if;end for;return false;end function;
Generic:={generic};Z5:={ml(entry['zero5'])};Inf5:={ml(entry['infinity5'])};Z7:={ml(entry['zero7'])};Inf7:={ml(entry['infinity7'])};
M5:=HilbertCuspForms(K7,I3^2*I7);D5:=NewformDecomposition(NewSubspace(M5));f5:=Eigenform(D5[1]);
M7:=HilbertCuspForms(K5,3^2*J5^3);D7:=NewformDecomposition(NewSubspace(M7));
ell:={prime};P5ideal:=Factorisation(ell*O7)[1][1];P7ideal:=Factorisation(ell*O5)[1][1];
E5:=HeckeEigenvalue(f5,P5ideal);B5:=MinimalPolynomial(E5);U5:=E5;f5k:=InertiaDegree(P5ideal);f5f:=InertiaDegree(Factorisation(ell*OF21)[1][1]);if f5f/f5k eq 2 then U5:=E5^2-2*ell^f5k;end if;Full5:=MinimalPolynomial(U5);q5:=Integers()!Norm(P5ideal);Mult5:=Common5(B5,x-(q5+1)) or Common5(B5,x+(q5+1));
printf "PRIME=%o\n",ell;
for packet in [24,28] do
 f7:=Eigenform(D7[packet]);E7:=HeckeEigenvalue(f7,P7ideal);B7:=MinimalPolynomial(E7);U7:=E7;f7k:=InertiaDegree(P7ideal);f7f:=InertiaDegree(Factorisation(ell*OF15)[1][1]);if f7f/f7k eq 2 then U7:=E7^2-2*ell^f7k;end if;Full7:=MinimalPolynomial(U7);q7:=Integers()!Norm(P7ideal);Mult7:=Common7(B7,x-(q7+1)) or Common7(B7,x+(q7+1));
 G:=0;for row in Generic do if Common5(B5,row[3]) and Common7(B7,row[4]) then G+:=1;end if;end for;
 ZZ:=Any5(Full5,Z5) and Any7(Full7,Z7);MI:=Mult5 and Any7(Full7,Inf7);IM:=Any5(Full5,Inf5) and Mult7;Alive:=G gt 0 or ZZ or MI or IM;
 printf "PAIR|%o|%o|%o|%o|%o|%o\n",packet,G,Integers()!ZZ,Integers()!MI,Integers()!IM,Integers()!Alive;
end for;
'''
def parse(text:str,prime:int)->list[dict[str,Any]]:
    marker=re.search(r'PRIME=(\d+)',text)
    if not marker or int(marker.group(1))!=prime:raise ResearchError('prime marker missing')
    rows=[]
    for m in re.finditer(r'PAIR\|(24|28)\|(\d+)\|([01])\|([01])\|([01])\|([01])',text):
        packet,g,zz,mi,im,alive=map(int,m.groups());rows.append({'packet':packet,'generic_parameter_count':g,'zero_zero':bool(zz),'multiplicative_infinity':bool(mi),'infinity_multiplicative':bool(im),'compatible':bool(alive)})
    if len(rows)!=2:raise ResearchError(f'expected two pair rows at {prime}')
    return rows
def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument('--joint-data',type=pathlib.Path,required=True);args=parser.parse_args();data=json.loads(args.joint_data.read_text());records=[]
    for prime in data['primes']:
        entry=prime_data(data,prime);source=code(entry);record={'prime':prime,'input_bytes':len(source.encode())}
        try:
            text=submit(source);record.update({'request_status':'completed','pairs':parse(text,prime),'output_tail':text[-1000:]})
        except Exception as exc:record.update({'request_status':'failed','error':f'{type(exc).__name__}: {exc}'})
        records.append(record)
    complete=all(record['request_status']=='completed' for record in records);survivors=[]
    if complete:
        for packet in PACKETS:
            if all(next(row for row in record['pairs'] if row['packet']==packet)['compatible'] for record in records):survivors.append(packet)
    body={'schema_version':1,'status':'complete' if complete else 'partial','calculator':CALCULATOR_URL,'source_joint_sha256':data['certificate_sha256'],'level_pairs':{'mod5':[2,1],'fixed7':[2,3]},'mod5_packet':1,'fixed7_packets':PACKETS,'primes':data['primes'],'records':records,'surviving_modular_pairs':[[1,packet] for packet in survivors] if complete else None,'conclusion':('the odd e3=2 modular-pair frontier is empty' if complete and not survivors else ('some modular pairs survive every tested prime' if complete else 'incomplete public-Magma run')),'nonclaim':'the modularity, packet reductions and exact HGM graph theorem remain imported research inputs'}
    result=dict(body);result['certificate_sha256']=digest(body);print(json.dumps(result,sort_keys=True,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
