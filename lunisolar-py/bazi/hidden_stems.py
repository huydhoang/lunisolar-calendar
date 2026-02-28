"""
Hidden Stems (藏干) — spec §2.2
================================
"""

from typing import List, Tuple

from .constants import EARTHLY_BRANCHES, BRANCH_HIDDEN_STEMS, HIDDEN_ROLES


def branch_hidden_with_roles(branch_idx: int) -> List[Tuple[str, str]]:
    """Return [(role, stem), …] for the hidden stems of the branch at *branch_idx*."""
    branch = EARTHLY_BRANCHES[branch_idx]
    stems = BRANCH_HIDDEN_STEMS[branch]
    return [(HIDDEN_ROLES[i], stems[i]) for i in range(len(stems))]
