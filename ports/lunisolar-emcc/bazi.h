/*
 * Bazi (Four Pillars of Destiny) analysis module — Emscripten C→WASM port.
 *
 * Mirrors the Rust implementation in ../lunisolar-rs/src/bazi.rs and the
 * Python implementation in ../../lunisolar-py/bazi.py.
 */

#ifndef BAZI_H
#define BAZI_H

#include <emscripten/emscripten.h>

/* ── Element constants ─────────────────────────────────────────────────────── */

#define WOOD  0
#define FIRE  1
#define EARTH 2
#define METAL 3
#define WATER 4

/* ── Struct definitions ────────────────────────────────────────────────────── */

typedef struct {
    int stem_idx;
    int branch_idx;
} BaziPillar;

typedef struct {
    int pair_a;            /* pillar index 0-3 */
    int pair_b;            /* pillar index 0-3 */
    int stem_a;            /* stem index 0-9 */
    int stem_b;            /* stem index 0-9 */
    int target_element;    /* WOOD..WATER */
} StemCombination;

typedef struct {
    int pair_a;
    int pair_b;
    int stem_a;
    int stem_b;
    int target_element;
    int month_support;     /* boolean */
    int leading_present;   /* boolean */
    int blocked;           /* boolean */
    int severely_clashed;  /* boolean */
    int proximity_score;
    const char *status;
    int confidence;
} Transformation;

typedef struct {
    const char *match_type; /* "exact" or "branch" */
    int natal_pillar;       /* pillar index 0-3 */
    int dynamic_stem_idx;
    int dynamic_branch_idx;
    int confidence;
} PhucNgamEvent;

typedef struct {
    const char *punishment_type;
    int pair_a;             /* pillar index 0-3 */
    int pair_b;             /* pillar index 0-3 */
    int branch_a;           /* branch index 0-11 */
    int branch_b;           /* branch index 0-11 */
    int severity;
    const char *life_area_1;
    const char *life_area_2;
} Punishment;

typedef struct {
    int element;           /* WOOD..WATER */
    const char *chinese;
    const char *vietnamese;
    const char *english;
} NaYinEntry;

typedef struct {
    int index;             /* 1-based stage index */
    const char *chinese;
    const char *english;
    const char *vietnamese;
    const char *strength_class; /* "strong" or "weak" */
} LifeStageDetail;

/* ── Extern constant declarations ──────────────────────────────────────────── */

extern const char *ELEMENT_NAMES[5];
extern const char *ELEMENT_NAMES_EN[5];

extern const int STEM_ELEMENT[10];
extern const int STEM_POLARITY[10];
extern const int BRANCH_ELEMENT[12];

extern const char *LONGEVITY_STAGES[12];
extern const char *LONGEVITY_STAGES_EN[12];
extern const char *LONGEVITY_STAGES_VI[12];
extern const int LONGEVITY_START[10];

/* ── Function declarations ─────────────────────────────────────────────────── */

EMSCRIPTEN_KEEPALIVE
int bazi_stem_element(int stem_idx);

EMSCRIPTEN_KEEPALIVE
int bazi_stem_polarity(int stem_idx);

EMSCRIPTEN_KEEPALIVE
int bazi_branch_element(int branch_idx);

EMSCRIPTEN_KEEPALIVE
void bazi_ganzhi_from_cycle(int cycle, int *stem_idx, int *branch_idx);

EMSCRIPTEN_KEEPALIVE
void bazi_changsheng_stage(int stem_idx, int branch_idx,
                           int *stage_idx, const char **stage_name);

EMSCRIPTEN_KEEPALIVE
int bazi_element_relation(int dm_elem, int other_elem);

EMSCRIPTEN_KEEPALIVE
const char *bazi_ten_god(int dm_stem_idx, int target_stem_idx);

EMSCRIPTEN_KEEPALIVE
int bazi_detect_stem_combinations(int pillars[4][2],
                                  StemCombination *results, int max_results);

EMSCRIPTEN_KEEPALIVE
int bazi_detect_transformations(int pillars[4][2],
                                Transformation *results, int max_results);

EMSCRIPTEN_KEEPALIVE
int bazi_detect_phuc_ngam(int pillars[4][2],
                          int dyn_stem, int dyn_branch,
                          PhucNgamEvent *results, int max_results);

EMSCRIPTEN_KEEPALIVE
int bazi_detect_punishments(int pillars[4][2],
                            Punishment *results, int max_results);

EMSCRIPTEN_KEEPALIVE
const NaYinEntry *bazi_nayin_for_cycle(int cycle);

EMSCRIPTEN_KEEPALIVE
void bazi_life_stage_detail(int stem_idx, int branch_idx, LifeStageDetail *out);

#endif /* BAZI_H */
