from src.schemas.keyword import KeywordCandidate
from .aba_service import AbaService
from src.utils.report_period import DateLike, ReportGranularity


class KeywordExpansionService:
    def collect_seed_terms(
        self,
        manual_terms: list[str],
        asin_terms: list[str],
    ) -> list[str]:
        # 合并人工输入词和 ASIN 反查词，并做大小写无关去重
        seen = set()
        results = []
        for term in [*manual_terms, *asin_terms]:
            clean_term = term.strip()
            if not clean_term:
                continue
            lowered = clean_term.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            results.append(clean_term)
        return results

    def expand_from_terms(
        self,
        terms: list[str],
        aba_service: AbaService,
        report_date: DateLike,
        report_granularity: ReportGranularity | str = ReportGranularity.WEEK,
    ) -> list[KeywordCandidate]:
        # 词 -> ASIN -> 词
        # 先保留高价值词自身，再继续找高转化 ASIN，最后从 ASIN 反查词
        candidates: list[KeywordCandidate] = []
        for term in terms:
            candidates.append(aba_service.build_keyword_candidate(term, source="high_value_term"))
            high_value_asins = aba_service.find_high_conversion_asins(
                search_term=term,
                report_date=report_date,
                report_granularity=report_granularity,
            )
            for asin in high_value_asins:
                for expanded_term in aba_service.reverse_lookup_terms_by_asin(
                    asin,
                    report_date,
                    report_granularity=report_granularity,
                ):
                    candidate = aba_service.build_keyword_candidate(
                        expanded_term,
                        source=f"term_asin_term:{term}->{asin}",
                    )
                    if asin not in candidate.related_asins:
                        candidate.related_asins.append(asin)
                    candidates.append(candidate)
        return self.deduplicate_candidates(candidates)

    def expand_from_asins(
        self,
        asins: list[str],
        aba_service: AbaService,
        report_date: DateLike,
        report_granularity: ReportGranularity | str = ReportGranularity.WEEK,
    ) -> list[KeywordCandidate]:
        # ASIN -> 词
        candidates: list[KeywordCandidate] = []
        for asin in asins:
            for term in aba_service.reverse_lookup_terms_by_asin(
                asin,
                report_date,
                report_granularity=report_granularity,
            ):
                candidate = aba_service.build_keyword_candidate(term, source=f"asin_term:{asin}")
                if asin not in candidate.related_asins:
                    candidate.related_asins.append(asin)
                candidates.append(candidate)
        return self.deduplicate_candidates(candidates)

    def merge_expanded_candidates(
        self,
        groups: list[list[KeywordCandidate]],
    ) -> list[KeywordCandidate]:
        # 合并双链路产出的候选词
        merged_candidates: list[KeywordCandidate] = []
        for group in groups:
            merged_candidates.extend(group)
        return self.deduplicate_candidates(merged_candidates)

    def deduplicate_candidates(self, candidates: list[KeywordCandidate]) -> list[KeywordCandidate]:
        # 同一搜索词可能来自多个入口，这里合并成一个候选对象
        merged: dict[str, KeywordCandidate] = {}
        for candidate in candidates:
            key = candidate.term.strip().lower()
            if key not in merged:
                merged[key] = candidate
                continue
            target = merged[key]
            target.related_asins.extend(
                asin for asin in candidate.related_asins if asin not in target.related_asins
            )
            target.notes.extend(
                note for note in candidate.notes if note not in target.notes
            )
            target.click_share = max(target.click_share, candidate.click_share)
            target.conversion_share = max(target.conversion_share, candidate.conversion_share)
            target.efficiency = max(target.efficiency, candidate.efficiency)
            if candidate.search_rank is not None:
                if target.search_rank is None:
                    target.search_rank = candidate.search_rank
                else:
                    target.search_rank = min(target.search_rank, candidate.search_rank)
        return list(merged.values())

    def filter_relevant_candidates(
        self,
        candidates: list[KeywordCandidate],
        product_title: str,
        product_features: list[str],
    ) -> tuple[list[KeywordCandidate], list[str]]:
        # 当前先用启发式规则过滤，后续可以替换成 LLM 判定
        approved: list[KeywordCandidate] = []
        skipped: list[str] = []
        context = f"{product_title} {' '.join(product_features)}".lower()
        for candidate in candidates:
            if self.is_candidate_relevant(candidate.term, context):
                candidate.relevance_score = 1.0
                approved.append(candidate)
            else:
                skipped.append(candidate.term)
        return approved, skipped

    def apply_rank_cutoff(
        self,
        candidates: list[KeywordCandidate],
        max_search_rank: int | None,
    ) -> list[KeywordCandidate]:
        # 在候选词汇总、去重、相关性过滤后，再按排名上限截断。
        if max_search_rank is None:
            return candidates
        filtered: list[KeywordCandidate] = []
        for candidate in candidates:
            if candidate.search_rank is None or candidate.search_rank <= max_search_rank:
                filtered.append(candidate)
        return filtered

    def is_candidate_relevant(self, term: str, context_text: str) -> bool:
        # 极简相关性判断：
        # 1. 明显品牌词先过滤
        # 2. 如果没有商品上下文，则先放行
        # 3. 否则要求至少有一个 token 能在商品上下文里命中
        lowered = term.lower()
        if "brand" in lowered:
            return False
        if not context_text.strip():
            return True
        tokens = [token for token in lowered.split() if token]
        return any(token in context_text for token in tokens) or len(tokens) == 1
