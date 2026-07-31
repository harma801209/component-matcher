import os
import unittest


os.environ.setdefault("COMPONENT_MATCHER_BUILD_MODE", "1")

import component_matcher as cm


class ElectrolyticMatchingRegressionTests(unittest.TestCase):
    def test_dip_spec_parses_as_leaded_electrolytic(self):
        spec = cm.parse_other_passive_query(
            "直插铝电解电容 DIP_470uF±20%/16V/D6.3*L12mm/105℃"
        )

        self.assertIsNotNone(spec)
        self.assertEqual(spec["器件类型"], "铝电解电容")
        self.assertEqual(spec["安装方式"], "插件")
        self.assertEqual(spec["_body_size"], "6.3*12mm")
        self.assertEqual(spec["工作温度"], "105℃")

    def test_exact_dimensions_are_complete_but_different_dimensions_need_confirmation(self):
        spec = cm.parse_other_passive_query(
            "直插铝电解电容 DIP_470uF±20%/16V/D6.3*L12mm/105℃"
        )
        exact = {
            "_body_size": "6.3*12mm",
            "_temp_low": -40,
            "_temp_high": 105,
            "_mount_style": "插件",
        }
        different = {
            "_body_size": "6.3*11.5mm",
            "_temp_low": -40,
            "_temp_high": 105,
            "_mount_style": "插件",
        }

        self.assertEqual(cm.electrolytic_candidate_confirmation_reasons(exact, spec), [])
        reasons = cm.electrolytic_candidate_confirmation_reasons(different, spec)
        self.assertTrue(any("外形尺寸不一致" in reason for reason in reasons))
        self.assertLess(
            cm.body_size_distance_for_match("6.3*11.5mm", "6.3*12mm"),
            cm.body_size_distance_for_match("10*16mm", "6.3*12mm"),
        )

    def test_real_search_index_returns_cross_brand_candidates_for_reported_specs(self):
        queries = [
            "直插铝电解电容 DIP_470uF±20%/16V/D6.3*L12mm/105℃",
            "直插铝电解电容 DIP_10uF±20%/400V/D6.3*L14mm/105℃",
        ]
        for query in queries:
            with self.subTest(query=query):
                spec = cm.parse_other_passive_query(query)
                pairs = cm.fetch_search_candidate_pairs(spec)
                self.assertIsNotNone(pairs)
                self.assertGreater(len(pairs), 0)
                self.assertGreater(len({brand for brand, _ in pairs}), 1)


if __name__ == "__main__":
    unittest.main()
