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

    # -------------------------
    # 1. 查询指定asin在指定周下有排名前三的关键词
    # -------------------------
    def get_top_asin_search_term(
        self,
        asin: str,
        report_date: int,
    ) -> list[dict]:
        """
        查询指定asin在指定周下有排名前三的关键词，按aba排名升序
        Args:
            week: 本年第几周
        """
        sql = """

        """
        params = {"asin": asin, "report_date": report_date}
        return self.pool.execute(sql, params, fetchall=True, return_type="dict")


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
        """
        params = {"search_term": search_term, "weeks": weeks}
        return self.pool.execute(sql, params, fetchall=True, return_type="dict")