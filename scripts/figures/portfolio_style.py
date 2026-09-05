"""Shared light-ground styling for the figures in this repository.

One place for the palette, the fonts and the small helpers, so every figure
looks like it belongs to the same report and reads on a white page.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

PAPER = "#FFFFFF"
INK = "#111827"
MUTED = "#4B5563"
FAINT = "#9CA3AF"
HAIR = "#E5E7EB"

BLUE, BLUE_SOFT = "#2563EB", "#BFDBFE"
GREEN, GREEN_SOFT = "#059669", "#A7F3D0"
AMBER, AMBER_SOFT = "#D97706", "#FDE68A"
RED, RED_SOFT = "#DC2626", "#FECACA"
SLATE, SLATE_SOFT = "#64748B", "#CBD5E1"

#: Ordered accents for categorical series. Blue first, red last, because red
#: should only ever mean "this is the bad case".
CYCLE = [BLUE, GREEN, AMBER, SLATE, RED]

FONTS = ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial", "sans-serif"]


def apply() -> None:
    """Set the rcParams once, at the top of a figure script."""
    mpl.rcParams.update({
        "figure.facecolor": PAPER,
        "savefig.facecolor": PAPER,
        "axes.facecolor": PAPER,
        "savefig.dpi": 200,
        "figure.dpi": 110,
        "font.family": "sans-serif",
        "font.sans-serif": FONTS,
        "text.color": INK,
        "axes.labelcolor": MUTED,
        "axes.edgecolor": HAIR,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.frameon": False,
        "axes.prop_cycle": mpl.cycler(color=CYCLE),
    })


def clean(ax, *, left: bool = True, bottom: bool = True, grid_axis: str = "y") -> None:
    """Strip the box down to the two spines that carry information."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_visible(left)
    ax.spines["bottom"].set_visible(bottom)
    ax.tick_params(length=0)
    if grid_axis in ("x", "y", "both"):
        ax.grid(True, axis=grid_axis, color=HAIR, lw=0.9, zorder=0)
    ax.set_axisbelow(True)


def title_block(fig, title: str, subtitle: str = "", *, y: float = 0.96,
                size: float = 21, x: float = 0.075) -> None:
    """Title and standfirst, with the gap measured in points rather than in
    figure fractions, so it does not drift when the canvas changes height."""
    fig.text(x, y, title, fontsize=size, color=INK, fontweight="600", va="top")
    if subtitle:
        gap = (size * 1.45) / (fig.get_figheight() * 72.0)
        fig.text(x, y - gap, subtitle, fontsize=11.6, color=MUTED, va="top",
                 linespacing=1.55)


def fits(fig, artist, *, margin: float = 0.02) -> bool:
    """True if a drawn text artist stays inside the canvas.

    Long footnotes running off the right edge is an easy mistake to make and a
    hard one to see in code, so every caption is measured once it exists rather
    than guessed at by counting characters.
    """
    fig.canvas.draw()
    box = artist.get_window_extent(fig.canvas.get_renderer())
    return box.x1 <= fig.bbox.x1 * (1.0 - margin) and box.x0 >= 0.0


def footnote(fig, lines, *, y: float = 0.085, x: float = 0.075,
             size: float = 9.6) -> None:
    """Sourcing and caveats along the bottom edge, one entry per line."""
    step = (size * 1.75) / (fig.get_figheight() * 72.0)
    for i, line in enumerate(lines):
        artist = fig.text(x, y - i * step, line, fontsize=size, color=FAINT,
                          va="top", linespacing=1.5)
        if not fits(fig, artist):
            print(f"    caption overflows the canvas: {line[:60]}...")


def note(ax, x, y, text, *, colour=None, size=10.0, weight="normal", **kw):
    """A short annotation placed in axes coordinates by default."""
    kw.setdefault("transform", ax.transAxes)
    return ax.text(x, y, text, fontsize=size, color=colour or MUTED,
                   fontweight=weight, **kw)


def save(fig, out_dir, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png")
    plt.close(fig)
    print(f"  wrote {name}.png")
