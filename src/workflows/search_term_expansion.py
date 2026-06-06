from src.constants.expansion import (
    EXPANSION_INTENSITY_CONFIGS,
    normalize_expansion_intensity,
)
from src.schemas.workflow import SearchTermExpansionRequest, SearchTermExpansionResult
from src.services.aba_service import AbaService
from src.services.ads_report_service import AdsReportService
from src.services.keyword_expansion_service import KeywordExpansionService
from src.strategy_engine.keyword_expansion import build_keyword_decision


def run_search_term_expansion(
    request: SearchTermExpansionRequest,
    aba_service: AbaService | None = None,
    ads_report_service: AdsReportService | None = None,
    keyword_service: KeywordExpansionService | None = None,
    executor=None,
) -> SearchTermExpansionResult:
    # workflow 只负责编排，不承担具体取数和策略计算细节
    aba_service = aba_service or AbaService()
    ads_report_service = ads_report_service or AdsReportService()
    keyword_service = keyword_service or KeywordExpansionService()
    intensity = normalize_expansion_intensity(request.expansion_intensity)
    intensity_config = EXPANSION_INTENSITY_CONFIGS[intensity]

    # 第一步：优先查询用户搜索词流量来源
    # 用户搜索词分为关键词和商品两类，其中商品类可直接作为 ASIN 种子
    user_search_term_rows = ads_report_service.get_user_search_term_rows(
        asin=request.product_asin,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    _, report_product_asins = ads_report_service.split_user_search_terms(user_search_term_rows)

    # 第二步：先从报表里挑“数据好的词”和“数据好的商品 ASIN”
    high_value_terms = keyword_service.collect_seed_terms(
        manual_terms=[
            *request.seed_search_terms,
            *ads_report_service.select_high_value_terms_by_strategy(
                user_search_term_rows,
            ),
        ],
        asin_terms=[],
    )
    high_value_asins = ads_report_service.select_high_value_product_asins_by_strategy(
        user_search_term_rows,
    )

    # 如果用户搜索词里没有商品流量，则回退到竞品 ASIN
    product_seed_asins = (
        high_value_asins
        if high_value_asins
        else [asin for asin in request.competitor_asins if asin]
    )

    # 第三步：构造用于扩词的起始词集合
    seeds = keyword_service.collect_seed_terms(
        manual_terms=[*request.seed_search_terms, *high_value_terms],
        asin_terms=[],
    )

    # 第四步：分两条链路扩词
    # 1. 词 -> ASIN -> 词
    term_chain_candidates = keyword_service.expand_from_terms(
        terms=high_value_terms,
        aba_service=aba_service,
        report_date=request.report_date,
        report_granularity=request.report_granularity,
    )
    # 2. ASIN -> 词
    asin_chain_candidates = keyword_service.expand_from_asins(
        asins=product_seed_asins,
        aba_service=aba_service,
        report_date=request.report_date,
        report_granularity=request.report_granularity,
    )

    # 第五步：候选池只接收第 3 步双链路产出，不直接纳入起始词自身
    candidates = keyword_service.merge_expanded_candidates(
        [term_chain_candidates, asin_chain_candidates]
    )

    # 第六步：过滤不相关词
    candidates, skipped_terms = keyword_service.filter_relevant_candidates(
        candidates=candidates,
        product_title=request.product_title,
        product_features=request.product_features,
    )
    candidates = keyword_service.apply_rank_cutoff(
        candidates=candidates,
        keep_rank_percent=intensity_config.keep_rank_percent,
    )
    placement_rows = ads_report_service.get_placement_data(
        asin=request.product_asin,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    # 第七步：为每个候选词生成投放位置和 bid 建议
    decisions = [
        build_keyword_decision(
            candidate=candidate,
            average_order_price=request.average_order_price,
            target_acos=request.target_acos,
            placement_rows=placement_rows,
        )
        for candidate in candidates
    ]

    # 第八步：如果启用自动执行，则把通过的策略交给执行层
    execution_summary = None
    if request.auto_execute and executor is not None:
        execution_summary = executor.launch_keywords(
            [decision for decision in decisions if decision.should_launch]
        )

    return SearchTermExpansionResult(
        seeds=seeds,
        product_seed_asins=product_seed_asins,
        high_value_terms=high_value_terms,
        high_value_asins=high_value_asins,
        candidates=candidates,
        decisions=decisions,
        skipped_terms=skipped_terms,
        execution_summary=execution_summary,
    )
