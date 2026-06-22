from src.schemas.keyword import KeywordCandidate
from src.schemas.strategy import KeywordExpansionDecision
from src.constants.placements import normalize_placement
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
    primary_placement_row = _get_primary_placement_row(
        placement_name=placement.primary,
        placement_rows=placement_rows or [],
    )
    conversion_rate = _to_positive_float(
        primary_placement_row.get("cvr") if primary_placement_row else None
    )
    effective_average_order_price, average_order_price_source = _resolve_average_order_price(
        average_order_price=average_order_price,
        placement_row=primary_placement_row,
    )
    bid = recommend_bid(
        average_order_price=effective_average_order_price,
        target_acos=target_acos,
        conversion_rate=conversion_rate,
        current_bid=current_bid,
        efficiency=candidate.efficiency,
        average_order_price_source=average_order_price_source,
        conversion_rate_source="placement.cvr" if conversion_rate is not None else None,
        placement_name=placement.primary,
        placement_metrics=_extract_placement_metrics(primary_placement_row),
    )

    return KeywordExpansionDecision(
        term=candidate.term,
        placement=placement,
        bid=bid,
        should_launch=True,
        reason="候选词已通过前置过滤，进入投放策略生成。",
    )


def _get_primary_placement_row(
    placement_name: str,
    placement_rows: list[dict],
) -> dict | None:
    for row in placement_rows:
        if normalize_placement(row.get("placement")) != placement_name:
            continue
        return row
    return None


def _resolve_average_order_price(
    average_order_price: float | None,
    placement_row: dict | None,
) -> tuple[float | None, str | None]:
    if average_order_price is not None:
        return average_order_price, "request.average_order_price"
    if not placement_row:
        return None, None

    # Bid 公式使用订单转化率，因此优先用订单口径估算客单价。
    resolved = _divide_positive(
        placement_row.get("sales_same_sku"),
        placement_row.get("orders_same_sku"),
    )
    if resolved is not None:
        return resolved, "placement.sales_same_sku / placement.orders_same_sku"

    resolved = _divide_positive(placement_row.get("sales"), placement_row.get("orders"))
    if resolved is not None:
        return resolved, "placement.sales / placement.orders"

    resolved = _divide_positive(
        placement_row.get("sales_same_sku"),
        placement_row.get("units_sold_same_sku"),
    )
    if resolved is not None:
        return resolved, "placement.sales_same_sku / placement.units_sold_same_sku"

    resolved = _divide_positive(placement_row.get("sales"), placement_row.get("units_sold"))
    if resolved is not None:
        return resolved, "placement.sales / placement.units_sold"
    return None, None


def _extract_placement_metrics(row: dict | None) -> dict:
    if not row:
        return {}
    metrics = {
        "raw_placement": row.get("placement"),
        "normalized_placement": normalize_placement(row.get("placement")),
    }
    for key in (
        "impressions",
        "clicks",
        "ctr",
        "spend",
        "cpc",
        "sales",
        "acos",
        "roas",
        "orders",
        "cvr",
        "units_sold",
        "sales_same_sku",
        "orders_same_sku",
        "units_sold_same_sku",
    ):
        if key in row:
            metrics[key] = row.get(key)
    return metrics


def _divide_positive(numerator, denominator) -> float | None:
    numerator_value = _to_positive_float(numerator)
    denominator_value = _to_positive_float(denominator)
    if numerator_value is None or denominator_value is None:
        return None
    return numerator_value / denominator_value


def _to_positive_float(value) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result > 0 else None
