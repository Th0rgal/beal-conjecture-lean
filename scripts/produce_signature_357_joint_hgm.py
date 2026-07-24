#!/usr/bin/env python3
"""Compute coupled HGM trace polynomials for the two-Frey (3,5,7) program.

For a local parameter u=C^7/A^3, the two Frey parameters satisfy

    t_5 = u,      t_7 = 1-u.

The pinned Pacetti--Villagra GP implementation computes the weight-two trace of
the fixed-7 motive with parameters (1/5,-1/5),(1/3,-1/3).  The same finite-HGM
routine computes the independent mod-5 motive with parameters
(1/7,-1/7),(1/3,-1/3).  This producer retains the parameter labels instead of
collapsing them into marginal candidate sets.

PARI/GP is an external producer.  The output consists only of integer trace
polynomials and finite parameter labels; a separate standard-library checker
performs all reductions and pair eliminations.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request
from typing import Any

SOURCE_URL = (
    "https://raw.githubusercontent.com/lucasvillagra/GFE-5p3/"
    "e88f914c577ab6cf9a45e5cdd82c1993477fb423/Codes/GPcode.gp"
)
EXPECTED_GIT_BLOB = "d829dbdfd5b710b2164f74ee5e1c1f92adae58d2"
PRIMES = [13, 29, 41]
USER_AGENT = (
    "beal-conjecture-lean-research/1.0 "
    "(+https://github.com/Th0rgal/beal-conjecture-lean)"
)


class ProducerError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def fetch_source() -> str:
    request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
    actual = git_blob_sha1(data)
    if actual != EXPECTED_GIT_BLOB:
        raise ProducerError(
            f"GP source blob mismatch: expected {EXPECTED_GIT_BLOB}, got {actual}"
        )
    return data.decode("utf-8")


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def gp_driver() -> str:
    primes = ",".join(str(prime) for prime in PRIMES)
    return rf'''
default(parisizemax,2G);
K5=nfinit(x^2-5);
K7=nfinit(x^3-x^2-2*x+1);
P=[{primes}];
for(ii=1,#P,
  ell=P[ii];
  f5=idealprimedec(K5,ell)[1][4];
  f7=idealprimedec(K7,ell)[1][4];
  for(u=2,ell-1,
    t7=(1-u)%ell;
    if(t7==0,t7=ell);
    A7=algdep(ell^f5*hgm(t7,[1/5,-1/5],[1/3,-1/3],ell,f5),2);
    A7=A7/content(A7);
    A5=algdep(ell^f7*hgm(u,[1/7,-1/7],[1/3,-1/3],ell,f7),3);
    A5=A5/content(A5);
    print("JOINT|",ell,"|",u,"|",t7,"|",f5,"|",f7,"|",A7,"|",A5)
  )
);
quit;
'''


def main() -> int:
    source = fetch_source()
    with tempfile.TemporaryDirectory() as directory:
        script = pathlib.Path(directory) / "joint.gp"
        script.write_text(source + "\n" + gp_driver(), encoding="utf-8")
        process = subprocess.run(
            ["gp", "-q", str(script)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=900,
            check=False,
        )
    if process.returncode:
        raise ProducerError(
            f"PARI/GP exited with {process.returncode}:\n{process.stderr[-8000:]}"
        )

    rows: list[dict[str, Any]] = []
    pattern = re.compile(
        r"^JOINT\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|([^|]+)\|(.+)$"
    )
    for line in process.stdout.splitlines():
        match = pattern.match(line.strip())
        if match is None:
            continue
        ell, u, t7, f5, f7 = (int(match.group(index)) for index in range(1, 6))
        rows.append(
            {
                "prime": ell,
                "u_mod_prime": u,
                "t7_mod_prime": t7,
                "residue_degree_K5": f5,
                "residue_degree_K7": f7,
                "fixed7_trace_polynomial": match.group(6).replace(" ", ""),
                "mod5_trace_polynomial": match.group(7).replace(" ", ""),
            }
        )

    expected_count = sum(prime - 2 for prime in PRIMES)
    if len(rows) != expected_count:
        raise ProducerError(
            f"expected {expected_count} parameter rows, got {len(rows)}; "
            f"GP stderr tail:\n{process.stderr[-4000:]}"
        )
    body = {
        "schema_version": 1,
        "status": "coupled finite-HGM trace-polynomial producer output",
        "source": {
            "repository": "lucasvillagra/GFE-5p3",
            "commit": "e88f914c577ab6cf9a45e5cdd82c1993477fb423",
            "path": "Codes/GPcode.gp",
            "git_blob_sha1": EXPECTED_GIT_BLOB,
            "pari_version": subprocess.run(
                ["gp", "--version-short"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                check=False,
            ).stdout.strip(),
        },
        "parameter_identity": "t5=u,t7=1-u",
        "primes": PRIMES,
        "row_count": len(rows),
        "rows": rows,
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_digest(body)
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
