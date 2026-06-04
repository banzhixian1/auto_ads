from src.constants.metrics import DEFAULT_DECAY, DEFAULT_WEEKS
from src.data_processor.aba_hot_search_term import weighted_aba_metrics
from src.schemas.keyword import KeywordCandidate


class AbaService:
    def __init__(self, repo=None):
        # repo 允许注入，方便后续接真实数据库或测试桩
        self.repo = repo

    def find_seed_terms_by_asin(self, asin: str, report_date: int) -> list[str]:
        # 从 ABA 数据里反查某个 ASIN 上榜过的搜索词
        if self.repo is None:
            return []
        rows = self.repo.get_top_asin_search_term(asin=asin, report_date=report_date)
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
        return KeywordCandidate(
            term=search_term,
            source=source,
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

    def find_high_conversion_asins(self, search_term: str, report_date: int) -> list[str]:
        # 这里后续要接“词找 ASIN”能力：
        # 给定一个高价值词，继续找该词下转化效率高的 ASIN
        # 当前仓库层尚未补 SQL，因此默认返回空列表
        return []

    def reverse_lookup_terms_by_asin(self, asin: str, report_date: int) -> list[str]:
        # 当前阶段直接复用 ABA 反查，后续可替换为更完整的 ASIN 找词逻辑
        return self.find_seed_terms_by_asin(asin=asin, report_date=report_date)
