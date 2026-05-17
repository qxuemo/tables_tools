"""达梦数据库连接管理."""
from typing import Any, Dict

# dmPython is the official Dameng Python driver
# pip install dmPython
try:
    import dmPython
except ImportError:
    dmPython = None


class DamengConnector:
    def __init__(self, conn_info: Dict[str, Any]):
        self.host = conn_info["host"]
        self.port = conn_info.get("port", 5236)
        self.user = conn_info["user"]
        self.password = conn_info["password"]
        self.schema = conn_info.get("schema", "")
        self._conn = None
        self._cursor = None

    def connect(self) -> None:
        if dmPython is None:
            raise ImportError(
                "dmPython is not installed. Run: pip install dmPython"
            )
        self._conn = dmPython.connect(
            user=self.user,
            password=self.password,
            server=self.host,
            port=self.port,
        )
        self._cursor = self._conn.cursor()
        if self.schema:
            # 校验 schema 名只含安全字符
            if not self.schema.replace("_", "").isalnum():
                raise ValueError(f"不安全的 schema 名: {self.schema}")
            self._cursor.execute(
                f'SET SCHEMA "{self.schema}"'
            )

    def query(self, sql: str, params: tuple = ()) -> Any:
        self._cursor.execute(sql, params)
        return self._cursor.fetchall()

    @property
    def cursor(self) -> Any:
        return self._cursor

    def close(self) -> None:
        if self._cursor:
            self._cursor.close()
        if self._conn:
            self._conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
