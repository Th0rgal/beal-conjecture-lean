#!/usr/bin/env python3
"""Inspect ModFrmHil Hecke caches after the level-19683 T2 memory failure."""
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
SetStoreModularForms(K,false);
I3:=Factorisation(3*OK)[1][1]; I2:=Factorisation(2*OK)[1][1];
M0:=HilbertCuspForms(K,I3^3); M:=NewSubspace(M0);
printf "NEW_DIM=%o\n",Dimension(M);
printf "PHASE=T2-attempt\n";
try
  TQ:=HeckeOperator(M,I2);
  printf "T2_RETURNED=true\n";
  printf "T2_ROWS=%o\n",Nrows(TQ);
catch e
  printf "T2_RETURNED=false\n";
  printf "T2_ERROR_TYPE=%o\n",e`Type;
  printf "T2_ERROR_OBJECT=%o\n",e`Object;
end try;
for name in ["Hecke","HeckeBig","HeckeBigColumns","HeckeCharPoly"] do
  assoc:=M``name;
  keys:=Keys(assoc);
  printf "CACHE|%o|COUNT=%o\n",name,#keys;
  for key in keys do
    value:=assoc[key];
    printf "CACHE_ENTRY|%o|KEY=%o|TYPE=%o",name,key,Type(value);
    if ISA(Type(value),Mtrx) then
      printf "|ROWS=%o|COLS=%o|RING=%o",Nrows(value),Ncols(value),BaseRing(value);
    elif Type(value) eq SeqEnum then
      printf "|LENGTH=%o",#value;
      if #value gt 0 then printf "|ELEMENT_TYPE=%o",Type(value[1]); end if;
    elif ISA(Type(value),RngUPolElt) then
      printf "|DEGREE=%o",Degree(value);
    end if;
    printf "\n";
  end for;
end for;
printf "DONE=true\n";
'''
    body: dict[str, Any] = {
        "schema_version": 2,
        "status": "level-19683 post-failure Hecke cache inventory",
    }
    output = ""
    try:
        output = submit(code)
        if "DONE=true" not in output:
            raise RuntimeError("cache inventory did not finish")
        body.update({
            "request_status": "completed",
            "output_tail": output[-18000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-22000:],
        })
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
