"""Central publication style for generated diagnostics and previews.

The paper still needs a future TikZ/PGFPlots reconstruction for its main
mathematical diagrams. This module keeps the current generated diagnostics
consistent, grayscale-tolerant, and free of provenance text inside axes.
"""

from __future__ import annotations


COLORBLIND_PALETTE = {
    "blue": "#0072B2",
    "orange": "#E69F00",
    "green": "#009E73",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "black": "#222222",
    "gray": "#666666",
}


def apply_style(plt) -> None:
    """Apply one compact, print-safe style to a Matplotlib module."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "axes.linewidth": 0.9,
            "lines.linewidth": 1.5,
            "lines.markersize": 4.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
