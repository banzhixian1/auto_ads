# 亚马逊搜索词排名数据表结构

## 表名：aba_brand_search_words_weeks

| 字段名 | 类型 | 说明 |
|--------|------|------|
| search_rank | int4 | 搜索排名 |
| search_term | varchar(255) | 搜索词 |
| top_brand_1 | varchar(255) | 排名第1的品牌 |
| top_brand_2 | varchar(255) | 排名第2的品牌 |
| top_brand_3 | varchar(255) | 排名第3的品牌 |
| top_category_1 | varchar(255) | 排名第1的品类 |
| top_category_2 | varchar(255) | 排名第2的品类 |
| top_category_3 | varchar(255) | 排名第3的品类 |
| top_product_1_asin | varchar(255) | 排名第1商品的ASIN码 |
| top_product_1_name | varchar(2048) | 排名第1商品名称 |
| top_product_1_click_share | numeric(10,2) | 排名第1商品点击占比 |
| top_product_1_conversion_share | numeric(10,2) | 排名第1商品转化占比 |
| top_product_1_img_url | varchar(255) | 排名第1商品图片URL |
| top_product_2_asin | varchar(255) | 排名第2商品的ASIN码 |
| top_product_2_name | varchar(2048) | 排名第2商品名称 |
| top_product_2_click_share | numeric(10,2) | 排名第2商品点击占比 |
| top_product_2_conversion_share | numeric(10,2) | 排名第2商品转化占比 |
| top_product_2_img_url | varchar(255) | 排名第2商品图片URL |
| top_product_3_asin | varchar(255) | 排名第3商品的ASIN码 |
| top_product_3_name | varchar(2048) | 排名第3商品名称 |
| top_product_3_click_share | numeric(10,2) | 排名第3商品点击占比 |
| top_product_3_conversion_share | numeric(10,2) | 排名第3商品转化占比 |
| top_product_3_img_url | varchar(255) | 排名第3商品图片URL |
| report_date | date | 报告日期 |
| amazon_keyword_url | varchar(1024) | 亚马逊关键词搜索URL |
| record_date | date | 记录日期 |
| rank_diff1p | float8 | 排名变化（环比差值） |
| click_share | float8 | 点击份额 |
| conversion_share | float8 | 转化份额 |

## 字段说明补充

- **ASIN**: Amazon Standard Identification Number，亚马逊标准识别号
- **click_share / conversion_share**: 前三商品总计的点击/转化份额，与 top_product_X 的商品级份额区分
- **rank_diff1p**: 通常指与上一期相比的排名变化，正数表示上升，负数表示下降