#!/usr/bin/env python3
"""Compute rigorous p-adic solubility profiles for reconstructed `(3,4,5)` curves.

For each affine projective chart of `y^2=f(u,v)`, this diagnostic builds the tree
of compatible solutions modulo `p^k`. A branch is certified soluble as soon as
the multivariate Hensel inequality `v_p(F)>2*v_p(gradient F)` holds. A curve is
certified insoluble when both chart trees become empty at finite precision.

The output uses reconstructed Edwards IDs only; it does not identify those IDs
with later paper `C_i` labels.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import signature345_local_utils as local


@dataclass(frozen=True)
class Chart:
    coefficients: tuple[int, ...]
    restrict_x_divisible_by_p: bool
    name: str


def vp(value: int, prime: int, infinity: int = 10**9) -> int:
    if value == 0:
        return infinity
    value = abs(value)
    result = 0
    while value % prime == 0:
        result += 1
        value //= prime
    return result


def hensel_certified(coefficients: tuple[int, ...], x: int, y: int, prime: int) -> bool:
    f_value = local.eval_integer(coefficients, x)
    equation = y * y - f_value
    derivative_x = -local.eval_integer(local.derivative(coefficients), x)
    derivative_y = 2 * y
    gradient_order = min(vp(derivative_x, prime), vp(derivative_y, prime))
    return vp(equation, prime) > 2 * gradient_order


def initial_nodes(chart: Chart, prime: int) -> set[tuple[int, int]]:
    nodes: set[tuple[int, int]] = set()
    x_values = [0] if chart.restrict_x_divisible_by_p else list(range(prime))
    for x in x_values:
        f_value = local.eval_integer(chart.coefficients, x) % prime
        for y in range(prime):
            if (y * y - f_value) % prime == 0:
                nodes.add((x, y))
    return nodes


def analyze_chart(chart: Chart, prime: int, maximum: int) -> dict[str, object]:
    nodes = initial_nodes(chart, prime)
    if not nodes:
        return {"status": "empty", "depth": 1, "chart": chart.name}

    for x, y in sorted(nodes):
        if hensel_certified(chart.coefficients, x, y, prime):
            return {
                "status": "soluble",
                "depth": 1,
                "chart": chart.name,
                "witness": [x, y],
            }

    modulus = prime
    for depth in range(1, maximum):
        next_modulus = modulus * prime
        lifted: set[tuple[int, int]] = set()
        for x, y in nodes:
            for a in range(prime):
                xx = x + a * modulus
                if chart.restrict_x_divisible_by_p and xx % prime:
                    continue
                f_value = local.eval_integer(chart.coefficients, xx)
                for b in range(prime):
                    yy = y + b * modulus
                    if (yy * yy - f_value) % next_modulus == 0:
                        if hensel_certified(chart.coefficients, xx, yy, prime):
                            return {
                                "status": "soluble",
                                "depth": depth + 1,
                                "chart": chart.name,
                                "witness": [xx, yy],
                            }
                        lifted.add((xx, yy))
        nodes = lifted
        modulus = next_modulus
        if not nodes:
            return {"status": "empty", "depth": depth + 1, "chart": chart.name}
        if len(nodes) > 200000:
            return {
                "status": "unresolved-large-tree",
                "depth": depth + 1,
                "chart": chart.name,
                "node_count": len(nodes),
            }

    return {
        "status": "unresolved",
        "depth": maximum,
        "chart": chart.name,
        "node_count": len(nodes),
    }


def analyze_curve(f, prime: int, maximum: int) -> dict[str, object]:
    coefficients = local.integral_coefficients(f)
    charts = [
        Chart(coefficients, False, "v-unit: f(x,1)"),
        Chart(tuple(reversed(coefficients)), True, "u-unit, v divisible by p: f(1,v)"),
    ]
    results = [analyze_chart(chart, prime, maximum) for chart in charts]
    soluble = next((item for item in results if item["status"] == "soluble"), None)
    if soluble is not None:
        return {"status": "soluble", "certificate": soluble, "charts": results}
    if all(item["status"] == "empty" for item in results):
        return {
            "status": "insoluble",
            "obstruction_depth": max(int(item["depth"]) for item in results),
            "charts": results,
        }
    return {"status": "unresolved", "charts": results}


def main() -> int:
    triples = local.reconstruct_triples()
    payload: dict[str, object] = {
        "prime_2": {},
        "prime_3": {},
        "paper_sets": {
            "no_Q2": [1, 4, 9, 10, 11, 13, 14, 18, 25, 26, 33, 35, 39, 45, 46, 48],
            "no_Q3": [20, 42],
        },
        "known_anchors": {"paper_2": 28, "paper_3": 2, "paper_5": 3},
    }
    for form_id, (f, _g, _h) in triples.items():
        payload["prime_2"][str(form_id)] = analyze_curve(f, 2, 40)  # type: ignore[index]
        payload["prime_3"][str(form_id)] = analyze_curve(f, 3, 25)  # type: ignore[index]
    print(json.dumps(payload, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
