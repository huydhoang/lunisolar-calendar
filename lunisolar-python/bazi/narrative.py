"""
Narrative Interpretation Generator
===================================
"""

from typing import Dict


def generate_narrative(
    chart: Dict,
    strength: str,
    structure: Dict,
    interactions: Dict[str, list],
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

    lines.append(
        "Overall chart shows dynamic interaction between "
        "structure and elemental balance."
    )
    return "\n".join(lines)
