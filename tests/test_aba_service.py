import unittest

from src.services.aba_service import AbaService


class FakeAbaRepository:
    def get_search_term_history(self, search_term: str, weeks: int = 8) -> list[dict]:
        return [
            {
                "report_date": "2026-06-01",
                "search_rank": 10,
                "click_share": 0.55,
                "conversion_share": 0.42,
                "top_product_1_asin": "A1",
                "top_product_1_click_share": 0.25,
                "top_product_1_conversion_share": 0.20,
                "top_product_2_asin": "A2",
                "top_product_2_click_share": 0.18,
                "top_product_2_conversion_share": 0.16,
                "top_product_3_asin": "A3",
                "top_product_3_click_share": 0.12,
                "top_product_3_conversion_share": 0.06,
            },
            {
                "report_date": "2026-05-25",
                "search_rank": 12,
                "click_share": 0.52,
                "conversion_share": 0.40,
                "top_product_1_asin": "A1",
                "top_product_1_click_share": 0.22,
                "top_product_1_conversion_share": 0.19,
                "top_product_2_asin": "A4",
                "top_product_2_click_share": 0.17,
                "top_product_2_conversion_share": 0.13,
                "top_product_3_asin": "A2",
                "top_product_3_click_share": 0.11,
                "top_product_3_conversion_share": 0.10,
            },
        ]


class AbaServiceTestCase(unittest.TestCase):
    def test_find_high_conversion_asins(self):
        service = AbaService(repo=FakeAbaRepository())

        result = service.find_high_conversion_asins("wireless mouse", "2026-06-04")

        self.assertIn("A1", result)
        self.assertIn("A2", result)
        self.assertNotIn("A4", result)
        self.assertNotIn("A3", result)


if __name__ == "__main__":
    unittest.main()
