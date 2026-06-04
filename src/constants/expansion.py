from dataclasses import dataclass
from enum import Enum


class ExpansionIntensity(str, Enum):
    """拓词强度枚举。"""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass(frozen=True, slots=True)
class ExpansionIntensityConfig:
    # 参与高价值入口筛选的最大搜索排名
    max_search_rank: int
    # 目标候选词数量，用于后续动态扩词时作为停止条件
    target_term_count: int
    # 是否纳入“尝试型”入口
    include_attempt_terms: bool


EXPANSION_INTENSITY_CONFIGS: dict[ExpansionIntensity, ExpansionIntensityConfig] = {
    ExpansionIntensity.CONSERVATIVE: ExpansionIntensityConfig(
        max_search_rank=200_000,
        target_term_count=30,
        include_attempt_terms=False,
    ),
    ExpansionIntensity.BALANCED: ExpansionIntensityConfig(
        max_search_rank=500_000,
        target_term_count=50,
        include_attempt_terms=True,
    ),
    ExpansionIntensity.AGGRESSIVE: ExpansionIntensityConfig(
        max_search_rank=1_500_000,
        target_term_count=80,
        include_attempt_terms=True,
    ),
}


def normalize_expansion_intensity(
    value: ExpansionIntensity | str,
) -> ExpansionIntensity:
    """将外部传入的拓词强度统一转为枚举。"""
    if isinstance(value, ExpansionIntensity):
        return value
    return ExpansionIntensity(str(value).strip().lower())
