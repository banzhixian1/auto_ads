import unittest

from src.services.aba_service import AbaService


class AbaMetricsTestCase(unittest.TestCase):
    def test_calculate_weighted_metrics(self):
        service = AbaService()
        history = [
            {"click_share": 0.30, "conversion_share": 0.24},
            {"click_share": 0.20, "conversion_share": 0.16},
        ]

        result = service.calculate_weighted_metrics(history)

        self.assertGreater(result["weighted_click_share"], 0)
        self.assertGreater(result["weighted_conv_share"], 0)
        self.assertAlmostEqual(result["efficiency"], 0.8, delta=0.05)


if __name__ == "__main__":
    unittest.main()
