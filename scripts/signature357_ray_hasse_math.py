"""Ray-class and Hasse--Witt arithmetic helpers for signature (3,5,7)."""
from __future__ import annotations

from signature357_ray_hasse_core import *  # noqa: F401,F403

# Arithmetic in Z[phi]/m, phi^2=phi+1.
def mul_phi(left: tuple[int, int], right: tuple[int, int], modulus: int) -> tuple[int, int]:
    a, b = left
    c, d = right
    return ((a * c + b * d) % modulus, (a * d + b * c + b * d) % modulus)


def discrete_log_phi(value: tuple[int, int], modulus: int, order: int) -> int:
    current = (1, 0)
    target = (value[0] % modulus, value[1] % modulus)
    for exponent in range(order):
        if current == target:
            return exponent
        current = mul_phi(current, (0, 1), modulus)
    raise CertificateError(f"no discrete logarithm for {value} modulo {modulus}")


def sign_x_plus_y_sqrt5(x: int, y: int) -> int:
    """Exact sign of x+y*sqrt(5), assuming the expression is nonzero."""
    if y == 0:
        return 1 if x > 0 else -1
    if y > 0:
        if x >= 0:
            return 1
        return 1 if 5 * y * y > x * x else -1
    if x <= 0:
        return -1
    return 1 if x * x > 5 * y * y else -1


def ray_coordinate(a: int, b: int) -> tuple[int, int]:
    r = discrete_log_phi((a, b), 3, 8)
    residue_mod_5 = (a + 3 * b) % 5
    try:
        s = next(exponent for exponent in range(4) if pow(3, exponent, 5) == residue_mod_5)
    except StopIteration as exc:
        raise CertificateError("principal generator is not a unit modulo sqrt(5)") from exc
    x = 2 * a + b
    e1 = int(sign_x_plus_y_sqrt5(x, b) < 0)
    e2 = int(sign_x_plus_y_sqrt5(x, -b) < 0)
    return ((3 * r + s + 2 * e1) % 4, (r + e1 + e2) % 2)


def character_value(character: tuple[int, int], ray: tuple[int, int]) -> F49:
    a, b = character
    u, v = ray
    return (I ** (a * u)) * ((-1) ** (b * v))


def legendre(value: int, prime: int) -> int:
    value %= prime
    if value == 0:
        return 0
    result = pow(value, (prime - 1) // 2, prime)
    return -1 if result == prime - 1 else result


def poly_mul(left: list[int], right: list[int], modulus: int | None = None) -> list[int]:
    out = [0] * (len(left) + len(right) - 1)
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            out[i + j] += a * b
    if modulus is not None:
        out = [value % modulus for value in out]
    while len(out) > 1 and out[-1] == 0:
        out.pop()
    return out


def poly_pow(poly: list[int], exponent: int, modulus: int | None = None) -> list[int]:
    result = [1]
    base = poly
    while exponent:
        if exponent & 1:
            result = poly_mul(result, base, modulus)
        base = poly_mul(base, base, modulus)
        exponent >>= 1
    return result


# Sparse polynomial in t: degree -> coefficient modulo 7.
TPoly = dict[int, int]


def tadd(left: TPoly, right: TPoly) -> TPoly:
    out = dict(left)
    for degree, value in right.items():
        out[degree] = (out.get(degree, 0) + value) % P
        if out[degree] == 0:
            del out[degree]
    return out


def tmul(left: TPoly, right: TPoly) -> TPoly:
    out: TPoly = {}
    for left_degree, left_value in left.items():
        for right_degree, right_value in right.items():
            degree = left_degree + right_degree
            out[degree] = (out.get(degree, 0) + left_value * right_value) % P
    return {degree: value for degree, value in out.items() if value % P}


def xpoly_mul(left: list[TPoly], right: list[TPoly]) -> list[TPoly]:
    out: list[TPoly] = [{} for _ in range(len(left) + len(right) - 1)]
    for i, a in enumerate(left):
        for j, b in enumerate(right):
            out[i + j] = tadd(out[i + j], tmul(a, b))
    return out


def xpoly_pow(poly: list[TPoly], exponent: int) -> list[TPoly]:
    result: list[TPoly] = [{0: 1}]
    base = poly
    while exponent:
        if exponent & 1:
            result = xpoly_mul(result, base)
        base = xpoly_mul(base, base)
        exponent >>= 1
    return result


def hasse_witt(poly: list[TPoly]) -> list[list[TPoly]]:
    powered = xpoly_pow(poly, (P - 1) // 2)
    def coefficient(index: int) -> TPoly:
        return powered[index] if index < len(powered) else {}
    return [
        [coefficient(P * row - column) for column in (1, 2)]
        for row in (1, 2)
    ]


def matrix_mul(left: list[list[TPoly]], right: list[list[TPoly]]) -> list[list[TPoly]]:
    return [
        [
            tadd(tmul(left[row][0], right[0][column]), tmul(left[row][1], right[1][column]))
            for column in range(2)
        ]
        for row in range(2)
    ]


def decode_tpoly(value: Any) -> TPoly:
    if not isinstance(value, list):
        raise CertificateError("t-polynomial encoding must be a list")
    out: TPoly = {}
    for term in value:
        if (
            not isinstance(term, list) or len(term) != 2
            or type(term[0]) is not int or type(term[1]) is not int
        ):
            raise CertificateError("invalid t-polynomial term")
        degree, coefficient = term
        if degree < 0 or coefficient % P == 0 or degree in out:
            raise CertificateError("noncanonical t-polynomial encoding")
        out[degree] = coefficient % P
    return out


def decode_matrix(value: Any) -> list[list[TPoly]]:
    if (
        not isinstance(value, list) or len(value) != 2
        or any(not isinstance(row, list) or len(row) != 2 for row in value)
    ):
        raise CertificateError("matrix must be 2 by 2")
    return [[decode_tpoly(entry) for entry in row] for row in value]

