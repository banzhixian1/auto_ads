from typing import Optional
from src.utils.report_period import (
    DateLike,
    ReportGranularity,
    resolve_latest_published_report_anchor_date,
)
from src.utils.db_conn_pool import create_pg_pool, SQLAlchemyPool

# 可选全局默认 pool
DEFAULT_POOL = create_pg_pool(database='am_aba_search_term', conn_name='default')


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

    # -------------------------
    # 1. 查询指定asin在指定周下有排名前三的关键词
    # -------------------------
    def get_top_asin_search_term(
        self,
        asin: str,
        report_date: DateLike,
        report_granularity: ReportGranularity | str = ReportGranularity.WEEK,
    ) -> list[dict]:
        """
        查询指定 ASIN 在目标报告周期下排名前三的关键词，按 ABA 排名升序返回。

        Args:
            asin: 需要查询的商品 ASIN。
            report_date: 自然日期，支持 str / date / datetime。
            report_granularity: 报告粒度，当前仓库仅支持 week。
        """
        target_date = resolve_latest_published_report_anchor_date(
            report_date=report_date,
            report_granularity=report_granularity,
        )

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
        weeks: int = 8,
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
    
