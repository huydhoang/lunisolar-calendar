"""
Bazi Terminology (八字术语翻译)
================================

Translation arrays and formatting utilities for Chinese metaphysical terms.
"""

from typing import List, Optional, Tuple

FORMAT_STRING = "cn/py/en/vi"

STEM_TRANS = [
    ("甲", "Jiǎ", "Yang Wood", "Giáp"),
    ("乙", "Yǐ", "Yin Wood", "Ất"),
    ("丙", "Bǐng", "Yang Fire", "Bính"),
    ("丁", "Dīng", "Yin Fire", "Đinh"),
    ("戊", "Wù", "Yang Earth", "Mậu"),
    ("己", "Jǐ", "Yin Earth", "Kỷ"),
    ("庚", "Gēng", "Yang Metal", "Canh"),
    ("辛", "Xīn", "Yin Metal", "Tân"),
    ("壬", "Rén", "Yang Water", "Nhâm"),
    ("癸", "Guǐ", "Yin Water", "Quý"),
]

BRANCH_TRANS = [
    ("子", "Zǐ", "Rat", "Tí"),
    ("丑", "Chǒu", "Ox", "Sửu"),
    ("寅", "Yín", "Tiger", "Dần"),
    ("卯", "Mǎo", "Rabbit", "Mão"),
    ("辰", "Chén", "Dragon", "Thìn"),
    ("巳", "Sì", "Snake", "Tỵ"),
    ("午", "Wǔ", "Horse", "Ngọ"),
    ("未", "Wèi", "Goat", "Mùi"),
    ("申", "Shēn", "Monkey", "Thân"),
    ("酉", "Yǒu", "Rooster", "Dậu"),
    ("戌", "Xū", "Dog", "Tuất"),
    ("亥", "Hài", "Pig", "Hợi"),
]

TENGOD_TRANS = [
    ("比肩", "Bǐ Jiān", "Friend", "Tỷ Kiên"),
    ("劫财", "Jié Cái", "Rob Wealth", "Kiếp Tài"),
    ("食神", "Shí Shén", "Eating God", "Thực Thần"),
    ("伤官", "Shāng Guān", "Hurting Officer", "Thương Quan"),
    ("偏财", "Piān Cái", "Indirect Wealth", "Thiên Tài"),
    ("正财", "Zhèng Cái", "Direct Wealth", "Chính Tài"),
    ("七杀", "Qī Shā", "Seven Killings", "Thất Sát"),
    ("正官", "Zhèng Guān", "Direct Officer", "Chính Quan"),
    ("偏印", "Piān Yìn", "Indirect Resource", "Thiên Ấn"),
    ("正印", "Zhèng Yìn", "Direct Resource", "Chính Ấn"),
]

INTERACTIONS_TRANS = [
    ("合", "Hé", "Combine", "Hợp"),
    ("冲", "Chōng", "Clash", "Xung"),
    ("刑", "Xíng", "Punishment", "Hình"),
    ("害", "Hài", "Harm", "Hại"),
    ("破", "Pò", "Destruction", "Phá"),
    ("六合", "Liù Hé", "Six Combinations", "Lục Hợp"),
    ("三合", "Sān Hé", "Three Combinations", "Tam Hợp"),
    ("三会", "Sān Huì", "Directional Combination", "Tam Hội"),
    ("六冲", "Liù Chōng", "Six Clashes", "Lục Xung"),
    ("六害", "Liù Hài", "Six Harms", "Lục Hại"),
    ("自刑", "Zì Xíng", "Self-Punishment", "Tự Hình"),
    ("三刑", "Sān Xíng", "Three Punishments", "Tam Hình"),
]

LIFESTAGE_TRANS = [
    ("长生", "Cháng Shēng", "Growth", "Trường Sinh"),
    ("沐浴", "Mù Yù", "Bath", "Mộc Dục"),
    ("冠带", "Guàn Dài", "Crown Belt", "Quan Đới"),
    ("临官", "Lín Guān", "Coming of Age", "Lâm Quan"),
    ("帝旺", "Dì Wàng", "Prosperity Peak", "Đế Vượng"),
    ("衰", "Shuāi", "Decline", "Suy"),
    ("病", "Bìng", "Sickness", "Bệnh"),
    ("死", "Sǐ", "Death", "Tử"),
    ("墓", "Mù", "Grave", "Mộ"),
    ("绝", "Jué", "Termination", "Tuyệt"),
    ("胎", "Tāi", "Conception", "Thai"),
    ("养", "Yǎng", "Nurture", "Dưỡng"),
]

STAR_TRANS = [
    ("天乙贵人", "Tiān Yǐ Guì Rén", "Nobleman", "Thiên Ất Quý Nhân"),
    ("文昌", "Wén Chāng", "Academic Star", "Văn Xương"),
    ("桃花", "Táo Huā", "Peach Blossom", "Đào Hoa"),
    ("驿马", "Yì Mǎ", "Travel Horse", "Dịch Mã"),
    ("将星", "Jiàng Xīng", "General Star", "Tướng Tinh"),
    ("华盖", "Huá Gài", "Canopy", "Hoa Cái"),
    ("羊刃", "Yáng Rèn", "Goat Blade", "Dương Nhận"),
    ("禄神", "Lù Shén", "Prosperity Star", "Lộc Thần"),
    ("红鸾", "Hóng Luán", "Red Cloud", "Hồng Loan"),
    ("血刃", "Xuè Rèn", "Blood Knife", "Huyết Nhận"),
    ("空亡", "Kōng Wáng", "Void", "Không Vong"),
]

TRANS_GROUPS = [
    STEM_TRANS, BRANCH_TRANS, TENGOD_TRANS,
    INTERACTIONS_TRANS, LIFESTAGE_TRANS, STAR_TRANS,
]


def get_trans_tuple(chinese_str: str) -> Optional[Tuple[str, str, str, str]]:
    for group in TRANS_GROUPS:
        for t in group:
            if t[0] == chinese_str:
                return t
    return None


def format_term(chinese_str: str, override_fmt: str = None) -> str:
    """Format a Chinese term based on FORMAT_STRING like 'cn/py/en/vi'."""
    if not chinese_str or chinese_str == "-":
        return chinese_str

    fmt = override_fmt or FORMAT_STRING
    opts = {"cn": 0, "py": 1, "en": 2, "vi": 3}
    parts = fmt.split("/")
    result_parts = []

    t = get_trans_tuple(chinese_str)
    if t:
        for p in parts:
            if p in opts:
                result_parts.append(t[opts[p]])
        return "/".join(result_parts)

    # 2-character GanZhi combinations
    if len(chinese_str) == 2:
        s_t = get_trans_tuple(chinese_str[0])
        b_t = get_trans_tuple(chinese_str[1])
        if s_t and b_t:
            combined_tuple = (
                chinese_str,
                f"{s_t[1]}{b_t[1].lower()}",
                f"{s_t[2]} {b_t[2]}",
                f"{s_t[3]} {b_t[3]}",
            )
            for p in parts:
                if p in opts:
                    result_parts.append(combined_tuple[opts[p]])
            return "/".join(result_parts)

    return chinese_str
