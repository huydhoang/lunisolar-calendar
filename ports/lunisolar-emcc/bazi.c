/*
 * Bazi (Four Pillars of Destiny) analysis module — Emscripten C→WASM port.
 *
 * Mirrors the Rust implementation in ../lunisolar-rs/src/bazi.rs and the
 * Python implementation in ../../lunisolar-py/bazi.py.
 */

#include <emscripten/emscripten.h>
#include <string.h>

#include "bazi.h"

/* ── Element names ─────────────────────────────────────────────────────────── */

const char *ELEMENT_NAMES[5] = {
    "\xe6\x9c\xa8",   /* 木 Wood  */
    "\xe7\x81\xab",   /* 火 Fire  */
    "\xe5\x9c\x9f",   /* 土 Earth */
    "\xe9\x87\x91",   /* 金 Metal */
    "\xe6\xb0\xb4"    /* 水 Water */
};

const char *ELEMENT_NAMES_EN[5] = {
    "Wood", "Fire", "Earth", "Metal", "Water"
};

/* ── Element & Polarity for each Heavenly Stem (0-9: 甲乙丙丁戊己庚辛壬癸) ── */

const int STEM_ELEMENT[10] = {
    WOOD, WOOD, FIRE, FIRE, EARTH,
    EARTH, METAL, METAL, WATER, WATER
};

const int STEM_POLARITY[10] = {  /* 0=Yang, 1=Yin */
    0, 1, 0, 1, 0,
    1, 0, 1, 0, 1
};

/* ── Element for each Earthly Branch (0-11: 子丑寅卯辰巳午未申酉戌亥) ──── */

const int BRANCH_ELEMENT[12] = {
    WATER, EARTH, WOOD, WOOD, EARTH, FIRE,
    FIRE, EARTH, METAL, METAL, EARTH, WATER
};

/* ── Hidden stems per branch (as stem indices, -1 = unused) ────────────────── */
/* Up to 3 hidden stems per branch: [main, middle, residual] */

static const int BRANCH_HIDDEN_STEMS[12][3] = {
    { 9, -1, -1},  /* 子: 癸 */
    { 5,  9,  7},  /* 丑: 己 癸 辛 */
    { 0,  2,  4},  /* 寅: 甲 丙 戊 */
    { 1, -1, -1},  /* 卯: 乙 */
    { 4,  1,  9},  /* 辰: 戊 乙 癸 */
    { 2,  4,  6},  /* 巳: 丙 戊 庚 */
    { 3,  5, -1},  /* 午: 丁 己 */
    { 5,  3,  1},  /* 未: 己 丁 乙 */
    { 6,  8,  4},  /* 申: 庚 壬 戊 */
    { 7, -1, -1},  /* 酉: 辛 */
    { 4,  7,  3},  /* 戌: 戊 辛 丁 */
    { 8,  0, -1}   /* 亥: 壬 甲 */
};

static const int BRANCH_HIDDEN_COUNT[12] = {
    1, 3, 3, 1, 3, 3, 2, 3, 3, 1, 3, 2
};

/* ── Five-Element Production / Control Cycles ──────────────────────────────── */
/* gen_of(elem)     → elem produces what   */
/* control_of(elem) → elem controls what   */

static const int GEN_MAP[5] = {
    FIRE, EARTH, METAL, WATER, WOOD
};
/* Wood→Fire, Fire→Earth, Earth→Metal, Metal→Water, Water→Wood */

static const int CONTROL_MAP[5] = {
    EARTH, METAL, WATER, WOOD, FIRE
};
/* Wood→Earth, Fire→Metal, Earth→Water, Metal→Wood, Water→Fire */

/* ── Stem Transformations (天干合化) ───────────────────────────────────────── */
/* 5 canonical pairs: (stem_a, stem_b, target_element) */

static const int STEM_TRANSFORMATIONS[5][3] = {
    {0, 5, EARTH},   /* 甲己 → Earth */
    {1, 6, METAL},   /* 乙庚 → Metal */
    {2, 7, WATER},   /* 丙辛 → Water */
    {3, 8, WOOD},    /* 丁壬 → Wood  */
    {4, 9, FIRE}     /* 戊癸 → Fire  */
};

/* ── Branch Interaction Tables ─────────────────────────────────────────────── */

/* Six Combinations (六合) */
static const int LIU_HE[6][2] = {
    {0, 1}, {2, 11}, {3, 10}, {4, 9}, {5, 8}, {6, 7}
};

/* Six Clashes (六冲) */
static const int LIU_CHONG[6][2] = {
    {0, 6}, {1, 7}, {2, 8}, {3, 9}, {4, 10}, {5, 11}
};

/* Harm pairs (六害) */
static const int HARM_PAIRS[6][2] = {
    {0, 7}, {1, 6}, {2, 5}, {3, 4}, {8, 11}, {9, 10}
};

/* Self-punishment branches (自刑): 辰(4), 午(6), 酉(9), 亥(11) */
static const int SELF_PUNISH_BRANCHES[4] = {4, 6, 9, 11};

/* Uncivil punishment pairs (无礼之刑) */
static const int UNCIVIL_PUNISH_PAIRS[1][2] = {
    {0, 3}
};

/* Bully punishment pairs (恃势之刑) */
static const int BULLY_PUNISH_PAIRS[6][2] = {
    {2, 5}, {5, 8}, {2, 8},
    {1, 10}, {10, 7}, {1, 7}
};

/* ── Twelve Longevity Stages (十二长生) ────────────────────────────────────── */

const char *LONGEVITY_STAGES[12] = {
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰",   "病",   "死",   "墓",   "绝",
    "胎",   "养"
};

const char *LONGEVITY_STAGES_EN[12] = {
    "Growth", "Bath", "Crown Belt", "Coming of Age", "Prosperity Peak",
    "Decline", "Sickness", "Death", "Grave", "Termination",
    "Conception", "Nurture"
};

const char *LONGEVITY_STAGES_VI[12] = {
    "Trường Sinh", "Mộc Dục", "Quan Đới", "Lâm Quan", "Đế Vượng",
    "Suy", "Bệnh", "Tử", "Mộ", "Tuyệt",
    "Thai", "Dưỡng"
};

/* Starting branch index for 长生 of each Heavenly Stem (0-9) */
const int LONGEVITY_START[10] = {
    11, 6,   /* 甲→亥, 乙→午 */
     2, 9,   /* 丙→寅, 丁→酉 */
     2, 9,   /* 戊→寅, 己→酉 */
     5, 0,   /* 庚→巳, 辛→子 */
     8, 3    /* 壬→申, 癸→卯 */
};

/* ── Na Yin Data (60 entries, indexed 0-59 for cycle 1-60) ─────────────────── */

static const NaYinEntry NAYIN_DATA[60] = {
    {METAL, "海中金", "Hải Trung Kim",    "Sea Metal"},             /*  1 甲子 */
    {METAL, "海中金", "Hải Trung Kim",    "Sea Metal"},             /*  2 乙丑 */
    {FIRE,  "爐中火", "Lư Trung Hỏa",    "Furnace Fire"},          /*  3 丙寅 */
    {FIRE,  "爐中火", "Lư Trung Hỏa",    "Furnace Fire"},          /*  4 丁卯 */
    {WOOD,  "大林木", "Đại Lâm Mộc",     "Great Forest Wood"},     /*  5 戊辰 */
    {WOOD,  "大林木", "Đại Lâm Mộc",     "Great Forest Wood"},     /*  6 己巳 */
    {EARTH, "路旁土", "Lộ Bàng Thổ",     "Roadside Earth"},        /*  7 庚午 */
    {EARTH, "路旁土", "Lộ Bàng Thổ",     "Roadside Earth"},        /*  8 辛未 */
    {METAL, "劍鋒金", "Kiếm Phong Kim",   "Sword-Point Metal"},     /*  9 壬申 */
    {METAL, "劍鋒金", "Kiếm Phong Kim",   "Sword-Point Metal"},     /* 10 癸酉 */
    {FIRE,  "山头火", "Sơn Đầu Hỏa",     "Mountain-Top Fire"},     /* 11 甲戌 */
    {FIRE,  "山头火", "Sơn Đầu Hỏa",     "Mountain-Top Fire"},     /* 12 乙亥 */
    {WATER, "澗下水", "Giản Hạ Thuỷ",    "Ravine Water"},          /* 13 丙子 */
    {WATER, "澗下水", "Giản Hạ Thuỷ",    "Ravine Water"},          /* 14 丁丑 */
    {EARTH, "城头土", "Thành Đầu Thổ",   "City Wall Earth"},       /* 15 戊寅 */
    {EARTH, "城头土", "Thành Đầu Thổ",   "City Wall Earth"},       /* 16 己卯 */
    {METAL, "白蜡金", "Bạch Lạp Kim",    "White Wax Metal"},       /* 17 庚辰 */
    {METAL, "白蜡金", "Bạch Lạp Kim",    "White Wax Metal"},       /* 18 辛巳 */
    {WOOD,  "杨柳木", "Dương Liễu Mộc",  "Willow Wood"},           /* 19 壬午 */
    {WOOD,  "杨柳木", "Dương Liễu Mộc",  "Willow Wood"},           /* 20 癸未 */
    {WATER, "井泉水", "Tỉnh Tuyền Thủy", "Well Spring Water"},     /* 21 甲申 */
    {WATER, "井泉水", "Tỉnh Tuyền Thủy", "Well Spring Water"},     /* 22 乙酉 */
    {EARTH, "屋上土", "Ốc Thượng Thổ",   "Rooftop Earth"},         /* 23 丙戌 */
    {EARTH, "屋上土", "Ốc Thượng Thổ",   "Rooftop Earth"},         /* 24 丁亥 */
    {FIRE,  "霹雳火", "Tích Lịch Hỏa",   "Thunderbolt Fire"},      /* 25 戊子 */
    {FIRE,  "霹雳火", "Tích Lịch Hỏa",   "Thunderbolt Fire"},      /* 26 己丑 */
    {WOOD,  "松柏木", "Tùng Bách Mộc",   "Pine & Cypress Wood"},   /* 27 庚寅 */
    {WOOD,  "松柏木", "Tùng Bách Mộc",   "Pine & Cypress Wood"},   /* 28 辛卯 */
    {WATER, "长流水", "Trường Lưu Thủy", "Long Flowing Water"},    /* 29 壬辰 */
    {WATER, "长流水", "Trường Lưu Thủy", "Long Flowing Water"},    /* 30 癸巳 */
    {METAL, "砂中金", "Sa Thạch Kim",    "Sand-Middle Metal"},      /* 31 甲午 */
    {METAL, "砂中金", "Sa Thạch Kim",    "Sand-Middle Metal"},      /* 32 乙未 */
    {FIRE,  "山下火", "Sơn Hạ Hỏa",     "Mountain-Base Fire"},     /* 33 丙申 */
    {FIRE,  "山下火", "Sơn Hạ Hỏa",     "Mountain-Base Fire"},     /* 34 丁酉 */
    {WOOD,  "平地木", "Bình Địa Mộc",    "Flat Land Wood"},         /* 35 戊戌 */
    {WOOD,  "平地木", "Bình Địa Mộc",    "Flat Land Wood"},         /* 36 己亥 */
    {EARTH, "壁上土", "Bích Thượng Thổ", "Wall Earth"},             /* 37 庚子 */
    {EARTH, "壁上土", "Bích Thượng Thổ", "Wall Earth"},             /* 38 辛丑 */
    {METAL, "金箔金", "Kim Bạc Kim",     "Gold Foil Metal"},        /* 39 壬寅 */
    {METAL, "金箔金", "Kim Bạc Kim",     "Gold Foil Metal"},        /* 40 癸卯 */
    {FIRE,  "覆灯火", "Phúc Đăng Hỏa",  "Covered Lamp Fire"},      /* 41 甲辰 */
    {FIRE,  "覆灯火", "Phúc Đăng Hỏa",  "Covered Lamp Fire"},      /* 42 乙巳 */
    {WATER, "天河水", "Thiên Hà Thủy",   "Sky River Water"},        /* 43 丙午 */
    {WATER, "天河水", "Thiên Hà Thủy",   "Sky River Water"},        /* 44 丁未 */
    {EARTH, "大驿土", "Đại Dịch Thổ",    "Great Post Earth"},       /* 45 戊申 */
    {EARTH, "大驿土", "Đại Dịch Thổ",    "Great Post Earth"},       /* 46 己酉 */
    {METAL, "钗钏金", "Thoa Xuyến Kim",  "Hairpin Metal"},          /* 47 庚戌 */
    {METAL, "钗钏金", "Thoa Xuyến Kim",  "Hairpin Metal"},          /* 48 辛亥 */
    {WOOD,  "桑柘木", "Tang Chá Mộc",    "Mulberry Wood"},          /* 49 壬子 */
    {WOOD,  "桑柘木", "Tang Chá Mộc",    "Mulberry Wood"},          /* 50 癸丑 */
    {WATER, "大溪水", "Đại Khê Thủy",    "Great Stream Water"},     /* 51 甲寅 */
    {WATER, "大溪水", "Đại Khê Thủy",    "Great Stream Water"},     /* 52 乙卯 */
    {EARTH, "沙中土", "Sa Trung Thổ",    "Sand Earth"},             /* 53 丙辰 */
    {EARTH, "沙中土", "Sa Trung Thổ",    "Sand Earth"},             /* 54 丁巳 */
    {FIRE,  "天上火", "Thiên Thượng Hỏa","Heavenly Fire"},          /* 55 戊午 */
    {FIRE,  "天上火", "Thiên Thượng Hỏa","Heavenly Fire"},          /* 56 己未 */
    {WOOD,  "石榴木", "Thạch Lựu Mộc",   "Pomegranate Wood"},       /* 57 庚申 */
    {WOOD,  "石榴木", "Thạch Lựu Mộc",   "Pomegranate Wood"},       /* 58 辛酉 */
    {WATER, "大海水", "Đại Hải Thủy",    "Great Ocean Water"},      /* 59 壬戌 */
    {WATER, "大海水", "Đại Hải Thủy",    "Great Ocean Water"}       /* 60 癸亥 */
};

/* ── Ten God names (十神) ──────────────────────────────────────────────────── */

static const char *TEN_GOD_NAMES[5][2] = {
    /* relation        same_pol   diff_pol  */
    /* same      */ { "比肩", "劫财" },
    /* sheng     */ { "偏印", "正印" },
    /* wo_sheng  */ { "食神", "伤官" },
    /* wo_ke     */ { "偏财", "正财" },
    /* ke        */ { "七杀", "正官" }
};

/* ── Internal helpers ──────────────────────────────────────────────────────── */

/* Euclidean remainder (always non-negative) */
static int mod12(int n) {
    int r = n % 12;
    return r < 0 ? r + 12 : r;
}

static int pair_in_set(int a, int b, const int set[][2], int count) {
    for (int i = 0; i < count; i++) {
        if ((a == set[i][0] && b == set[i][1]) ||
            (a == set[i][1] && b == set[i][0]))
            return 1;
    }
    return 0;
}

/* Returns target element index, or -1 if not a transformation pair */
static int stem_transformation_target(int s1, int s2) {
    for (int i = 0; i < 5; i++) {
        if ((s1 == STEM_TRANSFORMATIONS[i][0] && s2 == STEM_TRANSFORMATIONS[i][1]) ||
            (s1 == STEM_TRANSFORMATIONS[i][1] && s2 == STEM_TRANSFORMATIONS[i][0]))
            return STEM_TRANSFORMATIONS[i][2];
    }
    return -1;
}

static int is_self_punish_branch(int b) {
    for (int i = 0; i < 4; i++) {
        if (SELF_PUNISH_BRANCHES[i] == b) return 1;
    }
    return 0;
}

static int check_obstruction(int pillars[4][2], int p1, int p2) {
    int lo = p1 < p2 ? p1 : p2;
    int hi = p1 > p2 ? p1 : p2;
    if (hi - lo <= 1) return 0;
    int e1 = STEM_ELEMENT[pillars[p1][0]];
    int e2 = STEM_ELEMENT[pillars[p2][0]];
    for (int mid = lo + 1; mid < hi; mid++) {
        int ctrl = CONTROL_MAP[STEM_ELEMENT[pillars[mid][0]]];
        if (ctrl == e1 || ctrl == e2) return 1;
    }
    return 0;
}

static int check_severe_clash(int pillars[4][2], int target_element) {
    int dm_pol = STEM_POLARITY[pillars[2][0]];
    for (int i = 0; i < 4; i++) {
        int ctrl = CONTROL_MAP[STEM_ELEMENT[pillars[i][0]]];
        if (ctrl == target_element &&
            (i == 1 || STEM_POLARITY[pillars[i][0]] != dm_pol))
            return 1;
    }
    return 0;
}

/* ── Core lookup functions ─────────────────────────────────────────────────── */

EMSCRIPTEN_KEEPALIVE
int bazi_stem_element(int stem_idx) {
    if (stem_idx < 0 || stem_idx > 9) return -1;
    return STEM_ELEMENT[stem_idx];
}

EMSCRIPTEN_KEEPALIVE
int bazi_stem_polarity(int stem_idx) {
    if (stem_idx < 0 || stem_idx > 9) return -1;
    return STEM_POLARITY[stem_idx];
}

EMSCRIPTEN_KEEPALIVE
int bazi_branch_element(int branch_idx) {
    if (branch_idx < 0 || branch_idx > 11) return -1;
    return BRANCH_ELEMENT[branch_idx];
}

EMSCRIPTEN_KEEPALIVE
void bazi_ganzhi_from_cycle(int cycle, int *stem_idx, int *branch_idx) {
    if (cycle < 1 || cycle > 60 || !stem_idx || !branch_idx) return;
    *stem_idx = (cycle - 1) % 10;
    *branch_idx = (cycle - 1) % 12;
}

/* ── Twelve Longevity Stages ───────────────────────────────────────────────── */

EMSCRIPTEN_KEEPALIVE
void bazi_changsheng_stage(int stem_idx, int branch_idx,
                           int *stage_idx, const char **stage_name) {
    if (stem_idx < 0 || stem_idx > 9 ||
        branch_idx < 0 || branch_idx > 11 ||
        !stage_idx || !stage_name) return;

    int start = LONGEVITY_START[stem_idx];
    int offset;
    if (STEM_POLARITY[stem_idx] == 0) { /* Yang: forward */
        offset = mod12(branch_idx - start);
    } else { /* Yin: backward */
        offset = mod12(start - branch_idx);
    }
    int idx = offset + 1;  /* 1-based */
    *stage_idx = idx;
    *stage_name = LONGEVITY_STAGES[idx - 1];
}

/* ── Element Relation & Ten Gods ───────────────────────────────────────────── */

/*
 * Returns relation code:
 *   0 = same, 1 = sheng (resource), 2 = wo_sheng (output),
 *   3 = wo_ke (wealth), 4 = ke (power), -1 = invalid
 */
EMSCRIPTEN_KEEPALIVE
int bazi_element_relation(int dm_elem, int other_elem) {
    if (dm_elem < 0 || dm_elem > 4 || other_elem < 0 || other_elem > 4) return -1;
    if (other_elem == dm_elem) return 0;                /* same */
    if (GEN_MAP[other_elem] == dm_elem) return 1;       /* sheng */
    if (GEN_MAP[dm_elem] == other_elem) return 2;       /* wo_sheng */
    if (CONTROL_MAP[dm_elem] == other_elem) return 3;   /* wo_ke */
    if (CONTROL_MAP[other_elem] == dm_elem) return 4;   /* ke */
    return -1;
}

EMSCRIPTEN_KEEPALIVE
const char *bazi_ten_god(int dm_stem_idx, int target_stem_idx) {
    if (dm_stem_idx < 0 || dm_stem_idx > 9 ||
        target_stem_idx < 0 || target_stem_idx > 9) return "";

    int dm_elem = STEM_ELEMENT[dm_stem_idx];
    int t_elem = STEM_ELEMENT[target_stem_idx];
    int rel = bazi_element_relation(dm_elem, t_elem);
    if (rel < 0 || rel > 4) return "";

    int same_pol = (STEM_POLARITY[dm_stem_idx] == STEM_POLARITY[target_stem_idx]);
    return TEN_GOD_NAMES[rel][same_pol ? 0 : 1];
}

/* ── Interaction Detection ─────────────────────────────────────────────────── */

EMSCRIPTEN_KEEPALIVE
int bazi_detect_stem_combinations(int pillars[4][2],
                                  StemCombination *results, int max_results) {
    int count = 0;
    for (int i = 0; i < 4 && count < max_results; i++) {
        for (int j = i + 1; j < 4 && count < max_results; j++) {
            int s1 = pillars[i][0];
            int s2 = pillars[j][0];
            int target = stem_transformation_target(s1, s2);
            if (target >= 0) {
                results[count].pair_a = i;
                results[count].pair_b = j;
                results[count].stem_a = s1;
                results[count].stem_b = s2;
                results[count].target_element = target;
                count++;
            }
        }
    }
    return count;
}

EMSCRIPTEN_KEEPALIVE
int bazi_detect_transformations(int pillars[4][2],
                                Transformation *results, int max_results) {
    int count = 0;
    int month_branch_elem = BRANCH_ELEMENT[pillars[1][1]];

    /* Adjacent pillar pairs for proximity */
    static const int adjacent[3][2] = {{0,1}, {1,2}, {2,3}};

    for (int i = 0; i < 4 && count < max_results; i++) {
        for (int j = i + 1; j < 4 && count < max_results; j++) {
            int s1 = pillars[i][0];
            int s2 = pillars[j][0];
            int target = stem_transformation_target(s1, s2);
            if (target < 0) continue;

            int is_adjacent = pair_in_set(i, j, adjacent, 3);
            int proximity_score = is_adjacent ? 2 : 1;
            int blocked = check_obstruction(pillars, i, j);
            int month_support = (month_branch_elem == target);

            /* Leading stem — target element visible in other pillar stems */
            int leading = 0;
            for (int k = 0; k < 4; k++) {
                if (k != i && k != j && STEM_ELEMENT[pillars[k][0]] == target) {
                    leading = 1;
                    break;
                }
            }
            /* Also check hidden stems across all pillar branches */
            if (!leading) {
                for (int k = 0; k < 4 && !leading; k++) {
                    int br = pillars[k][1];
                    for (int h = 0; h < BRANCH_HIDDEN_COUNT[br]; h++) {
                        int hs = BRANCH_HIDDEN_STEMS[br][h];
                        if (hs >= 0 && STEM_ELEMENT[hs] == target) {
                            leading = 1;
                            break;
                        }
                    }
                }
            }

            int severely_clashed = check_severe_clash(pillars, target);

            const char *status;
            int confidence;

            if (proximity_score == 2 && month_support &&
                (leading || !severely_clashed) && !blocked) {
                status = "Hóa (successful)";
                confidence = leading ? 95 : 85;
            } else if (proximity_score >= 1 && (month_support || leading) && !blocked) {
                status = "Hợp (bound)";
                confidence = 65;
            } else if (blocked) {
                status = "Blocked";
                confidence = 10;
            } else {
                status = "Hợp (bound)";
                confidence = 40;
            }

            if (strcmp(status, "Hóa (successful)") == 0 && severely_clashed) {
                status = "Hóa (suppressed by clash)";
                confidence = confidence - 30;
                if (confidence < 20) confidence = 20;
            }

            results[count].pair_a = i;
            results[count].pair_b = j;
            results[count].stem_a = s1;
            results[count].stem_b = s2;
            results[count].target_element = target;
            results[count].month_support = month_support;
            results[count].leading_present = leading;
            results[count].blocked = blocked;
            results[count].severely_clashed = severely_clashed;
            results[count].proximity_score = proximity_score;
            results[count].status = status;
            results[count].confidence = confidence;
            count++;
        }
    }
    return count;
}

EMSCRIPTEN_KEEPALIVE
int bazi_detect_phuc_ngam(int pillars[4][2],
                          int dyn_stem, int dyn_branch,
                          PhucNgamEvent *results, int max_results) {
    int count = 0;
    for (int i = 0; i < 4 && count < max_results; i++) {
        int s = pillars[i][0];
        int b = pillars[i][1];
        if (s == dyn_stem && b == dyn_branch) {
            results[count].match_type = "exact";
            results[count].natal_pillar = i;
            results[count].dynamic_stem_idx = dyn_stem;
            results[count].dynamic_branch_idx = dyn_branch;
            results[count].confidence = (i == 1) ? 95 : 90;
            count++;
        } else if (b == dyn_branch) {
            results[count].match_type = "branch";
            results[count].natal_pillar = i;
            results[count].dynamic_stem_idx = dyn_stem;
            results[count].dynamic_branch_idx = dyn_branch;
            results[count].confidence = (i == 1) ? 70 : 60;
            count++;
        }
    }
    return count;
}

EMSCRIPTEN_KEEPALIVE
int bazi_detect_punishments(int pillars[4][2],
                            Punishment *results, int max_results) {
    int count = 0;
    for (int i = 0; i < 4 && count < max_results; i++) {
        for (int j = i + 1; j < 4 && count < max_results; j++) {
            int bi = pillars[i][1];
            int bj = pillars[j][1];
            int involves_day = (i == 2 || j == 2);
            int involves_month = (i == 1 || j == 1);
            int severity = involves_day ? 80 : (involves_month ? 70 : 50);

            /* Self-punishment */
            if (bi == bj && is_self_punish_branch(bi)) {
                results[count].punishment_type = "Tự hình (Self-punish)";
                results[count].pair_a = i;
                results[count].pair_b = j;
                results[count].branch_a = bi;
                results[count].branch_b = bj;
                results[count].severity = severity;
                results[count].life_area_1 = "health";
                results[count].life_area_2 = "self-sabotage";
                count++;
                if (count >= max_results) return count;
            }

            /* Uncivil punishment */
            if (pair_in_set(bi, bj, UNCIVIL_PUNISH_PAIRS, 1)) {
                results[count].punishment_type = "Vô lễ chi hình (Uncivil)";
                results[count].pair_a = i;
                results[count].pair_b = j;
                results[count].branch_a = bi;
                results[count].branch_b = bj;
                results[count].severity = severity;
                results[count].life_area_1 = "relationship";
                results[count].life_area_2 = "secrets";
                count++;
                if (count >= max_results) return count;
            }

            /* Bully punishment */
            if (pair_in_set(bi, bj, BULLY_PUNISH_PAIRS, 6)) {
                results[count].punishment_type = "Ỷ thế chi hình (Bully)";
                results[count].pair_a = i;
                results[count].pair_b = j;
                results[count].branch_a = bi;
                results[count].branch_b = bj;
                results[count].severity = severity;
                results[count].life_area_1 = "career";
                results[count].life_area_2 = "power struggles";
                count++;
                if (count >= max_results) return count;
            }

            /* Harm */
            if (pair_in_set(bi, bj, HARM_PAIRS, 6)) {
                results[count].punishment_type = "Hại (Harm)";
                results[count].pair_a = i;
                results[count].pair_b = j;
                results[count].branch_a = bi;
                results[count].branch_b = bj;
                results[count].severity = severity;
                results[count].life_area_1 = "health";
                results[count].life_area_2 = "relationship";
                count++;
                if (count >= max_results) return count;
            }
        }
    }
    return count;
}

/* ── Na Yin lookup ─────────────────────────────────────────────────────────── */

EMSCRIPTEN_KEEPALIVE
const NaYinEntry *bazi_nayin_for_cycle(int cycle) {
    if (cycle < 1 || cycle > 60) return (const NaYinEntry *)0;
    return &NAYIN_DATA[cycle - 1];
}

/* ── Life Stage Detail ─────────────────────────────────────────────────────── */

EMSCRIPTEN_KEEPALIVE
void bazi_life_stage_detail(int stem_idx, int branch_idx, LifeStageDetail *out) {
    if (!out || stem_idx < 0 || stem_idx > 9 ||
        branch_idx < 0 || branch_idx > 11) return;

    int stage_idx;
    const char *stage_name;
    bazi_changsheng_stage(stem_idx, branch_idx, &stage_idx, &stage_name);

    out->index = stage_idx;
    out->chinese = stage_name;
    out->english = LONGEVITY_STAGES_EN[stage_idx - 1];
    out->vietnamese = LONGEVITY_STAGES_VI[stage_idx - 1];
    out->strength_class = (stage_idx <= 5) ? "strong" : "weak";
}
