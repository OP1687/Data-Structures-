"""Shared matplotlib style / color palette for all Fuveme XBeach figures.

Palette follows the validated colorblind-safe categorical/sequential/diverging
scheme documented in the dataviz skill (references/palette.md): fixed hue
order for categorical series, single-hue light->dark ramps for magnitude, and
a blue<->red diverging pair with a neutral gray midpoint for signed
erosion/accretion quantities (erosion = red/loss, accretion = blue/gain).
"""
import matplotlib.pyplot as plt
import matplotlib as mpl

CATEGORICAL = {
    "blue": "#2a78d6",
    "orange": "#eb6834",
    "aqua": "#1baf7a",
    "yellow": "#eda100",
    "magenta": "#e87ba4",
    "green": "#008300",
    "violet": "#4a3aa7",
    "red": "#e34948",
}
CATEGORICAL_ORDER = ["blue", "orange", "aqua", "yellow", "magenta", "green", "violet", "red"]

SEQUENTIAL_BLUE = ["#cde2fb", "#9ec5f4", "#5598e7", "#2a78d6", "#184f95", "#0d366b"]

DIVERGING_BLUE_RED = {"accretion": "#2a78d6", "erosion": "#e34948", "neutral": "#c3c2b7"}

INK = {"primary": "#0b0b0b", "secondary": "#52514e", "muted": "#898781", "grid": "#e1e0d9"}
SURFACE = "#fcfcfb"


def categorical(i: int) -> str:
    return CATEGORICAL[CATEGORICAL_ORDER[i % len(CATEGORICAL_ORDER)]]


def apply_style():
    mpl.rcParams.update({
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": INK["muted"],
        "axes.labelcolor": INK["primary"],
        "text.color": INK["primary"],
        "xtick.color": INK["secondary"],
        "ytick.color": INK["secondary"],
        "axes.grid": True,
        "grid.color": INK["grid"],
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 10.5,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "figure.dpi": 150,
        "savefig.dpi": 220,
        "lines.linewidth": 1.8,
    })


def erosion_accretion_color(value: float) -> str:
    return DIVERGING_BLUE_RED["erosion"] if value < 0 else DIVERGING_BLUE_RED["accretion"]
