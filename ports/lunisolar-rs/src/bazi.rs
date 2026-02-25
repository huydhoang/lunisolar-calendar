//! Bazi (Four Pillars of Destiny) analysis module — ported from `bazi.py`.

use serde::Serialize;
use super::{HEAVENLY_STEMS, EARTHLY_BRANCHES};

// ── Element & Polarity Mappings (indexed parallel to HEAVENLY_STEMS) ────────

/// Element for each Heavenly Stem (indexed 0–9).
pub const STEM_ELEMENT: [&str; 10] = [
    "Wood", "Wood", "Fire", "Fire", "Earth",
    "Earth", "Metal", "Metal", "Water", "Water",
];

/// Polarity (Yin/Yang) for each Heavenly Stem.
pub const STEM_POLARITY: [&str; 10] = [
    "Yang", "Yin", "Yang", "Yin", "Yang",
    "Yin", "Yang", "Yin", "Yang", "Yin",
];

/// Element for each Earthly Branch (indexed 0–11).
pub const BRANCH_ELEMENT: [&str; 12] = [
    "Water", "Earth", "Wood", "Wood", "Earth", "Fire",
    "Fire", "Earth", "Metal", "Metal", "Earth", "Water",
];

/// Hidden stems for each Earthly Branch (main, [middle, [residual]]).
pub const BRANCH_HIDDEN_STEMS: [&[&str]; 12] = [
    &["癸"],                // 子
    &["己", "癸", "辛"],    // 丑
    &["甲", "丙", "戊"],    // 寅
    &["乙"],                // 卯
    &["戊", "乙", "癸"],    // 辰
    &["丙", "戊", "庚"],    // 巳
    &["丁", "己"],          // 午
    &["己", "丁", "乙"],    // 未
    &["庚", "壬", "戊"],    // 申
    &["辛"],                // 酉
    &["戊", "辛", "丁"],    // 戌
    &["壬", "甲"],          // 亥
];

// ── Stem Transformations (天干合化) ─────────────────────────────────────────

/// Five canonical stem-combination pairs: (stem_idx_a, stem_idx_b, target_element).
pub const STEM_TRANSFORMATIONS: [(usize, usize, &str); 5] = [
    (0, 5, "Earth"),  // 甲己 → Earth
    (1, 6, "Metal"),  // 乙庚 → Metal
    (2, 7, "Water"),  // 丙辛 → Water
    (3, 8, "Wood"),   // 丁壬 → Wood
    (4, 9, "Fire"),   // 戊癸 → Fire
];

// ── Twelve Longevity Stages (十二长生) ──────────────────────────────────────

pub const LONGEVITY_STAGES: [&str; 12] = [
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养",
];

pub const LONGEVITY_STAGES_EN: [&str; 12] = [
    "Growth", "Bath", "Crown Belt", "Coming of Age", "Prosperity Peak",
    "Decline", "Sickness", "Death", "Grave", "Termination",
    "Conception", "Nurture",
];

pub const LONGEVITY_STAGES_VI: [&str; 12] = [
    "Trường Sinh", "Mộc Dục", "Quan Đới", "Lâm Quan", "Đế Vượng",
    "Suy", "Bệnh", "Tử", "Mộ", "Tuyệt", "Thai", "Dưỡng",
];

/// Starting branch index for 长生 of each Heavenly Stem (indexed 0–9).
pub const LONGEVITY_START: [usize; 10] = [
    11, 6,  // 甲→亥, 乙→午
    2, 9,   // 丙→寅, 丁→酉
    2, 9,   // 戊→寅, 己→酉
    5, 0,   // 庚→巳, 辛→子
    8, 3,   // 壬→申, 癸→卯
];

// ── Five-Element Cycles ─────────────────────────────────────────────────────

/// Production cycle: element produces → result.
pub const GEN_MAP: [(&str, &str); 5] = [
    ("Wood", "Fire"), ("Fire", "Earth"), ("Earth", "Metal"),
    ("Metal", "Water"), ("Water", "Wood"),
];

/// Control cycle: element controls → result.
pub const CONTROL_MAP: [(&str, &str); 5] = [
    ("Wood", "Earth"), ("Fire", "Metal"), ("Earth", "Water"),
    ("Metal", "Wood"), ("Water", "Fire"),
];

// ── Branch Interactions ─────────────────────────────────────────────────────

/// Six Combinations (六合) — branch index pairs.
pub const LIU_HE: [(usize, usize); 6] = [
    (0, 1), (2, 11), (3, 10), (4, 9), (5, 8), (6, 7),
];

/// Six Clashes (六冲) — branch index pairs.
pub const LIU_CHONG: [(usize, usize); 6] = [
    (0, 6), (1, 7), (2, 8), (3, 9), (4, 10), (5, 11),
];

/// Six Harms (六害) — branch index pairs.
pub const LIU_HAI: [(usize, usize); 6] = [
    (0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10),
];

/// Harm pairs (害) — same as LIU_HAI.
pub const HARM_PAIRS: [(usize, usize); 6] = [
    (0, 7), (1, 6), (2, 5), (3, 4), (8, 11), (9, 10),
];

/// Self-punishment branches (自刑): 辰(4), 午(6), 酉(9), 亥(11).
pub const SELF_PUNISH_BRANCHES: [usize; 4] = [4, 6, 9, 11];

/// Uncivil punishment pairs (无礼之刑).
const UNCIVIL_PUNISH_PAIRS: [(usize, usize); 1] = [(0, 3)];

/// Bully punishment pairs (恃势之刑).
const BULLY_PUNISH_PAIRS: [(usize, usize); 6] = [
    (2, 5), (5, 8), (2, 8),
    (1, 10), (10, 7), (1, 7),
];

// ── Na Yin Data ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, Serialize)]
pub struct NaYinEntry {
    pub element: &'static str,
    pub chinese: &'static str,
    pub vietnamese: &'static str,
    pub english: &'static str,
}

pub const NAYIN_DATA: [NaYinEntry; 60] = [
    NaYinEntry { element: "Metal", chinese: "海中金", vietnamese: "Hải Trung Kim", english: "Sea Metal" },
    NaYinEntry { element: "Metal", chinese: "海中金", vietnamese: "Hải Trung Kim", english: "Sea Metal" },
    NaYinEntry { element: "Fire", chinese: "爐中火", vietnamese: "Lư Trung Hỏa", english: "Furnace Fire" },
    NaYinEntry { element: "Fire", chinese: "爐中火", vietnamese: "Lư Trung Hỏa", english: "Furnace Fire" },
    NaYinEntry { element: "Wood", chinese: "大林木", vietnamese: "Đại Lâm Mộc", english: "Great Forest Wood" },
    NaYinEntry { element: "Wood", chinese: "大林木", vietnamese: "Đại Lâm Mộc", english: "Great Forest Wood" },
    NaYinEntry { element: "Earth", chinese: "路旁土", vietnamese: "Lộ Bàng Thổ", english: "Roadside Earth" },
    NaYinEntry { element: "Earth", chinese: "路旁土", vietnamese: "Lộ Bàng Thổ", english: "Roadside Earth" },
    NaYinEntry { element: "Metal", chinese: "劍鋒金", vietnamese: "Kiếm Phong Kim", english: "Sword-Point Metal" },
    NaYinEntry { element: "Metal", chinese: "劍鋒金", vietnamese: "Kiếm Phong Kim", english: "Sword-Point Metal" },
    NaYinEntry { element: "Fire", chinese: "山头火", vietnamese: "Sơn Đầu Hỏa", english: "Mountain-Top Fire" },
    NaYinEntry { element: "Fire", chinese: "山头火", vietnamese: "Sơn Đầu Hỏa", english: "Mountain-Top Fire" },
    NaYinEntry { element: "Water", chinese: "澗下水", vietnamese: "Giản Hạ Thuỷ", english: "Ravine Water" },
    NaYinEntry { element: "Water", chinese: "澗下水", vietnamese: "Giản Hạ Thuỷ", english: "Ravine Water" },
    NaYinEntry { element: "Earth", chinese: "城头土", vietnamese: "Thành Đầu Thổ", english: "City Wall Earth" },
    NaYinEntry { element: "Earth", chinese: "城头土", vietnamese: "Thành Đầu Thổ", english: "City Wall Earth" },
    NaYinEntry { element: "Metal", chinese: "白蜡金", vietnamese: "Bạch Lạp Kim", english: "White Wax Metal" },
    NaYinEntry { element: "Metal", chinese: "白蜡金", vietnamese: "Bạch Lạp Kim", english: "White Wax Metal" },
    NaYinEntry { element: "Wood", chinese: "杨柳木", vietnamese: "Dương Liễu Mộc", english: "Willow Wood" },
    NaYinEntry { element: "Wood", chinese: "杨柳木", vietnamese: "Dương Liễu Mộc", english: "Willow Wood" },
    NaYinEntry { element: "Water", chinese: "井泉水", vietnamese: "Tỉnh Tuyền Thủy", english: "Well Spring Water" },
    NaYinEntry { element: "Water", chinese: "井泉水", vietnamese: "Tỉnh Tuyền Thủy", english: "Well Spring Water" },
    NaYinEntry { element: "Earth", chinese: "屋上土", vietnamese: "Ốc Thượng Thổ", english: "Rooftop Earth" },
    NaYinEntry { element: "Earth", chinese: "屋上土", vietnamese: "Ốc Thượng Thổ", english: "Rooftop Earth" },
    NaYinEntry { element: "Fire", chinese: "霹雳火", vietnamese: "Tích Lịch Hỏa", english: "Thunderbolt Fire" },
    NaYinEntry { element: "Fire", chinese: "霹雳火", vietnamese: "Tích Lịch Hỏa", english: "Thunderbolt Fire" },
    NaYinEntry { element: "Wood", chinese: "松柏木", vietnamese: "Tùng Bách Mộc", english: "Pine & Cypress Wood" },
    NaYinEntry { element: "Wood", chinese: "松柏木", vietnamese: "Tùng Bách Mộc", english: "Pine & Cypress Wood" },
    NaYinEntry { element: "Water", chinese: "长流水", vietnamese: "Trường Lưu Thủy", english: "Long Flowing Water" },
    NaYinEntry { element: "Water", chinese: "长流水", vietnamese: "Trường Lưu Thủy", english: "Long Flowing Water" },
    NaYinEntry { element: "Metal", chinese: "砂中金", vietnamese: "Sa Thạch Kim", english: "Sand-Middle Metal" },
    NaYinEntry { element: "Metal", chinese: "砂中金", vietnamese: "Sa Thạch Kim", english: "Sand-Middle Metal" },
    NaYinEntry { element: "Fire", chinese: "山下火", vietnamese: "Sơn Hạ Hỏa", english: "Mountain-Base Fire" },
    NaYinEntry { element: "Fire", chinese: "山下火", vietnamese: "Sơn Hạ Hỏa", english: "Mountain-Base Fire" },
    NaYinEntry { element: "Wood", chinese: "平地木", vietnamese: "Bình Địa Mộc", english: "Flat Land Wood" },
    NaYinEntry { element: "Wood", chinese: "平地木", vietnamese: "Bình Địa Mộc", english: "Flat Land Wood" },
    NaYinEntry { element: "Earth", chinese: "壁上土", vietnamese: "Bích Thượng Thổ", english: "Wall Earth" },
    NaYinEntry { element: "Earth", chinese: "壁上土", vietnamese: "Bích Thượng Thổ", english: "Wall Earth" },
    NaYinEntry { element: "Metal", chinese: "金箔金", vietnamese: "Kim Bạc Kim", english: "Gold Foil Metal" },
    NaYinEntry { element: "Metal", chinese: "金箔金", vietnamese: "Kim Bạc Kim", english: "Gold Foil Metal" },
    NaYinEntry { element: "Fire", chinese: "覆灯火", vietnamese: "Phúc Đăng Hỏa", english: "Covered Lamp Fire" },
    NaYinEntry { element: "Fire", chinese: "覆灯火", vietnamese: "Phúc Đăng Hỏa", english: "Covered Lamp Fire" },
    NaYinEntry { element: "Water", chinese: "天河水", vietnamese: "Thiên Hà Thủy", english: "Sky River Water" },
    NaYinEntry { element: "Water", chinese: "天河水", vietnamese: "Thiên Hà Thủy", english: "Sky River Water" },
    NaYinEntry { element: "Earth", chinese: "大驿土", vietnamese: "Đại Dịch Thổ", english: "Great Post Earth" },
    NaYinEntry { element: "Earth", chinese: "大驿土", vietnamese: "Đại Dịch Thổ", english: "Great Post Earth" },
    NaYinEntry { element: "Metal", chinese: "钗钏金", vietnamese: "Thoa Xuyến Kim", english: "Hairpin Metal" },
    NaYinEntry { element: "Metal", chinese: "钗钏金", vietnamese: "Thoa Xuyến Kim", english: "Hairpin Metal" },
    NaYinEntry { element: "Wood", chinese: "桑柘木", vietnamese: "Tang Chá Mộc", english: "Mulberry Wood" },
    NaYinEntry { element: "Wood", chinese: "桑柘木", vietnamese: "Tang Chá Mộc", english: "Mulberry Wood" },
    NaYinEntry { element: "Water", chinese: "大溪水", vietnamese: "Đại Khê Thủy", english: "Great Stream Water" },
    NaYinEntry { element: "Water", chinese: "大溪水", vietnamese: "Đại Khê Thủy", english: "Great Stream Water" },
    NaYinEntry { element: "Earth", chinese: "沙中土", vietnamese: "Sa Trung Thổ", english: "Sand Earth" },
    NaYinEntry { element: "Earth", chinese: "沙中土", vietnamese: "Sa Trung Thổ", english: "Sand Earth" },
    NaYinEntry { element: "Fire", chinese: "天上火", vietnamese: "Thiên Thượng Hỏa", english: "Heavenly Fire" },
    NaYinEntry { element: "Fire", chinese: "天上火", vietnamese: "Thiên Thượng Hỏa", english: "Heavenly Fire" },
    NaYinEntry { element: "Wood", chinese: "石榴木", vietnamese: "Thạch Lựu Mộc", english: "Pomegranate Wood" },
    NaYinEntry { element: "Wood", chinese: "石榴木", vietnamese: "Thạch Lựu Mộc", english: "Pomegranate Wood" },
    NaYinEntry { element: "Water", chinese: "大海水", vietnamese: "Đại Hải Thủy", english: "Great Ocean Water" },
    NaYinEntry { element: "Water", chinese: "大海水", vietnamese: "Đại Hải Thủy", english: "Great Ocean Water" },
];

// ── Internal helpers ────────────────────────────────────────────────────────

fn gen_of(element: &str) -> &'static str {
    match element {
        "Wood" => "Fire", "Fire" => "Earth", "Earth" => "Metal",
        "Metal" => "Water", "Water" => "Wood", _ => "",
    }
}

fn control_of(element: &str) -> &'static str {
    match element {
        "Wood" => "Earth", "Fire" => "Metal", "Earth" => "Water",
        "Metal" => "Wood", "Water" => "Fire", _ => "",
    }
}

fn pair_in_set(a: usize, b: usize, set: &[(usize, usize)]) -> bool {
    set.iter().any(|&(x, y)| (a == x && b == y) || (a == y && b == x))
}

fn stem_idx_of(stem: &str) -> Option<usize> {
    HEAVENLY_STEMS.iter().position(|&s| s == stem)
}

fn stem_transformation_target(s1: usize, s2: usize) -> Option<&'static str> {
    STEM_TRANSFORMATIONS.iter().find_map(|&(a, b, elem)| {
        if (s1 == a && s2 == b) || (s1 == b && s2 == a) {
            Some(elem)
        } else {
            None
        }
    })
}

fn is_self_punish_branch(b: usize) -> bool {
    SELF_PUNISH_BRANCHES.contains(&b)
}

// ── Core lookup functions ───────────────────────────────────────────────────

/// Return the element of a Heavenly Stem character.
pub fn stem_element(stem: &str) -> &'static str {
    stem_idx_of(stem).map(|i| STEM_ELEMENT[i]).unwrap_or("")
}

/// Return the polarity (Yang/Yin) of a Heavenly Stem character.
pub fn stem_polarity(stem: &str) -> &'static str {
    stem_idx_of(stem).map(|i| STEM_POLARITY[i]).unwrap_or("")
}

/// Return the element of an Earthly Branch character.
pub fn branch_element(branch: &str) -> &'static str {
    EARTHLY_BRANCHES.iter()
        .position(|&b| b == branch)
        .map(|i| BRANCH_ELEMENT[i])
        .unwrap_or("")
}

/// Convert a 1–60 sexagenary cycle number to (stem, branch) characters.
pub fn ganzhi_from_cycle(cycle: usize) -> (&'static str, &'static str) {
    assert!((1..=60).contains(&cycle), "cycle must be 1..=60");
    (HEAVENLY_STEMS[(cycle - 1) % 10], EARTHLY_BRANCHES[(cycle - 1) % 12])
}

// ── Twelve Longevity Stages ─────────────────────────────────────────────────

/// Return (1-based stage index, Chinese stage name) for stem at the given branch.
/// Yang stems progress forward; Yin stems progress backward.
pub fn changsheng_stage(stem_idx: usize, branch_idx: usize) -> (usize, &'static str) {
    let start = LONGEVITY_START[stem_idx];
    let offset = if STEM_POLARITY[stem_idx] == "Yang" {
        (branch_idx as isize - start as isize).rem_euclid(12) as usize
    } else {
        (start as isize - branch_idx as isize).rem_euclid(12) as usize
    };
    let idx = offset + 1;
    (idx, LONGEVITY_STAGES[idx - 1])
}

/// Full life-stage detail with Chinese, English, Vietnamese labels and strength class.
#[derive(Debug, Clone, Serialize)]
pub struct LifeStageDetail {
    pub index: usize,
    pub chinese: &'static str,
    pub english: &'static str,
    pub vietnamese: &'static str,
    pub strength_class: &'static str,
}

/// Return full life-stage detail for a stem at the given branch.
pub fn life_stage_detail(stem_idx: usize, branch_idx: usize) -> LifeStageDetail {
    let (idx, cn) = changsheng_stage(stem_idx, branch_idx);
    LifeStageDetail {
        index: idx,
        chinese: cn,
        english: LONGEVITY_STAGES_EN[idx - 1],
        vietnamese: LONGEVITY_STAGES_VI[idx - 1],
        strength_class: if idx <= 5 { "strong" } else { "weak" },
    }
}

// ── Element Relation & Ten Gods ─────────────────────────────────────────────

/// Classify the five-element relationship of `other_elem` to `dm_elem`.
pub fn element_relation(dm_elem: &str, other_elem: &str) -> &'static str {
    if other_elem == dm_elem { return "same"; }
    if gen_of(other_elem) == dm_elem { return "sheng"; }
    if gen_of(dm_elem) == other_elem { return "wo_sheng"; }
    if control_of(dm_elem) == other_elem { return "wo_ke"; }
    if control_of(other_elem) == dm_elem { return "ke"; }
    ""
}

/// Ten-God name of `target_stem_idx` relative to Day Master at `dm_stem_idx`.
/// Both indices are 0-based into `HEAVENLY_STEMS`.
pub fn ten_god(dm_stem_idx: usize, target_stem_idx: usize) -> &'static str {
    let dm_elem = STEM_ELEMENT[dm_stem_idx];
    let t_elem = STEM_ELEMENT[target_stem_idx];
    let rel = element_relation(dm_elem, t_elem);
    let same_pol = STEM_POLARITY[dm_stem_idx] == STEM_POLARITY[target_stem_idx];
    match (rel, same_pol) {
        ("same", true)     => "比肩",
        ("same", false)    => "劫财",
        ("sheng", true)    => "偏印",
        ("sheng", false)   => "正印",
        ("wo_sheng", true) => "食神",
        ("wo_sheng", false)=> "伤官",
        ("wo_ke", true)    => "偏财",
        ("wo_ke", false)   => "正财",
        ("ke", true)       => "七杀",
        ("ke", false)      => "正官",
        _ => "",
    }
}

// ── Interaction / Transformation types ──────────────────────────────────────

/// Four pillars: `[year, month, day, hour]`, each as `(stem_idx, branch_idx)` 0-based.
pub type FourPillars = [(usize, usize); 4];

#[derive(Debug, Clone, Serialize)]
pub struct StemCombination {
    pub pair: (usize, usize),
    pub stems: (usize, usize),
    pub target_element: &'static str,
}

#[derive(Debug, Clone, Serialize)]
pub struct Transformation {
    pub pair: (usize, usize),
    pub stems: (usize, usize),
    pub target_element: &'static str,
    pub month_support: bool,
    pub leading_present: bool,
    pub blocked: bool,
    pub severely_clashed: bool,
    pub proximity_score: u32,
    pub status: &'static str,
    pub confidence: u32,
}

#[derive(Debug, Clone, Serialize)]
pub struct PhucNgamEvent {
    pub match_type: &'static str,
    pub natal_pillar: usize,
    pub dynamic_stem_idx: usize,
    pub dynamic_branch_idx: usize,
    pub confidence: u32,
}

#[derive(Debug, Clone, Serialize)]
pub struct Punishment {
    pub punishment_type: &'static str,
    pub pair: (usize, usize),
    pub branches: (usize, usize),
    pub severity: u32,
    pub life_areas: &'static [&'static str],
}

// ── Internal detection helpers ──────────────────────────────────────────────

fn check_obstruction(pillars: &FourPillars, p1: usize, p2: usize) -> bool {
    let lo = p1.min(p2);
    let hi = p1.max(p2);
    if hi - lo <= 1 { return false; }
    let e1 = STEM_ELEMENT[pillars[p1].0];
    let e2 = STEM_ELEMENT[pillars[p2].0];
    for mid in (lo + 1)..hi {
        let ctrl = control_of(STEM_ELEMENT[pillars[mid].0]);
        if !ctrl.is_empty() && (ctrl == e1 || ctrl == e2) {
            return true;
        }
    }
    false
}

fn check_severe_clash(pillars: &FourPillars, target_element: &str) -> bool {
    let dm_pol = STEM_POLARITY[pillars[2].0];
    for (i, &(s_idx, _)) in pillars.iter().enumerate() {
        let ctrl = control_of(STEM_ELEMENT[s_idx]);
        if ctrl == target_element && (i == 1 || STEM_POLARITY[s_idx] != dm_pol) {
            return true;
        }
    }
    false
}

// ── Detection functions ─────────────────────────────────────────────────────

/// Detect Heavenly Stem Combination pairs (天干合) among the four pillars.
pub fn detect_stem_combinations(pillars: &FourPillars) -> Vec<StemCombination> {
    let mut results = Vec::new();
    for i in 0..4 {
        for j in (i + 1)..4 {
            let s1 = pillars[i].0;
            let s2 = pillars[j].0;
            if let Some(target) = stem_transformation_target(s1, s2) {
                results.push(StemCombination {
                    pair: (i, j),
                    stems: (s1, s2),
                    target_element: target,
                });
            }
        }
    }
    results
}

/// Detect stem transformations (合化) with full condition checking.
pub fn detect_transformations(
    pillars: &FourPillars,
    month_branch_idx: usize,
) -> Vec<Transformation> {
    let mut results = Vec::new();
    let month_elem = BRANCH_ELEMENT[month_branch_idx];
    let adjacent: [(usize, usize); 3] = [(0, 1), (1, 2), (2, 3)];

    for i in 0..4 {
        for j in (i + 1)..4 {
            let s1 = pillars[i].0;
            let s2 = pillars[j].0;
            let target = match stem_transformation_target(s1, s2) {
                Some(t) => t,
                None => continue,
            };

            let is_adjacent = pair_in_set(i, j, &adjacent);
            let proximity_score: u32 = if is_adjacent { 2 } else { 1 };
            let blocked = check_obstruction(pillars, i, j);
            let month_support = month_elem == target;

            // Leading stem — target element visible in other pillar stems
            let mut leading = false;
            for k in 0..4 {
                if k != i && k != j && STEM_ELEMENT[pillars[k].0] == target {
                    leading = true;
                    break;
                }
            }
            // Also check hidden stems across all pillar branches
            if !leading {
                'outer: for &(_, b_idx) in pillars.iter() {
                    for &hstem in BRANCH_HIDDEN_STEMS[b_idx] {
                        if let Some(idx) = stem_idx_of(hstem) {
                            if STEM_ELEMENT[idx] == target {
                                leading = true;
                                break 'outer;
                            }
                        }
                    }
                }
            }

            let severely_clashed = check_severe_clash(pillars, target);

            let (mut status, mut confidence): (&str, u32) = if proximity_score == 2
                && month_support
                && (leading || !severely_clashed)
                && !blocked
            {
                ("Hóa (successful)", if leading { 95 } else { 85 })
            } else if proximity_score >= 1 && (month_support || leading) && !blocked {
                ("Hợp (bound)", 65)
            } else if blocked {
                ("Blocked", 10)
            } else {
                ("Hợp (bound)", 40)
            };

            if status == "Hóa (successful)" && severely_clashed {
                status = "Hóa (suppressed by clash)";
                confidence = confidence.saturating_sub(30).max(20);
            }

            results.push(Transformation {
                pair: (i, j),
                stems: (s1, s2),
                target_element: target,
                month_support,
                leading_present: leading,
                blocked,
                severely_clashed,
                proximity_score,
                status,
                confidence,
            });
        }
    }
    results
}

/// Detect Phục Ngâm (伏吟) events comparing a dynamic pillar to natal pillars.
pub fn detect_phuc_ngam(
    pillars: &FourPillars,
    dynamic_stem_idx: usize,
    dynamic_branch_idx: usize,
) -> Vec<PhucNgamEvent> {
    let mut results = Vec::new();
    for (i, &(s, b)) in pillars.iter().enumerate() {
        if s == dynamic_stem_idx && b == dynamic_branch_idx {
            results.push(PhucNgamEvent {
                match_type: "exact",
                natal_pillar: i,
                dynamic_stem_idx,
                dynamic_branch_idx,
                confidence: if i == 1 { 95 } else { 90 },
            });
        } else if b == dynamic_branch_idx {
            results.push(PhucNgamEvent {
                match_type: "branch",
                natal_pillar: i,
                dynamic_stem_idx,
                dynamic_branch_idx,
                confidence: if i == 1 { 70 } else { 60 },
            });
        }
    }
    results
}

/// Detect punishments (刑) and harms (害) among the four pillars.
pub fn detect_punishments(pillars: &FourPillars) -> Vec<Punishment> {
    let mut results = Vec::new();
    for i in 0..4 {
        for j in (i + 1)..4 {
            let bi = pillars[i].1;
            let bj = pillars[j].1;
            let involves_day = i == 2 || j == 2;
            let involves_month = i == 1 || j == 1;
            let severity: u32 = if involves_day { 80 } else if involves_month { 70 } else { 50 };

            if bi == bj && is_self_punish_branch(bi) {
                results.push(Punishment {
                    punishment_type: "Tự hình (Self-punish)",
                    pair: (i, j),
                    branches: (bi, bj),
                    severity,
                    life_areas: &["health", "self-sabotage"],
                });
            }
            if pair_in_set(bi, bj, &UNCIVIL_PUNISH_PAIRS) {
                results.push(Punishment {
                    punishment_type: "Vô lễ chi hình (Uncivil)",
                    pair: (i, j),
                    branches: (bi, bj),
                    severity,
                    life_areas: &["relationship", "secrets"],
                });
            }
            if pair_in_set(bi, bj, &BULLY_PUNISH_PAIRS) {
                results.push(Punishment {
                    punishment_type: "Ỷ thế chi hình (Bully)",
                    pair: (i, j),
                    branches: (bi, bj),
                    severity,
                    life_areas: &["career", "power struggles"],
                });
            }
            if pair_in_set(bi, bj, &HARM_PAIRS) {
                results.push(Punishment {
                    punishment_type: "Hại (Harm)",
                    pair: (i, j),
                    branches: (bi, bj),
                    severity,
                    life_areas: &["health", "relationship"],
                });
            }
        }
    }
    results
}

// ── Na Yin lookup ───────────────────────────────────────────────────────────

/// Return Na Yin entry for the given 1–60 sexagenary cycle number.
pub fn nayin_for_cycle(cycle: usize) -> Option<&'static NaYinEntry> {
    if (1..=60).contains(&cycle) {
        Some(&NAYIN_DATA[cycle - 1])
    } else {
        None
    }
}

// ── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stem_element_lookup() {
        assert_eq!(stem_element("甲"), "Wood");
        assert_eq!(stem_element("丙"), "Fire");
        assert_eq!(stem_element("庚"), "Metal");
        assert_eq!(stem_element("癸"), "Water");
    }

    #[test]
    fn test_stem_polarity_lookup() {
        assert_eq!(stem_polarity("甲"), "Yang");
        assert_eq!(stem_polarity("乙"), "Yin");
    }

    #[test]
    fn test_branch_element_lookup() {
        assert_eq!(branch_element("子"), "Water");
        assert_eq!(branch_element("寅"), "Wood");
        assert_eq!(branch_element("午"), "Fire");
    }

    #[test]
    fn test_ganzhi_from_cycle() {
        assert_eq!(ganzhi_from_cycle(1), ("甲", "子"));
        assert_eq!(ganzhi_from_cycle(60), ("癸", "亥"));
    }

    #[test]
    fn test_changsheng_stage() {
        // 甲 (Yang Wood) starts at 亥(11), branch 亥(11) → offset 0 → stage 1 (长生)
        assert_eq!(changsheng_stage(0, 11), (1, "长生"));
        // 甲 at 子(0) → offset (0-11)%12 = 1 → stage 2 (沐浴)
        assert_eq!(changsheng_stage(0, 0), (2, "沐浴"));
    }

    #[test]
    fn test_element_relation() {
        assert_eq!(element_relation("Wood", "Wood"), "same");
        assert_eq!(element_relation("Wood", "Fire"), "wo_sheng");
        assert_eq!(element_relation("Wood", "Water"), "sheng");
        assert_eq!(element_relation("Wood", "Earth"), "wo_ke");
        assert_eq!(element_relation("Wood", "Metal"), "ke");
    }

    #[test]
    fn test_ten_god_self() {
        // 甲 vs 甲 → same element, same polarity → 比肩
        assert_eq!(ten_god(0, 0), "比肩");
        // 甲 vs 乙 → same element, different polarity → 劫财
        assert_eq!(ten_god(0, 1), "劫财");
    }

    #[test]
    fn test_nayin_for_cycle() {
        let ny = nayin_for_cycle(1).unwrap();
        assert_eq!(ny.element, "Metal");
        assert_eq!(ny.chinese, "海中金");
        assert_eq!(ny.english, "Sea Metal");

        let ny60 = nayin_for_cycle(60).unwrap();
        assert_eq!(ny60.element, "Water");
        assert_eq!(ny60.english, "Great Ocean Water");

        assert!(nayin_for_cycle(0).is_none());
        assert!(nayin_for_cycle(61).is_none());
    }

    #[test]
    fn test_detect_punishments_harm() {
        // 子(0) and 未(7) form a harm pair
        let pillars: FourPillars = [(0, 0), (1, 1), (2, 7), (3, 3)];
        let results = detect_punishments(&pillars);
        let harms: Vec<_> = results.iter()
            .filter(|p| p.punishment_type == "Hại (Harm)")
            .collect();
        assert_eq!(harms.len(), 1);
        assert_eq!(harms[0].branches, (0, 7));
    }
}
