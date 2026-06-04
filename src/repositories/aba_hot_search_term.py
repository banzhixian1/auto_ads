import datetime
from typing import Optional
from src.utils.db_conn_pool import create_pg_pool, SQLAlchemyPool

# 可选全局默认 pool
DEFAULT_POOL = create_pg_pool('am_aba_search_term')


class AbaHotSearchTermRepository:
    """
    ABA热门搜索词数据访问层
    只负责 SQL 查询和数据获取，不做指标计算
    """

    def __init__(self, pool: Optional[SQLAlchemyPool] = None):
        """
        初始化 Repository
        
        Args:
            pool: SQLAlchemyPool 实例，如果不传则使用全局默认 pool
        """
        self.pool = pool or DEFAULT_POOL

    def _normalize_report_week(self, report_date: int | str) -> str:
        """
        将业务侧传入的周标识统一转为 ISO 周字符串。

        Args:
            report_date: 业务周标识，约定格式为 YYYYWW，例如 202526。

        Returns:
            str: ISO 周字符串，格式为 YYYYWW。
        """
        return str(report_date).strip()

    # -------------------------
    # 1. 查询指定asin在指定周下有排名前三的关键词
    # -------------------------
    def get_top_asin_search_term(
        self,
        asin: str,
        year: int | None = None,
        week_number: int | None = None,
        report_date: int | str | None = None,
    ) -> list[dict]:
        """
        查询指定asin在指定周下排名前三的关键词，仅返回 search_term，按 aba 排名升序
        Args:
            year: ISO 年
            week: 本年第几周
        """
        if report_date is not None:
            normalized_week = self._normalize_report_week(report_date)
            if len(normalized_week) != 6 or not normalized_week.isdigit():
                raise ValueError(f"report_date 必须是 YYYYWW 格式，例如 202526，当前值: {report_date}")
            year = int(normalized_week[:4])
            week_number = int(normalized_week[4:])
        elif year is None or week_number is None:
            raise ValueError("year/week_number 和 report_date 至少需要提供一组。")

        date_string = f"{year}-W{week_number:02d}-6"
        target_date = datetime.datetime.strptime(date_string, "%G-W%V-%u").date()

        sql = """
            SELECT 
                search_term,
                search_rank,
                click_share,
                conversion_share,
                top_product_1_asin,
                top_product_1_name,
                top_product_1_click_share,
                top_product_1_conversion_share,
                top_product_2_asin,
                top_product_2_name,
                top_product_2_click_share,
                top_product_2_conversion_share,
                top_product_3_asin,
                top_product_3_name,
                top_product_3_click_share,
                top_product_3_conversion_share
            FROM 
                aba_brand_search_words_weeks
            WHERE 
                report_date = :target_date
                AND :asin IN (top_product_1_asin, top_product_2_asin, top_product_3_asin)
            ORDER BY 
                search_rank ASC
        """
        params = {"asin": asin, "target_date": target_date}
        rows = self.pool.query(sql, params=params)
        return rows

    # -------------------------
    # 2. 单关键词历史查询
    # -------------------------
    def get_search_term_history(
        self,
        search_term: str,
        weeks: int = 8
    ) -> list[dict]:
        """
        获取单个搜索词的历史周数据（按周倒序）
        """
        sql = """
            SELECT
                report_date,
                search_rank,
                click_share,
                conversion_share,
                top_product_1_asin,
                top_product_1_name,
                top_product_1_click_share,
                top_product_1_conversion_share,
                top_product_2_asin,
                top_product_2_name,
                top_product_2_click_share,
                top_product_2_conversion_share,
                top_product_3_asin,
                top_product_3_name,
                top_product_3_click_share,
                top_product_3_conversion_share
            FROM
                aba_brand_search_words_weeks
            WHERE
                search_term = :search_term
            ORDER BY
                report_date DESC
            LIMIT :weeks
        """
        params = {"search_term": search_term, "weeks": weeks}
        return self.pool.query(sql, params=params)
    
