"""
Admin API router - crawl-stats observability dashboard.

Reads the scraper's crawl-state SQLite DB (written by the Scrapy
PineconePipeline) and exposes run history + totals. Read-only; protected by
the optional API-key dependency.
"""

import os
import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from backend.app.core.security import require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])


def _state_db_path() -> str:
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
    )
    return os.getenv(
        "SARAL_STATE_DB",
        os.path.join(repo_root, "data", "processed", "crawl_state.sqlite"),
    )


def _read_stats(limit: int = 20) -> dict:
    path = _state_db_path()
    if not os.path.exists(path):
        return {"available": False, "db_path": path, "tracked_schemes": 0, "runs": []}

    conn = sqlite3.connect(path)
    try:
        tracked = conn.execute("SELECT COUNT(*) FROM schemes").fetchone()[0]
        cols = ["spider", "new", "changed", "skipped", "chunks", "failed", "finished"]
        rows = conn.execute(
            """
            SELECT spider, new, changed, skipped, chunks, failed, finished
            FROM crawl_runs ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        runs = [dict(zip(cols, r)) for r in rows]
    except sqlite3.OperationalError:
        runs, tracked = [], 0
    finally:
        conn.close()

    totals = {
        "new": sum(r["new"] or 0 for r in runs),
        "changed": sum(r["changed"] or 0 for r in runs),
        "skipped": sum(r["skipped"] or 0 for r in runs),
        "chunks": sum(r["chunks"] or 0 for r in runs),
    }
    return {
        "available": True,
        "db_path": path,
        "tracked_schemes": tracked,
        "totals_recent": totals,
        "runs": runs,
    }


@router.get("/admin/crawl-stats")
async def crawl_stats(limit: int = 20):
    """JSON crawl statistics for dashboards / monitoring."""
    return _read_stats(limit)


@router.get("/admin/crawl-stats/view", response_class=HTMLResponse)
async def crawl_stats_view(limit: int = 20):
    """Minimal HTML dashboard for the crawl run history."""
    data = _read_stats(limit)
    rows = "".join(
        f"<tr><td>{r['spider']}</td><td>{r['new']}</td><td>{r['changed']}</td>"
        f"<td>{r['skipped']}</td><td>{r['chunks']}</td><td>{r['finished']}</td></tr>"
        for r in data["runs"]
    ) or "<tr><td colspan='6'>No runs recorded yet</td></tr>"

    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>SARAL Crawl Stats</title>
<style>
 body{{background:#0a0a0c;color:#e7e9ee;font-family:system-ui,sans-serif;padding:32px}}
 h1{{font-weight:800;letter-spacing:-.02em}}
 .pill{{display:inline-block;margin:4px 8px 16px 0;padding:8px 14px;border:1px solid #ffffff1a;border-radius:12px;background:#ffffff08}}
 table{{width:100%;border-collapse:collapse;margin-top:12px}}
 th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid #ffffff14;font-size:14px}}
 th{{color:#10b981;text-transform:uppercase;font-size:11px;letter-spacing:.05em}}
</style></head><body>
<h1>Crawl Stats</h1>
<div>
 <span class="pill">Tracked schemes: <b>{data['tracked_schemes']}</b></span>
 <span class="pill">DB: {'found' if data['available'] else 'missing'}</span>
</div>
<table>
 <tr><th>Spider</th><th>New</th><th>Changed</th><th>Skipped</th><th>Chunks</th><th>Finished</th></tr>
 {rows}
</table>
</body></html>"""
    return HTMLResponse(html)
