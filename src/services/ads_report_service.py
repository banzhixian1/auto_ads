from src.repositories.ads_report import DateLike, AdsReportRepository


class AdsReportService:
    def __init__(self, repo: AdsReportRepository = None):
        # repo 允许注入真实报表仓库或测试桩
        self.repo = repo

    def get_user_search_term_rows(
        self,
        asin: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> list[dict]:
        # 从展示投放报表里拿指定 ASIN 的用户搜索词流量来源
        if self.repo is None or not asin or not start_date or not end_date:
            return []
        return self.repo.get_user_search_terms_by_asin(
            asin=asin,
            start_date=start_date,
            end_date=end_date,
        )

    def split_user_search_terms(
        self,
        rows: list[dict],
    ) -> tuple[list[str], list[str]]:
        # 约定：
        # 1. 关键词流量行使用 term_type='keyword'
        # 2. 商品流量行使用 term_type='product'
        # 3. 词值统一从 search_term 字段读取
        keyword_terms: list[str] = []
        product_asins: list[str] = []

        for row in rows:
            term_type = str(row.get("term_type", "")).strip().lower()
            term_value = str(row.get("search_term", "")).strip()
            if not term_value:
                continue

            if term_type == "keyword":
                keyword_terms.append(term_value)
            elif term_type == "product":
                product_asins.append(term_value)

        return keyword_terms, product_asins

    def select_high_value_terms(self, rows: list[dict]) -> list[str]:
        # 从报表关键词流量里先筛出“值得继续扩展”的词
        return self.select_high_value_terms_by_strategy(rows)

    def select_high_value_terms_by_strategy(
        self,
        rows: list[dict],
        include_attempt_terms: bool = True,
    ) -> list[str]:
        # 根据拓词强度筛选高价值词。
        selected_terms: list[str] = []
        for row in rows:
            term_type = str(row.get("term_type", "")).strip().lower()
            if term_type != "keyword":
                continue
            term_value = str(row.get("search_term", "")).strip()
            if not term_value:
                continue
            if self.is_high_value_row(row, include_attempt_terms=include_attempt_terms):
                selected_terms.append(term_value)
        return self.deduplicate_values(selected_terms)

    def select_high_value_product_asins(self, rows: list[dict]) -> list[str]:
        # 从报表商品流量里先筛出“值得继续扩展”的商品入口
        return self.select_high_value_product_asins_by_strategy(rows)

    def select_high_value_product_asins_by_strategy(
        self,
        rows: list[dict],
        include_attempt_terms: bool = True,
    ) -> list[str]:
        # 根据拓词强度筛选高价值商品入口。
        selected_asins: list[str] = []
        for row in rows:
            term_type = str(row.get("term_type", "")).strip().lower()
            if term_type != "product":
                continue
            term_value = str(row.get("search_term", "")).strip()
            if not term_value:
                continue
            if self.is_high_value_row(row, include_attempt_terms=include_attempt_terms):
                selected_asins.append(term_value)
        return self.deduplicate_values(selected_asins)

    def is_high_value_row(self, row: dict, include_attempt_terms: bool = True) -> bool:
        # 报表字段暂按最小假设处理：
        # 1. 优先策略：有订单视为高价值
        # 2. 尝试策略：没订单但有点击时，是否纳入由强度控制
        orders = self.to_float(row.get("orders"))
        clicks = self.to_float(row.get("clicks"))
        if orders > 0:
            return True
        if include_attempt_terms and clicks > 0:
            return True
        return False


    def deduplicate_values(self, values: list[str]) -> list[str]:
        # 去重并保留原始顺序
        seen = set()
        results: list[str] = []
        for value in values:
            lowered = value.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            results.append(value)
        return results

    def to_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
