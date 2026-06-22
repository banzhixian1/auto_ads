from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

from src.constants.expansion import ExpansionIntensity
from src.prompts.relevance import (
    product_features as DEFAULT_PRODUCT_FEATURES,
    product_title as DEFAULT_PRODUCT_TITLE,
)
from src.repositories.aba_hot_search_term import AbaHotSearchTermRepository
from src.repositories.ads_report import AdsReportRepository
from src.schemas.workflow import SearchTermExpansionRequest, SearchTermExpansionResult
from src.services.aba_service import AbaService
from src.services.ads_report_service import AdsReportService
from src.services.keyword_expansion_service import KeywordExpansionService
from src.utils.report_period import (
    ReportGranularity,
    resolve_latest_published_report_anchor_date,
)
from src.workflows.search_term_expansion import run_search_term_expansion


DEFAULT_ASIN = "B0BJP6C918"
DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_OUTPUT_ROOT = Path("debug_search_term_expansion_outputs")
DEFAULT_TARGET_ACOS = 0.30


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class RecordingAdsReportService(AdsReportService):
    def __init__(self, repo: AdsReportRepository):
        super().__init__(repo=repo)
        self.user_search_term_rows: list[dict] = []
        self.placement_rows: list[dict] = []

    def get_user_search_term_rows(
        self,
        asin: str,
        start_date,
        end_date,
    ) -> list[dict]:
        rows = super().get_user_search_term_rows(
            asin=asin,
            start_date=start_date,
            end_date=end_date,
        )
        self.user_search_term_rows = rows
        return rows

    def get_placement_data(
        self,
        asin: str,
        start_date,
        end_date,
    ) -> list[dict]:
        rows = super().get_placement_data(
            asin=asin,
            start_date=start_date,
            end_date=end_date,
        )
        self.placement_rows = rows
        return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the search-term expansion workflow.")
    parser.add_argument("--asin", default=DEFAULT_ASIN)
    parser.add_argument(
        "--report-date",
        default=None,
        help="自然日期。周报查询会自动使用该日期之前的最近完整周。",
    )
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--seed-search-terms", default="")
    parser.add_argument("--competitor-asins", default="")
    parser.add_argument(
        "--no-self-asin-fallback",
        action="store_true",
        help="广告报表没有商品流量入口时，不把当前 ASIN 作为 ASIN->词兜底种子。",
    )
    parser.add_argument("--product-title", default=DEFAULT_PRODUCT_TITLE)
    parser.add_argument(
        "--product-features",
        default="|".join(DEFAULT_PRODUCT_FEATURES),
        help="用 | 分隔多个商品特征。",
    )
    parser.add_argument("--average-order-price", type=float, default=None)
    parser.add_argument("--target-acos", type=float, default=DEFAULT_TARGET_ACOS)
    parser.add_argument(
        "--expansion-intensity",
        default=ExpansionIntensity.BALANCED.value,
        choices=[item.value for item in ExpansionIntensity],
    )
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--preview-limit", type=int, default=10)
    return parser.parse_args()


def normalize_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def parse_list(value: str) -> list[str]:
    if not value:
        return []
    separator = "|" if "|" in value else ","
    return [item.strip() for item in value.split(separator) if item.strip()]


def find_latest_aba_report_date_for_asin(
    repo: AbaHotSearchTermRepository,
    asin: str,
) -> date | None:
    rows = repo.pool.query(
        """
        SELECT MAX(report_date) AS report_date
        FROM aba_brand_search_words_weeks
        WHERE :asin IN (top_product_1_asin, top_product_2_asin, top_product_3_asin)
        """,
        params={"asin": asin},
    )
    if not rows:
        return None
    value = rows[0].get("report_date")
    return normalize_date(value) if value else None


def resolve_dates(
    args: argparse.Namespace,
    aba_repo: AbaHotSearchTermRepository,
) -> tuple[str, str, str, str, str | None]:
    asin = args.asin.strip().upper()
    latest_aba_report_date = find_latest_aba_report_date_for_asin(aba_repo, asin)

    if args.report_date:
        workflow_report_date = normalize_date(args.report_date)
    elif latest_aba_report_date:
        workflow_report_date = latest_aba_report_date + timedelta(days=7)
    else:
        workflow_report_date = date.today()

    aba_anchor_date = resolve_latest_published_report_anchor_date(
        report_date=workflow_report_date,
        report_granularity=ReportGranularity.WEEK,
    )
    end_date = normalize_date(args.end_date) if args.end_date else aba_anchor_date
    start_date = (
        normalize_date(args.start_date)
        if args.start_date
        else end_date - timedelta(days=max(args.lookback_days, 1) - 1)
    )
    if start_date > end_date:
        raise ValueError(f"start-date 不能晚于 end-date: {start_date} > {end_date}")

    return (
        workflow_report_date.isoformat(),
        aba_anchor_date.isoformat(),
        start_date.isoformat(),
        end_date.isoformat(),
        latest_aba_report_date.isoformat() if latest_aba_report_date else None,
    )


def build_output_dir(args: argparse.Namespace, start_date: str, end_date: str) -> Path:
    if args.output_dir:
        return Path(args.output_dir)
    safe_asin = args.asin.strip().upper() or "unknown_asin"
    return DEFAULT_OUTPUT_ROOT / f"{safe_asin}_{start_date}_{end_date}"


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(to_jsonable(value), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def build_summary(
    request: SearchTermExpansionRequest,
    result: SearchTermExpansionResult,
    ads_service: RecordingAdsReportService,
    latest_aba_report_date: str | None,
    aba_anchor_date: str,
) -> dict[str, Any]:
    launched_decisions = [
        decision for decision in result.decisions if decision.should_launch
    ]
    return {
        "asin": request.product_asin,
        "report_date": request.report_date,
        "resolved_aba_anchor_date": aba_anchor_date,
        "latest_available_aba_report_date_for_asin": latest_aba_report_date,
        "ads_start_date": request.start_date,
        "ads_end_date": request.end_date,
        "ads_user_search_term_rows": len(ads_service.user_search_term_rows),
        "ads_placement_rows": len(ads_service.placement_rows),
        "seed_terms": len(result.seeds),
        "product_seed_asins": result.product_seed_asins,
        "high_value_terms": result.high_value_terms,
        "high_value_asins": result.high_value_asins,
        "candidates": len(result.candidates),
        "decisions": len(result.decisions),
        "launchable_decisions": len(launched_decisions),
        "skipped_terms": len(result.skipped_terms),
        "execution_summary": result.execution_summary,
    }


def save_outputs(
    output_dir: Path,
    request: SearchTermExpansionRequest,
    result: SearchTermExpansionResult,
    summary: dict[str, Any],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "request": output_dir / "request.json",
        "summary": output_dir / "summary.json",
        "result": output_dir / "result.json",
        "candidates": output_dir / "candidates.json",
        "decisions": output_dir / "decisions.json",
        "skipped_terms": output_dir / "skipped_terms.json",
    }
    write_json(paths["request"], request)
    write_json(paths["summary"], summary)
    write_json(paths["result"], result)
    write_json(paths["candidates"], result.candidates)
    write_json(paths["decisions"], result.decisions)
    write_json(paths["skipped_terms"], result.skipped_terms)
    return paths


def print_summary(
    summary: dict[str, Any],
    result: SearchTermExpansionResult,
    paths: dict[str, Path],
    preview_limit: int,
) -> None:
    print("搜索词精准投放拓词流程完成")
    print(f"- ASIN: {summary['asin']}")
    print(f"- workflow report_date: {summary['report_date']}")
    print(f"- ABA 实际周报日期: {summary['resolved_aba_anchor_date']}")
    print(f"- 广告窗口: {summary['ads_start_date']} ~ {summary['ads_end_date']}")
    print(f"- 广告搜索词行: {summary['ads_user_search_term_rows']}")
    print(f"- 广告位历史行: {summary['ads_placement_rows']}")
    print(f"- 高价值词: {len(summary['high_value_terms'])}")
    print(f"- 高价值 ASIN: {len(summary['high_value_asins'])}")
    print(f"- 候选词: {summary['candidates']}")
    print(f"- 投放决策: {summary['decisions']}")

    if result.candidates:
        print("\n候选词预览:")
        for candidate, decision in zip(result.candidates[:preview_limit], result.decisions):
            bid = decision.bid.suggested_bid
            bid_text = "暂无" if bid is None else str(bid)
            print(
                f"  - {candidate.term} | rank={candidate.search_rank} "
                f"| placement={decision.placement.primary} | bid={bid_text}"
            )

    print("\n输出文件:")
    for name, path in paths.items():
        print(f"  - {name}: {path}")


def run() -> tuple[dict[str, Any], SearchTermExpansionResult, dict[str, Path], int]:
    args = parse_args()
    asin = args.asin.strip().upper()
    if not asin:
        raise ValueError("缺少 ASIN。")

    ads_repo = AdsReportRepository()
    aba_repo = AbaHotSearchTermRepository()
    report_date, aba_anchor_date, start_date, end_date, latest_aba_report_date = resolve_dates(
        args=args,
        aba_repo=aba_repo,
    )

    seed_terms = parse_list(args.seed_search_terms)
    competitor_asins = [item.upper() for item in parse_list(args.competitor_asins)]
    if not competitor_asins and not args.no_self_asin_fallback:
        competitor_asins = [asin]

    request = SearchTermExpansionRequest(
        report_date=report_date,
        report_granularity=ReportGranularity.WEEK,
        product_asin=asin,
        start_date=start_date,
        end_date=end_date,
        seed_search_terms=seed_terms,
        competitor_asins=competitor_asins,
        product_title=args.product_title,
        product_features=parse_list(args.product_features),
        expansion_intensity=args.expansion_intensity,
        average_order_price=args.average_order_price,
        target_acos=args.target_acos,
        auto_execute=False,
    )

    ads_service = RecordingAdsReportService(repo=ads_repo)
    result = run_search_term_expansion(
        request=request,
        aba_service=AbaService(repo=aba_repo),
        ads_report_service=ads_service,
        keyword_service=KeywordExpansionService(),
    )
    summary = build_summary(
        request=request,
        result=result,
        ads_service=ads_service,
        latest_aba_report_date=latest_aba_report_date,
        aba_anchor_date=aba_anchor_date,
    )
    paths = save_outputs(
        output_dir=build_output_dir(args, start_date=start_date, end_date=end_date),
        request=request,
        result=result,
        summary=summary,
    )
    return summary, result, paths, args.preview_limit


def main() -> None:
    summary, result, paths, preview_limit = run()
    print_summary(
        summary=summary,
        result=result,
        paths=paths,
        preview_limit=preview_limit,
    )


if __name__ == "__main__":
    main()