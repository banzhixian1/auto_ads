import unittest

from src.constants.placements import REST_OF_SEARCH, TOP_OF_SEARCH
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


if __name__ == "__main__":
    unittest.main()
