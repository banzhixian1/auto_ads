import json

from src.repositories.ads_report import (
    get_clicks_by_campaign_and_time,
    get_odrers_by_campaign_and_time,
)


rows = [
    {"campaign_id": "1002645191741", "date": "2024-09-26", "time": 19},
    {"campaign_id": "57944504171953", "date": "2024-09-26", "time": 20},
]

clicks_result = get_clicks_by_campaign_and_time(rows)
orders_result = get_odrers_by_campaign_and_time(rows)

print("clicks_result:")
print(json.dumps(clicks_result, ensure_ascii=False, indent=2))

print("orders_result:")
print(json.dumps(orders_result, ensure_ascii=False, indent=2))
