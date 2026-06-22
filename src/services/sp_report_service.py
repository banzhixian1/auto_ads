import json
from pathlib import Path
from typing import Any


def sp_rpt_json_to_list(report_path: str) -> list[dict[str, Any]]:
    """
    把亚马逊 Search Query Performance 报告 JSON 转为扁平行列表。

    Args:
        report_path(str): 报告路径

    Returns:
        list[dict]: 每个搜索词一行，包含报告元信息、ASIN、搜索词及曝光/点击/加购/购买指标
    """
    path = Path(report_path)
    with path.open("r", encoding="utf-8") as file:
        report_data = json.load(file)

    report_specification = report_data.get("reportSpecification", {})
    report_options = report_specification.get("reportOptions", {})
    rows: list[dict[str, Any]] = []
    for item in report_data.get("dataByAsin", []):
        search_query_data = item.get("searchQueryData") or {}
        impression_data = item.get("impressionData") or {}
        click_data = item.get("clickData") or {}
        cart_add_data = item.get("cartAddData") or {}
        purchase_data = item.get("purchaseData") or {}

        total_median_click_price = click_data.get("totalMedianClickPrice") or {}
        asin_median_click_price = click_data.get("asinMedianClickPrice") or {}
        total_median_cart_add_price = cart_add_data.get("totalMedianCartAddPrice") or {}
        asin_median_cart_add_price = cart_add_data.get("asinMedianCartAddPrice") or {}
        total_median_purchase_price = purchase_data.get("totalMedianPurchasePrice") or {}
        asin_median_purchase_price = purchase_data.get("asinMedianPurchasePrice") or {}

        row: dict[str, Any] = {
            "report_type": report_specification.get("reportType"),
            "report_period": report_options.get("reportPeriod"),
            "report_start_date": report_specification.get("dataStartTime"),
            "report_end_date": report_specification.get("dataEndTime"),
            "marketplace_ids": report_specification.get("marketplaceIds", []),
            "start_date": item.get("startDate"),
            "end_date": item.get("endDate"),
            "asin": item.get("asin"),
            "search_query": search_query_data.get("searchQuery"),
            "search_query_score": search_query_data.get("searchQueryScore"),
            "search_query_volume": search_query_data.get("searchQueryVolume"),
            "total_query_impression_count": impression_data.get("totalQueryImpressionCount"),
            "asin_impression_count": impression_data.get("asinImpressionCount"),
            "asin_impression_share": impression_data.get("asinImpressionShare"),
            "total_click_count": click_data.get("totalClickCount"),
            "total_click_rate": click_data.get("totalClickRate"),
            "asin_click_count": click_data.get("asinClickCount"),
            "asin_click_share": click_data.get("asinClickShare"),
            "total_median_click_price_amount": total_median_click_price.get("amount"),
            "total_median_click_price_currency_code": total_median_click_price.get("currencyCode"),
            "asin_median_click_price_amount": asin_median_click_price.get("amount"),
            "asin_median_click_price_currency_code": asin_median_click_price.get("currencyCode"),
            "total_same_day_shipping_click_count": click_data.get("totalSameDayShippingClickCount"),
            "total_one_day_shipping_click_count": click_data.get("totalOneDayShippingClickCount"),
            "total_two_day_shipping_click_count": click_data.get("totalTwoDayShippingClickCount"),
            "total_cart_add_count": cart_add_data.get("totalCartAddCount"),
            "total_cart_add_rate": cart_add_data.get("totalCartAddRate"),
            "asin_cart_add_count": cart_add_data.get("asinCartAddCount"),
            "asin_cart_add_share": cart_add_data.get("asinCartAddShare"),
            "total_median_cart_add_price_amount": total_median_cart_add_price.get("amount"),
            "total_median_cart_add_price_currency_code": total_median_cart_add_price.get("currencyCode"),
            "asin_median_cart_add_price_amount": asin_median_cart_add_price.get("amount"),
            "asin_median_cart_add_price_currency_code": asin_median_cart_add_price.get("currencyCode"),
            "total_same_day_shipping_cart_add_count": cart_add_data.get("totalSameDayShippingCartAddCount"),
            "total_one_day_shipping_cart_add_count": cart_add_data.get("totalOneDayShippingCartAddCount"),
            "total_two_day_shipping_cart_add_count": cart_add_data.get("totalTwoDayShippingCartAddCount"),
            "total_purchase_count": purchase_data.get("totalPurchaseCount"),
            "total_purchase_rate": purchase_data.get("totalPurchaseRate"),
            "asin_purchase_count": purchase_data.get("asinPurchaseCount"),
            "asin_purchase_share": purchase_data.get("asinPurchaseShare"),
            "total_median_purchase_price_amount": total_median_purchase_price.get("amount"),
            "total_median_purchase_price_currency_code": total_median_purchase_price.get("currencyCode"),
            "asin_median_purchase_price_amount": asin_median_purchase_price.get("amount"),
            "asin_median_purchase_price_currency_code": asin_median_purchase_price.get("currencyCode"),
            "total_same_day_shipping_purchase_count": purchase_data.get("totalSameDayShippingPurchaseCount"),
            "total_one_day_shipping_purchase_count": purchase_data.get("totalOneDayShippingPurchaseCount"),
            "total_two_day_shipping_purchase_count": purchase_data.get("totalTwoDayShippingPurchaseCount"),
        }
        rows.append(row)

    return rows
