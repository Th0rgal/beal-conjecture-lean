#!/usr/bin/env python3
"""Run the extended paired split-prime chain for signature (3,5,11)."""
from __future__ import annotations

import run_signature_3511_magma_fixed11_split_pair_chain as base

base.PRIMES = [19, 29, 31, 41, 59, 61, 71, 79, 89, 101, 109, 131]

if __name__ == "__main__":
    raise SystemExit(base.main())
