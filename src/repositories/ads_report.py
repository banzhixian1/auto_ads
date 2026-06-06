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

    def get_enabled_asin_campaign_scope_cte(self) -> str:
        """
        返回通用 CTE：通过 ASIN 找到关联且状态为 ENABLED 的广告活动。

        依赖参数：
        - asin: 已标准化为大写的 ASIN。
        """
        return """
            enabled_asin_campaign_scope AS (
                SELECT DISTINCT
                    ap.profile_id,
                    ap.campaign_id,
                    campaign.campaign_name,
                    campaign.ad_type,
                    campaign.state,
                    campaign.budget,
                    campaign.delivery_status
                FROM
                    amz_ad_ad_product ap
                    INNER JOIN amz_ad_campaign campaign
                        ON ap.profile_id = campaign.profile_id
                        AND ap.campaign_id = campaign.campaign_id
                WHERE
                    ap.campaign_id IS NOT NULL
                    AND UPPER(campaign.state) = 'ENABLED'
                    AND (
                        (
                            UPPER(ap.product_id_type) = 'ASIN'
                            AND UPPER(ap.product_id) = :asin
                        )
                        OR UPPER(ap.resolved_product_id) = :asin
                    )
            )
        """


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
            每条记录包含以下展示字段：
            - search_term: 用户搜索词
            - campaign_ad_group: 所属广告活动/组
            - impressions: 曝光量
            - clicks: 点击量
            - ctr: CTR
            - spend: 广告花费
            - cpc: CPC
            - sales: 广告总销售额
            - acos: ACoS
            - roas: ROAS
            - orders: 广告总订单量
            - cvr: CVR
            - cpa: CPA
            - units_sold: 广告总销量
            - term_type: 兼容字段，keyword 或 product

        Notes:
            该方法对应 workflow 的“查询用户搜索词”步骤，
            用于拆分关键词流量和商品流量，并进一步筛选高价值词与高价值 ASIN。
        """
        normalized_asin = str(asin).strip().upper()
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)

        if not normalized_asin:
            return []

        sql = f"""
            WITH {self.get_enabled_asin_campaign_scope_cte()}
            SELECT
                st.query AS search_term,
                CASE
                    WHEN NULLIF(MAX(st.campaign_name), '') IS NULL THEN NULLIF(MAX(st.ad_group_name), '')
                    WHEN NULLIF(MAX(st.ad_group_name), '') IS NULL THEN NULLIF(MAX(st.campaign_name), '')
                    WHEN MAX(st.campaign_name) = MAX(st.ad_group_name) THEN MAX(st.campaign_name)
                    ELSE CONCAT(MAX(st.campaign_name), ' / ', MAX(st.ad_group_name))
                END AS campaign_ad_group,
                SUM(st.impressions) AS impressions,
                SUM(st.clicks) AS clicks,
                ROUND(SUM(st.clicks) / NULLIF(SUM(st.impressions), 0), 6) AS ctr,
                ROUND(SUM(st.cost), 4) AS spend,
                ROUND(SUM(st.cost) / NULLIF(SUM(st.clicks), 0), 4) AS cpc,
                ROUND(SUM(st.attributed_sales_7d), 4) AS sales,
                ROUND(SUM(st.cost) / NULLIF(SUM(st.attributed_sales_7d), 0), 4) AS acos,
                ROUND(SUM(st.attributed_sales_7d) / NULLIF(SUM(st.cost), 0), 4) AS roas,
                SUM(st.attributed_conversions_7d) AS orders,
                ROUND(SUM(st.attributed_conversions_7d) / NULLIF(SUM(st.clicks), 0), 6) AS cvr,
                ROUND(SUM(st.cost) / NULLIF(SUM(st.attributed_conversions_7d), 0), 4) AS cpa,
                SUM(st.attributed_units_ordered_7d) AS units_sold,
                CASE
                    WHEN UPPER(COALESCE(st.query, '')) REGEXP '^[A-Z0-9]{{10}}$' THEN 'product'
                    ELSE 'keyword'
                END AS term_type
            FROM
                amz_ad_rpt_search_term st
                INNER JOIN enabled_asin_campaign_scope s
                    ON st.profile_id = s.profile_id
                    AND st.campaign_id = s.campaign_id
            WHERE
                st.report_date BETWEEN :start_date AND :end_date
                AND st.query IS NOT NULL
                AND st.query <> ''
            GROUP BY
                st.profile_id,
                st.campaign_id,
                st.ad_group_id,
                st.query,
                CASE
                    WHEN UPPER(COALESCE(st.query, '')) REGEXP '^[A-Z0-9]{{10}}$' THEN 'product'
                    ELSE 'keyword'
                END
            ORDER BY
                clicks DESC,
                campaign_ad_group ASC,
                search_term ASC
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
        asin: str | None = None,
    ) -> list[dict]:
        """
        查询指定用户搜索词在指定时间范围内的历史趋势数据。

        Args:
            target_type: 搜索词类型，取值建议为 keyword 或 product。
            target_value: 搜索词值。target_type 为 keyword 时传用户搜索词，
                target_type 为 product 时传商品 ASIN。
            start_date: 开始日期，支持 str / date / datetime。
            end_date: 结束日期，支持 str / date / datetime。
            time_granularity: 时间粒度，支持 TimeGranularity 枚举或对应字符串。
            asin: 当前商品 ASIN，用于限定 G+ 口径下的商品广告结构。

        Returns:
            list[dict]: 用户搜索词趋势数据列表。
            每条记录建议至少包含以下字段：
            - report_date: 报表周期
            - search_term: 用户搜索词
            - campaign_ad_group: 所属广告活动/组
            - impressions: 曝光量
            - clicks: 点击量
            - ctr: CTR
            - spend: 广告花费
            - cpc: CPC
            - sales: 销售额
            - acos: ACOS
            - roas: ROAS
            - orders: 广告总订单量
            - cvr: CVR
            - cpa: CPA
            - units_sold: 广告总销量
            - term_type: keyword 或 product

        Notes:
            该方法对应前端“用户搜索词趋势分析”弹窗，
            直接基于搜索词报表中的 query 字段按时间粒度聚合。
        """
        normalized_target_type = str(target_type).strip().lower()
        normalized_target_value = str(target_value).strip()
        normalized_asin = str(asin).strip().upper() if asin else ""
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)
        period_expression = self.get_report_period_expression(
            "st.report_date",
            time_granularity,
        )

        if not normalized_target_type or not normalized_target_value or not normalized_asin:
            return []

        if normalized_target_type == "keyword":
            target_filter = "st.query = :target_value"
            normalized_target_value_param = normalized_target_value
        elif normalized_target_type == "product":
            target_filter = "UPPER(st.query) = :target_value"
            normalized_target_value_param = normalized_target_value.upper()
        else:
            raise ValueError(f"不支持的投放目标类型: {target_type!r}")

        sql = f"""
            WITH {self.get_enabled_asin_campaign_scope_cte()},
            target_search_term_scope AS (
                SELECT
                    st.profile_id,
                    st.campaign_id,
                    st.ad_group_id,
                    CASE
                        WHEN NULLIF(MAX(st.campaign_name), '') IS NULL THEN NULLIF(MAX(st.ad_group_name), '')
                        WHEN NULLIF(MAX(st.ad_group_name), '') IS NULL THEN NULLIF(MAX(st.campaign_name), '')
                        WHEN MAX(st.campaign_name) = MAX(st.ad_group_name) THEN MAX(st.campaign_name)
                        ELSE CONCAT(MAX(st.campaign_name), ' / ', MAX(st.ad_group_name))
                    END AS campaign_ad_group,
                    COALESCE(SUM(st.clicks), 0) AS total_clicks,
                    COALESCE(SUM(st.impressions), 0) AS total_impressions
                FROM
                    amz_ad_rpt_search_term st
                    INNER JOIN enabled_asin_campaign_scope asin_scope
                        ON st.profile_id = asin_scope.profile_id
                        AND st.campaign_id = asin_scope.campaign_id
                WHERE
                    st.report_date BETWEEN :start_date AND :end_date
                    AND {target_filter}
                GROUP BY
                    st.profile_id,
                    st.campaign_id,
                    st.ad_group_id
                ORDER BY
                    total_clicks DESC,
                    campaign_ad_group ASC,
                    total_impressions DESC,
                    st.campaign_id ASC,
                    st.ad_group_id ASC
                LIMIT 1
            )
            SELECT
                {period_expression} AS report_date,
                :target_value AS search_term,
                MAX(target_scope.campaign_ad_group) AS campaign_ad_group,
                SUM(st.impressions) AS impressions,
                SUM(st.clicks) AS clicks,
                ROUND(SUM(st.clicks) / NULLIF(SUM(st.impressions), 0), 6) AS ctr,
                ROUND(SUM(st.cost), 4) AS spend,
                ROUND(SUM(st.cost) / NULLIF(SUM(st.clicks), 0), 4) AS cpc,
                ROUND(SUM(st.attributed_sales_7d), 4) AS sales,
                ROUND(SUM(st.cost) / NULLIF(SUM(st.attributed_sales_7d), 0), 4) AS acos,
                ROUND(SUM(st.attributed_sales_7d) / NULLIF(SUM(st.cost), 0), 4) AS roas,
                SUM(st.attributed_conversions_7d) AS orders,
                ROUND(SUM(st.attributed_conversions_7d) / NULLIF(SUM(st.clicks), 0), 6) AS cvr,
                ROUND(SUM(st.cost) / NULLIF(SUM(st.attributed_conversions_7d), 0), 4) AS cpa,
                SUM(st.attributed_units_ordered_7d) AS units_sold,
                CASE
                    WHEN :target_type = 'product' THEN 'product'
                    ELSE 'keyword'
                END AS term_type
            FROM
                amz_ad_rpt_search_term st
                INNER JOIN target_search_term_scope target_scope
                    ON st.profile_id = target_scope.profile_id
                    AND st.campaign_id = target_scope.campaign_id
                    AND st.ad_group_id <=> target_scope.ad_group_id
            WHERE
                st.report_date BETWEEN :start_date AND :end_date
                AND {target_filter}
            GROUP BY
                {period_expression}
            ORDER BY
                report_date DESC
        """
        params = {
            "target_type": normalized_target_type,
            "target_value": normalized_target_value_param,
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
            每条记录包含以下字段：
            - enabled: 是否有效，当前仅返回 ENABLED 活动
            - campaign_id: 广告活动 ID
            - campaign_name: 广告活动名称
            - ad_type: 广告类型
            - budget: 预算
            - impressions: 曝光量
            - clicks: 点击量
            - ctr: CTR
            - spend: 广告花费
            - cpc: CPC
            - vcpm: VCPM，按 viewable_impressions 计算
            - sales: 广告总销售额
            - acos: ACoS
            - roas: ROAS
            - orders: 广告总订单量
            - cvr: CVR
            - cpa: CPA
            - units_sold: 广告总销量

        Notes:
            该方法更适合做 ASIN 级别广告全局体检，
            当前拓词主流程还未直接调用，但后续预算、扩量、收缩判断会用到。
        """
        normalized_asin = str(asin).strip().upper()
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)

        if not normalized_asin:
            return []

        sql = f"""
            WITH {self.get_enabled_asin_campaign_scope_cte()}
            SELECT
                CASE
                    WHEN MAX(UPPER(scope.state)) = 'ENABLED' THEN 1
                    ELSE 0
                END AS enabled,
                scope.campaign_id,
                MAX(scope.campaign_name) AS campaign_name,
                COALESCE(MAX(rpt.ad_type), MAX(scope.ad_type)) AS ad_type,
                MAX(scope.budget) AS budget,
                SUM(rpt.impressions) AS impressions,
                SUM(rpt.clicks) AS clicks,
                ROUND(SUM(rpt.clicks) / NULLIF(SUM(rpt.impressions), 0), 6) AS ctr,
                ROUND(SUM(rpt.spend), 4) AS spend,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.clicks), 0), 4) AS cpc,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.viewable_impressions), 0) * 1000, 4) AS vcpm,
                ROUND(SUM(rpt.sales), 4) AS sales,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.sales), 0), 4) AS acos,
                ROUND(SUM(rpt.sales) / NULLIF(SUM(rpt.spend), 0), 4) AS roas,
                SUM(rpt.orders) AS orders,
                ROUND(SUM(rpt.orders) / NULLIF(SUM(rpt.clicks), 0), 6) AS cvr,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.orders), 0), 4) AS cpa,
                SUM(rpt.units_sold) AS units_sold
            FROM
                amz_ad_rpt_campaign rpt
                INNER JOIN enabled_asin_campaign_scope scope
                    ON rpt.profile_id = scope.profile_id
                    AND rpt.campaign_id = scope.campaign_id
            WHERE
                rpt.report_date BETWEEN :start_date AND :end_date
            GROUP BY
                scope.profile_id,
                scope.campaign_id
            ORDER BY
                clicks DESC,
                impressions DESC,
                scope.campaign_id ASC
        """
        params = {
            "asin": normalized_asin,
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
            list[dict]: 广告活动趋势数据列表。
            每条记录包含以下可用字段：
            - report_date: 报表周期
            - enabled: 是否有效
            - campaign_id: 广告活动 ID
            - campaign_name: 广告活动名称
            - ad_type: 广告类型
            - budget: 预算
            - impressions: 曝光量
            - clicks: 点击量
            - ctr: CTR
            - spend: 广告花费
            - cpc: CPC
            - vcpm: VCPM，按 viewable_impressions 计算
            - sales: 广告总销售额
            - acos: ACoS
            - roas: ROAS
            - orders: 广告总订单量
            - cvr: CVR
            - cpa: CPA
            - units_sold: 广告总销量

        Notes:
            该方法更适合 campaign 层级的预算、整体效果和结构分析，
            当前拓词主流程不是强依赖，但后续执行层和预算策略会用到。
        """
        normalized_campaign_id = str(campaign_id).strip()
        normalized_start_date = self.normalize_date_input(start_date)
        normalized_end_date = self.normalize_date_input(end_date)
        period_expression = self.get_report_period_expression(
            "rpt.report_date",
            time_granularity,
        )

        if not normalized_campaign_id:
            return []

        sql = f"""
            SELECT
                {period_expression} AS report_date,
                CASE
                    WHEN MAX(UPPER(campaign.state)) = 'ENABLED' THEN 1
                    ELSE 0
                END AS enabled,
                rpt.campaign_id,
                MAX(campaign.campaign_name) AS campaign_name,
                COALESCE(MAX(rpt.ad_type), MAX(campaign.ad_type)) AS ad_type,
                MAX(campaign.budget) AS budget,
                SUM(rpt.impressions) AS impressions,
                SUM(rpt.clicks) AS clicks,
                ROUND(SUM(rpt.clicks) / NULLIF(SUM(rpt.impressions), 0), 6) AS ctr,
                ROUND(SUM(rpt.spend), 4) AS spend,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.clicks), 0), 4) AS cpc,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.viewable_impressions), 0) * 1000, 4) AS vcpm,
                ROUND(SUM(rpt.sales), 4) AS sales,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.sales), 0), 4) AS acos,
                ROUND(SUM(rpt.sales) / NULLIF(SUM(rpt.spend), 0), 4) AS roas,
                SUM(rpt.orders) AS orders,
                ROUND(SUM(rpt.orders) / NULLIF(SUM(rpt.clicks), 0), 6) AS cvr,
                ROUND(SUM(rpt.spend) / NULLIF(SUM(rpt.orders), 0), 4) AS cpa,
                SUM(rpt.units_sold) AS units_sold
            FROM
                amz_ad_rpt_campaign rpt
                LEFT JOIN amz_ad_campaign campaign
                    ON rpt.profile_id = campaign.profile_id
                    AND rpt.campaign_id = campaign.campaign_id
            WHERE
                rpt.report_date BETWEEN :start_date AND :end_date
                AND rpt.campaign_id = :campaign_id
            GROUP BY
                {period_expression},
                rpt.campaign_id
            ORDER BY
                report_date DESC
        """
        params = {
            "campaign_id": normalized_campaign_id,
            "start_date": normalized_start_date,
            "end_date": normalized_end_date,
        }
        return self.pool.query(sql, params=params)
