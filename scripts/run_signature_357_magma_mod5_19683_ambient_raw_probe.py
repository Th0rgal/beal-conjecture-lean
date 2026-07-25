#!/usr/bin/env python3
"""Inspect ambient raw Hecke matrices and stored degeneracy maps at level 19683.

Magma constructs the independent newspace lazily.  This probe first forces
``Dimension(M)`` so the ``Ambient``, ``DegDown1`` and ``DegDownp`` attributes
are assigned, then inspects their dimensions and asks for the raw norm-8
Hecke matrix on the 244-dimensional indefinite ambient module.
"""
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


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def submit(code: str) -> str:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(URL, headers={"User-Agent": UA}), timeout=120
    ) as response:
        page = response.read().decode(errors="replace")
        referer = response.geturl()
    form = re.search(r"<form\b([^>]*)>(.*?)</form>", page, re.I | re.S)
    if form is None:
        raise RuntimeError("calculator page contains no form")
    attributes, body = form.groups()
    match = re.search(r"\baction=[\"']([^\"']*)", attributes, re.I)
    action = URL if match is None else urllib.parse.urljoin(
        URL, html.unescape(match.group(1))
    )
    hidden: dict[str, str] = {}
    for tag in re.findall(r"<input\b[^>]*>", body, re.I):
        type_match = re.search(r"\btype=[\"']([^\"']*)", tag, re.I)
        name_match = re.search(r"\bname=[\"']([^\"']*)", tag, re.I)
        value_match = re.search(r"\bvalue=[\"']([^\"']*)", tag, re.I)
        if type_match and type_match.group(1).lower() == "hidden" and name_match:
            hidden[html.unescape(name_match.group(1))] = (
                "" if value_match is None else html.unescape(value_match.group(1))
            )
    hidden["input"] = code
    parsed = urllib.parse.urlparse(action)
    request = urllib.request.Request(
        action,
        data=urllib.parse.urlencode(hidden).encode(),
        headers={
            "User-Agent": UA,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": referer,
            "Origin": f"{parsed.scheme}://{parsed.netloc}",
        },
    )
    with opener.open(request, timeout=300) as response:
        return html.unescape(
            re.sub(r"<[^>]+>", "", response.read().decode(errors="replace"))
        )


def main() -> int:
    code = r'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
I3:=Factorisation(3*OK)[1][1]; I2:=Factorisation(2*OK)[1][1];
M0:=HilbertCuspForms(K,I3^3); M:=NewSubspace(M0);
d:=Dimension(M);
printf "NEW_DIM=%o\n",d;
printf "HAS_AMBIENT=%o\n",assigned M`Ambient;
printf "HAS_DEGDOWN1=%o\n",assigned M`DegDown1;
printf "HAS_DEGDOWNP=%o\n",assigned M`DegDownp;
A:=M`Ambient;
printf "AMBIENT_DIM=%o\n",Dimension(A);
printf "AMBIENT_DEFINITE=%o\n",IsDefinite(A);
for name in ["DegDown1","DegDownp"] do
  assoc:=M``name;
  keys:=Keys(assoc);
  printf "ASSOC|%o|COUNT=%o\n",name,#keys;
  for key in keys do
    value:=assoc[key];
    printf "ENTRY|%o|KEY=%o|TYPE=%o",name,key,Type(value);
    if ISA(Type(value),Mtrx) then
      printf "|ROWS=%o|COLS=%o",Nrows(value),Ncols(value);
    elif ISA(Type(value),Map) then
      printf "|DOMAIN_TYPE=%o|CODOMAIN_TYPE=%o",Type(Domain(value)),Type(Codomain(value));
    end if;
    printf "\n";
  end for;
end for;
printf "PHASE=ambient-raw-start\n";
Raw:=HeckeMatrixRaw(A,I2);
printf "AMBIENT_RAW_ROWS=%o\n",Nrows(Raw);
printf "AMBIENT_RAW_COLS=%o\n",Ncols(Raw);
printf "AMBIENT_RAW_RING=%o\n",BaseRing(Raw);
'''
    body: dict[str, Any] = {
        "schema_version": 2,
        "status": "level-19683 forced ambient raw and degeneracy-map probe",
    }
    output = ""
    try:
        output = submit(code)
        if "AMBIENT_RAW_ROWS=" not in output:
            raise RuntimeError("ambient raw probe incomplete")
        body.update({
            "request_status": "completed",
            "output_tail": output[-12000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-16000:],
        })
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
