import json

from src.repositories.sp_report import (
    get_brand_analytics_search_query_weekly,
    insert_brand_analytics_search_query_weekly,
)


REPORT_PATH = "sp_rpt_test.json"
TEST_LIMIT = 10


def get_report_query_params(report_path: str) -> tuple[str, str]:
    with open(report_path, "r", encoding="utf-8") as file:
        report_data = json.load(file)
    first_row = report_data["dataByAsin"][0]
    return first_row["asin"], first_row["endDate"]


def main() -> None:
    """
    测试 SP 报表前 10 条数据的写入和读取。
    """
    asin, report_date = get_report_query_params(REPORT_PATH)
    inserted_count = insert_brand_analytics_search_query_weekly(
        report_path=REPORT_PATH,
        limit=TEST_LIMIT,
    )
    db_rows = get_brand_analytics_search_query_weekly(
        asin=asin,
        report_date=report_date,
    )

    print(f"读取 ASIN: {asin}")
    print(f"读取报告日期: {report_date}")
    print(f"写入行数: {inserted_count}")
    print(f"读取行数: {len(db_rows)}")
    print("读取前 3 条:")
    print(
        json.dumps(
            db_rows[:3],
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )

    assert inserted_count == TEST_LIMIT
    assert len(db_rows) == TEST_LIMIT


if __name__ == "__main__":
    main()
