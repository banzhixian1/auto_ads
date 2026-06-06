from src.schemas.keyword import KeywordCandidate
from src.schemas.strategy import KeywordExpansionDecision
from src.strategy_engine.bid_strategy import recommend_bid
from src.strategy_engine.placement_strategy import decide_placement


def build_keyword_decision(
    candidate: KeywordCandidate,
    average_order_price: float | None = None,
    target_acos: float | None = None,
    current_bid: float | None = None,
    placement_rows: list[dict] | None = None,
) -> KeywordExpansionDecision:
    # 先确定广告位，再生成出价建议
    placement = decide_placement(
        click_share=candidate.click_share,
        conversion_share=candidate.conversion_share,
        efficiency=candidate.efficiency,
    )
    conversion_rate = _get_primary_placement_cvr(
        placement_name=placement.primary,
        placement_rows=placement_rows or [],
    )
    bid = recommend_bid(
        average_order_price=average_order_price,
        target_acos=target_acos,
        conversion_rate=conversion_rate,
        current_bid=current_bid,
        efficiency=candidate.efficiency,
    )

    return KeywordExpansionDecision(
        term=candidate.term,
        placement=placement,
        bid=bid,
        should_launch=True,
        reason="候选词已通过前置过滤，进入投放策略生成。",
    )


def _get_primary_placement_cvr(
    placement_name: str,
    placement_rows: list[dict],
) -> float | None:
    for row in placement_rows:
        if str(row.get("placement", "")).strip().lower() != placement_name:
            continue
        try:
            cvr = float(row.get("cvr"))
        except (TypeError, ValueError):
            return None
        return cvr if cvr > 0 else None
    return None
