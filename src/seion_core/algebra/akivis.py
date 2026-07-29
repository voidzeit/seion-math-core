"""Akivis identity components for a binary product."""

from __future__ import annotations


def associator(product, x, y, z):
    return product(product(x, y), z) - product(x, product(y, z))


def akivis_residual(product, x, y, z):
    bracket = lambda a, b: product(a, b) - product(b, a)
    jac = bracket(x, bracket(y, z)) + bracket(y, bracket(z, x)) + bracket(z, bracket(x, y))
    associator_sum = (
        associator(product, x, y, z)
        + associator(product, y, z, x)
        + associator(product, z, x, y)
        - associator(product, y, x, z)
        - associator(product, z, y, x)
        - associator(product, x, z, y)
    )
    return jac - associator_sum

