from src.constants.metrics import HIGH_PERFORMANCE_EFFICIENCY
from src.schemas.strategy import BidRecommendation


def recommend_bid(
    average_order_price: float | None,
    target_acos: float | None,
    conversion_rate: float | None = None,
    current_bid: float | None = None,
    efficiency: float | None = None,
) -> BidRecommendation:
    # 有历史 bid 时优先做保守调价，避免直接重算出价导致波动过大
    if current_bid is not None and efficiency is not None:
        multiplier = 1.10 if efficiency >= HIGH_PERFORMANCE_EFFICIENCY else 0.90
        return BidRecommendation(
            suggested_bid=round(current_bid * multiplier, 2),
            reason="基于历史 bid 和效率做保守调整。",
        )

    # 没有历史 bid 时，用售价、目标 ACOS、预估转化率倒推可接受 CPC
    if (
        average_order_price is not None
        and target_acos is not None
        and conversion_rate not in (None, 0)
    ):
        max_cpc = average_order_price * target_acos * conversion_rate
        return BidRecommendation(
            suggested_bid=round(max_cpc, 2),
            reason="基于售价、目标 ACOS 和预估转化率倒推出价。",
        )

    # 信息不完整时只返回占位建议，不强行生成数字
    return BidRecommendation(
        suggested_bid=None,
        reason="缺少历史 bid 或足够的定价信息，暂不自动给出出价。",
        confidence="low",
    )
