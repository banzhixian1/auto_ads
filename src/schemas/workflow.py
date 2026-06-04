from dataclasses import dataclass, field

from src.schemas.keyword import KeywordCandidate
from src.schemas.strategy import KeywordExpansionDecision


# 工作流输入
@dataclass(slots=True)
class SearchTermExpansionRequest:
    report_date: int
    product_asin: str = ""
    start_date: str = ""
    end_date: str = ""
    seed_search_terms: list[str] = field(default_factory=list)
    seed_asins: list[str] = field(default_factory=list)
    competitor_asins: list[str] = field(default_factory=list)
    product_title: str = ""
    product_features: list[str] = field(default_factory=list)
    average_order_price: float | None = None
    target_acos: float | None = None
    auto_execute: bool = False


# 工作流输出
@dataclass(slots=True)
class SearchTermExpansionResult:
    seeds: list[str] = field(default_factory=list)
    product_seed_asins: list[str] = field(default_factory=list)
    high_value_terms: list[str] = field(default_factory=list)
    high_value_asins: list[str] = field(default_factory=list)
    candidates: list[KeywordCandidate] = field(default_factory=list)
    decisions: list[KeywordExpansionDecision] = field(default_factory=list)
    skipped_terms: list[str] = field(default_factory=list)
    execution_summary: str | None = None
