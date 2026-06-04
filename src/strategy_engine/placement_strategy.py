from src.constants.metrics import (
    DEFAULT_CLICK_SHARE_THRESHOLD,
    DEFAULT_CONVERSION_SHARE_THRESHOLD,
    DEFAULT_EFFICIENCY_THRESHOLD,
)
from src.constants.placements import REST_OF_SEARCH, TOP_OF_SEARCH
from src.schemas.strategy import PlacementDecision


def decide_placement(
    click_share: float,
    conversion_share: float,
    efficiency: float,
    click_share_threshold: float = DEFAULT_CLICK_SHARE_THRESHOLD,
    conversion_share_threshold: float = DEFAULT_CONVERSION_SHARE_THRESHOLD,
    efficiency_threshold: float = DEFAULT_EFFICIENCY_THRESHOLD,
) -> PlacementDecision:
    # 先把连续指标转成高低分类，后续按规则表走
    click_high = click_share >= click_share_threshold
    conversion_high = conversion_share >= conversion_share_threshold
    efficiency_high = efficiency >= efficiency_threshold

    # 高转化、高效率词优先抢搜索顶部
    if conversion_high and efficiency_high:
        return PlacementDecision(
            primary=TOP_OF_SEARCH,
            reason="转化份额和出单效率较高，优先争取搜索顶部流量。",
        )

    # 效率高但份额未起量，采用顶部优先并保留其余位置测试
    if not click_high and not conversion_high and efficiency_high:
        return PlacementDecision(
            primary=TOP_OF_SEARCH,
            secondary=[REST_OF_SEARCH],
            reason="效率高但份额未做起来，先抢顶部，同时保留其余位置测试。",
        )

    # 有点击和转化基础，但效率偏低，优先低成本位置
    if click_high and conversion_high and not efficiency_high:
        return PlacementDecision(
            primary=REST_OF_SEARCH,
            secondary=[TOP_OF_SEARCH],
            reason="有流量基础但效率偏低，优先其余位置控制成本。",
        )

    # 点击有但转化弱，避免顶部高 CPC 放大浪费
    if click_high and not conversion_high and not efficiency_high:
        return PlacementDecision(
            primary=REST_OF_SEARCH,
            reason="点击有份额但转化弱，先放在其余位置降低浪费。",
        )

    # 兜底策略：从其余位置低成本试投
    return PlacementDecision(
        primary=REST_OF_SEARCH,
        reason="当前指标不强，默认从成本更低的位置开始测试。",
    )
