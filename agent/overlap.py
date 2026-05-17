"""数据重合度采样验证."""
from typing import Any, Dict, Optional, Tuple

from .connector import DamengConnector


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

    # sample_pct=60 → LIMIT 按比例计算，需要先知道行数
    limit = sample_rows
    if strategy == "sample" and sample_pct is not None:
        try:
            rows = conn.query(
                f"SELECT COUNT(*) FROM {table_b_quoted}"
            )
            total = rows[0][0] if rows else 0
            if total > 0:
                limit = max(int(total * sample_pct / 100), 1)
        except Exception:
            limit = sample_rows
    elif strategy == "sample":
        limit = sample_rows

    # 构建 WHERE 条件
    where_b = ""
    if strategy == "recent" and recent_days is not None:
        where_b = (
            f" WHERE {time_column} >= SYSDATE - {recent_days}"
        )

    if limit > 0:
        # 达梦中随机采样: ORDER BY DBMS_RANDOM.VALUE
        # 对超大表用 SAMPLE 子句
        if limit < 5000:
            sql_b = (
                f"SELECT DISTINCT {col_b_quoted} FROM {table_b_quoted}"
                f"{where_b} ORDER BY DBMS_RANDOM.VALUE LIMIT {limit}"
            )
        else:
            pct = max(0.01, min(100, limit * 100.0 / 100000))  # 粗略估算
            sql_b = (
                f"SELECT DISTINCT {col_b_quoted} FROM {table_b_quoted}"
                f"{where_b} SAMPLE({pct:.1f})"
            )
    else:
        sql_b = (
            f"SELECT DISTINCT {col_b_quoted} FROM {table_b_quoted}"
            f"{where_b}"
        )

    try:
        # 取 A 表的字段值
        sql_a = (
            f"SELECT DISTINCT {col_a_quoted} FROM {table_a_quoted}"
            f" WHERE {col_a_quoted} IS NOT NULL LIMIT {min(sample_rows, 5000)}"
        )
        vals_a = set(r[0] for r in conn.query(sql_a))
        if not vals_a:
            return 0.0

        vals_b = set(r[0] for r in conn.query(sql_b))
        if not vals_b:
            return 0.0

        overlap = len(vals_a & vals_b) / len(vals_a)
        return round(overlap, 4)
    except Exception:
        return 0.0
