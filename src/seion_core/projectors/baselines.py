from __future__ import annotations

import numpy as np

from .projector import Projector


def random_projector(dimension: int, rank: int, seed: int = 0) -> Projector:
    rng = np.random.default_rng(seed)
    return Projector.from_matrix(rng.normal(size=(dimension, rank)), rank=rank, method="random")


def pca_projector(samples: np.ndarray, rank: int) -> Projector:
    samples = np.asarray(samples)
    if samples.ndim != 2:
        raise ValueError("samples must have shape (observations, dimension)")
    centered = samples - np.mean(samples, axis=0, keepdims=True)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    return Projector(vh[:rank].conj().T, method="pca")


def svd_projector(matrix: np.ndarray, rank: int) -> Projector:
    _, _, vh = np.linalg.svd(np.asarray(matrix), full_matrices=False)
    return Projector(vh[:rank].conj().T, method="svd")


def spectral_projector(matrix: np.ndarray, rank: int) -> Projector:
    matrix = np.asarray(matrix)
    hermitian = 0.5 * (matrix + matrix.conj().T)
    values, vectors = np.linalg.eigh(hermitian)
    return Projector(vectors[:, -rank:], method="spectral")

