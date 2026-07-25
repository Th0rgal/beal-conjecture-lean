#!/usr/bin/env python3
"""Inspect assigned ModFrmHil attributes for an independently computed newspace."""
from __future__ import annotations

import hashlib
import html
import http.cookiejar
import json
import re
import urllib.parse
import urllib.request
from typing import Any

URL = "https://magma.maths.usyd.edu.au/calc/"
UA = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


def digest(v: Any) -> str:
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def submit(code: str) -> str:
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with op.open(urllib.request.Request(URL, headers={"User-Agent": UA}), timeout=120) as r:
        page = r.read().decode(errors="replace"); referer = r.geturl()
    form = re.search(r"<form\b([^>]*)>(.*?)</form>", page, re.I | re.S)
    if form is None: raise RuntimeError("no form")
    attrs, body = form.groups()
    m = re.search(r"\baction=[\"']([^\"']*)", attrs, re.I)
    action = URL if m is None else urllib.parse.urljoin(URL, html.unescape(m.group(1)))
    hidden: dict[str,str] = {}
    for tag in re.findall(r"<input\b[^>]*>", body, re.I):
        tm=re.search(r"\btype=[\"']([^\"']*)",tag,re.I); nm=re.search(r"\bname=[\"']([^\"']*)",tag,re.I); vm=re.search(r"\bvalue=[\"']([^\"']*)",tag,re.I)
        if tm and tm.group(1).lower()=="hidden" and nm: hidden[html.unescape(nm.group(1))]="" if vm is None else html.unescape(vm.group(1))
    hidden["input"] = code
    parsed=urllib.parse.urlparse(action)
    req=urllib.request.Request(action,data=urllib.parse.urlencode(hidden).encode(),headers={"User-Agent":UA,"Content-Type":"application/x-www-form-urlencoded","Referer":referer,"Origin":f"{parsed.scheme}://{parsed.netloc}"})
    with op.open(req,timeout=300) as r: return html.unescape(re.sub(r"<[^>]+>","",r.read().decode(errors="replace")))


def main() -> int:
    code = r'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
I3:=Factorisation(3*OK)[1][1];
M0:=HilbertCuspForms(K,I3^3); M:=NewSubspace(M0);
printf "DIM=%o\n",Dimension(M);
A:=GetAttributes(ModFrmHil);
printf "ATTRIBUTE_COUNT=%o\n",#A;
for name in A do
  if assigned M``name then
    value:=M``name;
    printf "ASSIGNED|%o|%o",name,Type(value);
    if ISA(Type(value),Mtrx) then printf "|%o|%o",Nrows(value),Ncols(value); end if;
    if ISA(Type(value),ModFrmHil) then printf "|DIM=%o|DEF=%o",Dimension(value),IsDefinite(value); end if;
    printf "\n";
  end if;
end for;
printf "AMBIENT_DIM=%o\n",Dimension(M`Ambient);
printf "AMBIENT_DEFINITE=%o\n",IsDefinite(M`Ambient);
'''
    body: dict[str,Any]={"schema_version":1,"status":"ModFrmHil assigned-attribute inventory"}; out=""
    try:
        out=submit(code)
        if "AMBIENT_DIM=" not in out: raise RuntimeError("inventory incomplete")
        body.update({"request_status":"completed","output_tail":out[-12000:]})
    except Exception as exc:
        body.update({"request_status":"failed","error":f"{type(exc).__name__}: {exc}","output_tail":out[-15000:]})
    result=dict(body); result["certificate_sha256"]=digest(body); print(json.dumps(result,sort_keys=True,indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())
