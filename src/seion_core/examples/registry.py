from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .associative import coordinatewise_associative_law, lie_derived_law, matrix_algebra_ternary_law
from .filippov import filippov_4d_law
from .invariant_subspace import invariant_subspace_law, no_nontrivial_closed_subspace_control
from .octonion import octonion_ternary_law
from .rank_one import rank_one_law
from .random_laws import cyclic_random_law, ill_conditioned_law, random_ternary_law
from .torus import torus_fourier_law
from .zero_law import zero_law


@dataclass(frozen=True)
class ExampleSpec:
    identifier: str
    definition: str
    dimension: int
    arity: int
    field: str
    symmetries: tuple[str, ...]
    known_associator: str
    known_gji_fi_status: str
    known_projector: str | None
    references: tuple[str, ...]
    builder: Callable


_SPECS = [
    ExampleSpec("zero_law", "mu=0", 3, 3, "real", (), "zero", "trivially zero", None, (), zero_law),
    ExampleSpec("rank_one_cp", "rank-one CP ternary law", 3, 3, "real", (), "not generally zero", "not asserted", None, (), rank_one_law),
    ExampleSpec("associative_algebra", "coordinatewise associative ternary product", 3, 3, "real", ("full",), "zero", "not applicable", None, (), coordinatewise_associative_law),
    ExampleSpec("matrix_algebra", "(XY)Z on 2x2 matrices", 4, 3, "real", (), "zero by matrix associativity", "not asserted", None, (), matrix_algebra_ternary_law),
    ExampleSpec("lie_derived", "[[x,y],z] using the cross product", 3, 3, "real", (), "nonzero control", "not asserted", None, (), lie_derived_law),
    ExampleSpec("filippov_4d", "Levi-Civita 4D 3-Lie bracket", 4, 3, "real", ("antisymmetric",), "nonzero generally", "FI expected by definition", None, ("Filippov 1985",), filippov_4d_law),
    ExampleSpec("octonion", "left-nested octonion product", 8, 3, "real", (), "nonzero control", "not asserted", None, ("Baez 2002",), octonion_ternary_law),
    ExampleSpec("random_dense", "iid Gaussian dense tensor", 3, 3, "real", (), "random", "not asserted", None, (), random_ternary_law),
    ExampleSpec("random_scale_matched", "norm-matched iid Gaussian tensor", 3, 3, "real", (), "random", "not asserted", None, (), lambda dimension=3, seed=0, dtype=np.float64: random_ternary_law(dimension, seed, dtype, True)),
    ExampleSpec("cyclic_random", "cyclic symmetrization of a random tensor", 3, 3, "real", ("cyclic",), "random", "not asserted", None, (), cyclic_random_law),
    ExampleSpec("ill_conditioned", "diagonal tensor with separated scales", 3, 3, "real", ("full",), "zero", "not asserted", None, (), ill_conditioned_law),
    ExampleSpec("known_invariant_subspace", "block-supported random tensor", 4, 3, "real", (), "random within block", "not asserted", "rank-two coordinate projector", (), invariant_subspace_law),
    ExampleSpec("no_closed_subspace_control", "random dense negative control", 4, 3, "real", (), "random", "not asserted", None, (), no_nontrivial_closed_subspace_control),
    ExampleSpec("kernel_integrated_discrete", "finite weighted kernel model", 3, 3, "real", (), "finite model", "not asserted", None, (), lambda dimension=3, seed=0, dtype=np.float64: random_ternary_law(dimension, seed, dtype)),
    ExampleSpec("torus_fourier", "diagonal Fourier-mode law", 3, 3, "complex", ("full",), "zero", "not asserted", None, (), torus_fourier_law),
]


def registry() -> dict[str, ExampleSpec]:
    return {spec.identifier: spec for spec in _SPECS}


def available_examples() -> list[str]:
    return [spec.identifier for spec in _SPECS]


def get_example(identifier: str, **kwargs):
    spec = registry().get(identifier)
    if spec is None:
        raise KeyError(f"unknown canonical example {identifier!r}")
    value = spec.builder(**kwargs)
    if isinstance(value, tuple) and len(value) == 2:
        return value[0]
    if hasattr(value, "to_dense") and not hasattr(value, "tensor"):
        return value.to_dense()
    return value

