import unittest

from src.services.ads_report_service import AdsReportService


class AdsReportServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.service = AdsReportService()

    def test_calculate_average_acos_uses_total_spend_div_total_sales(self):
        rows = [
            {"term_type": "keyword", "search_term": "term a", "spend": 40, "sales": 200},
            {"term_type": "product", "search_term": "B001", "spend": 60, "sales": 100},
            {"term_type": "keyword", "search_term": "term b", "spend": 10, "sales": 0},
        ]

        result = self.service.calculate_average_acos(rows)

        self.assertEqual(result, 110 / 300)

    def test_select_high_value_terms_by_strategy_filters_by_row_acos_below_average(self):
        rows = [
            {"term_type": "keyword", "search_term": "good term", "spend": 10, "sales": 100},
            {"term_type": "keyword", "search_term": "bad term", "spend": 50, "sales": 100},
            {"term_type": "product", "search_term": "B001", "spend": 40, "sales": 200},
        ]

        result = self.service.select_high_value_terms_by_strategy(rows)

        self.assertEqual(result, ["good term"])

    def test_select_high_value_product_asins_by_strategy_filters_by_row_acos_below_average(self):
        rows = [
            {"term_type": "keyword", "search_term": "term a", "spend": 10, "sales": 100},
            {"term_type": "product", "search_term": "B001GOOD", "spend": 20, "sales": 200},
            {"term_type": "product", "search_term": "B001BAD", "spend": 50, "sales": 100},
        ]

        result = self.service.select_high_value_product_asins_by_strategy(rows)

        self.assertEqual(result, ["B001GOOD"])

    def test_product_asins_are_normalized_to_uppercase(self):
        rows = [
            {"term_type": "keyword", "search_term": "term a", "spend": 10, "sales": 100},
            {"term_type": "product", "search_term": "b001good", "spend": 20, "sales": 200},
            {"term_type": "product", "search_term": "b001bad", "spend": 50, "sales": 100},
        ]

        _, product_asins = self.service.split_user_search_terms(rows)
        high_value_asins = self.service.select_high_value_product_asins_by_strategy(rows)

        self.assertEqual(product_asins, ["B001GOOD", "B001BAD"])
        self.assertEqual(high_value_asins, ["B001GOOD"])

    def test_rows_without_sales_do_not_become_high_value(self):
        rows = [
            {"term_type": "keyword", "search_term": "good term", "spend": 10, "sales": 100},
            {"term_type": "keyword", "search_term": "no sales term", "spend": 10, "sales": 0},
            {"term_type": "product", "search_term": "B001", "spend": 10, "sales": 100},
        ]

        result = self.service.select_high_value_terms_by_strategy(rows)

        self.assertEqual(result, ["good term"])


if __name__ == "__main__":
    unittest.main()
