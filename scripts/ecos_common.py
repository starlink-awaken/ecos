#!/usr/bin/env python3
"""
ecos_common — 共享基础设施模块
消除 capture_watcher/filter_scorer/ssb_client 中的重复代码

提供:
  - DB_PATH, TZ 常量
  - _now() 时间工具
  - _get_conn() 数据库连接工厂
  - CREATE_SSB_EVENTS_SQL 建表语句
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

ECOS_HOME = Path(__file__).resolve().parent.parent
SSB_DB_DIR = ECOS_HOME / "LADS" / "ssb"
SSB_DB_PATH = SSB_DB_DIR / "ecos.db"
TZ = timezone(timedelta(hours=8), "CST")

# ─── 共享 SQL ───
CREATE_SSB_EVENTS_SQL = """
CREATE TABLE IF NOT EXISTS ssb_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    seq         INTEGER NOT NULL,
    event_id    TEXT NOT NULL UNIQUE,
    timestamp   TEXT NOT NULL,
    source_zone TEXT DEFAULT '',
    source_agent TEXT NOT NULL,
    event_type  TEXT NOT NULL DEFAULT 'UNKNOWN',
    action      TEXT DEFAULT '',
    target_zone TEXT DEFAULT '',
    target_agent TEXT DEFAULT '',
    priority    INTEGER DEFAULT 0,
    status      TEXT DEFAULT 'active',
    action_required TEXT DEFAULT '',
    confidence  REAL DEFAULT 0.0,
    payload_json TEXT,
    payload_size INTEGER DEFAULT 0,
    media_path  TEXT DEFAULT '',
    schema_version TEXT DEFAULT '1.0',
    agent_signature TEXT,
    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
)
"""


def now_iso() -> str:
    """ISO8601 timestamp with Asia/Shanghai timezone"""
    return datetime.now(TZ).isoformat()


def get_conn(db_path = None):
    """数据库连接工厂 — WAL模式, Row工厂"""
    conn = sqlite3.connect(str(db_path or SSB_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ensure_ssb_table(conn: sqlite3.Connection = None):
    """确保 SSB 表存在"""
    close_after = conn is None
    if conn is None:
        conn = get_conn()
    conn.execute(CREATE_SSB_EVENTS_SQL)
    conn.commit()
    if close_after:
        conn.close()
