import Mathlib

set_option linter.style.header false

/-!
# Signature `(4,5,7)` unit-group identities

These are the abstract commutative-group identities behind the full-modulus
power-residue conditions for a hypothetical primitive equation
`A^4 + B^5 = C^7`. They make no nonexistence or Beal claim.
-/

namespace BealUnified.Research

/-- If `A^4=C^(4k+1)`, then `A/C^k` is a fourth root of `C`. -/
theorem oneFour_fourth_root_case_one
    {G : Type*} [CommGroup G] (A C : G) (k : ℕ)
    (h : A ^ 4 = C ^ (4 * k + 1)) :
    (A * (C ^ k)⁻¹) ^ 4 = C := by
  calc
    (A * (C ^ k)⁻¹) ^ 4 = A ^ 4 * (C ^ (4 * k))⁻¹ := by group
    _ = C ^ (4 * k + 1) * (C ^ (4 * k))⁻¹ := by rw [h]
    _ = C := by group

/-- If `A^4=C^(4k+3)`, then `C^(k+1)/A` is a fourth root of `C`. -/
theorem oneFour_fourth_root_case_three
    {G : Type*} [CommGroup G] (A C : G) (k : ℕ)
    (h : A ^ 4 = C ^ (4 * k + 3)) :
    (C ^ (k + 1) * A⁻¹) ^ 4 = C := by
  calc
    (C ^ (k + 1) * A⁻¹) ^ 4 = C ^ (4 * k + 4) * (A ^ 4)⁻¹ := by group
    _ = C ^ (4 * k + 4) * (C ^ (4 * k + 3))⁻¹ := by rw [h]
    _ = C := by group

/-- If `A^4=C^7`, then `C^2/A` is a fourth root of `C`. -/
theorem signature457_fourth_root_of_C
    {G : Type*} [CommGroup G] (A C : G)
    (h : A ^ 4 = C ^ 7) :
    (C ^ 2 * A⁻¹) ^ 4 = C := by
  calc
    (C ^ 2 * A⁻¹) ^ 4 = C ^ 8 * (A ^ 4)⁻¹ := by group
    _ = C ^ 8 * (C ^ 7)⁻¹ := by rw [h]
    _ = C := by group

/--
If `s^4=1` and `A^4=s*B^5`, then `s*A/B` is a fourth root of `s*B`.
For the arithmetic application `s=-1`.
-/
theorem signature457_fourth_root_of_signed_B
    {G : Type*} [CommGroup G] (s A B : G)
    (hs : s ^ 4 = 1)
    (h : A ^ 4 = s * B ^ 5) :
    (s * A * B⁻¹) ^ 4 = s * B := by
  calc
    (s * A * B⁻¹) ^ 4 = s ^ 4 * A ^ 4 * (B ^ 4)⁻¹ := by group
    _ = A ^ 4 * (B ^ 4)⁻¹ := by rw [hs]; group
    _ = (s * B ^ 5) * (B ^ 4)⁻¹ := by rw [h]
    _ = s * B := by group

/-- If `B^5=C^7`, then `B^3/C^4` has seventh power `B`. -/
theorem signature457_common_parameter_seventh
    {G : Type*} [CommGroup G] (B C : G)
    (h : B ^ 5 = C ^ 7) :
    (B ^ 3 * (C ^ 4)⁻¹) ^ 7 = B := by
  calc
    (B ^ 3 * (C ^ 4)⁻¹) ^ 7 =
        B * (B ^ 5) ^ 4 * ((C ^ 7) ^ 4)⁻¹ := by group
    _ = B := by rw [h]; group

/-- If `B^5=C^7`, then the same parameter `B^3/C^4` has fifth power `C`. -/
theorem signature457_common_parameter_fifth
    {G : Type*} [CommGroup G] (B C : G)
    (h : B ^ 5 = C ^ 7) :
    (B ^ 3 * (C ^ 4)⁻¹) ^ 5 = C := by
  calc
    (B ^ 3 * (C ^ 4)⁻¹) ^ 5 =
        C * (B ^ 5) ^ 3 * ((C ^ 7) ^ 3)⁻¹ := by group
    _ = C := by rw [h]; group

end BealUnified.Research
