#!/usr/bin/env python3
"""Produce complete local mod-5 HGM trace data for signature (3,5,7).

For the independent plus-HGM over K7=Q(zeta_7)^+, a solution has parameter

    u = C^7/A^3.

At an auxiliary prime ell there are four reduction regimes: generic
u not in {0,1}, u=0, u=1, and u=infinity.  The existing joint producer records
only the generic K7 traces.  This producer computes the generic, zero, and
infinity traces over the full cyclotomic field F=Q(zeta_21), exactly as in the
published Pacetti--Villagra Torcomian elimination.  The u=1 case is represented
by the standard multiplicative target +/- (N+1) over K7.

PARI/GP is an external research producer.  The output contains only integer
trace polynomials and exact residue-degree metadata; a separate standard-library
checker must perform all reductions and elimination claims.
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
PRIMES = [13, 29, 41, 43]
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
K7=nfinit(x^3-x^2-2*x+1);
F21=nfinit(polcyclo(21));
P=[{primes}];

NormPoly(A)=A/content(A);

EmitPrime(p0)=
{{
  local(fK,fF,g,u,A,i);
  fK=idealprimedec(K7,p0)[1][4];
  fF=idealprimedec(F21,p0)[1][4];
  print("META|",p0,"|",fK,"|",fF);

  for(u=2,p0-1,
    A=algdep(p0^fF*hgm(lift(1/Mod(u,p0)),[1/7,-1/7],[1/3,-1/3],p0,fF),3);
    A=NormPoly(A);
    print("GENERIC|",p0,"|",u,"|",A)
  );

  g=lift(znprimroot(p0));
  for(i=1,7,
    A=algdep(Jacobi2(1/3,-1/3,1/7,-1/7,g^i,p0,fF),3);
    A=NormPoly(A);
    print("ZERO|",p0,"|",i,"|",A)
  );

  for(i=1,3,
    A=algdep(Jacobi3(1/3,-1/3,1/7,-1/7,g^i,p0,fF),3);
    A=NormPoly(A);
    print("INFINITY|",p0,"|",i,"|",A)
  );
}};

for(ii=1,#P,EmitPrime(P[ii]));
quit;
'''


def main() -> int:
    source = fetch_source()
    with tempfile.TemporaryDirectory() as directory:
        script = pathlib.Path(directory) / "mod5-complete-local.gp"
        script.write_text(source + "\n" + gp_driver(), encoding="utf-8")
        process = subprocess.run(
            ["gp", "-q", str(script)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1200,
            check=False,
        )
    if process.returncode:
        raise ProducerError(
            f"PARI/GP exited with {process.returncode}:\n{process.stderr[-8000:]}"
        )

    metadata: dict[int, dict[str, int]] = {}
    generic: list[dict[str, Any]] = []
    zero: list[dict[str, Any]] = []
    infinity: list[dict[str, Any]] = []

    meta_pattern = re.compile(r"^META\|(\d+)\|(\d+)\|(\d+)$")
    row_pattern = re.compile(r"^(GENERIC|ZERO|INFINITY)\|(\d+)\|(\d+)\|(.+)$")
    for raw_line in process.stdout.splitlines():
        line = raw_line.strip()
        match = meta_pattern.match(line)
        if match is not None:
            prime, degree_k, degree_f = map(int, match.groups())
            metadata[prime] = {
                "residue_degree_K7": degree_k,
                "residue_degree_F21": degree_f,
                "extension_residue_degree": degree_f // degree_k,
            }
            continue
        match = row_pattern.match(line)
        if match is None:
            continue
        kind, raw_prime, raw_parameter, polynomial = match.groups()
        record = {
            "prime": int(raw_prime),
            "parameter_index": int(raw_parameter),
            "trace_polynomial": polynomial.replace(" ", ""),
        }
        if kind == "GENERIC":
            generic.append(record)
        elif kind == "ZERO":
            zero.append(record)
        else:
            infinity.append(record)

    if sorted(metadata) != PRIMES:
        raise ProducerError(f"missing residue metadata: {metadata}")
    for prime in PRIMES:
        degrees = metadata[prime]
        if degrees["residue_degree_F21"] % degrees["residue_degree_K7"]:
            raise ProducerError(f"nonintegral residue-degree ratio at {prime}")
    expected_generic = sum(prime - 2 for prime in PRIMES)
    if len(generic) != expected_generic:
        raise ProducerError(
            f"expected {expected_generic} generic rows, got {len(generic)}; "
            f"stdout tail:\n{process.stdout[-4000:]}\n"
            f"stderr tail:\n{process.stderr[-4000:]}"
        )
    if len(zero) != 7 * len(PRIMES) or len(infinity) != 3 * len(PRIMES):
        raise ProducerError(
            f"unexpected degenerate row counts: zero={len(zero)}, "
            f"infinity={len(infinity)}"
        )

    body = {
        "schema_version": 1,
        "status": "complete local mod-5 HGM trace-polynomial producer output",
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
        "motive": "H((1/7,-1/7),(1/3,-1/3)|u)",
        "parameter": "u=C^7/A^3",
        "base_field": "K7=Q(zeta_7)^+",
        "full_cyclotomic_field": "F21=Q(zeta_21)",
        "primes": PRIMES,
        "residue_metadata": {str(key): value for key, value in metadata.items()},
        "generic_rows": generic,
        "zero_rows": zero,
        "infinity_rows": infinity,
        "multiplicative_rule": "at u=1 compare the K7 trace with +/- (N(P)+1)",
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_digest(body)
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
