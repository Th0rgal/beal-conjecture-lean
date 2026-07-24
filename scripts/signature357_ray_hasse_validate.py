"""Manifest validation for the signature-(3,5,7) ray/Hasse certificate."""
from __future__ import annotations

from signature357_ray_hasse_math import *  # noqa: F401,F403

def validate(data: dict[str, Any]) -> str:
    exact_keys(
        data,
        {
            "schema_version", "status", "equation", "fixed7_system", "source_pins",
            "candidate_product_rows", "ray_class_coordinates",
            "nodal_splitting_character", "ray_sieve_conclusion", "hasse_witt_mod7",
            "imported_lemmas", "conditional_conclusions", "nonclaim",
            "certificate_sha256",
        },
        "manifest",
    )
    if data["schema_version"] != 1:
        raise CertificateError("schema_version must equal 1")
    if data["status"] != (
        "research-certificate-with-imported-ray-class-local-trace-and-finite-flat-lemmas"
    ):
        raise CertificateError("unexpected certificate status")
    if data["equation"] != "A^3+B^5=C^7":
        raise CertificateError("unexpected equation")

    system = data["fixed7_system"]
    exact_keys(
        system,
        {
            "field", "residual_characteristic", "orientation", "paper_variables",
            "parameter", "reducible_semisimplification", "ray_modulus",
            "ray_class_group",
        },
        "fixed7_system",
    )
    if system != {
        "field": "K5=Q(sqrt(5))",
        "residual_characteristic": 7,
        "orientation": "B^5+(-C)^7+A^3=0",
        "paper_variables": ["a=B", "b=-C", "c=A", "q=5", "p=7", "r=3"],
        "parameter": "t=-B^5/A^3",
        "reducible_semisimplification": "psi*chi_7 direct_sum psi^(-1)",
        "ray_modulus": "3*(sqrt(5))*infinity_1*infinity_2",
        "ray_class_group": "C4 x C2",
    }:
        raise CertificateError("fixed-7 orientation or ray data mismatch")

    pins = data["source_pins"]
    if pins != {
        "candidate_repository": "lucasvillagra/GFE-5p3",
        "candidate_commit": "e88f914c577ab6cf9a45e5cdd82c1993477fb423",
        "candidate_path": "Outputs/Data.txt",
        "candidate_blob_sha1": "9c96357834f2298b4d91ab97812c38e84b8ef7a2",
        "elimination_code_path": "Codes/MagmaCode.m",
        "elimination_code_blob_sha1": "16455c3d35fb241e413db619a784267489ccba94",
        "paper_arxiv": "2512.17845v1",
    }:
        raise CertificateError("upstream source pins differ")

    rows = data["candidate_product_rows"]
    if not isinstance(rows, list) or len(rows) != 7:
        raise CertificateError("expected seven candidate-product rows")
    expected_order = [(17, I), (17, -I), (19, F49(1)), (19, F49(-1)),
                      (11, F49(1)), (71, F49(-1)), (13, F49(-1))]
    for row, (expected_prime, expected_psi) in zip(rows, expected_order):
        exact_keys(row, {"prime", "psi", "products"}, "candidate row")
        if row["prime"] != expected_prime or row["psi"] != expected_psi.as_json():
            raise CertificateError("candidate row order or character value mismatch")
        products = candidate_products(expected_prime, expected_psi)
        encoded = [product.as_json() for product in products]
        if row["products"] != encoded:
            raise CertificateError(
                f"candidate products differ at prime {expected_prime}: {encoded}"
            )

    expected_generators = {
        "11a=3+phi": (3, 1), "11b=3+2phi": (3, 2),
        "13_inert": (13, 0), "17_inert": (17, 0),
        "19a=4+phi": (4, 1), "19b=4+3phi": (4, 3),
        "71a=8+phi": (8, 1), "71b=8+7phi": (8, 7),
        "7_inert": (7, 0),
    }
    coordinates = data["ray_class_coordinates"]
    if set(coordinates) != set(expected_generators):
        raise CertificateError("ray-coordinate labels differ")
    computed_rays: dict[str, tuple[int, int]] = {}
    for label, generator in expected_generators.items():
        computed_rays[label] = ray_coordinate(*generator)
        if coordinates[label] != list(computed_rays[label]):
            raise CertificateError(f"ray coordinate mismatch for {label}")

    nodal = data["nodal_splitting_character"]
    exact_keys(
        nodal,
        {
            "fiber_factorization", "d_in_Z_phi", "d_description", "norm_d",
            "reductions", "all_listed_reductions_nonsquare",
            "ray_character_coordinates",
        },
        "nodal_splitting_character",
    )
    repeated = poly_pow([-1, -1, 1], 2)
    other = [1, -2, 5]
    factorized = poly_mul(repeated, other)
    target = [1, 0, 0, 10, 0, -12, 5]
    if factorized != target:
        raise CertificateError("t=1 fiber factorization failed")
    if nodal["fiber_factorization"] != (
        "5*x^6-12*x^5+10*x^3+1=(x^2-x-1)^2*(5*x^2-2*x+1)"
    ):
        raise CertificateError("factorization transcription mismatch")
    if nodal["d_in_Z_phi"] != [6, 3]:
        raise CertificateError("unexpected nodal square class")
    a, b = nodal["d_in_Z_phi"]
    norm = a * a + a * b - b * b
    if norm != 45 or nodal["norm_d"] != norm:
        raise CertificateError("Norm(d) must equal 45")
    roots_11 = [value for value in range(11) if (value * value - value - 1) % 11 == 0]
    roots_19 = [value for value in range(19) if (value * value - value - 1) % 19 == 0]
    reductions_11 = sorted((a + b * root) % 11 for root in roots_11)
    reductions_19 = sorted((a + b * root) % 19 for root in roots_19)
    if sorted(nodal["reductions"]["prime_11"]) != reductions_11 or reductions_11 != [7, 8]:
        raise CertificateError("d reductions at 11 differ")
    if sorted(nodal["reductions"]["prime_19"]) != reductions_19 or reductions_19 != [2, 13]:
        raise CertificateError("d reductions at 19 differ")
    if any(legendre(value, 11) != -1 for value in reductions_11):
        raise CertificateError("a d reduction at 11 is not a nonsquare")
    if any(legendre(value, 19) != -1 for value in reductions_19):
        raise CertificateError("a d reduction at 19 is not a nonsquare")
    if nodal["all_listed_reductions_nonsquare"] is not True:
        raise CertificateError("nonsquare summary flag missing")
    if nodal["ray_character_coordinates"] != [2, 0]:
        raise CertificateError("nodal splitting character is not recorded as (2,0)")
    eta = (2, 0)
    if not all(
        character_value(eta, computed_rays[label]) == F49(-1)
        for label in ("11a=3+phi", "11b=3+2phi", "19a=4+phi", "19b=4+3phi")
    ):
        raise CertificateError("the recorded nodal character has the wrong split-prime signs")

    characters = list(itertools.product(range(4), range(2)))
    after_17 = [
        character for character in characters
        if character_value(character, computed_rays["17_inert"]) not in {I, -I}
    ]
    if after_17 != [(0, 0), (0, 1), (2, 0), (2, 1)]:
        raise CertificateError("prime 17 did not reduce to quadratic characters")
    after_19 = [
        character for character in after_17
        if character_value(character, computed_rays["19a=4+phi"]) == F49(-1)
    ]
    if after_19 != [(2, 0), (2, 1)]:
        raise CertificateError("prime 19 did not force the order-two coordinate")
    after_11 = [
        character for character in after_19
        if all(
            character_value(character, computed_rays[label]) == F49(-1)
            for label in ("11a=3+phi", "11b=3+2phi")
        )
    ]
    if after_11 != [eta]:
        raise CertificateError("prime 11 did not isolate the nodal character")
    if character_value(eta, computed_rays["71a=8+phi"]) != F49(-1):
        raise CertificateError("eta value at 71 is wrong")
    if character_value(eta, computed_rays["13_inert"]) != F49(-1):
        raise CertificateError("eta value at 13 is wrong")

    sieve = data["ray_sieve_conclusion"]
    exact_keys(
        sieve,
        {
            "unique_reducibility_character", "character_coordinates",
            "forced_prime_divisors_of_C_before_prime7",
            "forced_divisibility_alternative", "prime2_obstruction",
            "prime2_obstruction_factorization",
        },
        "ray_sieve_conclusion",
    )
    if sieve["unique_reducibility_character"] != "eta=theta_(3*sqrt(5)*phi)":
        raise CertificateError("unique reducibility character description mismatch")
    if sieve["character_coordinates"] != [2, 0]:
        raise CertificateError("unique reducibility character coordinate mismatch")
    if sieve["forced_prime_divisors_of_C_before_prime7"] != [2, 19, 71]:
        raise CertificateError("forced C support mismatch")
    if sieve["forced_divisibility_alternative"] != "13 divides A*C":
        raise CertificateError("prime-13 alternative mismatch")
    if sieve["prime2_obstruction"] != 6084 or 6084 != 2**2 * 3**2 * 13**2:
        raise CertificateError("prime-2 obstruction arithmetic mismatch")
    if sieve["prime2_obstruction_factorization"] != [[2, 2], [3, 2], [13, 2]]:
        raise CertificateError("prime-2 obstruction factorization mismatch")

    hasse = data["hasse_witt_mod7"]
    exact_keys(
        hasse,
        {
            "generic_model", "generic_matrix", "generic_frobenius_product",
            "zero_model", "zero_matrix", "infinity_model", "infinity_matrix",
            "eta_at_inert_prime_7", "generic_implication",
            "zero_and_infinity_implication",
        },
        "hasse_witt_mod7",
    )
    generic_poly: list[TPoly] = [
        {2: 1}, {}, {}, {1: 3}, {}, {0: 2}, {0: 5}
    ]
    zero_poly: list[TPoly] = [{0: 1}, {}, {}, {}, {}, {0: 2}]
    infinity_poly: list[TPoly] = [{0: 1}, {}, {}, {0: 3}, {}, {}, {0: 5}]
    generic_matrix = hasse_witt(generic_poly)
    zero_matrix = hasse_witt(zero_poly)
    infinity_matrix = hasse_witt(infinity_poly)
    if generic_matrix != decode_matrix(hasse["generic_matrix"]):
        raise CertificateError(f"generic Hasse-Witt matrix differs: {generic_matrix}")
    if matrix_mul(generic_matrix, generic_matrix) != decode_matrix(
        hasse["generic_frobenius_product"]
    ):
        raise CertificateError("generic Hasse-Witt Frobenius product differs")
    if zero_matrix != decode_matrix(hasse["zero_matrix"]):
        raise CertificateError("zero-model Hasse-Witt matrix differs")
    if matrix_mul(zero_matrix, zero_matrix) != [[{}, {}], [{}, {}]]:
        raise CertificateError("zero-model stable Hasse-Witt rank is not zero")
    if infinity_matrix != decode_matrix(hasse["infinity_matrix"]):
        raise CertificateError("infinity-model Hasse-Witt matrix differs")
    if infinity_matrix != [[{}, {}], [{}, {}]]:
        raise CertificateError("infinity-model p-rank is not zero")
    if legendre(norm % 7, 7) != -1 or hasse["eta_at_inert_prime_7"] != -1:
        raise CertificateError("eta(Frob_7) is not certified as -1")
    if [value for value in range(1, 7) if pow(value, 5, 7) == 1] != [1]:
        raise CertificateError("t^5=1 is not unique in F_7^*")

    imported = data["imported_lemmas"]
    if not isinstance(imported, list) or len(imported) != 6:
        raise CertificateError("expected exactly six imported lemmas")
    required_import_tokens = (
        "reducible fixed-7", "candidate polynomials", "6084", "finite-flat",
        "Hasse-Witt", "plus HGM",
    )
    if any(not any(token in lemma for lemma in imported) for token in required_import_tokens):
        raise CertificateError("an imported-lemma category is missing")
    conclusions = data["conditional_conclusions"]
    if not isinstance(conclusions, list) or len(conclusions) != 3:
        raise CertificateError("expected three conditional conclusions")
    if "cannot both be reducible" not in conclusions[-1]:
        raise CertificateError("two-Frey dichotomy conclusion missing")
    if "finite arithmetic only" not in data["nonclaim"] or "does not prove" not in data["nonclaim"]:
        raise CertificateError("trust-boundary nonclaim is missing")

    digest = canonical_sha256(data)
    if digest != data["certificate_sha256"]:
        raise CertificateError(
            f"certificate digest mismatch: expected {data['certificate_sha256']}, got {digest}"
        )
    return digest

