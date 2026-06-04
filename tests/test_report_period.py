import unittest

from src.utils.report_period import (
    ReportGranularity,
    get_previous_report_anchor_date,
    resolve_latest_published_report_anchor_date,
    resolve_report_anchor_date,
)


class ReportPeriodTestCase(unittest.TestCase):
    def test_resolve_week_anchor_date(self):
        result = resolve_report_anchor_date("2026-06-04", ReportGranularity.WEEK)
        self.assertEqual(str(result), "2026-06-06")

    def test_resolve_latest_published_week_anchor_date(self):
        result = resolve_latest_published_report_anchor_date("2026-06-04", ReportGranularity.WEEK)
        self.assertEqual(str(result), "2026-05-30")

    def test_get_previous_month_anchor_date(self):
        result = get_previous_report_anchor_date("2026-06-30", ReportGranularity.MONTH)
        self.assertEqual(str(result), "2026-05-31")

    def test_get_previous_quarter_anchor_date(self):
        result = get_previous_report_anchor_date("2026-06-30", ReportGranularity.QUARTER)
        self.assertEqual(str(result), "2026-03-31")


if __name__ == "__main__":
    unittest.main()
