from src.constants.metrics import (
    DEFAULT_DECAY,
    DEFAULT_EFFICIENCY_THRESHOLD,
    DEFAULT_WEEKS,
)
from src.utils.report_period import DateLike, ReportGranularity
from src.data_processor.aba_hot_search_term import weighted_aba_metrics
from src.schemas.keyword import KeywordCandidate
from src.repositories.aba_hot_search_term import AbaHotSearchTermRepository


class AbaService:
    def __init__(self, repo: AbaHotSearchTermRepository = None):
        # repo 允许注入，方便后续接真实数据库或测试桩
        self.repo = repo

    def find_seed_terms_by_asin(
        self,
        asin: str,
        report_date: DateLike,
        report_granularity: ReportGranularity | str = ReportGranularity.WEEK,
    ) -> list[str]:
        # 从 ABA 数据里反查某个 ASIN 上榜过的搜索词
        if self.repo is None:
            return []
        rows = self.repo.get_top_asin_search_term(
            asin=asin,
            report_date=report_date,
            report_granularity=report_granularity,
        )
        return [row["search_term"] for row in rows if row.get("search_term")]

    def get_search_term_history(self, search_term: str, weeks: int = DEFAULT_WEEKS) -> list[dict]:
        # 查询搜索词历史周维度表现，用于后续加权计算
        if self.repo is None:
            return []
        return self.repo.get_search_term_history(search_term=search_term, weeks=weeks)

    def build_keyword_candidate(self, search_term: str, source: str) -> KeywordCandidate:
        # 把原始历史数据组装成候选词对象
        history = self.get_search_term_history(search_term)
        metrics = self.calculate_weighted_metrics(history)
        search_rank = self._get_best_search_rank(history)
        return KeywordCandidate(
            term=search_term,
            source=source,
            search_rank=search_rank,
            click_share=metrics["weighted_click_share"],
            conversion_share=metrics["weighted_conv_share"],
            efficiency=metrics["efficiency"],
        )

    def calculate_weighted_metrics(
        self,
        history: list[dict],
        decay: float = DEFAULT_DECAY,
    ) -> dict:
        # 没有历史数据时返回空指标，避免工作流中断
        if not history:
            return {
                "weighted_click_share": 0.0,
                "weighted_conv_share": 0.0,
                "efficiency": 0.0,
                "weights": [],
            }
        click_list = [float(item.get("click_share", 0.0)) for item in history]
        conv_list = [float(item.get("conversion_share", 0.0)) for item in history]
        return weighted_aba_metrics(click_list=click_list, conv_list=conv_list, decay=decay)

    def _get_best_search_rank(self, history: list[dict]) -> int | None:
        # 取历史窗口内最靠前的搜索排名，后续用于候选词截断。
        ranks: list[int] = []
        for item in history:
            rank = item.get("search_rank")
            if rank in (None, ""):
                continue
            try:
                ranks.append(int(rank))
            except (TypeError, ValueError):
                continue
        if not ranks:
            return None
        return min(ranks)

    def find_high_conversion_asins(
        self,
        search_term: str,
    ) -> list[str]:
        # 给定一个高价值词，找其历史周数据中出现在前三的商品，
        # 再按商品维度做时间加权，筛出数据好的商品。
        history = self.get_search_term_history(search_term)
        if not history:
            return []

        asin_histories = self._build_asin_histories(history)
        asin_scores: list[tuple[str, dict]] = []
        for asin, metrics_history in asin_histories.items():
            if len(metrics_history) < 2:
                continue
            weighted_metrics = self.calculate_weighted_metrics(metrics_history)
            if self._is_high_value_asin(weighted_metrics):
                asin_scores.append((asin, weighted_metrics))

        if asin_scores:
            asin_scores.sort(key=self._sort_key_for_asin_score, reverse=True)
            return [asin for asin, _ in asin_scores]

        fallback = self._select_fallback_top_click_asin(history)
        if fallback is None:
            return []
        return [fallback]

    def _build_asin_histories(self, history: list[dict]) -> dict[str, list[dict]]:
        # 把每周前三商品展开成 ASIN 维度的历史份额轨迹。
        asin_histories: dict[str, list[dict]] = {}
        for row in history:
            for index in range(1, 4):
                asin = row.get(f"top_product_{index}_asin")
                if not asin:
                    continue
                asin_histories.setdefault(asin, []).append(
                    {
                        "click_share": float(row.get(f"top_product_{index}_click_share", 0.0) or 0.0),
                        "conversion_share": float(
                            row.get(f"top_product_{index}_conversion_share", 0.0) or 0.0
                        ),
                    }
                )
        return asin_histories

    def _build_top_click_asin_histories(self, history: list[dict]) -> dict[str, list[dict]]:
        # 兜底时只看每周点击排名第一的商品，优先拿体量更大的代表商品。
        asin_histories: dict[str, list[dict]] = {}
        for row in history:
            asin = row.get("top_product_1_asin")
            if not asin:
                continue
            asin_histories.setdefault(asin, []).append(
                {
                    "click_share": float(row.get("top_product_1_click_share", 0.0) or 0.0),
                    "conversion_share": float(row.get("top_product_1_conversion_share", 0.0) or 0.0),
                }
            )
        return asin_histories

    def _select_fallback_top_click_asin(self, history: list[dict]) -> str | None:
        top_click_histories = self._build_top_click_asin_histories(history)
        if not top_click_histories:
            return None

        asin_scores: list[tuple[str, dict]] = []
        for asin, metrics_history in top_click_histories.items():
            weighted_metrics = self.calculate_weighted_metrics(metrics_history)
            asin_scores.append((asin, weighted_metrics))

        if not asin_scores:
            return None
        asin_scores.sort(key=self._sort_key_for_asin_score, reverse=True)
        return asin_scores[0][0]

    def _sort_key_for_asin_score(self, item: tuple[str, dict]) -> tuple[float, float, float]:
        _, weighted_metrics = item
        return (
            weighted_metrics["efficiency"],
            weighted_metrics["weighted_click_share"],
            weighted_metrics["weighted_conv_share"],
        )

    def _is_high_value_asin(self, weighted_metrics: dict) -> bool:
        # 数据好的商品定义：加权出单效率达到阈值。
        efficiency = float(weighted_metrics.get("efficiency", 0.0))
        return efficiency >= DEFAULT_EFFICIENCY_THRESHOLD

    def reverse_lookup_terms_by_asin(
        self,
        asin: str,
        report_date: DateLike,
        report_granularity: ReportGranularity | str = ReportGranularity.WEEK,
    ) -> list[str]:
        # 当前阶段直接复用 ABA 反查，后续可替换为更完整的 ASIN 找词逻辑
        return self.find_seed_terms_by_asin(
            asin=asin,
            report_date=report_date,
            report_granularity=report_granularity,
        )
