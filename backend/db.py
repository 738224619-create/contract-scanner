import sqlite3, json, os, uuid
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            created_at TEXT NOT NULL,
            risks_json TEXT NOT NULL,
            summary TEXT NOT NULL,
            content_hash TEXT DEFAULT '',
            content_text TEXT DEFAULT '',
            optimized_text TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS shares (
            id TEXT PRIMARY KEY,
            analysis_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        );
    """)
    for col in ["content_hash", "content_text", "optimized_text"]:
        try: conn.execute(f"SELECT {col} FROM analyses LIMIT 0")
        except: conn.execute(f"ALTER TABLE analyses ADD COLUMN {col} TEXT DEFAULT ''")
    conn.commit()
    conn.close()

def save(filename, risks, summary, content_hash="", content_text=""):
    conn = get_conn()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    risks_json = json.dumps([r.model_dump() for r in risks], ensure_ascii=False)
    cur = conn.execute(
        "INSERT INTO analyses (filename, created_at, risks_json, summary, content_hash, content_text) VALUES (?,?,?,?,?,?)",
        (filename, now, risks_json, summary, content_hash, content_text),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid

def save_optimized(aid, optimized):
    conn = get_conn()
    conn.execute("UPDATE analyses SET optimized_text = ? WHERE id = ?", (optimized, aid))
    conn.commit()
    conn.close()

def list_all():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, filename, created_at, summary, content_hash, CASE WHEN optimized_text!='' THEN 1 ELSE 0 END AS has_optimized FROM analyses ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_one(aid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM analyses WHERE id = ?", (aid,)).fetchone()
    conn.close()
    if not row: return None
    d = dict(row)
    d["risks"] = json.loads(d.pop("risks_json"))
    return d

def get_by_hash(hash_val, exclude_id=0):
    conn = get_conn()
    rows = conn.execute("SELECT id, filename, created_at, summary FROM analyses WHERE content_hash=? AND id!=? ORDER BY created_at DESC", (hash_val, exclude_id)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_share(aid):
    conn = get_conn()
    sid = uuid.uuid4().hex[:8]
    now = datetime.now()
    expires = now + timedelta(days=7)
    conn.execute("INSERT INTO shares (id, analysis_id, created_at, expires_at) VALUES (?,?,?,?)",
                 (sid, aid, now.strftime("%Y-%m-%d %H:%M:%S"), expires.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    return sid

def get_shared(sid):
    conn = get_conn()
    row = conn.execute("SELECT s.analysis_id, s.expires_at, a.filename, a.created_at, a.summary, a.risks_json FROM shares s JOIN analyses a ON s.analysis_id=a.id WHERE s.id=? AND s.expires_at > datetime('now')", (sid,)).fetchone()
    conn.close()
    if not row: return None
    d = dict(row)
    d["id"] = d.pop("analysis_id")
    d["risks"] = json.loads(d.pop("risks_json"))
    d.pop("expires_at", None)
    return d

init()
