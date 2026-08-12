"""Ops analytics store — orders/ads/metrics (not the brain).

Default: SQLite at kip_memory/data/analytics.db
Optional: Postgres when AGENCY_ANALYTICS_DSN=postgresql://...
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

_DB = Path(__file__).resolve().parents[1] / "kip_memory" / "data" / "analytics.db"


def _sqlite() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(_DB))
    c.row_factory = sqlite3.Row
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS metric_events (
            id TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            name TEXT,
            value REAL,
            unit TEXT,
            dims TEXT,
            ts REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_metric_kind_ts ON metric_events(kind, ts);
        CREATE TABLE IF NOT EXISTS sku_daily (
            day TEXT NOT NULL,
            sku TEXT NOT NULL,
            revenue REAL DEFAULT 0,
            orders INTEGER DEFAULT 0,
            ad_spend REAL DEFAULT 0,
            cogs REAL DEFAULT 0,
            returns INTEGER DEFAULT 0,
            PRIMARY KEY (day, sku)
        );
        """
    )
    c.commit()
    return c


def _pg_conn():
    dsn = (os.getenv("AGENCY_ANALYTICS_DSN") or "").strip()
    if not dsn:
        return None
    try:
        import psycopg

        conn = psycopg.connect(dsn)
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS metric_events (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT,
                    value DOUBLE PRECISION,
                    unit TEXT,
                    dims JSONB,
                    ts DOUBLE PRECISION NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sku_daily (
                    day TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    revenue DOUBLE PRECISION DEFAULT 0,
                    orders INTEGER DEFAULT 0,
                    ad_spend DOUBLE PRECISION DEFAULT 0,
                    cogs DOUBLE PRECISION DEFAULT 0,
                    returns INTEGER DEFAULT 0,
                    PRIMARY KEY (day, sku)
                );
                """
            )
        conn.commit()
        return conn
    except Exception:
        return None


def record_metric(
    kind: str,
    name: str = "",
    value: float = 0.0,
    unit: str = "",
    dims: dict | None = None,
) -> dict[str, Any]:
    mid = f"m_{uuid.uuid4().hex[:12]}"
    ts = time.time()
    dims = dims or {}
    pg = _pg_conn()
    if pg is not None:
        try:
            with pg.cursor() as cur:
                cur.execute(
                    "INSERT INTO metric_events(id,kind,name,value,unit,dims,ts) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)",
                    (mid, kind, name, float(value), unit, json.dumps(dims), ts),
                )
            pg.commit()
            pg.close()
            return {"ok": True, "id": mid, "backend": "postgres"}
        except Exception as e:
            try:
                pg.close()
            except Exception:
                pass
            # fall through sqlite
            err = str(e)
        else:
            err = None
    else:
        err = None

    c = _sqlite()
    c.execute(
        "INSERT INTO metric_events(id,kind,name,value,unit,dims,ts) VALUES (?,?,?,?,?,?,?)",
        (mid, kind, name, float(value), unit, json.dumps(dims), ts),
    )
    c.commit()
    c.close()
    out = {"ok": True, "id": mid, "backend": "sqlite", "path": str(_DB)}
    if err:
        out["postgres_error"] = err
    return out


def upsert_sku_daily(
    day: str,
    sku: str,
    *,
    revenue: float = 0.0,
    orders: int = 0,
    ad_spend: float = 0.0,
    cogs: float = 0.0,
    returns: int = 0,
) -> dict[str, Any]:
    pg = _pg_conn()
    if pg is not None:
        try:
            with pg.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sku_daily(day,sku,revenue,orders,ad_spend,cogs,returns)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (day,sku) DO UPDATE SET
                      revenue = sku_daily.revenue + EXCLUDED.revenue,
                      orders = sku_daily.orders + EXCLUDED.orders,
                      ad_spend = sku_daily.ad_spend + EXCLUDED.ad_spend,
                      cogs = sku_daily.cogs + EXCLUDED.cogs,
                      returns = sku_daily.returns + EXCLUDED.returns
                    """,
                    (day, sku, revenue, orders, ad_spend, cogs, returns),
                )
            pg.commit()
            pg.close()
            return {"ok": True, "backend": "postgres", "day": day, "sku": sku}
        except Exception as e:
            try:
                pg.close()
            except Exception:
                pass
            pg_err = str(e)
    else:
        pg_err = None

    c = _sqlite()
    row = c.execute("SELECT * FROM sku_daily WHERE day=? AND sku=?", (day, sku)).fetchone()
    if row:
        c.execute(
            """
            UPDATE sku_daily SET revenue=revenue+?, orders=orders+?, ad_spend=ad_spend+?,
              cogs=cogs+?, returns=returns+? WHERE day=? AND sku=?
            """,
            (revenue, orders, ad_spend, cogs, returns, day, sku),
        )
    else:
        c.execute(
            "INSERT INTO sku_daily(day,sku,revenue,orders,ad_spend,cogs,returns) VALUES (?,?,?,?,?,?,?)",
            (day, sku, revenue, orders, ad_spend, cogs, returns),
        )
    c.commit()
    c.close()
    out = {"ok": True, "backend": "sqlite", "day": day, "sku": sku}
    if pg_err:
        out["postgres_error"] = pg_err
    return out


def query_metrics(kind: str = "", limit: int = 50) -> dict[str, Any]:
    c = _sqlite()
    if kind:
        rows = c.execute(
            "SELECT * FROM metric_events WHERE kind=? ORDER BY ts DESC LIMIT ?",
            (kind, limit),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM metric_events ORDER BY ts DESC LIMIT ?", (limit,)
        ).fetchall()
    c.close()
    return {
        "ok": True,
        "events": [
            {
                "id": r["id"],
                "kind": r["kind"],
                "name": r["name"],
                "value": r["value"],
                "unit": r["unit"],
                "dims": json.loads(r["dims"] or "{}"),
                "ts": r["ts"],
            }
            for r in rows
        ],
    }


def sku_scoreboard(limit: int = 30) -> dict[str, Any]:
    c = _sqlite()
    rows = c.execute(
        """
        SELECT sku,
               SUM(revenue) as revenue,
               SUM(orders) as orders,
               SUM(ad_spend) as ad_spend,
               SUM(cogs) as cogs,
               SUM(returns) as returns
        FROM sku_daily
        GROUP BY sku
        ORDER BY revenue DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    c.close()
    board = []
    for r in rows:
        rev = float(r["revenue"] or 0)
        spend = float(r["ad_spend"] or 0)
        cogs = float(r["cogs"] or 0)
        cm = rev - spend - cogs
        board.append(
            {
                "sku": r["sku"],
                "revenue": rev,
                "orders": int(r["orders"] or 0),
                "ad_spend": spend,
                "cogs": cogs,
                "returns": int(r["returns"] or 0),
                "contribution": round(cm, 2),
                "roas": round(rev / spend, 3) if spend > 0 else None,
            }
        )
    return {"ok": True, "skus": board}


def get_analytics_tools() -> list:
    def analytics_record_metric(kind: str, name: str = "", value: float = 0.0, unit: str = "") -> dict:
        """Record an ops metric (ads CPA, revenue, etc.) — not brain memory."""
        return record_metric(kind, name=name, value=value, unit=unit)

    def analytics_sku_daily(
        day: str,
        sku: str,
        revenue: float = 0.0,
        orders: int = 0,
        ad_spend: float = 0.0,
        cogs: float = 0.0,
    ) -> dict:
        """Upsert daily SKU economics rollup."""
        return upsert_sku_daily(day, sku, revenue=revenue, orders=orders, ad_spend=ad_spend, cogs=cogs)

    def analytics_sku_scoreboard(limit: int = 20) -> dict:
        """SKU contribution / ROAS scoreboard from analytics DB."""
        return sku_scoreboard(limit=limit)

    def analytics_query_metrics(kind: str = "", limit: int = 30) -> dict:
        """Query recent metric events."""
        return query_metrics(kind=kind, limit=limit)

    return [
        analytics_record_metric,
        analytics_sku_daily,
        analytics_sku_scoreboard,
        analytics_query_metrics,
    ]
