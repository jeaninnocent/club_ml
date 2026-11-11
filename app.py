"""Plateforme du Club Machine Learning : espace apprenants + espace admin."""
import os, re, secrets, sqlite3, string, time, unicodedata, datetime as dt
from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from jinja2 import DictLoader
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE, "club.db"))
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")  # obligatoire pour l'espace admin
GH = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+?(\.git)?/?$")


def secret_key():
    if os.environ.get("SECRET_KEY"):
        return os.environ["SECRET_KEY"]
    p = os.path.join(BASE, ".secret")
    if not os.path.exists(p):
        open(p, "w").write(secrets.token_hex(32))
    return open(p).read().strip()


app = Flask(__name__)
app.secret_key = secret_key()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  PERMANENT_SESSION_LIFETIME=dt.timedelta(days=14))

# ---------- base de données ----------
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL, level TEXT DEFAULT '', pw TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, title TEXT NOT NULL, descr TEXT DEFAULT '',
  deadline TEXT DEFAULT '', xp INTEGER DEFAULT 100);
CREATE TABLE IF NOT EXISTS subs(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, task_id INTEGER NOT NULL,
  url TEXT NOT NULL, at TEXT NOT NULL, note REAL, comment TEXT DEFAULT '', xp_awarded INTEGER DEFAULT 0,
  UNIQUE(user_id, task_id));
"""


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.executescript(SCHEMA)
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()


def q(sql, *a):
    return db().execute(sql, a).fetchall()


def q1(sql, *a):
    r = q(sql, *a)
    return r[0] if r else None


def ex(sql, *a):
    d = db()
    c = d.execute(sql, a)
    d.commit()
    return c


# ---------- sécurité ----------
FAILS = {}


def throttled():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0]
    n, t = FAILS.get(ip, (0, 0))
    if n >= 8 and time.time() - t < 300:
        return ip, True
    if time.time() - t >= 300:
        FAILS.pop(ip, None)
    return ip, False


def fail(ip):
    n, _ = FAILS.get(ip, (0, 0))
    FAILS[ip] = (n + 1, time.time())


@app.before_request
def csrf_check():
    if request.method == "POST":
        if not session.get("_t") or request.form.get("_t") != session["_t"]:
            abort(400, "Session expirée : rechargez la page.")


@app.context_processor
def ctx():
    session.setdefault("_t", secrets.token_hex(16))
    return {"token": session["_t"], "late": is_late}


@app.after_request
def headers(r):
    r.headers["X-Frame-Options"] = "DENY"
    r.headers["X-Content-Type-Options"] = "nosniff"
    return r


def is_late(deadline, ts=None):
    if not deadline:
        return False
    return (ts or dt.date.today().isoformat())[:10] > deadline


def learner_only(f):
    def w(*a, **k):
        if not session.get("uid"):
            return redirect(url_for("login"))
        return f(*a, **k)
    w.__name__ = f.__name__
    return w


def admin_only(f):
    def w(*a, **k):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*a, **k)
    w.__name__ = f.__name__
    return w


# ---------- espace apprenant ----------
@app.route("/")
def home():
    return redirect(url_for("dashboard" if session.get("uid") else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip, blocked = throttled()
        if blocked:
            flash("Trop de tentatives. Réessayez dans quelques minutes.")
        else:
            u = q1("SELECT * FROM users WHERE username=?", request.form.get("username", "").strip().lower())
            if u and check_password_hash(u["pw"], request.form.get("password", "")):
                session.clear()
                session.permanent = True
                session["uid"] = u["id"]
                return redirect(url_for("dashboard"))
            fail(ip)
            flash("Identifiant ou mot de passe incorrect.")
    return render_template("login", title="Espace apprenant", admin=False)


@app.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    return redirect(url_for("login"))


def ranking():
    rows = q("""SELECT u.id,u.name,u.level,COALESCE(SUM(s.xp_awarded),0) xp,COUNT(s.id) n
                FROM users u LEFT JOIN subs s ON s.user_id=u.id GROUP BY u.id ORDER BY xp DESC,u.name""")
    out, prev, rank = [], None, 0
    for i, r in enumerate(rows, 1):
        if r["xp"] != prev:
            rank, prev = i, r["xp"]
        out.append(dict(r, rank=rank))
    return out


@app.route("/dashboard")
@learner_only
def dashboard():
    me = q1("SELECT * FROM users WHERE id=?", session["uid"])
    if not me:
        return redirect(url_for("logout"))
    tasks = q("""SELECT t.*, s.url, s.at, s.note, s.comment, s.xp_awarded FROM tasks t
                 LEFT JOIN subs s ON s.task_id=t.id AND s.user_id=? ORDER BY t.id DESC""", me["id"])
    mine = next((r for r in ranking() if r["id"] == me["id"]), None)
    notes = [t["note"] for t in tasks if t["note"] is not None]
    avg = round(sum(notes) / len(notes), 2) if notes else None
    return render_template("dashboard", me=me, tasks=tasks, mine=mine, avg=avg, total=len(ranking()))


@app.route("/submit/<int:tid>", methods=["POST"])
@learner_only
def submit(tid):
    if not q1("SELECT id FROM tasks WHERE id=?", tid):
        abort(404)
    url = request.form.get("url", "").strip()
    old = q1("SELECT * FROM subs WHERE user_id=? AND task_id=?", session["uid"], tid)
    if not GH.match(url):
        flash("Lien invalide. Format : https://github.com/pseudo/depot")
    elif old and old["note"] is not None:
        flash("Cet exercice est déjà noté : le rendu ne peut plus être modifié.")
    else:
        ex("""INSERT INTO subs(user_id,task_id,url,at) VALUES(?,?,?,?)
              ON CONFLICT(user_id,task_id) DO UPDATE SET url=excluded.url, at=excluded.at""",
           session["uid"], tid, url, dt.datetime.now().isoformat(timespec="minutes"))
        flash("Rendu enregistré.")
    return redirect(url_for("dashboard"))


@app.route("/classement")
@learner_only
def board():
    return render_template("board", rows=ranking(), uid=session["uid"])


# ---------- espace admin ----------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        ip, blocked = throttled()
        if not ADMIN_PASSWORD:
            flash("ADMIN_PASSWORD n'est pas configuré sur le serveur.")
        elif blocked:
            flash("Trop de tentatives. Réessayez dans quelques minutes.")
        elif (secrets.compare_digest(request.form.get("username", ""), ADMIN_USER)
              and secrets.compare_digest(request.form.get("password", ""), ADMIN_PASSWORD)):
            session.clear()
            session.permanent = True
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            fail(ip)
            flash("Identifiants administrateur incorrects.")
    return render_template("login", title="Espace administrateur", admin=True)


@app.route("/admin", methods=["GET", "POST"])
@admin_only
def admin():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            try:
                xp = max(0, int(request.form.get("xp") or 100))
            except ValueError:
                xp = 100
            ex("INSERT INTO tasks(title,descr,deadline,xp) VALUES(?,?,?,?)", title,
               request.form.get("descr", ""), request.form.get("deadline", ""), xp)
            flash("Exercice publié.")
        return redirect(url_for("admin"))
    tasks = q("""SELECT t.*, (SELECT COUNT(*) FROM subs WHERE task_id=t.id) n,
                 (SELECT COUNT(*) FROM subs WHERE task_id=t.id AND note IS NULL) todo FROM tasks t ORDER BY id DESC""")
    return render_template("admin", tasks=tasks, nusers=q1("SELECT COUNT(*) c FROM users")["c"])


@app.route("/admin/task/<int:tid>")
@admin_only
def admin_task(tid):
    t = q1("SELECT * FROM tasks WHERE id=?", tid) or abort(404)
    subs = q("""SELECT s.*, u.name, u.username FROM subs s JOIN users u ON u.id=s.user_id
                WHERE task_id=? ORDER BY s.at""", tid)
    missing = q("""SELECT name FROM users WHERE id NOT IN (SELECT user_id FROM subs WHERE task_id=?)
                   ORDER BY name""", tid)
    return render_template("admin_task", t=t, subs=subs, missing=missing)


@app.route("/admin/task/<int:tid>/delete", methods=["POST"])
@admin_only
def delete_task(tid):
    ex("DELETE FROM subs WHERE task_id=?", tid)
    ex("DELETE FROM tasks WHERE id=?", tid)
    return redirect(url_for("admin"))


@app.route("/admin/grade/<int:sid>", methods=["POST"])
@admin_only
def grade(sid):
    s = q1("SELECT s.*, t.xp txp FROM subs s JOIN tasks t ON t.id=s.task_id WHERE s.id=?", sid) or abort(404)
    try:
        note = float(request.form.get("note", "").replace(",", "."))
        assert 0 <= note <= 20
    except (ValueError, AssertionError):
        flash("La note doit être comprise entre 0 et 20.")
        return redirect(url_for("admin_task", tid=s["task_id"]))
    ex("UPDATE subs SET note=?, comment=?, xp_awarded=? WHERE id=?", note,
       request.form.get("comment", "").strip(), round(s["txp"] * note / 20), sid)
    flash("Note enregistrée.")
    return redirect(url_for("admin_task", tid=s["task_id"]))


def slug(name):
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    parts = re.sub(r"[^a-z0-9 ]", "", n).split()
    return ".".join([parts[0], parts[-1]] if len(parts) > 1 else parts) or "membre"


def new_password():
    alphabet = "".join(c for c in string.ascii_letters + string.digits if c not in "0O1lI")
    return "".join(secrets.choice(alphabet) for _ in range(8))


@app.route("/admin/learners", methods=["GET", "POST"])
@admin_only
def admin_learners():
    if request.method == "POST":
        created = []
        for line in request.form.get("names", "").splitlines():
            name, _, level = (p.strip() for p in line.partition(";"))
            if not name:
                continue
            base = username = slug(name)
            i = 1
            while q1("SELECT 1 FROM users WHERE username=?", username):
                i += 1
                username = f"{base}{i}"
            pw = new_password()
            ex("INSERT INTO users(username,name,level,pw) VALUES(?,?,?,?)", username, name, level,
               generate_password_hash(pw))
            created.append((name, username, pw))
        return render_template("creds", created=created)
    return render_template("learners", users=q("SELECT * FROM users ORDER BY name"))


@app.route("/admin/learners/<int:uid>/reset", methods=["POST"])
@admin_only
def reset(uid):
    u = q1("SELECT * FROM users WHERE id=?", uid) or abort(404)
    pw = new_password()
    ex("UPDATE users SET pw=? WHERE id=?", generate_password_hash(pw), uid)
    return render_template("creds", created=[(u["name"], u["username"], pw)])


@app.route("/admin/learners/<int:uid>/delete", methods=["POST"])
@admin_only
def delete_user(uid):
    ex("DELETE FROM subs WHERE user_id=?", uid)
    ex("DELETE FROM users WHERE id=?", uid)
    return redirect(url_for("admin_learners"))


# ---------- gabarits ----------
CSS = """:root{--bg:#f8fafc;--bg-alt:#f1f5f9;--card:#fff;--card-hover:#f8fafc;--tx:#0f172a;--tx-secondary:#64748b;--ac:#6366f1;--ac-hover:#4f46e5;--ac-light:#e0e7ff;--bd:#e2e8f0;--ok:#10b981;--ok-light:#d1fae5;--warn:#f59e0b;--warn-light:#fef3c7;--bad:#ef4444;--bad-light:#fee2e2;--shadow:0 1px 3px rgba(0,0,0,0.1),0 1px 2px rgba(0,0,0,0.06);--shadow-lg:0 10px 15px -3px rgba(0,0,0,0.1),0 4px 6px -2px rgba(0,0,0,0.05);--radius:10px;--radius-sm:6px}
@media(prefers-color-scheme:dark){:root{--bg:#0f172a;--bg-alt:#1e293b;--card:#1e293b;--card-hover:#334155;--tx:#f1f5f9;--tx-secondary:#cbd5e1;--ac:#818cf8;--ac-hover:#a5b4fc;--ac-light:#312e81;--bd:#334155;--ok:#10b981;--ok-light:#064e3b;--warn:#f59e0b;--warn-light:#78350f;--bad:#ef4444;--bad-light:#7f1d1d;--shadow:0 1px 3px rgba(0,0,0,0.3);--shadow-lg:0 10px 15px -3px rgba(0,0,0,0.3);color-scheme:dark}}
*{box-sizing:border-box;transition:color .2s,background-color .2s,border-color .2s}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}
header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;padding:16px 24px;background:var(--card);border-bottom:1px solid var(--bd);box-shadow:var(--shadow);position:sticky;top:0;z-index:100}header b{font-size:18px;font-weight:700;background:linear-gradient(135deg,var(--ac),#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
nav{display:flex;gap:20px;align-items:center}nav a{color:var(--ac);text-decoration:none;font-weight:500;font-size:14px;padding:6px 12px;border-radius:var(--radius-sm);transition:all .2s;position:relative}nav a:hover{background:var(--ac-light);color:var(--ac-hover)}nav a::after{content:'';position:absolute;bottom:-2px;left:12px;right:12px;height:2px;background:var(--ac);border-radius:1px;opacity:0;transition:opacity .2s}nav a:hover::after{opacity:1}
main{max-width:1100px;margin:0 auto;padding:32px 20px 80px}
h1{font-size:28px;font-weight:700;margin:0 0 8px;color:var(--tx)}h1+.sub{margin-bottom:24px}h2{font-size:18px;font-weight:600;margin:0 0 12px;color:var(--tx)}h3{font-size:15px;font-weight:600;margin:0 0 8px;color:var(--tx)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:var(--radius);padding:24px;margin-bottom:16px;box-shadow:var(--shadow);transition:all .3s ease;animation:slideUp .3s ease}@keyframes slideUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.card:hover{border-color:var(--ac);box-shadow:var(--shadow-lg)}
.card.primary{background:linear-gradient(135deg,var(--ac-light),var(--ac-light));border-color:var(--ac)}
input,textarea,select{font:inherit;width:100%;padding:11px 14px;border:1.5px solid var(--bd);border-radius:var(--radius-sm);background:var(--bg);color:var(--tx);margin:6px 0 12px;transition:all .2s;resize:vertical}
input:hover,textarea:hover,select:hover{border-color:var(--ac)}input:focus,textarea:focus,select:focus{outline:none;border-color:var(--ac);box-shadow:0 0 0 3px var(--ac-light);background:var(--card)}
input::placeholder{color:var(--tx-secondary)}input[type="date"]{cursor:pointer}
button{font:inherit;font-weight:600;border:none;padding:11px 18px;border-radius:var(--radius-sm);cursor:pointer;transition:all .2s;display:inline-flex;align-items:center;gap:8px;justify-content:center;position:relative;overflow:hidden}
button.primary{background:var(--ac);color:white;box-shadow:0 4px 12px rgba(99,102,241,0.4)}button.primary:hover{background:var(--ac-hover);transform:translateY(-2px);box-shadow:0 6px 20px rgba(99,102,241,0.6)}button.primary:active{transform:translateY(0)}
button.secondary{background:var(--bg-alt);color:var(--tx);border:1.5px solid var(--bd)}button.secondary:hover{background:var(--card);border-color:var(--ac)}
button.danger{background:var(--bad);color:white;box-shadow:0 4px 12px rgba(239,68,68,0.3)}button.danger:hover{background:#dc2626;transform:translateY(-2px)}button.danger:active{transform:translateY(0)}
button.small{padding:7px 12px;font-size:13px}button.icon{padding:8px;width:32px;height:32px;background:var(--bg-alt);color:var(--tx-secondary)}button.icon:hover{background:var(--ac);color:white}
button:disabled{opacity:.5;cursor:not-allowed;transform:none}
.sub{color:var(--tx-secondary);font-size:13px;font-weight:500}
.flash{padding:14px 16px;margin-bottom:16px;border-radius:var(--radius-sm);border-left:4px solid;display:flex;align-items:center;gap:10px;animation:slideDown .3s ease}@keyframes slideDown{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}
.flash.success{background:var(--ok-light);border-color:var(--ok);color:var(--ok)}
.flash.error{background:var(--bad-light);border-color:var(--bad);color:var(--bad)}
.flash.warning{background:var(--warn-light);border-color:var(--warn);color:var(--warn)}
.flash::before{content:'';width:4px;height:4px;border-radius:50%;background:currentColor}
.tag{font-size:12px;font-weight:600;padding:4px 10px;border-radius:16px;border:1px solid;display:inline-block;white-space:nowrap}
.tag.ok{background:var(--ok-light);border-color:var(--ok);color:var(--ok)}
.tag.bad{background:var(--bad-light);border-color:var(--bad);color:var(--bad)}
.tag.warn{background:var(--warn-light);border-color:var(--warn);color:var(--warn)}
.tag.blue{background:var(--ac-light);border-color:var(--ac);color:var(--ac)}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:14px;margin-top:12px}table th{background:var(--bg-alt);font-weight:600;padding:12px;text-align:left;border-bottom:2px solid var(--bd);color:var(--tx-secondary);font-size:12px;text-transform:uppercase;letter-spacing:.5px}table td{padding:12px;border-bottom:1px solid var(--bd);vertical-align:middle}table tr:hover{background:var(--card-hover)}table tr:last-child td{border-bottom:none}
.row{display:flex;gap:12px;align-items:flex-start;flex-wrap:wrap}.row input{margin:0;flex:1;min-width:140px}.row button{margin:0}
.row.centered{justify-content:center}.row.between{justify-content:space-between}.row.end{justify-content:flex-end}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:20px}
.stat{background:var(--card);border:1px solid var(--bd);border-radius:var(--radius);padding:18px;box-shadow:var(--shadow);transition:all .3s;animation:slideUp .3s ease}
.stat:hover{border-color:var(--ac);transform:translateY(-2px);box-shadow:var(--shadow-lg)}
.stat-label{color:var(--tx-secondary);font-size:12px;text-transform:uppercase;letter-spacing:.5px;font-weight:600;margin-bottom:8px}
.stat-value{font-size:26px;font-weight:700;color:var(--ac);margin-bottom:4px}
.stat-unit{color:var(--tx-secondary);font-size:12px}
.me{background:linear-gradient(135deg,var(--ac-light),var(--ac-light));border-left:4px solid var(--ac)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.5);z-index:1000;justify-content:center;align-items:center}
.modal-overlay.show{display:flex;animation:fadeIn .2s ease}@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.modal{background:var(--card);border-radius:var(--radius);padding:32px;max-width:500px;width:90%;box-shadow:var(--shadow-lg);animation:scaleIn .3s ease}@keyframes scaleIn{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}
form{margin:0}form .row:last-child{margin-top:20px}
.section{margin-bottom:32px}
.form-group{margin-bottom:14px}.form-group:last-child{margin-bottom:0}
.label{display:block;color:var(--tx);font-weight:600;margin-bottom:6px;font-size:14px}
.help{color:var(--tx-secondary);font-size:12px;margin-top:-8px;margin-bottom:12px}
.separator{height:1px;background:var(--bd);margin:20px 0}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;background:var(--bg-alt);color:var(--tx-secondary)}
.badge.success{background:var(--ok-light);color:var(--ok)}
.badge.danger{background:var(--bad-light);color:var(--bad)}
.badge.warning{background:var(--warn-light);color:var(--warn)}
.action-menu{display:flex;gap:6px}
.action-menu button{font-size:13px;padding:6px 10px;width:auto;height:auto}
.empty{text-align:center;padding:40px 20px;color:var(--tx-secondary)}
.empty svg{width:48px;height:48px;opacity:.3;margin-bottom:16px}
@media(max-width:768px){header{flex-direction:column;align-items:flex-start}nav{width:100%}main{padding:16px 12px 60px}h1{font-size:24px}.card{padding:16px}.stats{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}table{font-size:12px}table th,table td{padding:8px}button{padding:9px 14px}.row{gap:8px}}
@media print{header,button,.noprint,.action-menu{display:none}}"""

CSRF = '<input type="hidden" name="_t" value="{{ token }}">'

T = {
"layout": """<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Club Machine Learning</title><style>""" + CSS + """</style></head><body>
<header><b>Club Machine Learning</b><nav>{% if session.uid %}<a href="/dashboard">Mes exercices</a><a href="/classement">Classement</a><a href="/logout">Déconnexion</a>
{% elif session.admin %}<a href="/admin">Exercices</a><a href="/admin/learners">Apprenants</a><a href="/logout">Déconnexion</a>{% endif %}</nav></header>
<main>{% for m in get_flashed_messages() %}<div class="flash">{{ m }}</div>{% endfor %}{% block c %}{% endblock %}</main></body></html>""",

"login": """{% extends "layout" %}{% block c %}
<div style="min-height:calc(100vh - 180px);display:flex;align-items:center;justify-content:center">
  <div class="card" style="max-width:420px;width:100%">
    <div style="text-align:center;margin-bottom:32px">
      <div style="font-size:48px;margin-bottom:16px">{% if admin %}🔐{% else %}📚{% endif %}</div>
      <h1 style="margin:0 0 8px;font-size:24px">{{ title }}</h1>
      <p class="sub">Connectez-vous pour accéder à votre espace</p>
    </div>
    
    <form method="post">""" + CSRF + """
      <div class="form-group">
        <label class="label">Identifiant</label>
        <input name="username" autocomplete="username" autocapitalize="none" placeholder="Votre identifiant" required autofocus>
      </div>
      
      <div class="form-group">
        <label class="label">Mot de passe</label>
        <input name="password" type="password" autocomplete="current-password" placeholder="Votre mot de passe" required>
      </div>
      
      <button class="primary" style="width:100%;margin-top:20px">
        {% if admin %}🔓 Se connecter (Admin){% else %}📖 Se connecter{% endif %}
      </button>
    </form>
    
    <div style="text-align:center;margin-top:24px;padding-top:24px;border-top:1px solid var(--bd)">
      <p class="sub">
        {% if not admin %}
          Espace admin? <a href="/admin/login" style="color:var(--ac);text-decoration:none;font-weight:600">Accès administrateur →</a>
        {% else %}
          Apprenant? <a href="/login" style="color:var(--ac);text-decoration:none;font-weight:600">Espace apprenant →</a>
        {% endif %}
      </p>
    </div>
  </div>
</div>
{% endblock %}""",

"dashboard": """{% extends "layout" %}{% block c %}<h1>👋 Bonjour {{ me.name }}</h1>
<p class="sub">Vous êtes classé 🥇 n°{{ mine.rank }} sur {{ total }} apprenants</p>

<div class="stats">
  <div class="stat">
    <div class="stat-label">XP Total</div>
    <div class="stat-value">{{ mine.xp }}</div>
    <div class="stat-unit">points</div>
  </div>
  <div class="stat">
    <div class="stat-label">Classement</div>
    <div class="stat-value">{{ mine.rank }}<span style="font-size:16px">/{{ total }}</span></div>
    <div class="stat-unit">rang</div>
  </div>
  <div class="stat">
    <div class="stat-label">Moyenne</div>
    <div class="stat-value">{{ avg if avg is not none else '—' }}</div>
    <div class="stat-unit">{% if avg is not none %}/20{% endif %}</div>
  </div>
  <div class="stat">
    <div class="stat-label">Exercices</div>
    <div class="stat-value">{{ tasks|length }}</div>
    <div class="stat-unit">total</div>
  </div>
</div>

<div class="section">
  <h2>📝 Exercices</h2>
  {% if tasks %}
    {% for t in tasks %}
      <div class="card">
        <div class="row between" style="align-items:flex-start">
          <div style="flex:1">
            <div class="row" style="align-items:center;gap:10px">
              <h3 style="margin:0">{{ t.title }}</h3>
              {% if t.note is not none %}
                <span class="tag ok">✓ Noté</span>
              {% elif t.url %}
                <span class="tag {{ 'bad' if late(t.deadline, t.at) else 'ok' }}">
                  {% if late(t.deadline, t.at) %}⏰ En retard{% else %}✓ Rendu{% endif %}
                </span>
              {% else %}
                <span class="tag {{ 'bad' if late(t.deadline) else '' }}">
                  {% if late(t.deadline) %}⏰ En retard{% else %}📋 À rendre{% endif %}
                </span>
              {% endif %}
            </div>
            
            <p class="sub" style="margin-top:8px">
              {{ t.xp }} XP max
              {% if t.deadline %}· Date limite: <strong>{{ t.deadline }}</strong>{% endif %}
            </p>
            
            {% if t.descr %}
              <p style="white-space:pre-wrap;margin:12px 0 0;color:var(--tx-secondary)">{{ t.descr }}</p>
            {% endif %}
          </div>
          
          {% if t.note is not none %}
            <div style="background:var(--ok-light);border-radius:var(--radius-sm);padding:12px 16px;text-align:center;min-width:100px">
              <div class="stat-label" style="color:var(--ok)">Note</div>
              <div style="font-size:28px;font-weight:700;color:var(--ok)">{{ t.note }}</div>
              <div class="sub" style="color:var(--ok);margin-top:4px">/20</div>
            </div>
          {% endif %}
        </div>
        
        {% if t.note is not none %}
          <div class="separator"></div>
          <div class="row" style="justify-content:space-between;align-items:center">
            <div>
              <p class="sub">Retour de l'admin:</p>
              <p>{{ t.comment or 'Aucun commentaire' }}</p>
              <p style="margin:8px 0 0;color:var(--ok);font-weight:600">✓ +{{ t.xp_awarded }} XP gagnés</p>
            </div>
            <a href="{{ t.url }}" target="_blank" rel="noopener noreferrer">
              <button class="secondary small">🔗 Voir votre dépôt</button>
            </a>
          </div>
        {% elif t.url %}
          <div class="separator"></div>
          <div class="row" style="justify-content:space-between;align-items:center">
            <div>
              <p class="sub">Votre rendu:</p>
              <a href="{{ t.url }}" target="_blank" rel="noopener noreferrer" style="color:var(--ac);text-decoration:none;font-weight:600">{{ t.url }}</a>
              <p class="sub" style="margin-top:6px">Envoyé: {{ t.at.replace('T', ' ') }}</p>
            </div>
            <form method="post" action="/submit/{{ t.id }}" class="row" style="gap:8px">
              """ + CSRF + """
              <input name="url" value="{{ t.url }}" style="min-width:300px;margin:0" required>
              <button class="secondary small">✎ Mettre à jour</button>
            </form>
          </div>
        {% else %}
          <div class="separator"></div>
          <form method="post" action="/submit/{{ t.id }}">
            """ + CSRF + """
            <div class="row" style="gap:8px">
              <input name="url" placeholder="https://github.com/pseudo/mon-depot" style="margin:0" required>
              <button class="primary small">✓ Soumettre</button>
            </div>
          </form>
        {% endif %}
      </div>
    {% endfor %}
  {% else %}
    <div class="card">
      <div class="empty">
        <div style="font-size:32px;margin-bottom:8px">📭</div>
        <p><strong>Aucun exercice disponible</strong></p>
        <p class="sub">L'admin n'a pas encore publié d'exercices</p>
      </div>
    </div>
  {% endif %}
</div>
{% endblock %}""",

"board": """{% extends "layout" %}{% block c %}<h1>🏆 Classement XP</h1>
<p class="sub">Compétition entre apprenants - Top 10 en vert, reste en orange</p>

<div class="card">
  <div class="scroll">
    <table>
      <thead>
        <tr>
          <th style="width:70px">Rang</th>
          <th>Nom</th>
          <th>Niveau</th>
          <th style="width:80px">Rendus</th>
          <th style="width:100px;text-align:right">XP</th>
        </tr>
      </thead>
      <tbody>
        {% for r in rows %}
          <tr class="{% if r.id == uid %}me{% endif %} {% if r.rank <= 10 %}rank-top10{% else %}rank-rest{% endif %}">
            <td style="font-weight:700;font-size:15px">
              {% if r.rank == 1 %}
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:28px">🥇</span>
                  <strong style="color:var(--ac)">1er</strong>
                </div>
              {% elif r.rank == 2 %}
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:28px">🥈</span>
                  <strong style="color:var(--ac)">2e</strong>
                </div>
              {% elif r.rank == 3 %}
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="font-size:28px">🥉</span>
                  <strong style="color:var(--ac)">3e</strong>
                </div>
              {% else %}
                <strong style="color:var(--tx-secondary)">#{{ r.rank }}</strong>
              {% endif %}
            </td>
            <td>
              <div style="display:flex;align-items:center;gap:10px">
                <strong style="font-size:15px">{{ r.name }}</strong>
                {% if r.rank == 1 %}
                  <span class="badge" style="background:linear-gradient(135deg,#fbbf24,#f59e0b);color:white;border:none;font-weight:700">👑 Champion</span>
                {% elif r.rank == 2 %}
                  <span class="badge" style="background:linear-gradient(135deg,#60a5fa,#3b82f6);color:white;border:none;font-weight:700">⭐ Runner-up</span>
                {% elif r.rank == 3 %}
                  <span class="badge" style="background:linear-gradient(135deg,#f97316,#ea580c);color:white;border:none;font-weight:700">🔥 Podium</span>
                {% elif r.rank <= 10 %}
                  <span class="badge" style="background:var(--ok-light);color:var(--ok);border-color:var(--ok);font-weight:600">Top 10</span>
                {% endif %}
              </div>
            </td>
            <td>
              {% if r.level %}
                <span class="badge">{{ r.level }}</span>
              {% else %}
                <span class="sub">—</span>
              {% endif %}
            </td>
            <td style="text-align:center">
              <strong style="font-size:14px">{{ r.n }}</strong>
            </td>
            <td style="text-align:right">
              <strong style="font-size:18px;background:linear-gradient(135deg,var(--ac),#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{{ r.xp }}</strong>
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<style>
table tbody tr.rank-top10 {
  background: linear-gradient(90deg, var(--ok-light), transparent);
  border-left: 3px solid var(--ok);
}

table tbody tr.rank-top10:hover {
  background: linear-gradient(90deg, var(--ok-light), var(--card-hover));
  border-left-color: var(--ac);
}

table tbody tr.rank-rest {
  background: linear-gradient(90deg, var(--warn-light), transparent);
  border-left: 3px solid var(--warn);
}

table tbody tr.rank-rest:hover {
  background: linear-gradient(90deg, var(--warn-light), var(--card-hover));
  border-left-color: var(--ac);
}

table tbody tr.me {
  box-shadow: inset 0 0 0 2px var(--ac);
  font-weight:600;
}

table tbody tr.me.rank-top10 {
  background: linear-gradient(90deg, color-mix(in srgb, var(--ok-light), var(--ac-light)), transparent);
}

table tbody tr.me.rank-rest {
  background: linear-gradient(90deg, color-mix(in srgb, var(--warn-light), var(--ac-light)), transparent);
}
</style>
{% endblock %}""",

"admin": """{% extends "layout" %}{% block c %}<h1>✨ Tableau de bord</h1>
<p class="sub">Gérez vos exercices et suivez la progression des apprenants</p>

<div class="stats">
  <div class="stat">
    <div class="stat-label">Exercices</div>
    <div class="stat-value">{{ tasks|length }}</div>
  </div>
  <div class="stat">
    <div class="stat-label">Apprenants</div>
    <div class="stat-value">{{ nusers }}</div>
  </div>
  <div class="stat">
    <div class="stat-label">Rendus en attente</div>
    <div class="stat-value">{{ tasks|map(attribute='todo')|sum }}</div>
  </div>
</div>

<div class="section">
  <div class="card primary">
    <h2>📝 Créer un nouvel exercice</h2>
    <p class="sub">Définissez le titre, les consignes, la deadline et les points d'XP</p>
    <form method="post">""" + CSRF + """
      <div class="form-group">
        <label class="label">Titre de l'exercice *</label>
        <input name="title" placeholder="Ex: API REST avec FastAPI" required>
      </div>
      <div class="form-group">
        <label class="label">Consignes</label>
        <textarea name="descr" rows="4" placeholder="Décrivez les objectifs, les requirements..."></textarea>
      </div>
      <div class="row">
        <div class="form-group" style="flex:1">
          <label class="label">Date limite</label>
          <input name="deadline" type="date">
        </div>
        <div class="form-group" style="flex:0.8">
          <label class="label">XP maximum</label>
          <input name="xp" type="number" min="0" value="100">
        </div>
      </div>
      <button class="primary">✓ Publier l'exercice</button>
    </form>
  </div>
</div>

<div class="section">
  <h2>📚 Exercices publiés</h2>
  {% if tasks %}
    {% for t in tasks %}
      <div class="card">
        <div class="row between" style="align-items:flex-start">
          <div style="flex:1">
            <div class="row" style="align-items:center;gap:10px">
              <h3 style="margin:0">{{ t.title }}</h3>
              <span class="tag blue">{{ t.xp }} XP</span>
              {% if t.deadline %}<span class="tag">Limite: {{ t.deadline }}</span>{% endif %}
            </div>
            <p class="sub" style="margin-top:8px">
              <strong>{{ t.n }}/{{ nusers }}</strong> rendus · 
              <strong style="color:var(--warn)">{{ t.todo }}</strong> à noter
            </p>
          </div>
          <div class="action-menu">
            <a href="/admin/task/{{ t.id }}"><button class="primary small">Rendus & notes</button></a>
            <form method="post" action="/admin/task/{{ t.id }}/delete" onsubmit="return confirm('⚠️ Supprimer cet exercice et tous ses rendus ?')" style="margin:0">
              """ + CSRF + """
              <button class="danger small">Supprimer</button>
            </form>
          </div>
        </div>
      </div>
    {% endfor %}
  {% else %}
    <div class="card">
      <div class="empty">
        <div style="font-size:32px;margin-bottom:8px">📭</div>
        <p><strong>Aucun exercice publié</strong></p>
        <p class="sub">Créez votre premier exercice ci-dessus</p>
      </div>
    </div>
  {% endif %}
</div>
{% endblock %}""",

"admin_task": """{% extends "layout" %}{% block c %}<h1>{{ t.title }}</h1>
<p class="sub">{{ t.xp }} XP max · Les XP attribués = (XP max × note) / 20</p>

<div class="stats">
  <div class="stat">
    <div class="stat-label">Rendus reçus</div>
    <div class="stat-value">{{ subs|length }}/{{ subs|length + missing|length }}</div>
  </div>
  <div class="stat">
    <div class="stat-label">À noter</div>
    <div class="stat-value" style="color:var(--warn)">{{ subs|selectattr('note','none')|list|length }}</div>
  </div>
  <div class="stat">
    <div class="stat-label">Notés</div>
    <div class="stat-value" style="color:var(--ok)">{{ subs|rejectattr('note','none')|list|length }}</div>
  </div>
</div>

<div class="section">
  <h2>✅ Rendus reçus</h2>
  {% if subs %}
    {% for s in subs %}
      <div class="card">
        <div class="row between" style="align-items:flex-start">
          <div style="flex:1">
            <div class="row" style="align-items:center;gap:10px">
              <h3 style="margin:0">{{ s.name }}</h3>
              <span class="tag {{ 'bad' if late(t.deadline, s.at) else 'ok' }}">
                {% if late(t.deadline, s.at) %}⏰ En retard{% else %}✓ À temps{% endif %}
              </span>
            </div>
            <p class="sub" style="margin-top:8px">
              <strong>@{{ s.username }}</strong> · {{ s.at.replace('T', ' ') }}
            </p>
            <a href="{{ s.url }}" target="_blank" rel="noopener noreferrer" style="color:var(--ac);text-decoration:none;font-weight:600">🔗 Voir le dépôt →</a>
          </div>
          {% if s.note is not none %}
            <div style="background:var(--ok-light);border-radius:var(--radius-sm);padding:12px 16px;text-align:center">
              <div class="stat-label" style="color:var(--ok)">Note</div>
              <div style="font-size:24px;font-weight:700;color:var(--ok)">{{ s.note }}/20</div>
              <div class="sub" style="margin-top:4px">+{{ s.xp_awarded }} XP</div>
            </div>
          {% endif %}
        </div>
        
        {% if s.note is none %}
          <div class="separator"></div>
          <form method="post" action="/admin/grade/{{ s.id }}">
            """ + CSRF + """
            <div class="row" style="align-items:flex-end">
              <div style="flex:0.6">
                <label class="label">Note sur 20</label>
                <input name="note" type="number" step="0.25" min="0" max="20" placeholder="0-20" required>
              </div>
              <div style="flex:1;margin:0">
                <label class="label">Commentaire (optionnel)</label>
                <input name="comment" placeholder="Bravo! Quelques points à améliorer..." style="margin:0">
              </div>
              <button class="primary small">✓ Noter</button>
            </div>
          </form>
        {% else %}
          <div class="separator"></div>
          <div>
            <p class="sub">Commentaire:</p>
            <p>{{ s.comment or 'Aucun commentaire' }}</p>
          </div>
        {% endif %}
      </div>
    {% endfor %}
  {% else %}
    <div class="card">
      <div class="empty">
        <div style="font-size:32px;margin-bottom:8px">📬</div>
        <p><strong>Aucun rendu reçu</strong></p>
        <p class="sub">Les apprenants verront cet exercice bientôt</p>
      </div>
    </div>
  {% endif %}
</div>

{% if missing %}
  <div class="section">
    <h2>⏸️ Pas encore rendu</h2>
    <div class="card">
      <div class="row" style="gap:8px;flex-wrap:wrap">
        {% for m in missing %}
          <span class="badge">{{ m.name }}</span>
        {% endfor %}
      </div>
    </div>
  </div>
{% endif %}
{% endblock %}""",

"learners": """{% extends "layout" %}{% block c %}<h1>👥 Gestion des apprenants</h1>
<p class="sub">{{ users|length }} compte(s) créé(s)</p>

<div class="section">
  <div class="card primary">
    <h2>➕ Créer des comptes</h2>
    <p class="sub">Entrez un apprenant par ligne. Format: <code style="background:var(--bg);padding:2px 6px;border-radius:4px">Nom complet; Niveau</code></p>
    <form method="post">""" + CSRF + """
      <textarea name="names" rows="5" placeholder="Awa Koné; L3 TWIN&#10;Jean Kouassi; L2&#10;Marie Dupont" required></textarea>
      <p class="help">Les identifiants et mots de passe sont générés automatiquement et affichés une seule fois.</p>
      <button class="primary">✓ Créer les comptes</button>
    </form>
  </div>
</div>

<div class="section">
  <h2>📋 Liste des apprenants</h2>
  {% if users %}
    <div class="card scroll">
      <table>
        <thead>
          <tr>
            <th>Nom</th>
            <th>Niveau</th>
            <th>Identifiant</th>
            <th style="width:180px">Actions</th>
          </tr>
        </thead>
        <tbody>
          {% for u in users %}
            <tr>
              <td><strong>{{ u.name }}</strong></td>
              <td>
                {% if u.level %}
                  <span class="badge">{{ u.level }}</span>
                {% else %}
                  <span class="sub">—</span>
                {% endif %}
              </td>
              <td><code style="background:var(--bg-alt);padding:4px 8px;border-radius:4px;font-size:13px">{{ u.username }}</code></td>
              <td>
                <div class="action-menu">
                  <form method="post" action="/admin/learners/{{ u.id }}/reset" onsubmit="return confirm('🔄 Générer un nouveau mot de passe pour {{ u.name }} ?')" style="margin:0">
                    """ + CSRF + """
                    <button class="secondary small">🔑 MDP</button>
                  </form>
                  <form method="post" action="/admin/learners/{{ u.id }}/delete" onsubmit="return confirm('⚠️ Supprimer {{ u.name }} et tous ses rendus ?')" style="margin:0">
                    """ + CSRF + """
                    <button class="danger small">🗑️ Supprimer</button>
                  </form>
                </div>
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  {% else %}
    <div class="card">
      <div class="empty">
        <div style="font-size:32px;margin-bottom:8px">📭</div>
        <p><strong>Aucun apprenant</strong></p>
        <p class="sub">Créez des comptes ci-dessus pour commencer</p>
      </div>
    </div>
  {% endif %}
</div>
{% endblock %}""",

"creds": """{% extends "layout" %}{% block c %}<h1>🔐 Identifiants à transmettre</h1>
<div class="flash success" style="border-left-width:4px">
  <div style="flex:1">
    <strong>Succès!</strong> Les comptes ont été créés. Les mots de passe ci-dessous ne s'affichent qu'une seule fois.
  </div>
  <div style="font-size:24px">✓</div>
</div>

<p class="sub" style="margin-bottom:20px">📋 Notez ces identifiants, imprimez cette page, ou enregistrez-la avant de quitter.</p>

<div class="card scroll">
  <table>
    <thead>
      <tr>
        <th>Nom</th>
        <th>Identifiant</th>
        <th>Mot de passe</th>
      </tr>
    </thead>
    <tbody>
      {% for n,u,p in created %}
        <tr>
          <td><strong>{{ n }}</strong></td>
          <td><code style="background:var(--bg-alt);padding:6px 10px;border-radius:4px">{{ u }}</code></td>
          <td><code style="background:var(--bg-alt);padding:6px 10px;border-radius:4px;font-weight:700">{{ p }}</code></td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div class="row centered noprint" style="margin-top:24px;gap:12px">
  <button class="primary" onclick="window.print()">🖨️ Imprimer</button>
  <a href="/admin/learners"><button class="secondary">← Retour</button></a>
</div>
{% endblock %}""",
}
app.jinja_env.loader = DictLoader(T)

if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
