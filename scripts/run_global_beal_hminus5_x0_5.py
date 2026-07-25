#!/usr/bin/env python3
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
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def metadata(page: str) -> tuple[str, dict[str, str]]:
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
    return action, hidden


def submit(code: str) -> str:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(URL, headers={"User-Agent": UA}), timeout=120
    ) as response:
        page = response.read().decode(errors="replace")
        referer = response.geturl()
    action, hidden = metadata(page)
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
    with opener.open(request, timeout=600) as response:
        return html.unescape(
            re.sub(r"<[^>]+>", "", response.read().decode(errors="replace"))
        )


def magma_code() -> str:
    return r'''
Q<u>:=PolynomialRing(Rationals());
f:=(u^2+10*u+5)*(u^2+22*u+125);
C:=HyperellipticCurve(f);
P:=C![0,25,1];
printf "GENUS=%o\n",Genus(C);
printf "POINT_NONSINGULAR=%o\n",IsNonsingular(P);
E,phi:=EllipticCurve(C,P);
printf "ELLIPTIC=%o\n",E;
Emin,iso:=MinimalModel(E);
printf "MINIMAL=%o\n",Emin;
printf "AINVARIANTS=%o\n",aInvariants(Emin);
printf "CONDUCTOR=%o\n",Conductor(Emin);
printf "DISCRIMINANT=%o\n",Discriminant(Emin);
printf "JINVARIANT=%o\n",jInvariant(Emin);
printf "RANK_BOUNDS=%o\n",RankBounds(Emin);
T,tmap:=TorsionSubgroup(Emin);
printf "TORSION=%o\n",T;
printf "TORSION_ORDER=%o\n",#T;
for g in T do
  Qpt:=tmap(g);
  printf "TORSION_POINT|%o|%o\n",g,Qpt;
end for;
printf "MAP_POINT=%o\n",phi(P);
'''


def main() -> int:
    source = magma_code()
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "X0(5) intersection for Hminus modularity at fixed exponent 5",
        "curve": "Y^2=(u^2+10u+5)(u^2+22u+125)",
        "identity": (
            "(u^2+10u+5)^3-1728*u="
            "(u^2+4*u-1)^2*(u^2+22*u+125)"
        ),
        "input_bytes": len(source.encode()),
        "nonclaim": (
            "This computes the genus-one intersection and its Mordell-Weil data. "
            "A failed request or positive rank proves no modularity statement."
        ),
    }
    output = ""
    try:
        output = submit(source)
        body.update({"request_status": "completed", "output_tail": output[-16000:]})
    except Exception as exc:
        body.update(
            {
                "request_status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "output_tail": output[-20000:],
            }
        )
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
