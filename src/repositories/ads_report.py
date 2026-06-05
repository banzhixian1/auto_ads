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

    def get_report_period_expression(
        self,
        column_name: str,
        time_granularity: TimeGranularity | str,
    ) -> str:
        """根据时间粒度生成 MySQL 日期分组表达式。"""
        normalized_granularity = self.normalize_time_granularity(time_granularity)
        if normalized_granularity == TimeGranularity.DAY:
            return f"DATE({column_name})"
        if normalized_granularity == TimeGranularity.WEEK:
            return f"DATE_SUB(DATE({column_name}), INTERVAL WEEKDAY({column_name}) DAY)"
        if normalized_granularity == TimeGranularity.MONTH:
            return f"STR_TO_DATE(DATE_FORMAT({column_name}, '%Y-%m-01'), '%Y-%m-%d')"
        raise ValueError(f"不支持的时间粒度: {time_granularity!r}")


    # 用户搜索词 
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
        normalized_asin = str(asin).strip().upper()
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)

        if not normalized_asin:
            return []

        sql = """
            WITH target_asin_scope AS (
                SELECT
                    profile_id,
                    campaign_id,
                    ad_group_id
                FROM
                    amz_ad_rpt_ad
                WHERE
                    report_date BETWEEN :start_date AND :end_date
                    AND UPPER(asin) = :asin
                GROUP BY
                    profile_id,
                    campaign_id,
                    ad_group_id
            ),
            strict_asin_scope AS (
                SELECT
                    target_asin_scope.profile_id,
                    target_asin_scope.campaign_id,
                    target_asin_scope.ad_group_id
                FROM
                    target_asin_scope
                WHERE
                    NOT EXISTS (
                        SELECT
                            1
                        FROM
                            amz_ad_rpt_ad other_ad
                        WHERE
                            other_ad.report_date BETWEEN :start_date AND :end_date
                            AND other_ad.profile_id = target_asin_scope.profile_id
                            AND other_ad.campaign_id = target_asin_scope.campaign_id
                            AND other_ad.ad_group_id = target_asin_scope.ad_group_id
                            AND other_ad.asin IS NOT NULL
                            AND other_ad.asin <> ''
                            AND UPPER(other_ad.asin) <> :asin
                    )
            )
            SELECT
                CASE
                    WHEN UPPER(COALESCE(st.query, '')) REGEXP '^[A-Z0-9]{10}$' THEN 'product'
                    ELSE 'keyword'
                END AS term_type,
                st.query AS search_term,
                SUM(st.clicks) AS clicks,
                SUM(st.attributed_conversions_7d) AS orders,
                ROUND(SUM(st.cost), 4) AS spend,
                ROUND(SUM(st.attributed_sales_7d), 4) AS sales
            FROM
                amz_ad_rpt_search_term st
                INNER JOIN strict_asin_scope s
                    ON st.profile_id = s.profile_id
                    AND st.campaign_id = s.campaign_id
                    AND st.ad_group_id = s.ad_group_id
            WHERE
                st.report_date BETWEEN :start_date AND :end_date
                AND st.query IS NOT NULL
                AND st.query <> ''
            GROUP BY
                CASE
                    WHEN UPPER(COALESCE(st.query, '')) REGEXP '^[A-Z0-9]{10}$' THEN 'product'
                    ELSE 'keyword'
                END,
                st.query
            ORDER BY
                clicks DESC,
                search_term ASC
        """
        params = {
            "asin": normalized_asin,
            "start_date": normalized_start_date,
            "end_date": normalized_end_date,
        }
        return self.pool.query(sql, params=params)

    # 广告活动
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
        normalized_asin = str(asin).strip().upper()
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)

        if not normalized_asin:
            return []

        sql = """
            WITH asin_campaign_data AS (
                SELECT
                    campaign_id,
                    SUM(impressions) AS impressions,
                    SUM(clicks) AS clicks,
                    SUM(orders) AS orders,
                    ROUND(SUM(spend), 4) AS spend,
                    ROUND(SUM(sales), 4) AS sales
                FROM
                    amz_ad_rpt_ad
                WHERE
                    report_date BETWEEN :start_date AND :end_date
                    AND UPPER(asin) = :asin
                GROUP BY
                    campaign_id
            ),
            campaign_names AS (
                SELECT
                    st.campaign_id,
                    MAX(st.campaign_name) AS campaign_name
                FROM
                    amz_ad_rpt_search_term st
                    INNER JOIN asin_campaign_data ad_data
                        ON st.campaign_id = ad_data.campaign_id
                WHERE
                    st.report_date BETWEEN :start_date AND :end_date
                GROUP BY
                    st.campaign_id
            )
            SELECT
                ad_data.campaign_id,
                campaign_names.campaign_name,
                ad_data.impressions,
                ad_data.clicks,
                ad_data.orders,
                ad_data.spend,
                ad_data.sales,
                ROUND(ad_data.spend / NULLIF(ad_data.sales, 0), 4) AS acos,
                ROUND(ad_data.sales / NULLIF(ad_data.spend, 0), 4) AS roas
            FROM
                asin_campaign_data ad_data
                LEFT JOIN campaign_names
                    ON ad_data.campaign_id = campaign_names.campaign_id
            ORDER BY
                ad_data.clicks DESC,
                ad_data.impressions DESC,
                ad_data.campaign_id ASC
        """
        params = {
            "asin": normalized_asin,
            "start_date": normalized_start_date,
            "end_date": normalized_end_date,
        }
        return self.pool.query(sql, params=params)
    
    # 用户搜索词趋势
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
        normalized_target_type = str(target_type).strip().lower()
        normalized_target_value = str(target_value).strip()
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)
        period_expression = self.get_report_period_expression(
            "cp.report_date",
            time_granularity,
        )

        if not normalized_target_type or not normalized_target_value:
            return []

        if normalized_target_type == "keyword":
            target_filter = "st.keyword_text = :target_value"
            normalized_target_value_param = normalized_target_value
        elif normalized_target_type == "product":
            target_filter = """
                (
                    UPPER(st.keyword_text) = :target_value
                    OR UPPER(st.query) = :target_value
                )
            """
            normalized_target_value_param = normalized_target_value.upper()
        else:
            raise ValueError(f"不支持的投放目标类型: {target_type!r}")

        sql = f"""
            WITH target_campaign_scope AS (
                SELECT DISTINCT
                    st.profile_id,
                    st.campaign_id
                FROM
                    amz_ad_rpt_search_term st
                WHERE
                    st.report_date BETWEEN :start_date AND :end_date
                    AND {target_filter}
            )
            SELECT
                {period_expression} AS report_date,
                cp.placement,
                SUM(cp.impressions) AS impressions,
                SUM(cp.clicks) AS clicks,
                SUM(cp.orders) AS orders,
                ROUND(SUM(cp.spend), 4) AS spend,
                ROUND(SUM(cp.sales), 4) AS sales,
                ROUND(SUM(cp.spend) / NULLIF(SUM(cp.clicks), 0), 4) AS cpc,
                ROUND(SUM(cp.orders) / NULLIF(SUM(cp.clicks), 0), 6) AS cvr,
                ROUND(SUM(cp.spend) / NULLIF(SUM(cp.sales), 0), 4) AS acos
            FROM
                amz_ad_rpt_campaign_placement cp
                INNER JOIN target_campaign_scope target_scope
                    ON cp.profile_id = target_scope.profile_id
                    AND cp.campaign_id = target_scope.campaign_id
            WHERE
                cp.report_date BETWEEN :start_date AND :end_date
            GROUP BY
                {period_expression},
                cp.placement
            ORDER BY
                report_date ASC,
                cp.placement ASC
        """
        params = {
            "target_value": normalized_target_value_param,
            "start_date": normalized_start_date,
            "end_date": normalized_end_date,
        }
        return self.pool.query(sql, params=params)
    
    # 广告活动趋势
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
        normalized_campaign_id = str(campaign_id).strip()
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)
        period_expression = self.get_report_period_expression(
            "report_date",
            time_granularity,
        )

        if not normalized_campaign_id:
            return []

        sql = f"""
            SELECT
                {period_expression} AS report_date,
                campaign_id,
                SUM(impressions) AS impressions,
                SUM(clicks) AS clicks,
                SUM(orders) AS orders,
                ROUND(SUM(spend), 4) AS spend,
                ROUND(SUM(sales), 4) AS sales,
                ROUND(SUM(spend) / NULLIF(SUM(sales), 0), 4) AS acos,
                ROUND(SUM(sales) / NULLIF(SUM(spend), 0), 4) AS roas
            FROM
                amz_ad_rpt_campaign
            WHERE
                report_date BETWEEN :start_date AND :end_date
                AND campaign_id = :campaign_id
            GROUP BY
                {period_expression},
                campaign_id
            ORDER BY
                report_date ASC
        """
        params = {
            "campaign_id": normalized_campaign_id,
            "start_date": normalized_start_date,
            "end_date": normalized_end_date,
        }
        return self.pool.query(sql, params=params)
