from datetime import date, datetime
from typing import Any

from sqlalchemy import text

from src.services.sp_report_service import sp_rpt_json_to_list
from src.utils.db_conn_pool import SQLAlchemyPool, create_mysql_pool


DEFAULT_POOL = create_mysql_pool("dataiforce")


DateLike = str | date | datetime


def insert_brand_analytics_search_query_weekly(
    report_path: str,
    limit: int = None,
    pool: SQLAlchemyPool = None,
) -> int:
    """
    读取 SP 报告 JSON，转换后写入 MySQL。

    Args:
        report_path: SP 报告 JSON 文件路径。
        limit: 限制写入行数，不传则写入全部。
        pool: 数据库连接池，不传时默认连接 dataiforce。

    Returns:
        int: 实际插入行数。
    """
    rows = sp_rpt_json_to_list(report_path)
    if limit is not None:
        rows = rows[:limit]

    if not rows:
        return 0

    db_pool = pool or DEFAULT_POOL
    insert_rows: list[dict[str, Any]] = []
    report_keys: set[tuple[str, str]] = set()

    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("rows 的每个元素必须是 dict 类型")

        asin = str(row.get("asin") or "").strip().upper()
        report_date = row.get("end_date") or row.get("report_end_date") or row.get("report_date")
        if isinstance(report_date, datetime):
            report_date = report_date.date().isoformat()
        elif isinstance(report_date, date):
            report_date = report_date.isoformat()
        elif report_date is not None:
            report_date = date.fromisoformat(str(report_date).strip()[:10]).isoformat()

        if not asin or not report_date:
            continue

        report_keys.add((asin, report_date))
        insert_rows.append(
            {
                "asin": asin,
                "report_date": report_date,
                "search_query": row.get("search_query"),
                "search_query_score": row.get("search_query_score"),
                "search_query_volume": row.get("search_query_volume"),
                "total_query_impression_count": row.get("total_query_impression_count"),
                "asin_impression_count": row.get("asin_impression_count"),
                "asin_impression_share": row.get("asin_impression_share"),
                "total_click_count": row.get("total_click_count"),
                "total_click_rate": row.get("total_click_rate"),
                "asin_click_count": row.get("asin_click_count"),
                "asin_click_share": row.get("asin_click_share"),
                "total_median_click_price": row.get("total_median_click_price_amount")
                if row.get("total_median_click_price_amount") is not None
                else row.get("total_median_click_price"),
                "asin_median_click_price": row.get("asin_median_click_price_amount")
                if row.get("asin_median_click_price_amount") is not None
                else row.get("asin_median_click_price"),
                "total_same_day_shipping_click_count": row.get("total_same_day_shipping_click_count"),
                "total_one_day_shipping_click_count": row.get("total_one_day_shipping_click_count"),
                "total_two_day_shipping_click_count": row.get("total_two_day_shipping_click_count"),
                "total_cart_add_count": row.get("total_cart_add_count"),
                "total_cart_add_rate": row.get("total_cart_add_rate"),
                "asin_cart_add_count": row.get("asin_cart_add_count"),
                "asin_cart_add_share": row.get("asin_cart_add_share"),
                "total_median_cart_add_price": row.get("total_median_cart_add_price_amount")
                if row.get("total_median_cart_add_price_amount") is not None
                else row.get("total_median_cart_add_price"),
                "asin_median_cart_add_price": row.get("asin_median_cart_add_price_amount")
                if row.get("asin_median_cart_add_price_amount") is not None
                else row.get("asin_median_cart_add_price"),
                "total_same_day_shipping_cart_add_count": row.get("total_same_day_shipping_cart_add_count"),
                "total_one_day_shipping_cart_add_count": row.get("total_one_day_shipping_cart_add_count"),
                "total_two_day_shipping_cart_add_count": row.get("total_two_day_shipping_cart_add_count"),
                "total_purchase_count": row.get("total_purchase_count"),
                "total_purchase_rate": row.get("total_purchase_rate"),
                "asin_purchase_count": row.get("asin_purchase_count"),
                "asin_purchase_share": row.get("asin_purchase_share"),
                "total_median_purchase_price": row.get("total_median_purchase_price_amount")
                if row.get("total_median_purchase_price_amount") is not None
                else row.get("total_median_purchase_price"),
                "asin_median_purchase_price": row.get("asin_median_purchase_price_amount")
                if row.get("asin_median_purchase_price_amount") is not None
                else row.get("asin_median_purchase_price"),
                "total_same_day_shipping_purchase_count": row.get("total_same_day_shipping_purchase_count"),
                "total_one_day_shipping_purchase_count": row.get("total_one_day_shipping_purchase_count"),
                "total_two_day_shipping_purchase_count": row.get("total_two_day_shipping_purchase_count"),
            }
        )

    if not insert_rows:
        return 0

    delete_sql = """
        DELETE FROM amz_rpt_brand_analytics_search_query_weekly
        WHERE asin = :asin
            AND report_date = :report_date
    """
    insert_sql = """
        INSERT INTO amz_rpt_brand_analytics_search_query_weekly (
            asin,
            report_date,
            search_query,
            search_query_score,
            search_query_volume,
            total_query_impression_count,
            asin_impression_count,
            asin_impression_share,
            total_click_count,
            total_click_rate,
            asin_click_count,
            asin_click_share,
            total_median_click_price,
            asin_median_click_price,
            total_same_day_shipping_click_count,
            total_one_day_shipping_click_count,
            total_two_day_shipping_click_count,
            total_cart_add_count,
            total_cart_add_rate,
            asin_cart_add_count,
            asin_cart_add_share,
            total_median_cart_add_price,
            asin_median_cart_add_price,
            total_same_day_shipping_cart_add_count,
            total_one_day_shipping_cart_add_count,
            total_two_day_shipping_cart_add_count,
            total_purchase_count,
            total_purchase_rate,
            asin_purchase_count,
            asin_purchase_share,
            total_median_purchase_price,
            asin_median_purchase_price,
            total_same_day_shipping_purchase_count,
            total_one_day_shipping_purchase_count,
            total_two_day_shipping_purchase_count
        ) VALUES (
            :asin,
            :report_date,
            :search_query,
            :search_query_score,
            :search_query_volume,
            :total_query_impression_count,
            :asin_impression_count,
            :asin_impression_share,
            :total_click_count,
            :total_click_rate,
            :asin_click_count,
            :asin_click_share,
            :total_median_click_price,
            :asin_median_click_price,
            :total_same_day_shipping_click_count,
            :total_one_day_shipping_click_count,
            :total_two_day_shipping_click_count,
            :total_cart_add_count,
            :total_cart_add_rate,
            :asin_cart_add_count,
            :asin_cart_add_share,
            :total_median_cart_add_price,
            :asin_median_cart_add_price,
            :total_same_day_shipping_cart_add_count,
            :total_one_day_shipping_cart_add_count,
            :total_two_day_shipping_cart_add_count,
            :total_purchase_count,
            :total_purchase_rate,
            :asin_purchase_count,
            :asin_purchase_share,
            :total_median_purchase_price,
            :asin_median_purchase_price,
            :total_same_day_shipping_purchase_count,
            :total_one_day_shipping_purchase_count,
            :total_two_day_shipping_purchase_count
        )
    """

    session = db_pool.get_session()
    try:
        for asin, report_date in report_keys:
            session.execute(text(delete_sql), {"asin": asin, "report_date": report_date})
        session.execute(text(insert_sql), insert_rows)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return len(insert_rows)


def get_brand_analytics_search_query_weekly(
    asin: str,
    report_date: DateLike,
    pool: SQLAlchemyPool = None,
) -> list[dict]:
    """
    从 MySQL 读取指定 ASIN 的搜索词周报数据。

    Args:
        asin: 商品 ASIN。
        report_date: 报告日期，使用周报最后一天。
        pool: 数据库连接池，不传时默认连接 dataiforce。

    Returns:
        list[dict]: 搜索词周报数据。
    """
    normalized_asin = str(asin or "").strip().upper()
    if not normalized_asin:
        return []

    if isinstance(report_date, datetime):
        normalized_report_date = report_date.date().isoformat()
    elif isinstance(report_date, date):
        normalized_report_date = report_date.isoformat()
    else:
        normalized_report_date = date.fromisoformat(str(report_date).strip()[:10]).isoformat()

    params: dict[str, Any] = {
        "asin": normalized_asin,
        "report_date": normalized_report_date,
    }

    sql = f"""
        SELECT
            id,
            asin,
            report_date,
            search_query,
            search_query_score,
            search_query_volume,
            total_query_impression_count,
            asin_impression_count,
            asin_impression_share,
            total_click_count,
            total_click_rate,
            asin_click_count,
            asin_click_share,
            total_median_click_price,
            asin_median_click_price,
            total_same_day_shipping_click_count,
            total_one_day_shipping_click_count,
            total_two_day_shipping_click_count,
            total_cart_add_count,
            total_cart_add_rate,
            asin_cart_add_count,
            asin_cart_add_share,
            total_median_cart_add_price,
            asin_median_cart_add_price,
            total_same_day_shipping_cart_add_count,
            total_one_day_shipping_cart_add_count,
            total_two_day_shipping_cart_add_count,
            total_purchase_count,
            total_purchase_rate,
            asin_purchase_count,
            asin_purchase_share,
            total_median_purchase_price,
            asin_median_purchase_price,
            total_same_day_shipping_purchase_count,
            total_one_day_shipping_purchase_count,
            total_two_day_shipping_purchase_count
        FROM
            amz_rpt_brand_analytics_search_query_weekly
        WHERE
            asin = :asin
            AND report_date = :report_date
        ORDER BY
            report_date DESC,
            search_query_score ASC,
            search_query ASC
    """
    db_pool = pool or DEFAULT_POOL
    return db_pool.query(sql, params=params)
