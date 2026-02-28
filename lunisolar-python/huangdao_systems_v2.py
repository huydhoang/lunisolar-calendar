#!/usr/bin/env python3
"""
Efficient Huangdao Systems Calculator — Backward-compatible Facade
===================================================================

Real code lives in the ``huangdao/`` package.  This file re-exports every
public name so that existing ``from huangdao_systems_v2 import ...``
statements continue to work without modification.
"""

from huangdao.constants import (
    EarthlyBranch,
    GreatYellowPathSpirit,
    BRANCH_ORDER,
    BRANCH_INDEX,
    BUILDING_BRANCH_BY_MONTH,
    AZURE_DRAGON_MONTHLY_START,
    MNEMONIC_FORMULAS,
    SPIRIT_SEQUENCE,
)
from huangdao.construction_stars import ConstructionStars
from huangdao.great_yellow_path import GreatYellowPath
from huangdao.calculator import HuangdaoCalculator

from shared.constants import EARTHLY_BRANCH_PINYIN, PRINCIPAL_TERM_NAMES
from lunisolar.api import solar_to_lunisolar, solar_to_lunisolar_batch
from shared.models import LunisolarDateDTO


def main():
    from huangdao.__main__ import main as _main
    _main()


if __name__ == "__main__":
    main()