"""加载 scan_config.json 和 connections.json 配置."""
import json
import os
from typing import Any, Dict, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def load_scan_config() -> Dict[str, Any]:
    path = os.path.join(DATA_DIR, "scan_config.json")
    if not os.path.exists(path):
        return _default_scan_config()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_connections() -> List[Dict[str, Any]]:
    path = os.path.join(DATA_DIR, "connections.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_connection(db_id: str) -> Optional[Dict[str, Any]]:
    for conn in load_connections():
        if conn.get("id") == db_id:
            return conn
    return None


def get_db_data_dir(db_id: str) -> str:
    d = os.path.join(DATA_DIR, db_id)
    os.makedirs(d, exist_ok=True)
    return d


def _default_scan_config() -> Dict[str, Any]:
    return {
        "agent_command": "python scan.py",
        "ws_port": 8765,
        "default_strategy": "sample",
        "sample_rows": 1000,
        "overlap_threshold": 0.5,
        "large_table_rules": [],
        "exclude_tables": [],
    }
