"""
dashboard.py — Simple local web dashboard showing open escalation requests.
Run: uv run python src/dashboard.py
Open: http://localhost:8080
"""

import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, str(Path(__file__).parent))
from db import get_all_escalations

URGENCY_COLOR = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}


def render_html(escalations: list[dict]) -> str:
    rows = ""
    for e in escalations:
        color = URGENCY_COLOR.get(e["urgency"], "#6b7280")
        rows += f"""
        <tr>
            <td><strong>{e['ref_id']}</strong></td>
            <td>{e['caller_name'] or 'Unknown'}</td>
            <td>{e['reason']}</td>
            <td>{e['summary']}</td>
            <td>{e['already_checked']}</td>
            <td style="color:{color};font-weight:bold">{e['urgency'].upper()}</td>
            <td>{e['language']}</td>
            <td>{e['follow_up']}</td>
            <td><span style="color:{'#22c55e' if e['status']=='open' else '#6b7280'}">{e['status']}</span></td>
            <td>{e['created_at'][:19].replace('T',' ')}</td>
        </tr>"""

    if not rows:
        rows = "<tr><td colspan='10' style='text-align:center;color:#6b7280'>No escalations yet</td></tr>"

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Artha — Escalations Dashboard</title>
    <meta http-equiv="refresh" content="15">
    <style>
        body {{ font-family: sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
        h1 {{ color: #34d399; margin-bottom: 0.25rem; }}
        p {{ color: #94a3b8; margin-top: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; font-size: 0.85rem; }}
        th {{ background: #1e293b; padding: 0.75rem; text-align: left; color: #94a3b8; border-bottom: 1px solid #334155; }}
        td {{ padding: 0.75rem; border-bottom: 1px solid #1e293b; vertical-align: top; }}
        tr:hover td {{ background: #1e293b; }}
    </style>
</head>
<body>
    <h1>Artha — FinSaathi Escalations</h1>
    <p>Auto-refreshes every 15 seconds. Showing {len(escalations)} request(s).</p>
    <table>
        <thead>
            <tr>
                <th>Ref ID</th><th>Caller</th><th>Reason</th><th>Summary</th>
                <th>Already Checked</th><th>Urgency</th><th>Language</th>
                <th>Follow-up</th><th>Status</th><th>Created</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        escalations = get_all_escalations()
        html = render_html(escalations).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html)

    def log_message(self, *args):
        pass  # suppress request logs


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8080), Handler)
    print("Dashboard running at http://localhost:8080")
    server.serve_forever()
