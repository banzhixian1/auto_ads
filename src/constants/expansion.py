from dataclasses import dataclass
from enum import Enum


class ExpansionIntensity(str, Enum):
    """拓词强度枚举。"""

    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass(frozen=True, slots=True)
class ExpansionIntensityConfig:
    # 最终候选池按搜索排名保留的比例
    keep_rank_percent: float


EXPANSION_INTENSITY_CONFIGS: dict[ExpansionIntensity, ExpansionIntensityConfig] = {
    ExpansionIntensity.CONSERVATIVE: ExpansionIntensityConfig(
        keep_rank_percent=0.3,
    ),
    ExpansionIntensity.BALANCED: ExpansionIntensityConfig(
        keep_rank_percent=0.5,
    ),
    ExpansionIntensity.AGGRESSIVE: ExpansionIntensityConfig(
        keep_rank_percent=0.8,
    ),
}


def normalize_expansion_intensity(
    value: ExpansionIntensity | str,
) -> ExpansionIntensity:
    """将外部传入的拓词强度统一转为枚举。"""
    if isinstance(value, ExpansionIntensity):
        return value
    return ExpansionIntensity(str(value).strip().lower())
