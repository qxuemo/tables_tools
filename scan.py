"""TableScope Agent 入口 — 连接达梦 → 扫描 → 分析 → WS 推送 → 写入 JSON → 退出.

用法:
    python scan.py --db prod-main
    python scan.py --db prod-main --strategy full
    python scan.py --db prod-main --strategy sample --sample-rows 500
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time

# 确保 agent 包能导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.config import (
    get_db_data_dir,
    load_connection,
    load_scan_config,
)
from agent.connector import DamengConnector
from agent.scanner import TableScanner
from agent.analyzer import analyze
from agent.ws_server import ProgressServer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("tablescope")


def main() -> None:
    parser = argparse.ArgumentParser(description="TableScope 数据库扫描工具")
    parser.add_argument(
        "--db", required=True, help="数据库连接 ID (对应 connections.json)"
    )
    parser.add_argument(
        "--strategy",
        choices=["sample", "recent", "full"],
        default=None,
        help="采样策略，默认使用 scan_config.json 中的配置",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=None,
        help="采样行数，覆盖配置文件",
    )
    parser.add_argument(
        "--ws-port",
        type=int,
        default=None,
        help="WebSocket 端口，覆盖配置文件",
    )
    args = parser.parse_args()

    # 加载配置
    conn_info = load_connection(args.db)
    if conn_info is None:
        logger.error(f"未找到数据库连接: {args.db}")
        sys.exit(1)

    config = load_scan_config()
    ws_port = args.ws_port or config.get("ws_port", 8765)

    # 启动 WebSocket 服务器
    progress = ProgressServer(ws_port)

    async def run() -> None:
        await progress.start()

        try:
            start_time = time.time()

            # 发送启动消息
            await progress.broadcast({
                "type": "phase",
                "phase": "connecting",
                "message": f"正在连接 {conn_info.get('name', args.db)}...",
            })

            # 连接数据库
            with DamengConnector(conn_info) as conn:
                schema = conn_info.get("schema", "")
                scanner = TableScanner(conn, schema)

                # Phase 1: 扫描表结构
                await progress.broadcast({
                    "type": "phase",
                    "phase": "scanning",
                    "message": "正在扫描表结构...",
                })

                def scan_progress(table_name: str, done: int, total: int) -> None:
                    progress.send_sync({
                        "type": "progress",
                        "phase": "scanning",
                        "current_table": table_name,
                        "tables_done": done,
                        "tables_total": total,
                        "candidates_found": 0,
                    })

                tables = scanner.scan_all(
                    exclude_patterns=config.get("exclude_tables", []),
                    progress_cb=scan_progress,
                )

                logger.info(f"扫描完成: {len(tables)} 张表")

                # 写入 schema.json
                data_dir = get_db_data_dir(args.db)
                schema_data = {
                    "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "strategy": args.strategy or config.get("default_strategy", "sample"),
                    "tables": tables,
                }
                with open(os.path.join(data_dir, "schema.json"), "w", encoding="utf-8") as f:
                    json.dump(schema_data, f, ensure_ascii=False, indent=2)

                # Phase 2: 关联分析
                await progress.broadcast({
                    "type": "phase",
                    "phase": "matching",
                    "message": "正在字段名匹配...",
                })

                def analyze_progress(
                    phase: str, done: int, total: int, found: int
                ) -> None:
                    progress.send_sync({
                        "type": "progress",
                        "phase": phase,
                        "tables_done": done,
                        "tables_total": total,
                        "candidates_found": found,
                    })

                def candidate_found(relation: dict) -> None:
                    progress.send_sync({
                        "type": "candidate",
                        **relation,
                    })

                relations = analyze(
                    conn,
                    args.db,
                    tables,
                    progress_cb=analyze_progress,
                    candidate_cb=candidate_found,
                )

                elapsed = int(time.time() - start_time)

                # 更新连接的最后扫描时间
                from agent.config import DATA_DIR
                conn_path = os.path.join(DATA_DIR, "connections.json")
                if os.path.exists(conn_path):
                    with open(conn_path, "r", encoding="utf-8") as f:
                        connections = json.load(f)
                    for c in connections:
                        if c.get("id") == args.db:
                            c["last_scan"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                    with open(conn_path, "w", encoding="utf-8") as f:
                        json.dump(connections, f, ensure_ascii=False, indent=2)

                await progress.broadcast({
                    "type": "done",
                    "tables_scanned": len(tables),
                    "relations_found": len(relations),
                    "elapsed_seconds": elapsed,
                })

                logger.info(
                    f"分析完成: {len(relations)} 条关联, "
                    f"耗时 {elapsed}s"
                )

        except Exception as e:
            logger.exception("扫描失败")
            await progress.broadcast({
                "type": "error",
                "message": str(e),
            })
            # 等待前端收到错误消息
            await asyncio.sleep(2)
        finally:
            await asyncio.sleep(1)  # 让最后的消息发出去
            await progress.stop()

    asyncio.run(run())


if __name__ == "__main__":
    main()
