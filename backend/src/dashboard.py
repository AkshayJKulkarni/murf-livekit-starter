"""
dashboard.py — Local web dashboard showing call analytics + escalation requests.
Run: uv run python src/dashboard.py
Open: http://localhost:8080
"""

import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, str(Path(__file__).parent))
from db import get_all_escalations, get_call_stats

URGENCY_COLOR = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}


def render_html(stats: dict, escalations: list[dict]) -> str:
    success_rate = round((stats["successful"] / stats["total"]) * 100) if stats["total"] else 0

    recent_rows = ""
    for c in stats["recent"]:
        color = "#22c55e" if c["outcome"] == "success" else "#ef4444"
        recent_rows += f"""
        <tr>
            <td>{c['call_id']}</td>
            <td style="color:{color};font-weight:bold">{c['outcome'].upper()}</td>
            <td>{c['reason']}</td>
            <td>{c['language']}</td>
            <td>{c['created_at'][:19].replace('T', ' ')}</td>
        </tr>"""
    if not recent_rows:
        recent_rows = "<tr><td colspan='5' style='text-align:center;color:#6b7280'>No calls yet</td></tr>"

    esc_rows = ""
    for e in escalations:
        color = URGENCY_COLOR.get(e["urgency"], "#6b7280")
        esc_rows += f"""
        <tr>
            <td><strong>{e['ref_id']}</strong></td>
            <td>{e['caller_name'] or 'Unknown'}</td>
            <td>{e['reason']}</td>
            <td>{e['summary']}</td>
            <td style="color:{color};font-weight:bold">{e['urgency'].upper()}</td>
            <td><span style="color:{'#22c55e' if e['status']=='open' else '#6b7280'}">{e['status']}</span></td>
            <td>{e['created_at'][:19].replace('T', ' ')}</td>
        </tr>"""
    if not esc_rows:
        esc_rows = "<tr><td colspan='7' style='text-align:center;color:#6b7280'>No escalations yet</td></tr>"

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Artha — Analytics Dashboard</title>
    <meta http-equiv="refresh" content="15">
    <style>
        body {{ font-family: sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
        h1 {{ color: #34d399; margin-bottom: 0.25rem; }}
        h2 {{ color: #94a3b8; font-size: 1rem; margin: 2rem 0 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
        p {{ color: #94a3b8; margin-top: 0; font-size: 0.85rem; }}
        .stats {{ display: flex; gap: 1.5rem; margin: 1.5rem 0; }}
        .stat {{ background: #1e293b; border-radius: 0.75rem; padding: 1.25rem 2rem; text-align: center; min-width: 140px; }}
        .stat .number {{ font-size: 2.5rem; font-weight: bold; line-height: 1; }}
        .stat .label {{ color: #94a3b8; font-size: 0.8rem; margin-top: 0.25rem; }}
        .total .number {{ color: #e2e8f0; }}
        .success .number {{ color: #22c55e; }}
        .failed .number {{ color: #ef4444; }}
        .rate .number {{ color: #34d399; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
        th {{ background: #1e293b; padding: 0.75rem; text-align: left; color: #94a3b8; border-bottom: 1px solid #334155; }}
        td {{ padding: 0.75rem; border-bottom: 1px solid #1e293b; vertical-align: top; }}
        tr:hover td {{ background: #1e293b; }}
    </style>
</head>
<body>
    <h1>Artha — FinSaathi Analytics</h1>
    <p>Auto-refreshes every 15 seconds.</p>

    <div class="stats">
        <div class="stat total"><div class="number">{stats['total']}</div><div class="label">Total Calls</div></div>
        <div class="stat success"><div class="number">{stats['successful']}</div><div class="label">Successful</div></div>
        <div class="stat failed"><div class="number">{stats['failed']}</div><div class="label">Failed</div></div>
        <div class="stat rate"><div class="number">{success_rate}%</div><div class="label">Success Rate</div></div>
    </div>

    <h2>Recent Calls</h2>
    <table>
        <thead><tr><th>Call ID</th><th>Outcome</th><th>Reason</th><th>Language</th><th>Time</th></tr></thead>
        <tbody>{recent_rows}</tbody>
    </table>

    <h2>Open Escalations ({len(escalations)})</h2>
    <table>
        <thead><tr><th>Ref ID</th><th>Caller</th><th>Reason</th><th>Summary</th><th>Urgency</th><th>Status</th><th>Created</th></tr></thead>
        <tbody>{esc_rows}</tbody>
    </table>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        stats = get_call_stats()
        escalations = get_all_escalations()
        html = render_html(stats, escalations).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8080), Handler)
    print("Dashboard running at http://localhost:8080")
    server.serve_forever()
