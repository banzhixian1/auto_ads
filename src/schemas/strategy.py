from dataclasses import dataclass, field


# 广告位决策结果
@dataclass(slots=True)
class PlacementDecision:
    primary: str
    secondary: list[str] = field(default_factory=list)
    reason: str = ""


# 出价建议结果
@dataclass(slots=True)
class BidRecommendation:
    suggested_bid: float | None
    reason: str
    confidence: str = "medium"


# 单个候选词最终投放决策
@dataclass(slots=True)
class KeywordExpansionDecision:
    term: str
    placement: PlacementDecision
    bid: BidRecommendation
    should_launch: bool
    reason: str
