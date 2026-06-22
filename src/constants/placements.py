# 广告位常量，统一避免业务代码里散落字符串
TOP_OF_SEARCH = "top_of_search"
REST_OF_SEARCH = "rest_of_search"
PRODUCT_PAGES = "product_pages"


def normalize_placement(value) -> str:
    """Normalize raw placement labels into the three strategy placements."""
    raw = str(value or "").strip().lower()
    if not raw:
        return ""

    normalized = raw.replace("-", "_")
    token = "_".join(normalized.replace("/", " ").split())
    words = token.replace("_", " ")

    if token in {TOP_OF_SEARCH, "top"} or ("top" in words and "search" in words):
        return TOP_OF_SEARCH
    if (
        token in {PRODUCT_PAGES, "product_page", "page", "detail"}
        or "product page" in words
        or "detail" in words
    ):
        return PRODUCT_PAGES
    if token in {REST_OF_SEARCH, "other"} or (
        ("rest" in words or "other" in words) and "search" in words
    ):
        return REST_OF_SEARCH

    # The strategy layer only reasons over top/rest/product-page placements.
    # Unknown non-top/non-product placements are safest as rest-of-search traffic.
    return REST_OF_SEARCH


# 面向中文展示时使用的标签
PLACEMENT_LABELS = {
    TOP_OF_SEARCH: "搜索结果顶部",
    REST_OF_SEARCH: "搜索结果其余位置",
    PRODUCT_PAGES: "商品详情页",
}
