#!/usr/bin/env python3
"""Extend the fixed-11 residual chain with additional auxiliary primes.

The first five-prime chain leaves dimensions 9, 50 and 84 at levels (2,2),
(2,3) and (3,2).  This wrapper reuses the guarded producer but enlarges the
ordered prime set.  A request failure or positive final dimension remains an
explicit unresolved result.
"""
from __future__ import annotations

import run_signature_3511_magma_fixed11_chain as base

# Keep the inexpensive first-stage primes first, then add independent rows from
# the same pinned Pacetti--Villagra candidate table.  Early zero exits avoid
# constructing unnecessary Hecke operators.
base.PRIMES = [13, 17, 19, 31, 41, 29, 59, 61, 71, 79, 89, 101, 109, 131]

if __name__ == "__main__":
    raise SystemExit(base.main())
