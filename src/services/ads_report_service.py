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

    def get_placement_data(
        self,
        asin: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> list[dict]:
        # 读取商品在不同广告位的历史汇总表现，用于未投词初始 bid 估算。
        if self.repo is None or not asin or not start_date or not end_date:
            return []
        return self.repo.get_placement_data(
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
    ) -> list[str]:
        # 根据报表聚合 ACOS 基线筛选高价值词。
        selected_terms: list[str] = []
        average_acos = self.calculate_average_acos(rows)
        for row in rows:
            term_type = str(row.get("term_type", "")).strip().lower()
            if term_type != "keyword":
                continue
            term_value = str(row.get("search_term", "")).strip()
            if not term_value:
                continue
            if self.is_high_value_row(
                row,
                average_acos=average_acos,
            ):
                selected_terms.append(term_value)
        return self.deduplicate_values(selected_terms)

    def select_high_value_product_asins(self, rows: list[dict]) -> list[str]:
        # 从报表商品流量里先筛出“值得继续扩展”的商品入口
        return self.select_high_value_product_asins_by_strategy(rows)

    def select_high_value_product_asins_by_strategy(
        self,
        rows: list[dict],
    ) -> list[str]:
        # 根据报表聚合 ACOS 基线筛选高价值商品入口。
        selected_asins: list[str] = []
        average_acos = self.calculate_average_acos(rows)
        for row in rows:
            term_type = str(row.get("term_type", "")).strip().lower()
            if term_type != "product":
                continue
            term_value = str(row.get("search_term", "")).strip()
            if not term_value:
                continue
            if self.is_high_value_row(
                row,
                average_acos=average_acos,
            ):
                selected_asins.append(term_value)
        return self.deduplicate_values(selected_asins)

    def calculate_average_acos(self, rows: list[dict]) -> float | None:
        # 基线 ACOS 使用“所有用户搜索词的总花费 / 总销售额”。
        total_spend = 0.0
        total_sales = 0.0
        for row in rows:
            term_value = str(row.get("search_term", "")).strip()
            if not term_value:
                continue
            total_spend += self.to_float(row.get("spend"))
            total_sales += self.to_float(row.get("sales"))
        if total_sales <= 0:
            return None
        return total_spend / total_sales

    def is_high_value_row(
        self,
        row: dict,
        average_acos: float | None = None,
    ) -> bool:
        # “数据好”定义为：单行 ACOS 低于全量用户搜索词的聚合 ACOS 基线。
        if average_acos is None:
            return False
        row_acos = self.calculate_row_acos(row)
        if row_acos is None:
            return False
        return row_acos < average_acos

    def calculate_row_acos(self, row: dict) -> float | None:
        spend = self.to_float(row.get("spend"))
        sales = self.to_float(row.get("sales"))
        if sales > 0:
            return spend / sales
        acos = self.to_float(row.get("acos"))
        if acos > 0:
            return acos
        return None


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
