"""Local-only stoppage portal, linked to OAK no-count incidents. Never edits counts."""
import html
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BRISBANE = timezone(timedelta(hours=10))
REASONS = ('Loading delay', 'Conveyor maintenance', 'Equipment fault', 'Safety stoppage', 'Break', 'No incoming tyres', 'Other')

def init(db):
    with sqlite3.connect(db, timeout=15) as con:
        con.execute('CREATE TABLE IF NOT EXISTS management_reasons (id INTEGER PRIMARY KEY, created TEXT NOT NULL, incident_id TEXT, reason TEXT NOT NULL, notes TEXT NOT NULL, submitted_by TEXT NOT NULL)')
        con.execute('''CREATE TABLE IF NOT EXISTS no_count_incidents (
            incident_id TEXT PRIMARY KEY, started TEXT NOT NULL, ended TEXT,
            duration_seconds INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT 'OPEN')''')

def sync_incidents(db, now=None):
    """Reconstruct 10+ minute no-count gaps from real OAK counts for today's Brisbane shift.
    Includes 05:00-to-first-count and current open gap; safe to call repeatedly.
    """
    now = (now or datetime.now(BRISBANE)).astimezone(BRISBANE)
    start = now.replace(hour=5, minute=0, second=0, microsecond=0)
    end = start.replace(hour=17, minute=5)
    if now < start:
        return
    stop = min(now, end)
    init(db)
    with sqlite3.connect(db, timeout=15) as con:
        rows = con.execute('SELECT ts,metric_utc FROM counts WHERE source=? ORDER BY id', ('OAK-D S2 PoE / CAT5',)).fetchall()
        times = []
        for ts, epoch in rows:
            try:
                stamp = datetime.fromtimestamp(epoch, BRISBANE) if epoch is not None else datetime.fromisoformat(ts)
                if stamp.tzinfo is None:
                    stamp = stamp.replace(tzinfo=BRISBANE)
                stamp = stamp.astimezone(BRISBANE)
                if start <= stamp <= stop:
                    times.append(stamp)
            except (ValueError, TypeError, OverflowError):
                continue
        times.sort()
        previous = start
        for index, following in enumerate(times + [stop]):
            duration = int((following - previous).total_seconds())
            if duration >= 600:
                incident_id = previous.strftime('%Y%m%d-%H%M%S')
                is_open = index == len(times) and now < end
                con.execute('''INSERT INTO no_count_incidents(incident_id,started,ended,duration_seconds,status)
                    VALUES(?,?,?,?,?) ON CONFLICT(incident_id) DO UPDATE SET
                    ended=excluded.ended,duration_seconds=excluded.duration_seconds,status=excluded.status''',
                    (incident_id, previous.isoformat(timespec='seconds'), None if is_open else following.isoformat(timespec='seconds'), duration, 'OPEN' if is_open else 'CLOSED'))
            previous = following

def launch(db, host='127.0.0.1', port=8765):
    """Local-only. For phones use an authenticated secure tunnel, not public port forwarding."""
    init(db)
    token = secrets.token_urlsafe(24)
    class Handler(BaseHTTPRequestHandler):
        def authorised(self):
            path = urlparse(self.path)
            return path.path == '/' and parse_qs(path.query).get('token', [''])[0] == token
        def do_GET(self):
            if not self.authorised():
                self.send_error(403); return
            sync_incidents(db)
            with sqlite3.connect(db, timeout=15) as con:
                incidents = con.execute('''SELECT i.incident_id,i.started,i.ended,i.duration_seconds,i.status,
                    r.reason,r.notes,r.submitted_by FROM no_count_incidents i LEFT JOIN management_reasons r
                    ON r.id=(SELECT MAX(id) FROM management_reasons WHERE incident_id=i.incident_id)
                    ORDER BY i.started DESC LIMIT 50''').fetchall()
            blocks = []
            for iid, started, ended, seconds, status, reason, notes, author in incidents:
                iid_html = html.escape(iid, quote=True)
                options = ''.join(f'<option value="{html.escape(r, quote=True)}" {"selected" if r == reason else ""}>{html.escape(r)}</option>' for r in REASONS)
                blocks.append(f'''<section><div class="heading"><strong>{html.escape(started[11:16])} · {html.escape(started[:10])}</strong><span>{html.escape(status)}</span></div>
                <p>Duration: {seconds // 60} min {seconds % 60} sec · Incident #{iid_html}</p>
                <form method="post" action="/?token={token}"><input type="hidden" name="incident" value="{iid_html}">
                <label>Stoppage reason<select name="reason"><option value="">Choose a reason</option>{options}</select></label>
                <label>Explanation<textarea name="notes" maxlength="1000" rows="2">{html.escape(notes or '')}</textarea></label>
                <label>Reported by<input name="by" maxlength="80" required value="{html.escape(author or '', quote=True)}"></label>
                <button type="submit">{'Update reason' if reason else 'Save reason'}</button></form></section>''')
            content = ''.join(blocks) or '<section>No 10-minute stoppages recorded for this shift yet.</section>'
            page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TyreTrack Management</title><style>
            body{{font:16px system-ui;background:#101923;color:#eaf2f7;margin:0;padding:18px}}main{{max-width:700px;margin:auto}}
            section{{background:#1c2c3b;padding:18px;border-radius:14px;margin:14px 0}}.heading{{display:flex;justify-content:space-between;gap:12px}}
            input,select,textarea,button{{box-sizing:border-box;width:100%;padding:12px;margin:7px 0 15px;border-radius:8px;border:1px solid #506374;font:inherit}}
            button{{background:#29ba78;color:#071b12;font-weight:700;cursor:pointer}}p{{color:#b7cbd5}}a{{color:#7fdfb2}}</style></head>
            <body><main><h1>TYRETRACK · Stoppage Reasons</h1><p>Automatically detected 10-minute no-count events, Brisbane time. Select the reason for each incident. Tyre counts cannot be edited here.</p>
            <p><a href="/?token={token}">Refresh incidents</a></p>{content}</main></body></html>'''
            payload = page.encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(payload)))
            self.end_headers(); self.wfile.write(payload)
        def do_POST(self):
            if not self.authorised():
                self.send_error(403); return
            try:
                size = int(self.headers.get('Content-Length','0'))
            except ValueError:
                self.send_error(400); return
            if size < 0 or size > 4096:
                self.send_error(413); return
            form = parse_qs(self.rfile.read(size).decode('utf-8','replace'))
            get = lambda key: form.get(key,[''])[0].strip()
            if get('reason') not in REASONS or not get('by') or len(get('by')) > 80:
                self.send_error(400); return
            with sqlite3.connect(db, timeout=15) as con:
                valid = con.execute('SELECT 1 FROM no_count_incidents WHERE incident_id=?',(get('incident'),)).fetchone()
                if not valid:
                    self.send_error(400); return
                con.execute('INSERT INTO management_reasons(created,incident_id,reason,notes,submitted_by) VALUES(?,?,?,?,?)',
                            (datetime.now(BRISBANE).isoformat(timespec='seconds'),get('incident'),get('reason'),get('notes')[:1000],get('by')))
            self.send_response(303); self.send_header('Location',f'/?token={token}'); self.end_headers()
        def log_message(self, *_): pass
    server = ThreadingHTTPServer((host,port),Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f'http://{host}:{port}/?token={token}'
