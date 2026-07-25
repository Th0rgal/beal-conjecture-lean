#!/usr/bin/env python3
"""Produce mod-5 HGM zero traces at 19, 71, 79, 89 and 131.

The strengthened fixed-7 ray-character sieve forces 19*71*79*89*131 to divide C
in the Dahmen--Siksek even branch. For u=C^7/A^3 this means u=0 at all five
primes. Only the zero-specialization trace polynomials are needed.

PARI/GP is an external research producer. A downstream Magma computation uses
these polynomials as necessary conditions; the source theorem forcing the prime
divisors remains an explicit research dependency.
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
PRIMES = [19, 71, 79, 89, 131]


class ProducerError(RuntimeError):
    pass


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fetch_source() -> str:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "beal-conjecture-lean-research/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
    if git_blob_sha1(data) != EXPECTED_GIT_BLOB:
        raise ProducerError("GP source blob mismatch")
    return data.decode("utf-8")


def driver() -> str:
    primes = ",".join(map(str, PRIMES))
    return rf'''
default(parisizemax,2000000000);
K7=nfinit(x^3-x^2-2*x+1);
F21=nfinit(polcyclo(21));
P=[{primes}];
NormPoly(A)=A/content(A);
EmitPrime(p0)=
{{
  local(fK,fF,g,A,i);
  fK=idealprimedec(K7,p0)[1][4];
  fF=idealprimedec(F21,p0)[1][4];
  print("META|",p0,"|",fK,"|",fF);
  g=lift(znprimroot(p0));
  for(i=1,7,
    A=algdep(Jacobi2(1/3,-1/3,1/7,-1/7,g^i,p0,fF),3);
    A=NormPoly(A);
    print("ZERO|",p0,"|",i,"|",A)
  );
}};
for(ii=1,#P,EmitPrime(P[ii]));
quit;
'''


def main() -> int:
    source = fetch_source()
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / "forced-zero.gp"
        path.write_text(source + "\n" + driver(), encoding="utf-8")
        process = subprocess.run(
            ["gp", "-q", str(path)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1800,
            check=False,
        )
    if process.returncode:
        raise ProducerError(process.stderr[-8000:])

    metadata: dict[str, dict[str, int]] = {}
    rows: list[dict[str, Any]] = []
    meta = re.compile(r"^META\|(\d+)\|(\d+)\|(\d+)$")
    zero = re.compile(r"^ZERO\|(\d+)\|(\d+)\|(.+)$")
    for raw in process.stdout.splitlines():
        line = raw.strip()
        match = meta.match(line)
        if match:
            prime, degree_k, degree_f = map(int, match.groups())
            metadata[str(prime)] = {
                "residue_degree_K7": degree_k,
                "residue_degree_F21": degree_f,
                "extension_residue_degree": degree_f // degree_k,
            }
            continue
        match = zero.match(line)
        if match:
            prime, index, polynomial = match.groups()
            rows.append(
                {
                    "prime": int(prime),
                    "parameter_index": int(index),
                    "trace_polynomial": polynomial.replace(" ", ""),
                }
            )
    if sorted(map(int, metadata)) != PRIMES or len(rows) != 7 * len(PRIMES):
        raise ProducerError(
            f"incomplete forced-zero output: metadata={metadata}, rows={len(rows)}"
        )

    body = {
        "schema_version": 2,
        "status": "even-branch strengthened forced-zero mod-5 HGM producer output",
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
        "fixed7_reducibility_input": {
            "manifest": "Research/Signature357/fixed7_global_reducibility_sieve.json",
            "manifest_sha256": "d09fafd74cb4513067372721b15327e23d386e26a87933fee744240458cdd46d",
            "conclusion": "19*71*79*89*131 divides C in the even branch",
        },
        "motive": "H((1/7,-1/7),(1/3,-1/3)|u)",
        "parameter": "u=C^7/A^3",
        "primes": PRIMES,
        "residue_metadata": metadata,
        "zero_rows": rows,
    }
    result = dict(body)
    result["certificate_sha256"] = canonical_sha256(body)
    json.dump(result, sys.stdout, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
