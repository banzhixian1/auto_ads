import unittest

from src.constants.placements import (
    PRODUCT_PAGES,
    REST_OF_SEARCH,
    TOP_OF_SEARCH,
    normalize_placement,
)
from src.schemas.keyword import KeywordCandidate
from src.strategy_engine.keyword_expansion import build_keyword_decision


class KeywordExpansionStrategyTestCase(unittest.TestCase):
    def test_high_efficiency_term_prefers_top_of_search(self):
        candidate = KeywordCandidate(
            term="wireless mouse",
            source="seed_term",
            click_share=0.18,
            conversion_share=0.20,
            efficiency=1.11,
            relevance_score=1.0,
        )

        decision = build_keyword_decision(
            candidate=candidate,
            average_order_price=25.0,
            target_acos=0.25,
            placement_rows=[
                {"placement": TOP_OF_SEARCH, "cvr": 0.1},
                {"placement": REST_OF_SEARCH, "cvr": 0.05},
            ],
        )

        self.assertEqual(decision.placement.primary, TOP_OF_SEARCH)
        self.assertTrue(decision.should_launch)

    def test_new_keyword_bid_uses_primary_placement_cvr_and_default_acos(self):
        candidate = KeywordCandidate(
            term="wireless mouse",
            source="seed_term",
            click_share=0.18,
            conversion_share=0.20,
            efficiency=1.11,
            relevance_score=1.0,
        )

        decision = build_keyword_decision(
            candidate=candidate,
            average_order_price=30.0,
            placement_rows=[
                {"placement": TOP_OF_SEARCH, "cvr": 0.2},
                {"placement": REST_OF_SEARCH, "cvr": 0.05},
            ],
        )

        self.assertEqual(decision.bid.suggested_bid, 2.4)

    def test_new_keyword_bid_derives_average_order_price_from_primary_placement(self):
        candidate = KeywordCandidate(
            term="wireless mouse",
            source="seed_term",
            click_share=0.18,
            conversion_share=0.20,
            efficiency=1.11,
            relevance_score=1.0,
        )

        decision = build_keyword_decision(
            candidate=candidate,
            target_acos=0.25,
            placement_rows=[
                {
                    "placement": TOP_OF_SEARCH,
                    "cvr": 0.1,
                    "sales": 200,
                    "orders": 10,
                },
                {
                    "placement": REST_OF_SEARCH,
                    "cvr": 0.05,
                    "sales": 500,
                    "orders": 10,
                },
            ],
        )

        self.assertEqual(decision.bid.suggested_bid, 0.5)
        self.assertEqual(
            decision.bid.calculation["formula"],
            "average_order_price * target_acos * conversion_rate",
        )
        self.assertEqual(decision.bid.calculation["inputs"]["average_order_price"], 20.0)
        self.assertEqual(
            decision.bid.calculation["inputs"]["average_order_price_source"],
            "placement.sales / placement.orders",
        )
        self.assertEqual(decision.bid.calculation["inputs"]["conversion_rate"], 0.1)
        self.assertEqual(decision.bid.calculation["raw_bid"], 0.5)

    def test_new_keyword_bid_prefers_same_sku_average_order_price(self):
        candidate = KeywordCandidate(
            term="wireless mouse",
            source="seed_term",
            click_share=0.18,
            conversion_share=0.20,
            efficiency=1.11,
            relevance_score=1.0,
        )

        decision = build_keyword_decision(
            candidate=candidate,
            target_acos=0.25,
            placement_rows=[
                {
                    "placement": TOP_OF_SEARCH,
                    "cvr": 0.1,
                    "sales": 500,
                    "orders": 10,
                    "sales_same_sku": 200,
                    "orders_same_sku": 10,
                },
            ],
        )

        self.assertEqual(decision.bid.suggested_bid, 0.5)

    def test_low_efficiency_term_prefers_rest_of_search(self):
        candidate = KeywordCandidate(
            term="generic mouse",
            source="seed_term",
            click_share=0.25,
            conversion_share=0.10,
            efficiency=0.4,
            relevance_score=1.0,
        )

        decision = build_keyword_decision(candidate=candidate)

        self.assertEqual(decision.placement.primary, REST_OF_SEARCH)

    def test_rest_of_search_bid_accepts_other_placement_alias(self):
        candidate = KeywordCandidate(
            term="ponchos",
            source="seed_term",
            click_share=0.6765,
            conversion_share=0.1727,
            efficiency=0.255,
            relevance_score=1.0,
        )

        decision = build_keyword_decision(
            candidate=candidate,
            target_acos=0.30,
            placement_rows=[
                {
                    "placement": "other",
                    "cvr": 0.1781,
                    "sales": 13306.45,
                    "orders": 1068,
                },
            ],
        )

        self.assertEqual(decision.placement.primary, REST_OF_SEARCH)
        self.assertEqual(decision.bid.suggested_bid, 0.67)
        self.assertEqual(decision.bid.calculation["inputs"]["placement"], REST_OF_SEARCH)
        self.assertEqual(
            decision.bid.calculation["inputs"]["placement_metrics"]["raw_placement"],
            "other",
        )
        self.assertEqual(
            decision.bid.calculation["inputs"]["placement_metrics"]["normalized_placement"],
            REST_OF_SEARCH,
        )

    def test_normalize_placement_maps_short_report_values_to_strategy_values(self):
        self.assertEqual(normalize_placement("top"), TOP_OF_SEARCH)
        self.assertEqual(normalize_placement("page"), PRODUCT_PAGES)
        self.assertEqual(normalize_placement("other"), REST_OF_SEARCH)


if __name__ == "__main__":
    unittest.main()
