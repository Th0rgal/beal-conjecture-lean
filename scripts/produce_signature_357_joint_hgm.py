#!/usr/bin/env python3
"""Compute correctly labelled coupled HGM traces for the two-Frey (3,5,7) program.

The mathematical specialization parameters are

    u = C^7/A^3,      v = -B^5/A^3,      u + v = 1.

The pinned PARI/GP routine ``hgm(z, ...)`` uses the reciprocal finite-HGM
coordinate: its argument is ``z=t_0^(-1)``.  This convention is anchored by
Pacetti--Villagra Torcomian, Table 7.1: at the mathematical specialization
``t_0=3`` and the prime over 29, the RM trace polynomial is ``x^2-2*x-44``;
the pinned routine returns that polynomial at ``z=10=3^(-1) mod 29``, not at
``z=3``.

Consequently this producer evaluates

    z5 = u^(-1),      z7 = v^(-1),

so that ``(z5-1)*(z7-1)=1``.  It retains both the mathematical parameters and
the implementation arguments.  PARI/GP is only the external producer; the
output contains integer polynomials and finite parameter labels for replay by
standard-library checkers.
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
PARAMETER_CONVENTION_SHA256 = "c32eb5bb8c060dc6c3625011aa073a0b7f081ad57d2aa51a58daa1abed4df141"
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
default(parisizemax,2000000000);
K5=nfinit(x^2-5);
K7=nfinit(x^3-x^2-2*x+1);
P=[{primes}];

EmitRow(p0,u,f5,f7)=
{{
  local(v,z5,z7,A7,A5);
  v=lift(Mod(1-u,p0));
  z5=lift(1/Mod(u,p0));
  z7=lift(1/Mod(v,p0));
  A7=algdep(p0^f5*hgm(z7,[1/5,-1/5],[1/3,-1/3],p0,f5),2);
  A7=A7/content(A7);
  A5=algdep(p0^f7*hgm(z5,[1/7,-1/7],[1/3,-1/3],p0,f7),3);
  A5=A5/content(A5);
  print("JOINT|",p0,"|",u,"|",v,"|",z5,"|",z7,"|",f5,"|",f7,"|",A7,"|",A5);
}};

EmitPrime(p0)=
{{
  local(f5,f7);
  f5=idealprimedec(K5,p0)[1][4];
  f7=idealprimedec(K7,p0)[1][4];
  for(u=2,p0-1,EmitRow(p0,u,f5,f7));
}};

for(ii=1,#P,EmitPrime(P[ii]));
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
        r"^JOINT\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|([^|]+)\|(.+)$"
    )
    for line in process.stdout.splitlines():
        match = pattern.match(line.strip())
        if match is None:
            continue
        prime, u, v, z5, z7, f5, f7 = (
            int(match.group(index)) for index in range(1, 8)
        )
        if (u + v) % prime != 1:
            raise ProducerError(f"mathematical parameter relation failed at {prime}")
        if (u * z5) % prime != 1 or (v * z7) % prime != 1:
            raise ProducerError(f"reciprocal GP coordinate failed at {prime}")
        if ((z5 - 1) * (z7 - 1)) % prime != 1:
            raise ProducerError(f"GP-coordinate coupling failed at {prime}")
        rows.append(
            {
                "prime": prime,
                "u_mod_prime": u,
                "v_mod_prime": v,
                "gp_argument_mod5": z5,
                "gp_argument_fixed7": z7,
                "residue_degree_K5": f5,
                "residue_degree_K7": f7,
                "fixed7_trace_polynomial": match.group(8).replace(" ", ""),
                "mod5_trace_polynomial": match.group(9).replace(" ", ""),
            }
        )

    expected_count = sum(prime - 2 for prime in PRIMES)
    if len(rows) != expected_count:
        raise ProducerError(
            f"expected {expected_count} parameter rows, got {len(rows)}; "
            f"GP stdout tail:\n{process.stdout[-4000:]}\n"
            f"GP stderr tail:\n{process.stderr[-4000:]}"
        )
    body = {
        "schema_version": 2,
        "status": (
            "coupled finite-HGM trace-polynomial producer output with "
            "source-anchored reciprocal GP coordinates"
        ),
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
        "parameter_convention_certificate": {
            "path": "Research/Signature357/gp_parameter_convention.json",
            "sha256": PARAMETER_CONVENTION_SHA256,
            "conclusion": "GP hgm argument z equals the inverse mathematical parameter",
        },
        "mathematical_parameter_identity": "u=C^7/A^3,v=-B^5/A^3,u+v=1",
        "gp_parameter_identity": (
            "z5=u^(-1),z7=v^(-1),(z5-1)*(z7-1)=1"
        ),
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
