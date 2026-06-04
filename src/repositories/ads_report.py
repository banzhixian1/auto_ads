from enum import Enum
from typing import Optional
from datetime import date, datetime
from src.utils.db_conn_pool import create_mysql_pool, SQLAlchemyPool

# 可选全局默认 pool
DEFAULT_POOL = create_mysql_pool('dataiforce')

DateLike = str | date | datetime


class TimeGranularity(str, Enum):
    """广告报表时间粒度枚举。"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class AdsReportRepository:
    """
    广告报表数据访问层
    只负责 SQL 查询和数据获取，不做指标计算
    """

    def __init__(self, pool: Optional[SQLAlchemyPool] = None):
        """
        初始化 Repository
        
        Args:
            pool: SQLAlchemyPool 实例，如果不传则使用全局默认 pool
        """
        self.pool = pool or DEFAULT_POOL

    def normalize_date_input(self, value: DateLike) -> str:
        """
        将日期参数统一规范化为 YYYY-MM-DD 字符串。

        Args:
            value: 支持 str、date、datetime 三种输入类型。

        Returns:
            str: 规范化后的日期字符串。

        Raises:
            TypeError: 当输入类型不是 str / date / datetime 时抛出。
            ValueError: 当字符串无法按 ISO 日期格式解析时抛出。
        """
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, str):
            return date.fromisoformat(value).isoformat()
        raise TypeError(f"不支持的日期类型: {type(value)!r}")

    def normalize_time_granularity(
        self,
        value: TimeGranularity | str,
    ) -> TimeGranularity:
        """
        将时间粒度参数统一转为 TimeGranularity 枚举。

        Args:
            value: 时间粒度枚举，或对应字符串。

        Returns:
            TimeGranularity: 标准化后的时间粒度枚举值。

        Raises:
            ValueError: 当输入值不在支持范围内时抛出。
        """
        if isinstance(value, TimeGranularity):
            return value
        return TimeGranularity(str(value).strip().lower())

    def get_user_search_terms_by_asin(
        self,
        asin: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> list[dict]:
        """
        查询指定 ASIN 在指定时间范围内的用户搜索词流量来源。

        Args:
            asin: 需要查询的商品 ASIN。
            start_date: 开始日期，支持 str / date / datetime。
            end_date: 结束日期，支持 str / date / datetime。

        Returns:
            list[dict]: 用户搜索词明细列表。
            每条记录建议至少包含以下字段：
            - term_type: 流量类型，取值建议为 keyword 或 product
            - search_term: 搜索词文本，或商品流量对应的 ASIN
            - clicks: 点击量
            - orders: 订单量
            - spend: 花费
            - sales: 销售额

        Notes:
            该方法对应 workflow 的“查询用户搜索词”步骤，
            用于拆分关键词流量和商品流量，并进一步筛选高价值词与高价值 ASIN。
        """
        raise NotImplementedError("请在这里补充广告报表 SQL。")

    def get_asin_ads_data(
        self,
        asin: str,
        start_date: DateLike,
        end_date: DateLike,
    ) -> list[dict]:
        """
        查询指定 ASIN 在指定时间范围内的广告活动汇总数据。

        Args:
            asin: 需要查询的商品 ASIN。
            start_date: 开始日期，支持 str / date / datetime。
            end_date: 结束日期，支持 str / date / datetime。

        Returns:
            list[dict]: 广告活动维度的汇总数据列表。
            每条记录建议至少包含以下字段：
            - campaign_id: 广告活动 ID
            - campaign_name: 广告活动名称
            - impressions: 曝光量
            - clicks: 点击量
            - orders: 订单量
            - spend: 花费
            - sales: 销售额
            - acos: ACOS
            - roas: ROAS

        Notes:
            该方法更适合做 ASIN 级别广告全局体检，
            当前拓词主流程还未直接调用，但后续预算、扩量、收缩判断会用到。
        """
        raise NotImplementedError("请在这里补充广告报表 SQL。")
    
    def get_target_data(
        self,
        target_type: str,
        target_value: str,
        start_date: DateLike,
        end_date: DateLike,
        time_granularity: TimeGranularity | str,
    ) -> list[dict]:
        """
        查询指定投放目标在指定时间范围内的历史表现数据。

        Args:
            target_type: 投放目标类型，取值建议为 keyword 或 product。
            target_value: 投放目标值。target_type 为 keyword 时传关键词文本，
                target_type 为 product 时传商品 ASIN。
            start_date: 开始日期，支持 str / date / datetime。
            end_date: 结束日期，支持 str / date / datetime。
            time_granularity: 时间粒度，支持 TimeGranularity 枚举或对应字符串。

        Returns:
            list[dict]: 投放目标表现数据列表。
            每条记录建议至少包含以下字段：
            - placement: 广告位，如 top_of_search / rest_of_search / product_pages
            - bid: 历史 bid
            - impressions: 曝光量
            - clicks: 点击量
            - orders: 订单量
            - spend: 花费
            - sales: 销售额
            - cpc: CPC
            - cvr: CVR
            - acos: ACOS

        Notes:
            该方法对应 workflow 的“定位置定 bid”步骤：
            - 有历史数据时，可基于不同 placement 的表现和历史 bid 做调价
            - 没有历史数据时，可退化为使用位置平均转化率和售价倒推 bid
        """
        raise NotImplementedError("请在这里补充广告报表 SQL。")
    
    def get_campaign_data(
        self,
        campaign_id: str,
        start_date: DateLike,
        end_date: DateLike,
        time_granularity: TimeGranularity | str,
    ) -> list[dict]:
        """
        查询指定广告活动在指定时间范围内的汇总数据。

        Args:
            campaign_id: 广告活动 ID。
            start_date: 开始日期，支持 str / date / datetime。
            end_date: 结束日期，支持 str / date / datetime。
            time_granularity: 时间粒度，支持 TimeGranularity 枚举或对应字符串。

        Returns:
            list[dict]: 广告活动汇总数据列表。
            每条记录建议至少包含以下字段：
            - campaign_id: 广告活动 ID
            - impressions: 曝光量
            - clicks: 点击量
            - orders: 订单量
            - spend: 花费
            - sales: 销售额
            - acos: ACOS
            - roas: ROAS

        Notes:
            该方法更适合 campaign 层级的预算、整体效果和结构分析，
            当前拓词主流程不是强依赖，但后续执行层和预算策略会用到。
        """
        raise NotImplementedError("请在这里补充广告报表 SQL。")
