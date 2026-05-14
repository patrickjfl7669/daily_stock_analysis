# -*- coding: utf-8 -*-
"""
台灣股市智能分析系統 - 台股專用
"""
import os
import sys
import uuid
import logging
import argparse
from datetime import datetime

# ==========================
# 全域鎖死：台股模式
# ==========================
os.environ["MARKET_REGION"] = "tw"
os.environ["MARKET_REVIEW_REGION"] = "tw"
os.environ["REPORT_LANGUAGE"] = "zh-TW"
os.environ["STOCK_LIST"] = "TWII,TF,2330"
os.environ["FORCE_TW"] = "1"

logger = logging.getLogger(__name__)

# ==========================
# 台股代號強制支援
# ==========================
def tw_stock_code(code):
    code = str(code).upper().strip()
    if code in ["TWII", "TF", "2330"]:
        return code
    return code

# ==========================
# 主流程
# ==========================
def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("==================================")
    logger.info("  台灣股市智能分析系統 (台股專用)")
    logger.info("==================================")

    try:
        from src.config import get_config
        config = get_config()

        # 強制覆蓋 config
        config.stock_list = ["TWII", "TF", "2330"]
        config.market_review_region = "tw"
        config.force_tw_market = True

        # 覆蓋股票解析
        try:
            import data_provider.base
            data_provider.base.canonical_stock_code = tw_stock_code
        except:
            pass

        # 啟動分析
        from src.core.pipeline import StockAnalysisPipeline
        from src.core.market_review import run_market_review

        query_id = uuid.uuid4().hex
        pipeline = StockAnalysisPipeline(config=config, query_id=query_id)

        # 分析台股
        results = pipeline.run(
            stock_codes=["TWII", "TF", "2330"],
            send_notification=True,
            merge_notification=True
        )

        # 強制台股大盤
        try:
            run_market_review(
                notifier=pipeline.notifier,
                analyzer=pipeline.analyzer,
                search_service=pipeline.search_service,
                override_region="tw",
                send_notification=True,
                merge_notification=True
            )
        except Exception as e:
            logger.warning(f"大盤復盤（台股）: {e}")

        logger.info("✅ 台股分析完成！")

    except Exception as e:
        logger.exception(f"執行失敗: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
