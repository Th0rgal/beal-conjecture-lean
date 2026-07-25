#!/usr/bin/env python3
"""Probe Magma's undocumented HeckeMatrixRaw API on a tiny definite HMF space."""
from __future__ import annotations

import hashlib
import html
import http.cookiejar
import json
import re
import urllib.parse
import urllib.request
from typing import Any

CALCULATOR_URL = "https://magma.maths.usyd.edu.au/calc/"
USER_AGENT = "Mozilla/5.0 beal-conjecture-lean-research/1.0"


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def submit(code: str) -> str:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    with opener.open(
        urllib.request.Request(CALCULATOR_URL, headers={"User-Agent": USER_AGENT}), timeout=120
    ) as response:
        landing = response.read().decode(errors="replace")
        landing_url = response.geturl()
    form = re.search(r"<form\b([^>]*)>(.*?)</form>", landing, flags=re.I | re.S)
    if form is None:
        raise RuntimeError("calculator page contains no form")
    attributes, form_body = form.groups()
    action_match = re.search(r"\baction=[\"']([^\"']*)", attributes, flags=re.I)
    action = CALCULATOR_URL if action_match is None else urllib.parse.urljoin(
        CALCULATOR_URL, html.unescape(action_match.group(1))
    )
    hidden: dict[str, str] = {}
    for tag in re.findall(r"<input\b[^>]*>", form_body, flags=re.I):
        tm = re.search(r"\btype=[\"']([^\"']*)", tag, flags=re.I)
        nm = re.search(r"\bname=[\"']([^\"']*)", tag, flags=re.I)
        vm = re.search(r"\bvalue=[\"']([^\"']*)", tag, flags=re.I)
        if tm and tm.group(1).lower() == "hidden" and nm:
            hidden[html.unescape(nm.group(1))] = "" if vm is None else html.unescape(vm.group(1))
    hidden["input"] = code
    parsed = urllib.parse.urlparse(action)
    request = urllib.request.Request(
        action,
        data=urllib.parse.urlencode(hidden).encode(),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": landing_url,
            "Origin": f"{parsed.scheme}://{parsed.netloc}",
        },
    )
    with opener.open(request, timeout=300) as response:
        return html.unescape(re.sub(r"<[^>]+>", "", response.read().decode(errors="replace")))


def main() -> int:
    code = r'''
_<x>:=PolynomialRing(Rationals());
K<w>:=NumberField(x^3-x^2-2*x+1); OK:=Integers(K);
I3:=Factorisation(3*OK)[1][1]; I2:=Factorisation(2*OK)[1][1];
M0:=HilbertCuspForms(K,I3); M:=NewSubspace(M0);
printf "DIM=%o\n",Dimension(M);
printf "IS_DEFINITE=%o\n",IsDefinite(M);
printf "PHASE=raw-start\n";
T:=HeckeMatrixRaw(M,I2);
printf "RAW_ROWS=%o\n",Nrows(T);
printf "RAW_COLS=%o\n",Ncols(T);
printf "RAW_RING=%o\n",BaseRing(T);
printf "RAW_MATRIX=%o\n",T;
'''
    body: dict[str, Any] = {
        "schema_version": 1,
        "status": "Magma HeckeMatrixRaw API probe",
        "calculator": CALCULATOR_URL,
    }
    output = ""
    try:
        output = submit(code)
        match = re.search(r"(?:^|\n)RAW_ROWS=(\d+)(?:\n|$)", output)
        if match is None:
            raise RuntimeError("raw API did not return a matrix")
        body.update({
            "request_status": "completed",
            "raw_rows": int(match.group(1)),
            "output_tail": output[-5000:],
        })
    except Exception as exc:
        body.update({
            "request_status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": output[-8000:],
        })
    result = dict(body)
    result["certificate_sha256"] = digest(body)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
