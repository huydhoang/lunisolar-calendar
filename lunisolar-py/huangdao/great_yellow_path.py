"""GreatYellowPath — Great Yellow Path (大黄道) Calculator."""

from __future__ import annotations

from .constants import (
    AZURE_DRAGON_MONTHLY_START,
    GreatYellowPathSpirit,
    SPIRIT_SEQUENCE,
)


class GreatYellowPath:
    """Great Yellow Path (大黄道) Calculator"""

    def calculate_spirit(self, lunar_month: int, day_branch_index: int) -> GreatYellowPathSpirit:
        """Calculate spirit for the day."""
        azure_start = AZURE_DRAGON_MONTHLY_START[lunar_month]
        spirit_index = (day_branch_index - azure_start.index) % 12
        return SPIRIT_SEQUENCE[spirit_index]
