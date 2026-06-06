# repositories 与 services 使用说明

## 1. 适用范围

这两层是当前项目业务主链路的核心：

- `repositories`：取原始数据
- `services`：做业务动作和模块组合

边界原则：

- repository 不做业务判断
- service 不直接写 SQL

---

## 2. `src/repositories`

当前主要文件：

- `aba_hot_search_term.py`
- `ads_report.py`

### 2.1 `AbaHotSearchTermRepository`

#### 用途

访问 ABA 热门搜索词周报表：

- `aba_brand_search_words_weeks`

#### 主要方法

##### `get_top_asin_search_term(...)`

用途：

- 查询指定 ASIN 在目标报告周期中进入前三商品的搜索词

输入：

- `asin`
- `report_date`
- `report_granularity`

当前支持：

- `week`

当前语义：

- 外部传自然日期
- 先根据报告粒度规则解析“最近已产出报告周期”
- 再查该周期对应的周表数据

返回字段重点包括：

- `search_term`
- `search_rank`
- `click_share`
- `conversion_share`
- `top_product_1_asin / 2 / 3`
- `top_product_1_click_share / 2 / 3`
- `top_product_1_conversion_share / 2 / 3`

##### `get_search_term_history(...)`

用途：

- 获取单个搜索词最近若干周的历史数据

输入：

- `search_term`
- `weeks`

返回字段重点包括：

- `report_date`
- `search_rank`
- `click_share`
- `conversion_share`
- 各周前三商品及其份额字段

#### 当前限制

- 当前仓库底层只接了周表
- `day/month/quarter` 粒度接口已统一，但会抛 `NotImplementedError`

---

### 2.2 `AdsReportRepository`

#### 用途

访问广告报表原始数据。

#### 主要方法

##### `get_user_search_terms_by_asin(...)`

用途：

- 查询指定 ASIN 在指定时间范围内的用户搜索词流量来源

返回字段：

- `search_term`
- `campaign_ad_group`
- `impressions`
- `clicks`
- `ctr`
- `spend`
- `cpc`
- `sales`
- `acos`
- `roas`
- `orders`
- `cvr`
- `cpa`
- `units_sold`
- `term_type`

##### `get_target_data(...)`

用途：

- 查询指定搜索词/商品 ASIN 的历史趋势数据
- 需要传入当前 ASIN，按 G+ 口径限定商品对应的 ENABLED 广告结构
- 当同一搜索词命中多个广告活动/广告组时，趋势自动使用汇总列表排序最高的那条广告结构

返回字段：

- `report_date`
- 与 `get_user_search_terms_by_asin(...)` 相同的搜索词维度字段

##### `get_asin_ads_data(...)`

用途：

- 查询 ASIN 维度广告活动汇总数据

返回字段：

- `enabled`
- `campaign_id`
- `campaign_name`
- `ad_type`
- `budget`
- `impressions`
- `clicks`
- `ctr`
- `spend`
- `cpc`
- `vcpm`
- `sales`
- `acos`
- `roas`
- `orders`
- `cvr`
- `cpa`
- `units_sold`

##### `get_campaign_data(...)`

用途：

- 查询 campaign 级别的历史趋势数据

返回字段：

- `report_date`
- 与 `get_asin_ads_data(...)` 相同的广告活动维度字段

#### 注意事项

- 这些方法当前更多是接口约定和占位，SQL 是否补齐要看具体文件实现状态
- 对业务层来说，不应直接依赖 repository 的原始字段做复杂业务判断，优先通过 service 封装

---

## 3. `src/services`

当前主要文件：

- `aba_service.py`
- `ads_report_service.py`
- `keyword_expansion_service.py`

### 3.1 `AbaService`

#### 用途

围绕 ABA 数据做业务级封装。

#### 主要能力

##### `find_seed_terms_by_asin(...)`

用途：

- 从 ABA 周报中反查某个 ASIN 上榜过的搜索词

##### `get_search_term_history(...)`

用途：

- 获取搜索词历史周数据，供后续加权计算使用

##### `build_keyword_candidate(...)`

用途：

- 将搜索词历史数据组装成 `KeywordCandidate`

当前会补齐：

- `search_rank`
- `click_share`
- `conversion_share`
- `efficiency`

##### `find_high_conversion_asins(...)`

用途：

- 在“词 -> ASIN -> 词”链路中，找该搜索词对应的数据好的商品

当前规则：

- 商品至少出现 2 周
- 加权出单效率 >= 0.80

##### `reverse_lookup_terms_by_asin(...)`

用途：

- 当前直接复用 `find_seed_terms_by_asin(...)`
- 作为 ASIN -> 词 的统一入口

#### 注意事项

- 当前 `find_high_conversion_asins(...)` 还没有按 `report_date/report_granularity` 截断历史窗口
- 当前是“最近 N 周”的历史聚合逻辑

---

### 3.2 `AdsReportService`

#### 用途

围绕广告报表做业务级整理和高价值入口筛选。

#### 主要能力

##### `get_user_search_term_rows(...)`

用途：

- 从报表仓库取某个商品的用户搜索词流量来源

##### `split_user_search_terms(...)`

用途：

- 将报表行拆成：
  - 关键词流量
  - 商品流量（ASIN）

##### `select_high_value_terms_by_strategy(...)`

用途：

- 根据拓词强度筛选高价值词入口

当前规则：

- 优先策略：有订单
- 尝试策略：无订单但有点击

是否纳入尝试策略由 `include_attempt_terms` 控制。

##### `select_high_value_product_asins_by_strategy(...)`

用途：

- 根据拓词强度筛选高价值商品入口

规则与高价值词一致。

#### 注意事项

- 当前这里不再做最终排名截断
- 排名截断已经移到候选词汇总、去重、相关性过滤之后

---

### 3.3 `KeywordExpansionService`

#### 用途

承接拓词主链路中的候选词扩展、去重、过滤与截断。

#### 主要能力

##### `collect_seed_terms(...)`

用途：

- 合并人工种子词和其它来源词
- 做大小写无关去重

##### `expand_from_terms(...)`

用途：

- 执行 `词 -> ASIN -> 词` 链路

##### `expand_from_asins(...)`

用途：

- 执行 `ASIN -> 词` 链路

##### `merge_expanded_candidates(...)`

用途：

- 合并双链路候选词

##### `deduplicate_candidates(...)`

用途：

- 合并同名候选词
- 汇总 `related_asins`
- 保留更优的 `search_rank`

##### `filter_relevant_candidates(...)`

用途：

- 当前做启发式相关性过滤
- 后续可替换为 AI 判断

##### `apply_rank_cutoff(...)`

用途：

- 在候选词汇总、去重、相关性过滤之后
- 按拓词强度配置的最大搜索排名做截断

#### 注意事项

- 这里的 `apply_rank_cutoff(...)` 是最终候选词池截断，不是报表入口筛选
- 相关性过滤后再截断，是当前实现约定

---

## 4. 推荐调用关系

### 4.1 正常业务链路

推荐顺序：

1. `repositories` 取原始数据
2. `services` 组合和筛选
3. `strategy_engine` 决策
4. `workflows` 编排整条链路

### 4.2 不推荐做法

- workflow 直接写 SQL
- service 直接访问数据库连接池而不走 repository
- repository 直接写业务规则

---

## 5. 当前拓词主流程中各层分工

### repositories

- 读 ABA 周报
- 读广告报表

### services

- 反查种子词
- 筛高价值入口
- 词/ASIN 双链路扩词
- 候选词去重、相关性过滤、最终截断

### workflows

- 串起“查询入口 -> 双链路扩词 -> 候选词截断 -> 策略生成”

---

## 6. 使用建议

- 如果你需要“原始表数据”，优先找 repository
- 如果你需要“业务上能直接用的结果”，优先找 service
- 如果你不确定该调哪个，先看是否已经存在 `service` 封装，能用就不要直接下沉到 repository
