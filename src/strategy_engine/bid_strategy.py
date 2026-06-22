from typing import Any

from src.constants.metrics import HIGH_PERFORMANCE_EFFICIENCY
from src.schemas.strategy import BidRecommendation

DEFAULT_INITIAL_TARGET_ACOS = 0.40


def recommend_bid(
    average_order_price: float | None,
    target_acos: float | None,
    conversion_rate: float | None = None,
    current_bid: float | None = None,
    efficiency: float | None = None,
    average_order_price_source: str | None = None,
    conversion_rate_source: str | None = None,
    placement_name: str | None = None,
    placement_metrics: dict[str, Any] | None = None,
) -> BidRecommendation:
    # 有历史 bid 时优先做保守调价，避免直接重算出价导致波动过大
    if current_bid is not None and efficiency is not None:
        multiplier = 1.10 if efficiency >= HIGH_PERFORMANCE_EFFICIENCY else 0.90
        raw_bid = current_bid * multiplier
        suggested_bid = round(raw_bid, 2)
        return BidRecommendation(
            suggested_bid=suggested_bid,
            reason="基于历史 bid 和效率做保守调整。",
            calculation={
                "method": "current_bid_adjustment",
                "formula": "current_bid * multiplier",
                "inputs": {
                    "current_bid": current_bid,
                    "efficiency": efficiency,
                    "high_performance_efficiency": HIGH_PERFORMANCE_EFFICIENCY,
                    "multiplier": multiplier,
                },
                "raw_bid": raw_bid,
                "rounding": "round(raw_bid, 2)",
                "suggested_bid": suggested_bid,
            },
        )

    # 没有历史 bid 时，用售价、目标 ACOS、预估转化率倒推可接受 CPC
    if (
        average_order_price is not None
        and conversion_rate not in (None, 0)
    ):
        effective_target_acos = (
            target_acos if target_acos is not None else DEFAULT_INITIAL_TARGET_ACOS
        )
        raw_bid = average_order_price * effective_target_acos * conversion_rate
        suggested_bid = round(raw_bid, 2)
        return BidRecommendation(
            suggested_bid=suggested_bid,
            reason="基于售价、目标 ACOS 和对应广告位平均转化率倒推出初始出价。",
            calculation={
                "method": "initial_bid_from_unit_economics",
                "formula": "average_order_price * target_acos * conversion_rate",
                "inputs": {
                    "placement": placement_name,
                    "average_order_price": average_order_price,
                    "average_order_price_source": average_order_price_source,
                    "target_acos": effective_target_acos,
                    "target_acos_source": "request" if target_acos is not None else "default",
                    "default_target_acos": DEFAULT_INITIAL_TARGET_ACOS,
                    "conversion_rate": conversion_rate,
                    "conversion_rate_source": conversion_rate_source,
                    "placement_metrics": placement_metrics or {},
                },
                "raw_bid": raw_bid,
                "rounding": "round(raw_bid, 2)",
                "suggested_bid": suggested_bid,
            },
        )

    # 信息不完整时只返回占位建议，不强行生成数字
    missing_inputs = []
    if current_bid is None:
        missing_inputs.append("current_bid")
    if average_order_price is None:
        missing_inputs.append("average_order_price")
    if conversion_rate in (None, 0):
        missing_inputs.append("conversion_rate")
    return BidRecommendation(
        suggested_bid=None,
        reason="缺少历史 bid 或足够的定价信息，暂不自动给出出价。",
        confidence="low",
        calculation={
            "method": "insufficient_information",
            "required_paths": [
                "current_bid + efficiency",
                "average_order_price + target_acos + conversion_rate",
            ],
            "missing_inputs": missing_inputs,
            "inputs": {
                "placement": placement_name,
                "average_order_price": average_order_price,
                "average_order_price_source": average_order_price_source,
                "target_acos": target_acos,
                "conversion_rate": conversion_rate,
                "conversion_rate_source": conversion_rate_source,
                "current_bid": current_bid,
                "efficiency": efficiency,
                "placement_metrics": placement_metrics or {},
            },
        },
    )
