import BealUnified.Statement
import BealUnified.FLTReduction
import BealUnified.Parity
import BealUnified.Valuations
import BealUnified.CyclotomicQuotient
import BealUnified.CyclotomicCofactor
import BealUnified.ExponentNormalization
import BealUnified.ModEight
import BealUnified.Research.BR20
import BealUnified.PrimitiveDivisors
import BealUnified.ABC

/-!
# Trusted Beal entrypoint

This module is the supported production import.  Its transitive imports are
checked by `scripts/check_trusted_boundary.py`: they contain no proof
placeholders or declarations depending on nonstandard axioms, and never import the
opt-in `BealUnified.Challenge` namespace.
-/
