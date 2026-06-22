import argparse
import csv
import json
from datetime import date, datetime
from decimal import Decimal
from html import escape
from pathlib import Path

from src.repositories.ads_report import AdsReportRepository, TimeGranularity


DEFAULT_ASIN = "B0BJP6C918"
DEFAULT_START_DATE = "2026-05-20"
DEFAULT_END_DATE = "2026-05-25"
DEFAULT_SEARCH_TYPE = "keyword"
DEFAULT_SEARCH_VALUE = "stroller hooks"
DEFAULT_CAMPAIGN_ID = None
DEFAULT_GRANULARITY = TimeGranularity.DAY
DEFAULT_LIMIT = 120
DEFAULT_OUTPUT_ROOT = Path("debug_ads_report_outputs")

CURRENCY_COLUMNS = {"budget", "spend", "cpc", "vcpm", "sales", "cpa"}
PERCENT_COLUMNS = {"ctr", "acos", "cvr"}
INTEGER_COLUMNS = {"impressions", "clicks", "orders", "units_sold"}

COLUMN_LABELS = {
    "report_date": "日期",
    "enabled": "有效",
    "search_term": "用户搜索词",
    "campaign_ad_group": "所属广告活动/组",
    "campaign_id": "广告活动ID",
    "campaign_name": "广告活动",
    "ad_type": "广告类型",
    "budget": "预算",
    "impressions": "曝光量",
    "clicks": "点击量",
    "ctr": "CTR",
    "spend": "广告花费",
    "cpc": "CPC",
    "vcpm": "VCPM",
    "sales": "广告总销售额",
    "acos": "ACOS",
    "roas": "ROAS",
    "orders": "广告总订单量",
    "cvr": "CVR",
    "cpa": "CPA",
    "units_sold": "广告总销量",
    "term_type": "搜索词类型",
}

DATASET_TITLES = {
    "get_user_search_terms_by_asin": "搜索词汇总",
    "get_target_data": "搜索词趋势",
    "get_asin_ads_data": "广告活动汇总",
    "get_campaign_data": "广告活动趋势",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export ads report data for manual G+ reconciliation.")
    parser.add_argument("--asin", default=DEFAULT_ASIN)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--search-type", default=DEFAULT_SEARCH_TYPE, choices=["keyword", "product"])
    parser.add_argument("--search-value", default=DEFAULT_SEARCH_VALUE)
    parser.add_argument("--campaign-id", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument(
        "--granularity",
        default=DEFAULT_GRANULARITY.value,
        choices=[item.value for item in TimeGranularity],
    )
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


def serialize_value(value):
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def serialize_rows(rows: list[dict]) -> list[dict]:
    return [
        {column: serialize_value(value) for column, value in row.items()}
        for row in rows
    ]


def to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def format_display_value(column: str, value) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if column == "enabled":
        return "是" if str(value) == "1" else "否"

    number = to_decimal(value)
    if number is not None:
        if column in PERCENT_COLUMNS:
            return f"{number * Decimal('100'):.2f}%"
        if column in CURRENCY_COLUMNS:
            return f"${number:,.2f}"
        if column in INTEGER_COLUMNS:
            return f"{int(number):,}"
        if column == "roas":
            return f"{number:,.2f}"

    return str(value)


def column_label(column: str) -> str:
    return COLUMN_LABELS.get(column, column)


def html_table(rows: list[dict], limit: int) -> str:
    if not rows:
        return '<p class="empty">No rows.</p>'

    preview_rows = rows[:limit]
    columns = list(preview_rows[0].keys())
    header = "".join(f"<th>{escape(column_label(column))}</th>" for column in columns)
    body_rows = []
    for row in preview_rows:
        cells = []
        for column in columns:
            raw = row.get(column)
            display = format_display_value(column, raw)
            raw_text = "" if raw is None else str(serialize_value(raw))
            class_name = "num" if to_decimal(raw) is not None and column != "campaign_id" else "text"
            cells.append(
                f'<td class="{class_name}" title="{escape(raw_text)}">{escape(display)}</td>'
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    more = ""
    if len(rows) > limit:
        more = f'<p class="note">Only first {limit:,} rows shown. Total rows: {len(rows):,}.</p>'

    return (
        '<div class="table-wrap">'
        "<table>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
        "</div>"
        f"{more}"
    )


def markdown_table(rows: list[dict], limit: int) -> str:
    if not rows:
        return "_No rows._\n"

    preview_rows = rows[:limit]
    columns = list(preview_rows[0].keys())
    labels = [column_label(column) for column in columns]
    lines = [
        "| " + " | ".join(labels) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in preview_rows:
        values = [
            format_display_value(column, row.get(column)).replace("|", "\\|")
            for column in columns
        ]
        lines.append("| " + " | ".join(values) + " |")

    if len(rows) > limit:
        lines.append("")
        lines.append(f"_Only first {limit} rows shown. Total rows: {len(rows)}._")

    return "\n".join(lines) + "\n"


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(
        json.dumps(serialize_rows(rows), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return

    columns = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in serialize_rows(rows):
            writer.writerow(row)


def write_dataset(output_dir: Path, name: str, rows: list[dict]) -> tuple[Path, Path]:
    csv_path = output_dir / f"{name}.csv"
    json_path = output_dir / f"{name}.json"
    write_csv(csv_path, rows)
    write_json(json_path, rows)
    return csv_path, json_path


def build_output_dir(args: argparse.Namespace) -> Path:
    if args.output_dir:
        return Path(args.output_dir)
    safe_search = args.search_value.replace(" ", "_").replace("/", "_")
    return DEFAULT_OUTPUT_ROOT / f"{args.asin}_{args.start_date}_{args.end_date}_{safe_search}_gplus"


def load_datasets(args: argparse.Namespace) -> tuple[dict[str, list[dict]], dict]:
    repo = AdsReportRepository()

    search_summary = repo.get_user_search_terms_by_asin(
        asin=args.asin,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    campaign_summary = repo.get_asin_ads_data(
        asin=args.asin,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    selected_campaign_id = args.campaign_id
    if selected_campaign_id is None and campaign_summary:
        selected_campaign_id = campaign_summary[0]["campaign_id"]

    search_trend = repo.get_target_data(
        target_type=args.search_type,
        target_value=args.search_value,
        start_date=args.start_date,
        end_date=args.end_date,
        time_granularity=TimeGranularity(args.granularity),
        asin=args.asin,
    )

    campaign_trend = []
    if selected_campaign_id is not None:
        campaign_trend = repo.get_campaign_data(
            campaign_id=str(selected_campaign_id),
            start_date=args.start_date,
            end_date=args.end_date,
            time_granularity=TimeGranularity(args.granularity),
        )

    datasets = {
        "get_user_search_terms_by_asin": search_summary,
        "get_target_data": search_trend,
        "get_asin_ads_data": campaign_summary,
        "get_campaign_data": campaign_trend,
    }
    params = {
        "asin": args.asin,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "search_type": args.search_type,
        "search_value": args.search_value,
        "campaign_id_for_trend": serialize_value(selected_campaign_id),
        "granularity": args.granularity,
        "preview_limit": args.limit,
    }
    return datasets, params


def render_html_report(
    datasets: dict[str, list[dict]],
    params: dict,
    paths: dict[str, tuple[Path, Path]],
    output_dir: Path,
) -> str:
    cards = "".join(
        f"""
        <section class="card">
          <div class="card-label">{escape(DATASET_TITLES[name])}</div>
          <div class="card-value">{len(rows):,}</div>
          <div class="card-sub">rows</div>
        </section>
        """
        for name, rows in datasets.items()
    )
    params_html = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
        for key, value in params.items()
    )
    sections = []
    for name, rows in datasets.items():
        csv_path, json_path = paths[name]
        sections.append(
            f"""
            <section class="dataset" id="{escape(name)}">
              <div class="section-title">
                <div>
                  <h2>{escape(DATASET_TITLES[name])}</h2>
                  <p>{len(rows):,} rows. Showing first {min(len(rows), params["preview_limit"]):,} rows.</p>
                </div>
                <div class="links">
                  <a href="{escape(csv_path.name)}">CSV</a>
                  <a href="{escape(json_path.name)}">JSON</a>
                </div>
              </div>
              {html_table(rows, params["preview_limit"])}
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ads Report Reconciliation</title>
  <style>
    :root {{
      --ink: #132033;
      --muted: #64748b;
      --line: #dbe3ef;
      --soft: #f6f8fb;
      --accent: #0f62fe;
      --accent-soft: #e8f0ff;
      --panel: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 0%, #eaf2ff 0, transparent 28rem),
        linear-gradient(180deg, #f8fafc 0%, #eef3f8 100%);
      font-family: "Microsoft YaHei", "Noto Sans SC", "PingFang SC", sans-serif;
    }}
    header {{
      padding: 32px 40px 20px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.72);
      backdrop-filter: blur(10px);
      position: sticky;
      top: 0;
      z-index: 10;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .subtitle {{ margin: 0; color: var(--muted); }}
    main {{ padding: 24px 40px 48px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 16px;
      margin-bottom: 20px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(15, 35, 66, 0.06);
    }}
    .card-label {{ color: var(--muted); font-size: 13px; }}
    .card-value {{ margin-top: 8px; font-size: 30px; font-weight: 800; }}
    .card-sub {{ color: var(--muted); font-size: 12px; }}
    .params, .dataset {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      margin-bottom: 22px;
      box-shadow: 0 10px 30px rgba(15, 35, 66, 0.05);
      overflow: hidden;
    }}
    .params h2, .dataset h2 {{ margin: 0; font-size: 20px; }}
    .params {{ padding: 20px; }}
    .params table {{ width: 100%; border-collapse: collapse; }}
    .params th, .params td {{ padding: 8px 10px; border-bottom: 1px solid var(--line); text-align: left; }}
    .params th {{ width: 220px; color: var(--muted); }}
    .section-title {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      padding: 20px;
      border-bottom: 1px solid var(--line);
      background: linear-gradient(90deg, #ffffff, #f7faff);
    }}
    .section-title p {{ margin: 6px 0 0; color: var(--muted); }}
    .links {{ display: flex; gap: 10px; }}
    .links a {{
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }}
    .table-wrap {{ max-height: 680px; overflow: auto; }}
    table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-size: 13px; }}
    th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #f1f5f9;
      border-bottom: 1px solid var(--line);
      color: #1e293b;
      text-align: left;
      padding: 11px 12px;
      white-space: nowrap;
    }}
    td {{
      border-bottom: 1px solid #e8edf4;
      padding: 10px 12px;
      vertical-align: top;
      max-width: 460px;
    }}
    tbody tr:nth-child(even) {{ background: #f8fbff; }}
    tbody tr:hover {{ background: #edf4ff; }}
    td.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
    td.text {{ text-align: left; }}
    .note, .empty {{ padding: 12px 20px 18px; color: var(--muted); }}
    code {{ background: #eef2f7; padding: 2px 5px; border-radius: 6px; }}
    @media (max-width: 900px) {{
      header, main {{ padding-left: 18px; padding-right: 18px; }}
      .cards {{ grid-template-columns: 1fr 1fr; }}
      .section-title {{ align-items: flex-start; flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Ads Report Reconciliation</h1>
    <p class="subtitle">Readable report for manual comparison with G+ frontend. Raw CSV/JSON are in <code>{escape(str(output_dir))}</code>.</p>
  </header>
  <main>
    <div class="cards">{cards}</div>
    <section class="params">
      <h2>Parameters</h2>
      <table>{params_html}</table>
    </section>
    {"".join(sections)}
  </main>
</body>
</html>
"""


def render_markdown_report(
    datasets: dict[str, list[dict]],
    params: dict,
    paths: dict[str, tuple[Path, Path]],
) -> str:
    lines = [
        "# Ads Report Reconciliation",
        "",
        "## Parameters",
        "",
        *[f"- {key}: `{value}`" for key, value in params.items()],
        "",
    ]
    for name, rows in datasets.items():
        csv_path, json_path = paths[name]
        lines.extend(
            [
                f"## {DATASET_TITLES[name]}",
                "",
                f"- Rows: {len(rows)}",
                f"- CSV: `{csv_path.as_posix()}`",
                f"- JSON: `{json_path.as_posix()}`",
                "",
                markdown_table(rows, params["preview_limit"]),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    output_dir = build_output_dir(args)
    output_dir.mkdir(parents=True, exist_ok=True)

    datasets, params = load_datasets(args)
    paths = {
        name: write_dataset(output_dir, name, rows)
        for name, rows in datasets.items()
    }

    parameters_path = output_dir / "parameters.json"
    parameters_path.write_text(
        json.dumps(params, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    html_path = output_dir / "report.html"
    markdown_path = output_dir / "summary.md"
    legacy_markdown_path = Path("debug_ads_report_result.md")

    html_path.write_text(render_html_report(datasets, params, paths, output_dir), encoding="utf-8")
    markdown_report = render_markdown_report(datasets, params, paths)
    markdown_path.write_text(markdown_report, encoding="utf-8")
    legacy_markdown_path.write_text(markdown_report, encoding="utf-8")

    print(f"Wrote {html_path}")
    print(f"Wrote {markdown_path}")
    print(f"Wrote {legacy_markdown_path}")
    print(f"Wrote {parameters_path}")
    for name, rows in datasets.items():
        csv_path, json_path = paths[name]
        print(f"{name}: rows={len(rows)}, csv={csv_path}, json={json_path}")


if __name__ == "__main__":
    main()
