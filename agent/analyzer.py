"""关联分析引擎 — 协调匹配和重合度验证."""
import json
import os
from typing import Any, Callable, Dict, List, Optional

from .config import get_db_data_dir, load_scan_config
from .connector import DamengConnector
from .matcher import match_all
from .overlap import sample_overlap


def analyze(
    conn: DamengConnector,
    db_id: str,
    tables: List[Dict[str, Any]],
    progress_cb: Optional[Callable] = None,
    candidate_cb: Optional[Callable] = None,
) -> List[Dict[str, Any]]:
    config = load_scan_config()
    threshold = config.get("overlap_threshold", 0.5)

    # Phase 1: 字段名匹配
    if progress_cb:
        progress_cb("matching", 0, 0, 0)

    candidates = match_all(tables, progress_cb=None)
    total = len(candidates)

    if progress_cb:
        progress_cb("analyzing", 0, total, 0)

    # Phase 2: 数据重合度验证
    relations: List[Dict[str, Any]] = []
    for i, cand in enumerate(candidates):
        table_a = cand["from_table"]
        col_a = cand["from_column"]
        table_b = cand["to_table"]
        col_b = cand["to_column"]

        # 获取目标表的行数来决定采样策略
        strategy = _pick_strategy(tables, table_b, config)

        overlap = sample_overlap(
            conn, table_a, col_a, table_b, col_b,
            strategy=strategy,
            sample_rows=config.get("sample_rows", 1000),
            recent_days=_recent_days_for_table(tables, table_b, config),
        )

        confidence = (
            "high" if overlap >= 0.8
            else "medium" if overlap >= threshold
            else "low"
        )

        if overlap >= threshold:
            relation = {
                "from_table": table_a,
                "from_column": col_a,
                "to_table": table_b,
                "to_column": col_b,
                "match_type": cand["match_type"],
                "overlap_rate": overlap,
                "confidence": confidence,
            }
            relations.append(relation)

            if candidate_cb:
                candidate_cb(relation)

        if progress_cb:
            progress_cb("analyzing", i + 1, total, len(relations))

    # 写入结果
    data_dir = get_db_data_dir(db_id)
    with open(os.path.join(data_dir, "relations.json"), "w", encoding="utf-8") as f:
        json.dump(relations, f, ensure_ascii=False, indent=2)

    return relations


def _pick_strategy(
    tables: List[Dict[str, Any]],
    table_name: str,
    config: Dict[str, Any],
) -> str:
    """根据配置和表大小选择采样策略."""
    table_info = None
    for t in tables:
        if t["name"] == table_name:
            table_info = t
            break

    if table_info is None:
        return config.get("default_strategy", "sample")

    row_count = table_info.get("row_count", 0)
    rules = sorted(
        config.get("large_table_rules", []),
        key=lambda r: r.get("min_rows", 0),
        reverse=True,
    )

    for rule in rules:
        if row_count >= rule.get("min_rows", 0):
            return rule.get("strategy", config.get("default_strategy", "sample"))

    return config.get("default_strategy", "sample")


def _recent_days_for_table(
    tables: List[Dict[str, Any]],
    table_name: str,
    config: Dict[str, Any],
) -> Optional[int]:
    for t in tables:
        if t["name"] == table_name:
            row_count = t.get("row_count", 0)
            rules = sorted(
                config.get("large_table_rules", []),
                key=lambda r: r.get("min_rows", 0),
                reverse=True,
            )
            for rule in rules:
                if (
                    row_count >= rule.get("min_rows", 0)
                    and rule.get("strategy") == "recent"
                ):
                    return rule.get("recent_days")
    return None
