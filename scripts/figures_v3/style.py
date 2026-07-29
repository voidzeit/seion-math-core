"""Central colorblind-safe publication style for the v3 figure suite."""

from __future__ import annotations

import matplotlib as mpl


COLORS = {
    "black": "#1A1A1A",
    "gray": "#6B7280",
    "light": "#E5E7EB",
    "blue": "#0072B2",
    "sky": "#56B4E9",
    "green": "#009E73",
    "orange": "#E69F00",
    "vermillion": "#D55E00",
    "purple": "#CC79A7",
    "yellow": "#F0E442",
}

MARKERS = ("o", "s", "^", "D", "v", "P", "X")
LINESTYLES = ("-", "--", "-.", ":")


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "serif",
            "font.serif": ["STIX Two Text", "STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.5,
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.2,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.35,
            "lines.markersize": 4.5,
            "patch.linewidth": 0.9,
            "grid.color": "#D1D5DB",
            "grid.linewidth": 0.45,
            "grid.alpha": 0.75,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "legend.frameon": False,
            "figure.constrained_layout.use": True,
        }
    )


def panel_label(ax, label: str) -> None:
    ax.text(
        -0.12,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=10,
        fontweight="bold",
        va="bottom",
        color=COLORS["black"],
    )


def light_grid(ax, axis: str = "both") -> None:
    ax.grid(True, which="major", axis=axis)
    ax.set_axisbelow(True)
