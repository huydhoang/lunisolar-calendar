"""
Tests for the Bazi analysis module.

Validates core tables, Ten Gods, Longevity Stages, Branch Interactions,
Luck Pillars, and integration with the lunisolar engine against the
spec at ``@specs/bazi-analysis-framework.md``.
"""

import unittest

from bazi import (
    BRANCH_HIDDEN_STEMS,
    CONTROL_MAP,
    EARTHLY_BRANCHES,
    GEN_MAP,
    HEAVENLY_STEMS,
    LONGEVITY_START,
    STEM_ELEMENT,
    STEM_POLARITY,
    ZI_XING_BRANCHES,
    _element_relation,
    annual_analysis,
    branch_hidden_with_roles,
    build_chart,
    changsheng_stage,
    classify_structure,
    classify_structure_professional,
    detect_branch_interactions,
    detect_self_punishment,
    detect_xing,
    ganzhi_from_cycle,
    generate_luck_pillars,
    generate_narrative,
    normalize_gender,
    parse_ganzhi,
    rate_chart,
    recommend_useful_god,
    score_day_master,
    ten_god,
    weighted_ten_god_distribution,
)


class TestCoreTables(unittest.TestCase):
    """Verify core tables match the spec."""

    def test_heavenly_stems_count(self):
        self.assertEqual(len(HEAVENLY_STEMS), 10)

    def test_earthly_branches_count(self):
        self.assertEqual(len(EARTHLY_BRANCHES), 12)

    def test_stem_element_coverage(self):
        for s in HEAVENLY_STEMS:
            self.assertIn(s, STEM_ELEMENT)

    def test_stem_polarity_coverage(self):
        for s in HEAVENLY_STEMS:
            self.assertIn(s, STEM_POLARITY)

    def test_stem_polarity_alternates(self):
        """Yang/Yin must alternate."""
        for i, s in enumerate(HEAVENLY_STEMS):
            expected = 'Yang' if i % 2 == 0 else 'Yin'
            self.assertEqual(STEM_POLARITY[s], expected)

    def test_gen_map_cycle(self):
        """Production cycle: Wood→Fire→Earth→Metal→Water→Wood."""
        self.assertEqual(GEN_MAP['Wood'], 'Fire')
        self.assertEqual(GEN_MAP['Fire'], 'Earth')
        self.assertEqual(GEN_MAP['Earth'], 'Metal')
        self.assertEqual(GEN_MAP['Metal'], 'Water')
        self.assertEqual(GEN_MAP['Water'], 'Wood')

    def test_control_map_cycle(self):
        """Control cycle: Wood→Earth, Fire→Metal, etc."""
        self.assertEqual(CONTROL_MAP['Wood'], 'Earth')
        self.assertEqual(CONTROL_MAP['Fire'], 'Metal')
        self.assertEqual(CONTROL_MAP['Earth'], 'Water')
        self.assertEqual(CONTROL_MAP['Metal'], 'Wood')
        self.assertEqual(CONTROL_MAP['Water'], 'Fire')


class TestHiddenStems(unittest.TestCase):
    """Hidden stems verified against spec §2.2."""

    def test_cardinal_branches_single_stem(self):
        """子, 卯, 酉 have one hidden stem each."""
        self.assertEqual(BRANCH_HIDDEN_STEMS['子'], ['癸'])
        self.assertEqual(BRANCH_HIDDEN_STEMS['卯'], ['乙'])
        self.assertEqual(BRANCH_HIDDEN_STEMS['酉'], ['辛'])

    def test_horse_two_stems(self):
        """午 has two hidden stems: 丁 (main), 己 (middle)."""
        self.assertEqual(BRANCH_HIDDEN_STEMS['午'], ['丁', '己'])

    def test_pig_two_stems(self):
        """亥 has two hidden stems: 壬, 甲."""
        self.assertEqual(BRANCH_HIDDEN_STEMS['亥'], ['壬', '甲'])

    def test_ox_three_stems(self):
        """丑 = 己 (main), 癸 (middle), 辛 (residual)."""
        self.assertEqual(BRANCH_HIDDEN_STEMS['丑'], ['己', '癸', '辛'])

    def test_tiger_three_stems(self):
        """寅 = 甲 (main), 丙 (middle), 戊 (residual)."""
        self.assertEqual(BRANCH_HIDDEN_STEMS['寅'], ['甲', '丙', '戊'])

    def test_goat_three_stems_order(self):
        """未 = 己 (main), 丁 (middle), 乙 (residual) per spec."""
        self.assertEqual(BRANCH_HIDDEN_STEMS['未'], ['己', '丁', '乙'])

    def test_dog_three_stems(self):
        """戌 = 戊 (main), 辛 (middle), 丁 (residual)."""
        self.assertEqual(BRANCH_HIDDEN_STEMS['戌'], ['戊', '辛', '丁'])

    def test_all_branches_covered(self):
        for b in EARTHLY_BRANCHES:
            self.assertIn(b, BRANCH_HIDDEN_STEMS)

    def test_branch_hidden_with_roles(self):
        roles = branch_hidden_with_roles('寅')
        self.assertEqual(roles, [('main', '甲'), ('middle', '丙'), ('residual', '戊')])

    def test_branch_hidden_with_roles_single(self):
        roles = branch_hidden_with_roles('子')
        self.assertEqual(roles, [('main', '癸')])


class TestGanzhi(unittest.TestCase):
    """Tests for ganzhi_from_cycle and parse_ganzhi."""

    def test_ganzhi_from_cycle_jiazi(self):
        """Cycle 1 = 甲子."""
        self.assertEqual(ganzhi_from_cycle(1), ('甲', '子'))

    def test_ganzhi_from_cycle_yichou(self):
        """Cycle 2 = 乙丑."""
        self.assertEqual(ganzhi_from_cycle(2), ('乙', '丑'))

    def test_ganzhi_from_cycle_bingyin(self):
        """Cycle 3 = 丙寅."""
        self.assertEqual(ganzhi_from_cycle(3), ('丙', '寅'))

    def test_ganzhi_from_cycle_dingsi(self):
        """Cycle 54 = 丁巳."""
        self.assertEqual(ganzhi_from_cycle(54), ('丁', '巳'))

    def test_ganzhi_from_cycle_bingwu(self):
        """Cycle 43 = 丙午."""
        self.assertEqual(ganzhi_from_cycle(43), ('丙', '午'))

    def test_ganzhi_from_cycle_jiawu(self):
        """Cycle 31 = 甲午."""
        self.assertEqual(ganzhi_from_cycle(31), ('甲', '午'))

    def test_ganzhi_from_cycle_bounds(self):
        """Cycle 60 is valid; 0 and 61 raise ValueError."""
        stem, branch = ganzhi_from_cycle(60)
        self.assertIn(stem, HEAVENLY_STEMS)
        self.assertIn(branch, EARTHLY_BRANCHES)
        with self.assertRaises(ValueError):
            ganzhi_from_cycle(0)
        with self.assertRaises(ValueError):
            ganzhi_from_cycle(61)


class TestParseGanzhi(unittest.TestCase):

    def test_valid(self):
        self.assertEqual(parse_ganzhi('甲子'), ('甲', '子'))

    def test_whitespace(self):
        self.assertEqual(parse_ganzhi(' 乙丑 '), ('乙', '丑'))

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            parse_ganzhi('甲')

    def test_invalid_stem(self):
        with self.assertRaises(ValueError):
            parse_ganzhi('X子')

    def test_invalid_branch(self):
        with self.assertRaises(ValueError):
            parse_ganzhi('甲X')


class TestTenGods(unittest.TestCase):
    """Ten Gods verified against spec §1.1 relationship table."""

    def test_same_element_same_polarity(self):
        """比肩: same element, same polarity."""
        self.assertEqual(ten_god('甲', '甲'), '比肩')

    def test_same_element_diff_polarity(self):
        """劫财: same element, opposite polarity."""
        self.assertEqual(ten_god('甲', '乙'), '劫财')

    def test_i_produce_same_polarity(self):
        """食神: element I produce, same polarity."""
        # 甲(Wood Yang) produces Fire; 丙(Fire Yang) = same polarity → 食神
        self.assertEqual(ten_god('甲', '丙'), '食神')

    def test_i_produce_diff_polarity(self):
        """伤官: element I produce, opposite polarity."""
        # 甲(Wood Yang) produces Fire; 丁(Fire Yin) = diff polarity → 伤官
        self.assertEqual(ten_god('甲', '丁'), '伤官')

    def test_i_control_same_polarity(self):
        """偏财: element I control, same polarity."""
        # 甲(Wood Yang) controls Earth; 戊(Earth Yang) → 偏财
        self.assertEqual(ten_god('甲', '戊'), '偏财')

    def test_i_control_diff_polarity(self):
        """正财: element I control, opposite polarity."""
        # 甲(Wood Yang) controls Earth; 己(Earth Yin) → 正财
        self.assertEqual(ten_god('甲', '己'), '正财')

    def test_controls_me_same_polarity(self):
        """七杀: element that controls me, same polarity."""
        # 甲(Wood Yang) controlled by Metal; 庚(Metal Yang) → 七杀
        self.assertEqual(ten_god('甲', '庚'), '七杀')

    def test_controls_me_diff_polarity(self):
        """正官: element that controls me, opposite polarity."""
        # 甲(Wood Yang) controlled by Metal; 辛(Metal Yin) → 正官
        self.assertEqual(ten_god('甲', '辛'), '正官')

    def test_produces_me_same_polarity(self):
        """偏印: element that produces me, same polarity."""
        # 甲(Wood Yang) produced by Water; 壬(Water Yang) → 偏印
        self.assertEqual(ten_god('甲', '壬'), '偏印')

    def test_produces_me_diff_polarity(self):
        """正印: element that produces me, opposite polarity."""
        # 甲(Wood Yang) produced by Water; 癸(Water Yin) → 正印
        self.assertEqual(ten_god('甲', '癸'), '正印')

    def test_fire_dm(self):
        """Cross-check with a Fire Day Master."""
        # 丙(Fire Yang): Water controls Fire
        self.assertEqual(ten_god('丙', '壬'), '七杀')
        self.assertEqual(ten_god('丙', '癸'), '正官')
        # Fire produces Earth
        self.assertEqual(ten_god('丙', '戊'), '食神')
        # Wood produces Fire
        self.assertEqual(ten_god('丙', '甲'), '偏印')


class TestLongevityStages(unittest.TestCase):
    """Longevity stages verified against spec §3.3 and §3.4 examples."""

    def test_starting_branches(self):
        """Each stem starts at the branch listed in spec §3.3."""
        for stem, expected_branch in LONGEVITY_START.items():
            idx, stage = changsheng_stage(stem, expected_branch)
            self.assertEqual(idx, 1, f"{stem} at {expected_branch} should be stage 1 (长生)")
            self.assertEqual(stage, '长生')

    def test_yang_wood_forward_example(self):
        """Spec §3.4: 甲 forward from 亥 → 卯 is 帝旺 (stage 5)."""
        idx, stage = changsheng_stage('甲', '卯')
        self.assertEqual(idx, 5)
        self.assertEqual(stage, '帝旺')

    def test_yang_wood_decline(self):
        """甲 at 辰 should be 衰 (stage 6)."""
        idx, stage = changsheng_stage('甲', '辰')
        self.assertEqual(idx, 6)
        self.assertEqual(stage, '衰')

    def test_yin_wood_backward_example(self):
        """Spec §3.4: 乙 backward from 午 → 巳 is 沐浴 (stage 2)."""
        idx, stage = changsheng_stage('乙', '巳')
        self.assertEqual(idx, 2)
        self.assertEqual(stage, '沐浴')

    def test_yin_wood_officer(self):
        """乙 backward: 午→巳→辰→卯 = 临官 (stage 4)."""
        idx, stage = changsheng_stage('乙', '卯')
        self.assertEqual(idx, 4)
        self.assertEqual(stage, '临官')

    def test_yang_fire_starts_at_yin(self):
        """丙 starts at 寅."""
        idx, stage = changsheng_stage('丙', '寅')
        self.assertEqual(idx, 1)
        self.assertEqual(stage, '长生')

    def test_yang_earth_shares_with_fire(self):
        """戊 starts at 寅 (same as 丙), per spec §3.3 note."""
        idx, stage = changsheng_stage('戊', '寅')
        self.assertEqual(idx, 1)
        self.assertEqual(stage, '长生')


class TestBuildChart(unittest.TestCase):

    def setUp(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        self.chart = build_chart(1, 2, 3, 54, "male")

    def test_day_master(self):
        self.assertEqual(self.chart['day_master']['stem'], '丙')
        self.assertEqual(self.chart['day_master']['element'], 'Fire')

    def test_four_pillars(self):
        self.assertEqual(self.chart['pillars']['year']['stem'], '甲')
        self.assertEqual(self.chart['pillars']['year']['branch'], '子')
        self.assertEqual(self.chart['pillars']['month']['stem'], '乙')
        self.assertEqual(self.chart['pillars']['month']['branch'], '丑')
        self.assertEqual(self.chart['pillars']['day']['stem'], '丙')
        self.assertEqual(self.chart['pillars']['day']['branch'], '寅')
        self.assertEqual(self.chart['pillars']['hour']['stem'], '丁')
        self.assertEqual(self.chart['pillars']['hour']['branch'], '巳')

    def test_gender_stored(self):
        self.assertEqual(self.chart['gender'], 'male')

    def test_ten_gods_assigned(self):
        # Year stem 甲 (Wood) vs DM 丙 (Fire): Wood produces Fire → 偏印
        self.assertEqual(self.chart['pillars']['year']['ten_god'], '偏印')

    def test_hidden_stems_present(self):
        hidden = self.chart['pillars']['day']['hidden']
        self.assertEqual(len(hidden), 3)
        self.assertEqual(hidden[0], ('main', '甲'))


class TestScoreDayMaster(unittest.TestCase):

    def test_example_chart(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        score, strength = score_day_master(chart)
        self.assertIsInstance(score, int)
        self.assertIn(strength, ('strong', 'weak', 'balanced'))

    def test_strong_fire_chart(self):
        """丙 DM in month branch 午 (Fire peak) should be strong."""
        # 甲午=31, 丙午=43, 丁巳=54
        chart = build_chart(31, 43, 43, 54, "male")
        score, strength = score_day_master(chart)
        self.assertEqual(strength, 'strong')


class TestBranchInteractions(unittest.TestCase):

    def test_six_combination(self):
        """子 + 丑 should trigger 六合."""
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        interactions = detect_branch_interactions(chart)
        self.assertTrue(any('子' in p and '丑' in p for p in interactions['六合']))

    def test_six_clash(self):
        """子 + 午 should trigger 六冲."""
        # 甲子=1, 乙丑=2, 丙午=43, 丁巳=54
        chart = build_chart(1, 2, 43, 54, "male")
        interactions = detect_branch_interactions(chart)
        self.assertTrue(any('子' in p and '午' in p for p in interactions['六冲']))

    def test_self_punishment(self):
        """午 + 午 should trigger 自刑."""
        # year=甲午=31, month=丙午=43, day=丙寅=3, hour=丁巳=54
        chart = build_chart(31, 43, 3, 54, "male")
        interactions = detect_branch_interactions(chart)
        self.assertTrue(len(interactions['自刑']) > 0)
        entry = interactions['自刑'][0]
        self.assertEqual(entry['branch'], '午')
        self.assertEqual(entry['count'], 2)
        self.assertIn(entry['mode'], ('complete', 'partial'))

    def test_no_false_self_punishment(self):
        """子 + 子 is NOT a self-punishment branch (子 not in ZI_XING set)."""
        self.assertNotIn('子', ZI_XING_BRANCHES)

    def test_san_he(self):
        """寅 + 午 + 戌 → Fire 三合."""
        # year=甲寅=51, month=丙午=43, day=戊戌=35, hour=庚子=37
        chart = build_chart(51, 43, 35, 37, "male")
        interactions = detect_branch_interactions(chart)
        self.assertTrue(len(interactions['三合']) > 0)

    def test_harm(self):
        """子 + 未 should trigger 害."""
        # 甲子=1, 己未=56, 丙寅=3, 丁巳=54
        chart = build_chart(1, 56, 3, 54, "male")
        interactions = detect_branch_interactions(chart)
        self.assertTrue(any('子' in p and '未' in p for p in interactions['害']))

    def test_san_he_partial_no_match(self):
        """Only 2 of 3 三合 branches should NOT trigger 三合."""
        # year=甲寅=51, month=丙午=43, day=丙寅=3, hour=丁巳=54
        chart = build_chart(51, 43, 3, 54, "male")
        interactions = detect_branch_interactions(chart)
        self.assertEqual(len(interactions['三合']), 0)

    def test_xing_partial_match(self):
        """2 of 3 punishment branches should still trigger 刑 (partial)."""
        # year=甲寅=51(寅), month=丙申=33(申), day=丙寅=3(寅), hour=丁卯=4(卯)
        # branches = {寅, 申, 卯} → 2 of {寅,巳,申} → partial
        chart = build_chart(51, 33, 3, 4, "male")
        interactions = detect_branch_interactions(chart)
        self.assertTrue(len(interactions['刑']) > 0)
        entry = interactions['刑'][0]
        self.assertEqual(entry['mode'], 'partial')
        self.assertEqual(entry['found'], 2)


class TestLuckPillars(unittest.TestCase):

    def test_count(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        pillars = generate_luck_pillars(chart, count=8)
        self.assertEqual(len(pillars), 8)

    def test_forward_yang_male(self):
        """Yang year + male → forward. 乙丑 → next is 丙寅."""
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        pillars = generate_luck_pillars(chart, count=3)
        self.assertEqual(pillars[0], ('丙', '寅'))
        self.assertEqual(pillars[1], ('丁', '卯'))
        self.assertEqual(pillars[2], ('戊', '辰'))

    def test_backward_yin_male(self):
        """Yin year + male → backward. 乙丑 month → prev is 甲子."""
        # 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(2, 2, 3, 54, "male")
        pillars = generate_luck_pillars(chart, count=2)
        self.assertEqual(pillars[0], ('甲', '子'))
        self.assertEqual(pillars[1], ('癸', '亥'))

    def test_forward_yin_female(self):
        """Yin year + female → forward."""
        # 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(2, 2, 3, 54, "female")
        pillars = generate_luck_pillars(chart, count=1)
        self.assertEqual(pillars[0], ('丙', '寅'))


class TestAnnualAnalysis(unittest.TestCase):

    def test_basic_analysis(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54; flowing year 丙午=43
        chart = build_chart(1, 2, 3, 54, "male")
        result = annual_analysis(chart, 43)
        self.assertIn('year_ten_god', result)
        self.assertIn('interactions', result)
        self.assertIn('strength_delta', result)

    def test_year_ten_god(self):
        """丙 year stem vs 丙 DM → 比肩."""
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54; flowing year 丙午=43
        chart = build_chart(1, 2, 3, 54, "male")
        result = annual_analysis(chart, 43)
        self.assertEqual(result['year_ten_god'], '比肩')


class TestStructure(unittest.TestCase):

    def test_basic_structure(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        _, strength = score_day_master(chart)
        structure = classify_structure(chart, strength)
        self.assertIsInstance(structure, str)

    def test_professional_structure(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        _, strength = score_day_master(chart)
        struct, score = classify_structure_professional(chart, strength)
        self.assertIsInstance(struct, str)
        self.assertIsInstance(score, (int, float))


class TestUsefulGod(unittest.TestCase):

    def test_strong_dm(self):
        result = recommend_useful_god(
            {'day_master': {'element': 'Fire'}}, 'strong'
        )
        # Strong Fire DM: favorable = [Earth (output), Metal (wealth)]
        self.assertEqual(result['favorable'], ['Earth', 'Metal'])
        self.assertEqual(result['avoid'], ['Fire'])

    def test_weak_dm(self):
        result = recommend_useful_god(
            {'day_master': {'element': 'Fire'}}, 'weak'
        )
        # Weak Fire DM: favorable = [Wood (resource), Fire (companion)]
        self.assertEqual(result['favorable'], ['Wood', 'Fire'])
        self.assertEqual(result['avoid'], ['Metal'])


class TestChartRating(unittest.TestCase):

    def test_rating_range(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        rating = rate_chart(chart)
        self.assertGreaterEqual(rating, 0)
        self.assertLessEqual(rating, 100)


class TestNarrative(unittest.TestCase):

    def test_narrative_contains_day_master(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        _, strength = score_day_master(chart)
        interactions = detect_branch_interactions(chart)
        structure = classify_structure(chart, strength)
        narrative = generate_narrative(chart, strength, structure, interactions)
        self.assertIn('Day Master', narrative)
        self.assertIn('丙', narrative)
        self.assertIn('Fire', narrative)


class TestWeightedDistribution(unittest.TestCase):

    def test_month_pillar_weighted_higher(self):
        # 甲子=1, 乙丑=2, 丙寅=3, 丁巳=54
        chart = build_chart(1, 2, 3, 54, "male")
        dist = weighted_ten_god_distribution(chart)
        self.assertIsInstance(dist, dict)
        self.assertTrue(all(v > 0 for v in dist.values()))


class TestNormalizeGender(unittest.TestCase):
    """Tests for gender validation and normalization."""

    def test_canonical_male(self):
        self.assertEqual(normalize_gender('male'), 'male')

    def test_canonical_female(self):
        self.assertEqual(normalize_gender('female'), 'female')

    def test_short_alias_m(self):
        self.assertEqual(normalize_gender('m'), 'male')

    def test_short_alias_f(self):
        self.assertEqual(normalize_gender('f'), 'female')

    def test_chinese_male(self):
        self.assertEqual(normalize_gender('男'), 'male')

    def test_chinese_female(self):
        self.assertEqual(normalize_gender('女'), 'female')

    def test_case_insensitive(self):
        self.assertEqual(normalize_gender('Male'), 'male')
        self.assertEqual(normalize_gender('FEMALE'), 'female')

    def test_whitespace_stripped(self):
        self.assertEqual(normalize_gender('  male  '), 'male')

    def test_none_raises(self):
        with self.assertRaises(ValueError):
            normalize_gender(None)

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            normalize_gender('unknown')

    def test_build_chart_validates_gender(self):
        with self.assertRaises(ValueError):
            build_chart(1, 2, 3, 54, "invalid_gender")

    def test_build_chart_normalizes_gender(self):
        chart = build_chart(1, 2, 3, 54, "m")
        self.assertEqual(chart['gender'], 'male')

    def test_generate_luck_pillars_validates_gender(self):
        """Luck pillar generation validates the chart's stored gender."""
        chart = build_chart(1, 2, 3, 54, "male")
        chart['gender'] = 'invalid'
        with self.assertRaises(ValueError):
            generate_luck_pillars(chart)


class TestDetectSelfPunishment(unittest.TestCase):
    """Tests for the robust detect_self_punishment function."""

    def test_basic_self_punishment(self):
        """午 + 午 detected as self-punishment."""
        chart = build_chart(31, 43, 3, 54, "male")
        results = detect_self_punishment(chart)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['branch'], '午')
        self.assertEqual(results[0]['count'], 2)
        self.assertEqual(results[0]['mode'], 'partial')

    def test_no_self_punishment_non_zi_branch(self):
        """子 + 子 is not a self-punishment branch."""
        chart = build_chart(1, 37, 3, 54, "male")  # 庚子=37, 甲子=1
        results = detect_self_punishment(chart)
        self.assertEqual(len(results), 0)

    def test_require_adjacent_true(self):
        """With require_adjacent=True, adjacent 午 pillars detected."""
        chart = build_chart(31, 43, 3, 54, "male")  # year=午, month=午 (adjacent)
        results = detect_self_punishment(chart, require_adjacent=True)
        self.assertEqual(len(results), 1)

    def test_require_adjacent_non_adjacent(self):
        """With require_adjacent=True, non-adjacent duplicates are filtered out."""
        # year=戊辰(5), month=乙丑(2), day=壬辰(29), hour=丁巳(54)
        # 辰 at positions 0 and 2 (year and day) — not adjacent
        chart = build_chart(5, 2, 29, 54, "male")
        results = detect_self_punishment(chart, require_adjacent=True)
        self.assertEqual(len(results), 0)

    def test_require_exposed_main(self):
        """With require_exposed_main=True, checks main hidden stem exposure."""
        chart = build_chart(31, 43, 3, 54, "male")
        results = detect_self_punishment(chart, require_exposed_main=True)
        # 午 main hidden stem is 丁; year stem is 甲, month stem is 丙
        # Neither is 丁, so this should NOT match
        self.assertEqual(len(results), 0)

    def test_require_exposed_main_positive(self):
        """With require_exposed_main=True, matches when main stem IS exposed."""
        # year=戊辰(5), month=庚辰(17), day=丙寅(3), hour=丁巳(54)
        # 辰 at positions 0,1; main hidden stem of 辰 is 戊; year stem is 戊 → exposed
        chart = build_chart(5, 17, 3, 54, "male")
        results = detect_self_punishment(chart, require_exposed_main=True)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['branch'], '辰')


class TestDetectXing(unittest.TestCase):
    """Tests for the graded detect_xing function."""

    def test_partial_xing(self):
        """2 of 3 punishment branches detected as partial."""
        # year=甲寅=51(寅), month=丙申=33(申), day=丙寅=3(寅), hour=丁卯=4(卯)
        # branches = {寅, 申, 卯} → 2 of {寅,巳,申} → partial
        chart = build_chart(51, 33, 3, 4, "male")
        results = detect_xing(chart, strict=False)
        partial = [r for r in results if r['mode'] == 'partial']
        self.assertTrue(len(partial) > 0)

    def test_strict_no_partial(self):
        """strict=True should NOT report partial matches."""
        # branches = {寅, 申, 卯} → only 2 of {寅,巳,申}
        chart = build_chart(51, 33, 3, 4, "male")
        results = detect_xing(chart, strict=True)
        partial = [r for r in results if r['mode'] == 'partial']
        self.assertEqual(len(partial), 0)

    def test_complete_xing(self):
        """All 3 branches present → complete mode."""
        # 寅巳申 = graceless punishment. Need 寅, 巳, 申 in branches.
        # 甲寅=51, 辛巳=18, 壬申=9, 丁卯=4
        chart = build_chart(51, 18, 9, 4, "male")
        results = detect_xing(chart, strict=False)
        complete = [r for r in results if r['mode'] == 'complete']
        self.assertTrue(len(complete) > 0)

    def test_strict_complete_xing(self):
        """strict=True should report complete matches."""
        chart = build_chart(51, 18, 9, 4, "male")
        results = detect_xing(chart, strict=True)
        self.assertTrue(len(results) > 0)
        self.assertTrue(all(r['mode'] == 'complete' for r in results))


if __name__ == '__main__':
    unittest.main()
