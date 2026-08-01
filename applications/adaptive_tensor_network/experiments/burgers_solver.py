"""Real 1D viscous Burgers-equation finite-difference solver (mission
AI3 Level 3: "reduced surrogate for Burgers equation").

u_t + u u_x = nu u_xx, periodic boundary conditions, explicit
finite-difference (upwind advection + central diffusion), fixed grid and
time horizon. Not a toy - a genuine (if small) numerical PDE solve, used
to generate ground-truth (parameters -> final state) training pairs for
the tensor-network surrogate.
"""

from __future__ import annotations

import numpy as np


def solve_burgers(
    nu: float,
    fourier_coeffs: np.ndarray,
    *,
    grid_size: int = 32,
    domain_length: float = 2 * np.pi,
    t_final: float = 0.5,
    cfl: float = 0.2,
) -> np.ndarray:
    """Initial condition: u0(x) = sum_k fourier_coeffs[k] * sin((k+1) x).
    Returns the final state u(x, t_final) on the grid, shape (grid_size,).
    """

    dx = domain_length / grid_size
    x = np.linspace(0, domain_length, grid_size, endpoint=False)
    u = np.zeros(grid_size)
    for k, coeff in enumerate(fourier_coeffs):
        u += coeff * np.sin((k + 1) * x)

    max_speed = max(np.max(np.abs(u)), 1e-6)
    dt_advect = cfl * dx / max_speed
    dt_diffuse = cfl * dx * dx / max(nu, 1e-6)
    dt = min(dt_advect, dt_diffuse, 0.01)
    n_steps = max(1, int(np.ceil(t_final / dt)))
    dt = t_final / n_steps

    for _ in range(n_steps):
        u_left = np.roll(u, 1)
        u_right = np.roll(u, -1)
        # upwind advection (u >= 0 assumed dominant direction per sample;
        # use a simple switched upwind scheme for robustness)
        dudx_backward = (u - u_left) / dx
        dudx_forward = (u_right - u) / dx
        advect = np.where(u >= 0, u * dudx_backward, u * dudx_forward)
        diffuse = nu * (u_right - 2 * u + u_left) / dx**2
        u = u + dt * (-advect + diffuse)
    return u


def generate_dataset(n_samples: int, *, seed: int, grid_size: int = 32, n_fourier_modes: int = 3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns (nu_values, fourier_coeffs, final_states) - nu_values shape
    (n_samples,), fourier_coeffs shape (n_samples, n_fourier_modes),
    final_states shape (n_samples, grid_size)."""

    rng = np.random.default_rng(seed)
    nu_values = rng.uniform(0.01, 0.3, size=n_samples)
    fourier_coeffs = rng.uniform(-1.0, 1.0, size=(n_samples, n_fourier_modes))
    final_states = np.zeros((n_samples, grid_size))
    for i in range(n_samples):
        final_states[i] = solve_burgers(nu_values[i], fourier_coeffs[i], grid_size=grid_size)
    return nu_values, fourier_coeffs, final_states
