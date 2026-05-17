"""字段名匹配规则 — 规则 A/B/C."""
import re
from typing import Any, Dict, List, Tuple


def match_all(
    tables: List[Dict[str, Any]],
    progress_cb=None,
) -> List[Dict[str, Any]]:
    """对所有表两两执行匹配，返回候选关联列表."""
    candidates: List[Dict[str, Any]] = []
    table_names = [t["name"] for t in tables]
    table_cols = {
        t["name"]: {c["name"]: c for c in t["columns"]} for t in tables
    }
    total = len(tables)

    for i, table_a in enumerate(tables):
        if progress_cb:
            progress_cb(table_a["name"], i + 1, total)
        cols_a = table_cols[table_a["name"]]

        for table_b_name in table_names:
            if table_a["name"] == table_b_name:
                continue
            cols_b = table_cols[table_b_name]

            for col_a_name, col_a_info in cols_a.items():
                # 规则 A: 字段名完全相同
                if col_a_name in cols_b:
                    candidates.append({
                        "from_table": table_a["name"],
                        "from_column": col_a_name,
                        "to_table": table_b_name,
                        "to_column": col_a_name,
                        "match_type": "exact_name",
                    })
                    continue

                # 规则 C: A.col 包含 B表名 + id 特征
                table_b_stem = _table_stem(table_b_name)
                if _is_id_reference(col_a_name, table_b_stem):
                    target_col = _find_id_column(cols_b)
                    if target_col:
                        candidates.append({
                            "from_table": table_a["name"],
                            "from_column": col_a_name,
                            "to_table": table_b_name,
                            "to_column": target_col,
                            "match_type": "id_pattern",
                        })
                        continue

                # 规则 B: col 名包含目标表的关键字
                if _has_keyword(col_a_name, table_b_name):
                    target_cols = _find_matching_columns(cols_b, col_a_name)
                    for tc in target_cols:
                        candidates.append({
                            "from_table": table_a["name"],
                            "from_column": col_a_name,
                            "to_table": table_b_name,
                            "to_column": tc,
                            "match_type": "keyword",
                        })

    # 去重
    seen = set()
    unique: List[Dict[str, Any]] = []
    for c in candidates:
        key = (c["from_table"], c["from_column"], c["to_table"], c["to_column"])
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _table_stem(table_name: str) -> str:
    """提取表名主干：去掉常见前缀后缀 (_info, _main, _rec 等)."""
    name = table_name.lower()
    for suffix in ["_info", "_main", "_rec", "_detail", "_log", "_cfg", "_config"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    return name


def _is_id_reference(col_name: str, table_stem: str) -> bool:
    """判断字段名是否指向某表的 ID，如 order_id → order."""
    col_lower = col_name.lower()
    stem_lower = table_stem.lower()
    return col_lower in (
        stem_lower + "_id",
        stem_lower + "id",
        stem_lower + "_no",
        stem_lower + "_code",
    ) or bool(re.match(rf"^{stem_lower}_\w+_id$", col_lower))


def _find_id_column(cols: Dict[str, Any]) -> str or None:
    """找目标表的 ID 类字段."""
    for col_name in cols:
        low = col_name.lower()
        if low in ("id", "sid", "pk_id") or low.endswith("_id"):
            return col_name
    return None


def _has_keyword(col_name: str, table_name: str) -> bool:
    """字段名是否包含表名的关键子串."""
    col_lower = col_name.lower()
    tbl_lower = table_name.lower()
    # 去掉数字日期后缀（如 order_detail_20260517）
    tbl_clean = re.sub(r"[\d_]{4,}$", "", tbl_lower).strip("_")
    # 表名至少 3 个字符才算有效关键字
    if len(tbl_clean) < 3:
        return False
    return tbl_clean in col_lower


def _find_matching_columns(
    cols: Dict[str, Any], col_name: str
) -> List[str]:
    """找目标表中与源字段相关的列."""
    col_lower = col_name.lower()
    matches = []
    for cname in cols:
        if col_lower in cname.lower() or cname.lower() in col_lower:
            matches.append(cname)
    return matches[:3]  # 最多返回 3 个
