"""
Narrative Interpretation Generator
===================================
"""

from typing import Dict, List, Optional


def generate_narrative(
    chart: Dict,
    strength: str,
    structure: Dict,
    interactions: Dict[str, list],
    *,
    missing_elements: Optional[List[Dict]] = None,
    competing_frames: Optional[List[Dict]] = None,
) -> str:
    """Generate a human-readable interpretation of the natal chart."""
    dm = chart["day_master"]["stem"]
    elem = chart["day_master"]["element"]
    gender = chart.get("gender", "male")

    lines = [
        f"Day Master: {dm} ({elem})",
        f"Structure: {structure.get('primary', 'Unknown')}",
        f"Strength: {strength}",
    ]

    if structure.get("primary") == "伤官格":
        lines.append("")
        lines.append("=== HURT OFFICER (伤官) ANALYSIS ===")
        lines.append("")
        lines.append(
            "The chart contains significant 伤官 (Hurt Officer) energy, representing"
        )
        lines.append("a rebellious, creative, and critical nature.")
        lines.append("")
        lines.append("CAREER ADVICE:")
        lines.append(
            "- Pursue creative fields, consulting, or technical expertise with autonomy"
        )
        lines.append(
            "- Practice 'Restraint of Speech' to avoid self-sabotage in professional settings"
        )
        lines.append("- Avoid rigid hierarchies that may trigger conflict")
        lines.append("")
        if gender == "female":
            lines.append("RELATIONSHIP ADVICE:")
            lines.append(
                "- In female charts, Officer (官) represents the husband/partner"
            )
            lines.append("- Heavy Hurt Officer (Earth) weakens the Officer's star")
            lines.append(
                "- Suggest: Late marriage or tolerant partner in Metal/Wood fields"
            )
            lines.append("- Consciously reduce critical nature to maintain harmony")
        lines.append("")
        lines.append("ELEMENTAL REMEDY:")
        lines.append("- Increase Wood (Mộc) energy to control Earth and protect Water")
        lines.append("- Areas: Education, culture, greenery, lifelong learning")

    else:
        personality = {
            "strong": "Self-driven, assertive, independent.",
            "weak": "Adaptive, sensitive to environment, relationship-oriented.",
            "balanced": "Balanced temperament with moderate adaptability.",
        }
        lines.append(f"Personality: {personality.get(strength, '')}")

    if interactions.get("六冲"):
        lines.append("Chart shows internal conflicts (clashes present).")
    if interactions.get("三合"):
        lines.append("Strong elemental harmony (Three Harmony formation).")
    if interactions.get("六合"):
        lines.append("Partnership tendencies indicated (Six Combination present).")
    if interactions.get("自刑"):
        lines.append(
            "Self-punishment pattern detected — watch for self-sabotage tendencies."
        )

    # Missing elements analysis
    if missing_elements:
        lines.append("")
        for me in missing_elements:
            elem_name = me["element"]
            tg_cat = me["ten_god_category"]
            rel = me["relation"]
            lines.append(f"Missing element: {elem_name} ({tg_cat}).")
            if rel == "ke":
                lines.append(
                    "  → Missing Officer/Power (官殺) signifies freedom-loving nature, "
                    "rejection of strict hierarchy and authority. "
                    "For males, may indicate challenges with children; "
                    "career may favor self-employment or creative fields."
                )
            elif rel == "wo_ke":
                lines.append(
                    "  → Missing Wealth (財星) suggests difficulty accumulating material "
                    "resources; may need extra effort in financial management."
                )
            elif rel == "sheng":
                lines.append(
                    "  → Missing Resource/Seal (印星) indicates lack of formal support "
                    "systems; self-reliant but may feel isolated under pressure."
                )

    # Competing frames analysis
    if competing_frames:
        lines.append("")
        for cf in competing_frames:
            conflict = cf["conflict_type"]
            branch = cf["branch"]
            lines.append(f"⚠ Branch {branch} conflict: {conflict}.")
            if "群比争财" in conflict:
                lines.append(
                    "  → WARNING: Companions/siblings contest with you for wealth. "
                    "High risk in partnerships, joint ventures, and lending. "
                    "For males, may also indicate marital stress "
                    "(spouse under pressure from rivals)."
                )

    lines.append(
        "Overall chart shows dynamic interaction between "
        "structure and elemental balance."
    )
    return "\n".join(lines)
