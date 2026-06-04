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
        report_date: int | str,
    ) -> list[dict]:
        """
        查询指定 ASIN 在指定周下进入 ABA 前三商品的搜索词，按 ABA 排名升序返回。

        Args:
            asin: 需要查询的商品 ASIN。
            report_date: 业务周标识，约定格式为 YYYYWW，例如 202526。

        Returns:
            list[dict]: 搜索词列表，每条记录至少包含：
            - search_term: 搜索词
            - search_rank: 搜索排名
            - matched_position: 命中的商品位次（1/2/3）
            - click_share: 该 ASIN 在该词下的点击份额
            - conversion_share: 该 ASIN 在该词下的转化份额
            - report_date: 周报日期
        """
        sql = """
        SELECT
            search_term,
            search_rank,
            CASE
                WHEN top_product_1_asin = :asin THEN 1
                WHEN top_product_2_asin = :asin THEN 2
                WHEN top_product_3_asin = :asin THEN 3
            END AS matched_position,
            CASE
                WHEN top_product_1_asin = :asin THEN top_product_1_click_share
                WHEN top_product_2_asin = :asin THEN top_product_2_click_share
                WHEN top_product_3_asin = :asin THEN top_product_3_click_share
            END AS click_share,
            CASE
                WHEN top_product_1_asin = :asin THEN top_product_1_conversion_share
                WHEN top_product_2_asin = :asin THEN top_product_2_conversion_share
                WHEN top_product_3_asin = :asin THEN top_product_3_conversion_share
            END AS conversion_share,
            report_date
        FROM aba_brand_search_words_weeks
        WHERE to_char(report_date, 'IYYYIW') = :report_week
          AND (
              top_product_1_asin = :asin
              OR top_product_2_asin = :asin
              OR top_product_3_asin = :asin
          )
        ORDER BY search_rank ASC
        """
        params = {
            "asin": asin,
            "report_week": self._normalize_report_week(report_date),
        }
        return self.pool.query(sql, params, fetchall=True, return_dict=True)


    # -------------------------
    # 2. 单关键词历史查询
    # -------------------------
    def get_search_term_history(
        self,
        search_term: str,
        weeks: int = 8
    ) -> list[dict]:
        """
        获取单个搜索词的历史周数据（按周倒序）。

        Args:
            search_term: 搜索词文本。
            weeks: 返回最近多少周的数据。

        Returns:
            list[dict]: 历史周数据列表，每条记录至少包含：
            - report_date: 周报日期
            - search_rank: 搜索排名
            - click_share: 该词前三商品总点击份额
            - conversion_share: 该词前三商品总转化份额
        """
        sql = """
        SELECT
            report_date,
            search_rank,
            click_share,
            conversion_share
        FROM aba_brand_search_words_weeks
        WHERE search_term = :search_term
        ORDER BY report_date DESC
        LIMIT :weeks
        """
        params = {"search_term": search_term, "weeks": weeks}
        return self.pool.query(sql, params, fetchall=True, return_dict=True)
    
