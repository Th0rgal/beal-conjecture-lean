#!/usr/bin/env python3
"""Produce complete mod-5 HGM local trace data at inert, twist-trivial primes.

The rational primes 11 and 23 are inert in K7=Q(zeta_7)^+ and split in the
quadratic extension Q(zeta_7)/K7 used for the odd-branch cyclotomic untwist.
Thus the twisted residual trace equals the original HGM trace and, by the
semilinear Galois symmetry, lies in F5.

This wrapper reuses the pinned complete-local producer with exactly these two
primes. PARI/GP remains an external producer; downstream Magma jobs perform the
residual polynomial test.
"""
from __future__ import annotations

import produce_signature_357_mod5_complete_local as base


base.PRIMES = [11, 23]


if __name__ == "__main__":
    raise SystemExit(base.main())
