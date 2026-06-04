from dataclasses import dataclass, field


# 搜索词种子
@dataclass(slots=True)
class KeywordSeed:
    term: str
    source: str


# ASIN 种子
@dataclass(slots=True)
class AsinSeed:
    asin: str
    source: str


# 拓词流程中的候选词对象
@dataclass(slots=True)
class KeywordCandidate:
    term: str
    source: str
    search_rank: int | None = None
    click_share: float = 0.0
    conversion_share: float = 0.0
    efficiency: float = 0.0
    relevance_score: float = 0.0
    related_asins: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
