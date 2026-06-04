from src.schemas.keyword import KeywordCandidate
from src.schemas.strategy import KeywordExpansionDecision
from src.strategy_engine.bid_strategy import recommend_bid
from src.strategy_engine.placement_strategy import decide_placement


def build_keyword_decision(
    candidate: KeywordCandidate,
    average_order_price: float | None = None,
    target_acos: float | None = None,
    conversion_rate: float | None = None,
    current_bid: float | None = None,
) -> KeywordExpansionDecision:
    # 先确定广告位，再生成出价建议
    placement = decide_placement(
        click_share=candidate.click_share,
        conversion_share=candidate.conversion_share,
        efficiency=candidate.efficiency,
    )
    bid = recommend_bid(
        average_order_price=average_order_price,
        target_acos=target_acos,
        conversion_rate=conversion_rate,
        current_bid=current_bid,
        efficiency=candidate.efficiency,
    )
    # 当前实现里 relevance_score > 0 视为通过相关性判断
    should_launch = candidate.relevance_score > 0
    reason = "相关性通过，进入投放策略生成。"
    if not should_launch:
        reason = "相关性未通过，跳过投放。"

    return KeywordExpansionDecision(
        term=candidate.term,
        placement=placement,
        bid=bid,
        should_launch=should_launch,
        reason=reason,
    )
