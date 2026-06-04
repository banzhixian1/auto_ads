from datetime import date, datetime
from enum import Enum


DateLike = str | date | datetime


class ReportGranularity(str, Enum):
    """报告粒度枚举。"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"


def normalize_report_date(value: DateLike) -> date:
    """将自然日期统一转换为 `date`。"""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def normalize_report_granularity(
    value: ReportGranularity | str,
) -> ReportGranularity:
    """将外部传入的报告粒度统一转为枚举。"""
    if isinstance(value, ReportGranularity):
        return value
    return ReportGranularity(str(value).strip().lower())


def resolve_report_anchor_date(
    report_date: DateLike,
    report_granularity: ReportGranularity | str,
) -> date:
    """
    根据自然日期和报告粒度，解析出当前报告周期对应的锚点日期。

    规则约定：
    - day: 当天
    - week: 当前 ISO 周的周六
    - month / quarter: 当前先预留接口，后续按实际报表落库规则补充
    """
    normalized_date = normalize_report_date(report_date)
    granularity = normalize_report_granularity(report_granularity)

    if granularity == ReportGranularity.DAY:
        return normalized_date

    if granularity == ReportGranularity.WEEK:
        iso_year, iso_week, _ = normalized_date.isocalendar()
        date_string = f"{iso_year}-W{iso_week:02d}-6"
        return datetime.strptime(date_string, "%G-W%V-%u").date()

    raise NotImplementedError(f"当前暂未支持 {granularity.value} 粒度的锚点日期解析。")


def get_previous_report_anchor_date(
    anchor_date: DateLike,
    report_granularity: ReportGranularity | str,
) -> date:
    """
    根据当前周期锚点日期，计算上一周期的锚点日期。
    """
    normalized_date = normalize_report_date(anchor_date)
    granularity = normalize_report_granularity(report_granularity)

    if granularity == ReportGranularity.DAY:
        return normalized_date.fromordinal(normalized_date.toordinal() - 1)

    if granularity == ReportGranularity.WEEK:
        return normalized_date.fromordinal(normalized_date.toordinal() - 7)

    if granularity == ReportGranularity.MONTH:
        year = normalized_date.year
        month = normalized_date.month
        if month == 1:
            year -= 1
            month = 12
        else:
            month -= 1
        # 上一个月的月末
        if month == 12:
            next_month_first_day = date(year + 1, 1, 1)
        else:
            next_month_first_day = date(year, month + 1, 1)
        return next_month_first_day.fromordinal(next_month_first_day.toordinal() - 1)

    if granularity == ReportGranularity.QUARTER:
        current_quarter = (normalized_date.month - 1) // 3 + 1
        previous_quarter = current_quarter - 1
        year = normalized_date.year
        if previous_quarter == 0:
            previous_quarter = 4
            year -= 1
        quarter_end_month = previous_quarter * 3
        if quarter_end_month == 12:
            next_month_first_day = date(year + 1, 1, 1)
        else:
            next_month_first_day = date(year, quarter_end_month + 1, 1)
        return next_month_first_day.fromordinal(next_month_first_day.toordinal() - 1)

    raise NotImplementedError(f"当前暂未支持 {granularity.value} 粒度的上一周期解析。")


def resolve_latest_published_report_anchor_date(
    report_date: DateLike,
    report_granularity: ReportGranularity | str,
) -> date:
    """
    根据自然日期和报告粒度，解析“当前时点应该使用的最近已产出报告周期”的锚点日期。

    当前按保守规则处理：
    - day: 取前一天的日报
    - week: 取上一个完整周的周报
    - month: 取上一个完整月的月报
    - quarter: 取上一个完整季度的季报
    """
    current_anchor = resolve_report_anchor_date(report_date, report_granularity)
    return get_previous_report_anchor_date(current_anchor, report_granularity)
