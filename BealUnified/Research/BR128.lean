import Mathlib.LinearAlgebra.Matrix.Determinant.Basic

set_option linter.style.header false

/-!
# BR-128: presentation-matrix maximal minors

This file records only the direct determinant computation for the integer
presentation matrix with rows `(x, 0, -z)` and `(0, y, -z)`.  It does not
assert a Smith-normal-form classification or any consequence for Beal.
-/

namespace BealUnified.Research

/--
The three `2 × 2` column minors of the presentation matrix
`[[x, 0, -z], [0, y, -z]]` are `x*y`, `-(x*z)`, and `y*z`.

This is the bounded algebraic input for a future Smith-normal-form bridge;
the bridge itself is deliberately outside this declaration.
-/
theorem smithPresentation_maximal_minors (x y z : ℤ) :
    Matrix.det !![x, 0; 0, y] = x * y ∧
      Matrix.det !![x, -z; 0, -z] = -(x * z) ∧
        Matrix.det !![0, -z; y, -z] = y * z := by
  constructor
  · simp [Matrix.det_fin_two]
  constructor
  · simp [Matrix.det_fin_two]
  · simp [Matrix.det_fin_two, mul_comm]

end BealUnified.Research
