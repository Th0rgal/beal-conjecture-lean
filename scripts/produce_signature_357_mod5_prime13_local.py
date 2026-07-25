#!/usr/bin/env python3
"""Produce only the complete mod-5 local HGM data at the split prime 13."""
from __future__ import annotations

import produce_signature_357_mod5_complete_local as base

base.PRIMES = [13]

if __name__ == "__main__":
    raise SystemExit(base.main())
