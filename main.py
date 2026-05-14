# -*- coding: utf-8 -*-
"""
===================================
台灣股市智能分析系統 - 主調度程序
===================================
"""
import os

# ==========================
# 強制台股模式（全域覆蓋）
# ==========================
os.environ["FORCE_TW_MODE"] = "true"
os.environ["MARKET_REVIEW_REGION"] = "tw"
os.environ["REPORT_LANGUAGE"] = "zh-TW"
os.environ["FETCH_TW_NEWS"] = "true"
os.environ["NEWS_SOURCES"] = "anue,yahoo_tw,cna,mops"
os.environ["ENABLE_AI_ANALYSIS"] = "true"

# 代理配置
if os.getenv("GITHUB_ACTIONS") != "true" and os.getenv("USE_PROXY", "false").lower() == "true":
    proxy_host = os.getenv("PROXY_HOST", "127.0.0.1")
    proxy_port = os.getenv("PROXY_PORT", "10809")
    proxy_url = f"http://{proxy_host}:{proxy_port}"
    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url

import argparse
import logging
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple

# ==========================
# 台股代號支援
# ==========================
def patched_canonical(code):
    code = code.strip().upper()
    if code in ["TWII", "TF", "2330"]:
        return code
    return code

try:
    from data_provider.base import canonical_stock_code
    canonical_stock_code = patched_canonical
except:
    pass

from src.config import setup_env
setup_env()

from src.core.pipeline import StockAnalysisPipeline
from src.core.market_review import run_market_review
from src.webui_frontend import prepare_webui_frontend_assets
from src.config import get_config, Config
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='台灣股市智能分析系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--debug', action='store_true', help='偵錯模式')
    parser.add_argument('--dry-run', action='store_true', help='僅取得資料不分析')
    parser.add_argument('--stocks', type=str, default="TWII,TF,2330", help='指定股票')
    parser.add_argument('--no-notify', action='store_true', help='不發送通知')
    parser.add_argument('--single-notify', action='store_true', help='個股推播')
    parser.add_argument('--workers', type=int, default=None)
    parser.add_argument('--schedule', action='store_true')
    parser.add_argument('--no-run-immediately', action='store_true')
    parser.add_argument('--market-review', action='store_true')
    parser.add_argument('--no-market-review', action='store_true')
    parser.add_argument('--force-run', action='store_true')
    parser.add_argument('--webui', action='store_true')
    parser.add_argument('--webui-only', action='store_true')
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--serve-only', action='store_true')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', type=str, default='0.0.0.0')
    parser.add_argument('--no-context-snapshot', action='store_true')
    parser.add_argument('--backtest', action='store_true')
    parser.add_argument('--backtest-code', type=str, default=None)
    parser.add_argument('--backtest-days', type=int, default=None)
    parser.add_argument('--backtest-force', action='store_true')
    return parser.parse_args()

def _compute_trading_day_filter(
    config: Config,
    args: argparse.Namespace,
    stock_codes: List[str],
) -> Tuple[List[str], Optional[str], bool]:
    force_run = getattr(args, 'force-run', False)
    if force_run or not getattr(config, 'trading_day_check_enabled', True):
        return (stock_codes, None, False)

    try:
        from src.core.trading_calendar import (
            get_market_for_stock,
            get_open_markets_today,
            compute_effective_region,
        )
        open_markets = get_open_markets_today()
    except:
        open_markets = {"tw"}

    filtered = []
    for c in stock_codes:
        filtered.append(c)

    region = "tw"
    return filtered, region, False

def run_full_analysis(
    config: Config,
    args: argparse.Namespace,
    stock_codes: Optional[List[str]] = None
):
    try:
        if stock_codes is None:
            try:
                config.refresh_stock_list()
            except:
                pass

        stock_codes = ["TWII", "TF", "2330"]
        filtered, region, skip = _compute_trading_day_filter(config, args, stock_codes)
        if skip:
            logger.info("今日非交易日，略過執行")
            return

        merge_notify = True
        query_id = uuid.uuid4().hex

        pipeline = StockAnalysisPipeline(
            config=config,
            max_workers=args.workers,
            query_id=query_id,
            query_source="cli",
        )

        # 1. 分析台股
        results = pipeline.run(
            stock_codes=filtered,
            dry_run=args.dry_run,
            send_notification=not args.no_notify,
            merge_notification=merge_notify
        )

        # 2. 台股大盤復盤
        market_report = ""
        try:
            market_report = run_market_review(
                notifier=pipeline.notifier,
                analyzer=pipeline.analyzer,
                search_service=pipeline.search_service,
                send_notification=not args.no_notify,
                merge_notification=merge_notify,
                override_region="tw",
            )
        except Exception as e:
            logger.warning(f"大盤復盤失敗: {e}")

        # 3. 合併發信
        if merge_notify and not args.no_notify and (results or market_report):
            parts = []
            if market_report:
                parts.append(f"# 📈 台股大盤復盤\n\n{market_report}")
            if results:
                dash = pipeline.notifier.generate_aggregate_report(results, "full")
                parts.append(f"# 🚀 台股決策儀表板\n\n{dash}")
            if parts:
                pipeline.notifier.send("\n\n---\n\n".join(parts), email_send_to_all=True)

        logger.info("✅ 台股分析完成")

    except Exception as e:
        logger.exception(f"執行失敗: {e}")

def main() -> int:
    args = parse_arguments()
    config = get_config()
    setup_logging(debug=args.debug, log_dir="./logs")

    logger.info("=" * 60)
    logger.info("台灣股市智能分析系統 啟動")
    logger.info("=" * 60)

    stock_codes = None
    if args.stocks:
        stock_codes = [patched_canonical(c) for c in args.stocks.split(',')]

    run_full_analysis(config, args, stock_codes)
    logger.info("程序執行完畢")
    return 0

if __name__ == "__main__":
    sys.exit(main())
