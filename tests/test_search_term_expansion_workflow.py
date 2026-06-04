import unittest

from src.schemas.workflow import SearchTermExpansionRequest
from src.workflows.search_term_expansion import run_search_term_expansion


class FakeAbaService:
    def find_seed_terms_by_asin(self, asin: str, report_date: int) -> list[str]:
        return ["wireless mouse", "ergonomic mouse"]

    def find_high_conversion_asins(self, search_term: str, report_date: int) -> list[str]:
        mapping = {
            "wireless mouse": ["B00TERM1"],
            "office mouse": ["B00TERM2"],
        }
        return mapping.get(search_term, [])

    def reverse_lookup_terms_by_asin(self, asin: str, report_date: int) -> list[str]:
        mapping = {
            "B001FLOW": ["wireless mouse", "gaming mouse"],
            "B000TEST": ["wireless mouse", "ergonomic mouse"],
            "B000TEST2": ["office mouse", "bluetooth mouse"],
            "B00TERM1": ["portable mouse", "gaming mouse"],
            "B00TERM2": ["office mouse", "silent mouse"],
        }
        return mapping.get(asin, ["wireless mouse"])

    def build_keyword_candidate(self, search_term: str, source: str):
        from src.schemas.keyword import KeywordCandidate

        metrics_map = {
            "wireless mouse": (0.22, 0.19, 0.86),
            "ergonomic mouse": (0.12, 0.18, 1.50),
            "gaming mouse": (0.28, 0.14, 0.50),
            "office mouse": (0.10, 0.08, 0.80),
            "portable mouse": (0.16, 0.17, 1.06),
            "bluetooth mouse": (0.14, 0.12, 0.86),
            "silent mouse": (0.18, 0.16, 0.89),
        }
        click_share, conversion_share, efficiency = metrics_map.get(
            search_term,
            (0.0, 0.0, 0.0),
        )
        return KeywordCandidate(
            term=search_term,
            source=source,
            click_share=click_share,
            conversion_share=conversion_share,
            efficiency=efficiency,
        )


class FakeAdsReportService:
    def __init__(self, rows: list[dict]):
        self.rows = rows

    def get_user_search_term_rows(self, asin: str, start_date: str, end_date: str) -> list[dict]:
        return self.rows

    def split_user_search_terms(self, rows: list[dict]) -> tuple[list[str], list[str]]:
        keyword_terms: list[str] = []
        product_asins: list[str] = []
        for row in rows:
            if row["term_type"] == "keyword":
                keyword_terms.append(row["search_term"])
            elif row["term_type"] == "product":
                product_asins.append(row["search_term"])
        return keyword_terms, product_asins

    def select_high_value_terms(self, rows: list[dict]) -> list[str]:
        return [row["search_term"] for row in rows if row["term_type"] == "keyword" and row.get("orders", 0) > 0]

    def select_high_value_product_asins(self, rows: list[dict]) -> list[str]:
        return [row["search_term"] for row in rows if row["term_type"] == "product" and row.get("orders", 0) > 0]


class SearchTermExpansionWorkflowTestCase(unittest.TestCase):
    def test_run_search_term_expansion(self):
        request = SearchTermExpansionRequest(
            report_date=202526,
            product_asin="B00SELF",
            start_date="2026-05-01",
            end_date="2026-05-31",
            seed_search_terms=["wireless mouse"],
            competitor_asins=["B000TEST"],
            product_title="Wireless ergonomic mouse",
            product_features=["silent click", "usb receiver"],
            average_order_price=29.9,
            target_acos=0.25,
        )

        result = run_search_term_expansion(
            request=request,
            aba_service=FakeAbaService(),
            ads_report_service=FakeAdsReportService(
                rows=[
                    {"term_type": "keyword", "search_term": "wireless mouse", "orders": 3, "clicks": 10},
                    {"term_type": "product", "search_term": "B001FLOW", "orders": 2, "clicks": 8},
                ]
            ),
        )

        self.assertIn("wireless mouse", result.seeds)
        self.assertEqual(result.product_seed_asins, ["B001FLOW"])
        self.assertEqual(result.high_value_terms, ["wireless mouse"])
        self.assertEqual(result.high_value_asins, ["B001FLOW"])
        candidate_terms = [candidate.term for candidate in result.candidates]
        self.assertIn("portable mouse", candidate_terms)
        self.assertIn("gaming mouse", candidate_terms)
        self.assertIn("wireless mouse", candidate_terms)
        self.assertEqual(len(result.decisions), len(result.candidates))
        self.assertEqual(result.skipped_terms, [])

    def test_fallback_to_competitor_asins_when_report_has_no_product_terms(self):
        request = SearchTermExpansionRequest(
            report_date=202526,
            product_asin="B00SELF",
            start_date="2026-05-01",
            end_date="2026-05-31",
            competitor_asins=["B000TEST", "B000TEST2"],
            product_title="Wireless ergonomic mouse",
            product_features=["silent click", "usb receiver"],
        )

        result = run_search_term_expansion(
            request=request,
            aba_service=FakeAbaService(),
            ads_report_service=FakeAdsReportService(
                rows=[
                    {"term_type": "keyword", "search_term": "wireless mouse", "orders": 1, "clicks": 5},
                ]
            ),
        )

        self.assertEqual(result.product_seed_asins, ["B000TEST", "B000TEST2"])
        self.assertIn("wireless mouse", result.seeds)
        self.assertIn("bluetooth mouse", [candidate.term for candidate in result.candidates])


if __name__ == "__main__":
    unittest.main()
