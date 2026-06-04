# utils 使用说明

## 1. 适用范围

`src/utils` 放基础设施和通用工具，不直接承接 Amazon 广告业务流程。

当前主要包括：

- `db_conn_pool.py`
- `report_period.py`
- `configer.py`
- `logger.py`
- `requests_client.py`
- `utils.py`

---

## 2. `db_conn_pool.py`

### 2.1 用途

统一管理数据库连接池、SQLAlchemy Session 创建和多连接配置读取。

### 2.2 主要入口

- `SQLAlchemyPool`
- `create_mysql_pool(...)`
- `create_pg_pool(...)`

### 2.3 配置方式

配置文件位于：

- `configs/db_conn_pool.ini`

支持多连接配置节，命名方式为：

- `mysql_<conn_name>`
- `pg_<conn_name>`

例如：

- `mysql_default`
- `mysql_erp`
- `pg_default`
- `pg_aba`

调用示例：

```python
from src.utils.db_conn_pool import create_pg_pool

pool = create_pg_pool(database="am_aba_search_term", conn_name="aba")
```

### 2.4 `SQLAlchemyPool` 使用方式

#### 查询

```python
rows = pool.query(
    sql="SELECT * FROM some_table WHERE id = :id",
    params={"id": 1},
)
```

默认行为：

- `fetchall=True`
- `return_dict=True`

因此默认返回：

- `list[dict]`

如果只取一条：

```python
row = pool.query(
    sql="SELECT * FROM some_table WHERE id = :id",
    params={"id": 1},
    fetchall=False,
)
```

#### 执行写操作

```python
affected = pool.execute(
    sql="UPDATE some_table SET name = :name WHERE id = :id",
    params={"id": 1, "name": "new"},
)
```

返回值：

- 受影响行数 `rowcount`

### 2.5 session 约定

#### 不传 `session`

由 `SQLAlchemyPool` 自己：

- 创建 session
- 执行 SQL
- `commit/rollback`
- `close`

适合：

- 单次独立查询
- 单次独立写操作

#### 传入 `session`

由外部自己管理事务边界，`SQLAlchemyPool` 只负责执行 SQL。

适合：

- 一个 workflow / service 内多个写操作共享事务
- 多个 repository 组合执行

示例：

```python
session = pool.get_session()
try:
    repo_a.pool.execute(sql_a, params_a, session=session)
    repo_b.pool.execute(sql_b, params_b, session=session)
    session.commit()
except Exception:
    session.rollback()
    raise
finally:
    session.close()
```

### 2.6 注意事项

- `create_mysql_pool` / `create_pg_pool` 的数据库类型由代码决定，不从配置里动态判断
- 配置文件支持多连接，但默认仓库不一定都显式指定非 `default` 连接名
- 连接池是按 `db_url` 缓存的，同一 `db_url` 会复用同一个 `SQLAlchemyPool`

---

## 3. `report_period.py`

### 3.1 用途

统一处理：

- 自然日期输入
- 报告粒度
- 当前报告周期锚点
- 最近已产出报告周期

这是“报表时间语义”工具，不负责查库。

### 3.2 主要对象

- `DateLike`
- `ReportGranularity`
- `normalize_report_date(...)`
- `normalize_report_granularity(...)`
- `resolve_report_anchor_date(...)`
- `get_previous_report_anchor_date(...)`
- `resolve_latest_published_report_anchor_date(...)`

### 3.3 输入约定

`DateLike` 支持：

- `YYYY-MM-DD` 字符串
- `date`
- `datetime`

`ReportGranularity` 当前支持：

- `day`
- `week`
- `month`
- `quarter`

### 3.4 当前周期锚点

```python
from src.utils.report_period import resolve_report_anchor_date, ReportGranularity

anchor = resolve_report_anchor_date("2026-06-04", ReportGranularity.WEEK)
```

当前规则：

- `day` -> 当天
- `week` -> 当前 ISO 周的周六

### 3.5 最近已产出报告周期

```python
from src.utils.report_period import resolve_latest_published_report_anchor_date

latest_week = resolve_latest_published_report_anchor_date("2026-06-04", "week")
```

当前按保守规则处理：

- `day` -> 前一天
- `week` -> 上一个完整周
- `month` -> 上一个完整月
- `quarter` -> 上一个完整季度

### 3.6 注意事项

- 这里处理的是“报告发布时间规则”，不是“数据库缺数兜底”
- 当前 `month` / `quarter` 的上一周期推导已实现
- 但具体仓库是否支持这些粒度，要看对应表和 SQL 是否已接入

---

## 4. `configer.py`

### 4.1 用途

统一管理 `.ini` 配置文件读取和初始化默认值。

### 4.2 主要入口

- `read_config(config_name)`
- `save_config(config, config_name)`
- `init_config_section(config_name, section, defaults, required_fields=None)`

### 4.3 推荐用法

```python
from src.utils.configer import init_config_section, read_config

init_config_section(
    "my_config",
    "service",
    {"host": "127.0.0.1", "port": 8000},
)
config = read_config("my_config")
```

### 4.4 注意事项

- `init_config_section(...)` 会在配置节缺失时自动写入默认值
- `required_fields` 用于声明必须配置项
- 当前项目大量基础设施模块都依赖它初始化默认配置

---

## 5. `logger.py`

### 5.1 用途

统一项目日志器和日志轮转逻辑，并提供 Web 路由日志过滤器。

### 5.2 主要对象

- `logger`
- `RouteFilter`

### 5.3 推荐使用

```python
from src.utils.logger import logger

logger.info("message")
logger.error("error", exc_info=True)
```

### 5.4 `RouteFilter`

主要用于过滤 `werkzeug` 路由日志，避免静态资源或常见状态码刷屏。

适合在 Flask 应用中挂到 `werkzeug` logger。

---

## 6. `requests_client.py`

### 6.1 用途

封装通用 HTTP 请求客户端，统一超时、重试、基础请求行为。

### 6.2 主要对象

- `RequestsClient`
- `RequestsTokenClient`

### 6.3 适用场景

- 基础外部 HTTP 调用
- 带 token 的接口调用
- `apis` 层不想直接裸调 `requests` 时

### 6.4 注意事项

- 这是通用请求层，不应承接具体业务逻辑
- 业务层应在 `apis` 中调用它，而不是直接把复杂逻辑写进这里

---

## 7. `utils.py`

### 7.1 用途

放少量通用辅助函数，目前主要包括两类：

- LLM 输出校验和重试
- 图像基础处理

### 7.2 LLM 相关函数

- `type_check(...)`
- `enum_check(...)`
- `schema_check(...)`
- `generate_with_retry(...)`
- `GenerationRetryError`

适合场景：

- 模型输出必须满足固定类型/枚举/schema
- 失败后希望自动回灌提示并重试

### 7.3 图像相关函数

- `resize_with_aspect_ratio(...)`

适合场景：

- 对模型输入图片做尺寸收敛

### 7.4 注意事项

- `utils.py` 当前包含多种辅助函数，调用时要先确认是否已有更明确的上层入口
- 对业务流程来说，优先通过 `services` / `adapters` / `apis` 调用，而不是直接把业务逻辑写在 `utils.py`
