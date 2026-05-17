"""数据重合度采样验证."""
import logging
from typing import Any, Dict, Optional, Tuple

from .connector import DamengConnector

logger = logging.getLogger(__name__)


def _safe_set(values: Any) -> set:
    """构建 set，跳过不可哈希的类型."""
    s = set()
    for v in values:
        try:
            s.add(v[0] if isinstance(v, (tuple, list)) else v)
        except TypeError:
            logger.debug("跳过不可哈希的类型: %s", type(v))
            continue
    return s


def sample_overlap(
    conn: DamengConnector,
    table_a: str,
    col_a: str,
    table_b: str,
    col_b: str,
    strategy: str = "sample",
    sample_rows: int = 1000,
    sample_pct: Optional[int] = None,
    recent_days: Optional[int] = None,
    time_column: str = "create_time",
) -> float:
    """采样计算两个字段之间的值重合度，返回 0.0 ~ 1.0."""
    col_a_quoted = f'"{col_a}"'
    col_b_quoted = f'"{col_b}"'
    table_a_quoted = f'"{table_a}"'
    table_b_quoted = f'"{table_b}"'

    # sample_pct=60 -> LIMIT 按比例计算
    limit = sample_rows
    if strategy == "sample" and sample_pct is not None:
        try:
            rows = conn.query(
                f"SELECT COUNT(*) FROM {table_b_quoted}"
            )
            total = rows[0][0] if rows else 0
            if total > 0:
                limit = max(int(total * sample_pct / 100), 1)
        except Exception as e:
            logger.warning("获取表 %s 行数失败: %s", table_b, e)
            limit = sample_rows
    elif strategy == "sample":
        limit = sample_rows

    # 构建 WHERE 条件（对 A 和 B 都应用）
    where_clause = ""
    if strategy == "recent" and recent_days is not None:
        where_clause = (
            f" WHERE {time_column} >= SYSDATE - {recent_days}"
        )

    if limit > 0:
        if limit < 5000:
            sql_b = (
                f"SELECT DISTINCT {col_b_quoted} FROM {table_b_quoted}"
                f"{where_clause} ORDER BY DBMS_RANDOM.VALUE LIMIT {limit}"
            )
        else:
            pct = max(0.01, min(100, 100.0 / max(total, 1) * limit))
            sql_b = (
                f"SELECT DISTINCT {col_b_quoted} FROM {table_b_quoted}"
                f" SAMPLE({pct:.1f}){where_clause}"
            )
    else:
        sql_b = (
            f"SELECT DISTINCT {col_b_quoted} FROM {table_b_quoted}"
            f"{where_clause}"
        )

    try:
        # 取 A 表的字段值（也加时间过滤以保证对称）
        sql_a = (
            f"SELECT DISTINCT {col_a_quoted} FROM {table_a_quoted}"
            f" WHERE {col_a_quoted} IS NOT NULL"
            f"{where_clause.replace('WHERE', 'AND') if where_clause else ''}"
            f" LIMIT {min(sample_rows, 5000)}"
        )
        vals_a = _safe_set(conn.query(sql_a))
        if not vals_a:
            return 0.0

        vals_b = _safe_set(conn.query(sql_b))
        if not vals_b:
            return 0.0

        overlap = len(vals_a & vals_b) / len(vals_a)
        return round(overlap, 4)
    except Exception as e:
        logger.warning(
            "重合度计算失败 (%s.%s <-> %s.%s): %s",
            table_a, col_a, table_b, col_b, e
        )
        return 0.0
