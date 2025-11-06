"""EIA API category constants."""

from __future__ import annotations

from enum import IntEnum
from typing import Final


class Category(IntEnum):
    """Root category IDs for major EIA datasets."""

    ROOT = 371
    ELECTRICITY = 0
    SEDS = 40203
    PETROLEUM = 714755
    NATURAL_GAS = 714804
    TOTAL_ENERGY = 711224
    COAL = 717234
    STEO = 829714
    AEO = 964164
    CRUDE_OIL = 1292190
    INTERNATIONAL_ENERGY = 2134384
    USESOD = 2123635
    CO2_EMISSIONS = 2251604
    US_NUCLEAR_OUTAGES = 2889994


# Legacy lowercase aliases for backward compatibility
ROOT: Final[int] = Category.ROOT
ELECTRICITY: Final[int] = Category.ELECTRICITY
SEDS: Final[int] = Category.SEDS
PETROLEUM: Final[int] = Category.PETROLEUM
NATURAL_GAS: Final[int] = Category.NATURAL_GAS
TOTAL_ENERGY: Final[int] = Category.TOTAL_ENERGY
COAL: Final[int] = Category.COAL
STEO: Final[int] = Category.STEO
AEO: Final[int] = Category.AEO
CRUDE_OIL: Final[int] = Category.CRUDE_OIL
INTERNATIONAL_ENERGY: Final[int] = Category.INTERNATIONAL_ENERGY
USESOD: Final[int] = Category.USESOD
CO2_EMISSIONS: Final[int] = Category.CO2_EMISSIONS
US_NUCLEAR_OUTAGES: Final[int] = Category.US_NUCLEAR_OUTAGES
