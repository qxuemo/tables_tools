"""表结构扫描 — 读取表、列、注释、行数."""
from typing import Any, Dict, List, Optional

from .connector import DamengConnector


class TableScanner:
    def __init__(self, connector: DamengConnector, schema: str = ""):
        self.conn = connector
        self.schema = schema

    def scan_all(
        self,
        exclude_patterns: Optional[List[str]] = None,
        progress_cb=None,
    ) -> List[Dict[str, Any]]:
        tables = self._get_tables(exclude_patterns or [])
        result: List[Dict[str, Any]] = []
        total = len(tables)

        for i, table_name in enumerate(tables):
            if progress_cb:
                progress_cb(table_name, i + 1, total)
            row_count = self._get_row_count(table_name)
            columns = self._get_columns(table_name)
            result.append({
                "name": table_name,
                "columns": columns,
                "row_count": row_count,
            })

        return result

    def _get_tables(self, exclude_patterns: List[str]) -> List[str]:
        if self.schema:
            sql = "SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER = ?"
            rows = self.conn.query(sql, (self.schema,))
            tables = [r[0] for r in rows]
        else:
            rows = self.conn.query(
                "SELECT TABLE_NAME FROM ALL_TABLES WHERE OWNER = USER"
            )
        tables = [r[0] for r in rows]

        # 通配符过滤
        import fnmatch

        filtered: List[str] = []
        for t in tables:
            excluded = False
            for p in exclude_patterns:
                if fnmatch.fnmatch(t.upper(), p.upper()):
                    excluded = True
                    break
            if not excluded:
                filtered.append(t)
        return sorted(filtered)

    def _get_row_count(self, table_name: str) -> int:
        try:
            rows = self.conn.query(
                f'SELECT COUNT(*) FROM "{table_name}"'
            )
            return rows[0][0] if rows else 0
        except Exception:
            return 0

    def _get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        columns = self.conn.query(
            "SELECT COLUMN_NAME, DATA_TYPE FROM ALL_TAB_COLUMNS "
            "WHERE TABLE_NAME = ? ORDER BY COLUMN_ID",
            (table_name,),
        )
        comments_map = self._get_comments(table_name)

        return [
            {
                "name": col[0],
                "type": col[1],
                "comment": comments_map.get(col[0]),
            }
            for col in columns
        ]

    def _get_comments(self, table_name: str) -> Dict[str, Optional[str]]:
        try:
            rows = self.conn.query(
                "SELECT COLUMN_NAME, COMMENTS FROM ALL_COL_COMMENTS "
                "WHERE TABLE_NAME = ?",
                (table_name,),
            )
            return {
                r[0]: (r[1] if r[1] else None) for r in rows
            }
        except Exception:
            return {}
