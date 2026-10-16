"""Task 3: Personal Blog Site (Flask + SQLite). Run: pip install flask && python app.py"""
import sqlite3, os
from datetime import datetime
from functools import wraps
from flask import Flask, g, redirect, render_template_string, request, session, url_for, flash, abort
from jinja2 import DictLoader

app = Flask(__name__)
app.secret_key = "change-this-secret"
ADMIN_PASSWORD = "admin123"  # change before deploying
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blog.db")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB); g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close(_):
    d = g.pop("db", None)
    if d: d.close()

def init():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, body TEXT NOT NULL, published INTEGER DEFAULT 0, created TEXT, updated TEXT)""")
    c.commit(); c.close()

def admin_only(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("admin"): return redirect(url_for("login"))
        return f(*a, **k)
    return w

BASE = """<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>{% block title %}My Blog{% endblock %}</title><style>
body{font-family:Georgia,serif;margin:0;background:#f6f8f6;color:#222}
nav{background:#2e7d32;padding:14px 24px;display:flex;gap:18px;align-items:center}
nav a{color:#fff;text-decoration:none;font-family:Arial}nav .brand{font-weight:bold;font-size:1.2em;margin-right:auto}
main{max-width:720px;margin:24px auto;padding:0 16px}
.card{background:#fff;padding:18px 22px;margin-bottom:16px;border-radius:8px;box-shadow:0 1px 3px #0002}
.card h2{margin:0 0 4px}.meta{color:#777;font:13px Arial}a{color:#2e7d32}
input,textarea{width:100%;padding:8px;margin:6px 0 12px;box-sizing:border-box;font:inherit}
button,.btn{background:#2e7d32;color:#fff;border:0;padding:8px 16px;border-radius:4px;cursor:pointer;text-decoration:none;font:14px Arial}
.danger{background:#c62828}.flash{background:#e8f5e9;padding:10px;border-radius:4px;margin-bottom:12px}
.tag{font:12px Arial;padding:2px 8px;border-radius:10px;background:#ddd}.pub{background:#c8e6c9}
</style></head><body><nav><a class=brand href="{{ url_for('home') }}">✍ My Blog</a>
<a href="{{ url_for('home') }}">Home</a><a href="{{ url_for('about') }}">About</a>
{% if session.admin %}<a href="{{ url_for('admin') }}">Dashboard</a><a href="{{ url_for('new') }}">New post</a>
<a href="{{ url_for('logout') }}">Logout</a>{% else %}<a href="{{ url_for('login') }}">Login</a>{% endif %}</nav>
<main>{% for m in get_flashed_messages() %}<div class=flash>{{ m }}</div>{% endfor %}{% block body %}{% endblock %}</main></body></html>"""

HOME = """{% extends 'base' %}{% block body %}<h1>Latest posts</h1>
{% for p in posts %}<div class=card><h2><a href="{{ url_for('post', id=p.id) }}">{{ p.title }}</a></h2>
<div class=meta>{{ p.created }}</div><p>{{ p.body[:200] }}{% if p.body|length > 200 %}…{% endif %}</p></div>
{% else %}<p>No published posts yet.</p>{% endfor %}{% endblock %}"""

POST = """{% extends 'base' %}{% block title %}{{ p.title }}{% endblock %}{% block body %}
<div class=card><h1>{{ p.title }}</h1><div class=meta>Published {{ p.created }}{% if p.updated != p.created %} · edited {{ p.updated }}{% endif %}</div>
{% for para in p.body.split('\\n\\n') %}<p>{{ para }}</p>{% endfor %}</div><a href="{{ url_for('home') }}">← Back</a>{% endblock %}"""

FORM = """{% extends 'base' %}{% block body %}<h1>{{ 'Edit' if p else 'New' }} post</h1><form method=post>
<label>Title</label><input name=title required value="{{ p.title if p else '' }}">
<label>Body (blank line = new paragraph)</label><textarea name=body rows=12 required>{{ p.body if p else '' }}</textarea>
<label><input type=checkbox name=published style="width:auto" {{ 'checked' if p and p.published }}> Publish</label><br><br>
<button>Save</button></form>{% endblock %}"""

ADMIN = """{% extends 'base' %}{% block body %}<h1>Dashboard</h1>
{% for p in posts %}<div class=card><b>{{ p.title }}</b> <span class="tag {{ 'pub' if p.published }}">{{ 'Published' if p.published else 'Draft' }}</span>
<div class=meta>{{ p.updated }}</div><br><a class=btn href="{{ url_for('edit', id=p.id) }}">Edit</a>
<form method=post action="{{ url_for('toggle', id=p.id) }}" style="display:inline"><button>{{ 'Unpublish' if p.published else 'Publish' }}</button></form>
<form method=post action="{{ url_for('delete', id=p.id) }}" style="display:inline" onsubmit="return confirm('Delete?')"><button class=danger>Delete</button></form></div>
{% else %}<p>Nothing yet. <a href="{{ url_for('new') }}">Write your first post</a>.</p>{% endfor %}{% endblock %}"""

LOGIN = """{% extends 'base' %}{% block body %}<h1>Admin login</h1><form method=post>
<input type=password name=password placeholder=Password autofocus><button>Login</button></form>{% endblock %}"""

ABOUT = """{% extends 'base' %}{% block body %}<div class=card><h1>About</h1>
<p>A personal blog built with Python and Flask. Edit this page in app.py.</p></div>{% endblock %}"""

app.jinja_loader = DictLoader({"base": BASE, "home": HOME, "post": POST, "form": FORM,
                               "admin": ADMIN, "login": LOGIN, "about": ABOUT})

def now(): return datetime.now().strftime("%d %b %Y, %H:%M")

@app.route("/")
def home():
    return render_template_string(app.jinja_loader.get_source(app.jinja_env, "home")[0],
        posts=db().execute("SELECT * FROM posts WHERE published=1 ORDER BY id DESC").fetchall())

def render(_tpl, **kw):
    return render_template_string(app.jinja_loader.get_source(app.jinja_env, _tpl)[0], **kw)

@app.route("/post/<int:id>")
def post(id):
    p = db().execute("SELECT * FROM posts WHERE id=?", (id,)).fetchone()
    if not p or (not p["published"] and not session.get("admin")): abort(404)
    return render("post", p=p)

@app.route("/about")
def about(): return render("about")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True; return redirect(url_for("admin"))
        flash("Wrong password.")
    return render("login")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("home"))

@app.route("/admin")
@admin_only
def admin():
    return render("admin", posts=db().execute("SELECT * FROM posts ORDER BY id DESC").fetchall())

@app.route("/new", methods=["GET", "POST"])
@admin_only
def new():
    if request.method == "POST":
        db().execute("INSERT INTO posts(title,body,published,created,updated) VALUES(?,?,?,?,?)",
                     (request.form["title"], request.form["body"], int("published" in request.form), now(), now()))
        db().commit(); flash("Post saved."); return redirect(url_for("admin"))
    return render("form", p=None)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_only
def edit(id):
    p = db().execute("SELECT * FROM posts WHERE id=?", (id,)).fetchone() or abort(404)
    if request.method == "POST":
        db().execute("UPDATE posts SET title=?,body=?,published=?,updated=? WHERE id=?",
                     (request.form["title"], request.form["body"], int("published" in request.form), now(), id))
        db().commit(); flash("Post updated."); return redirect(url_for("admin"))
    return render("form", p=p)

@app.route("/toggle/<int:id>", methods=["POST"])
@admin_only
def toggle(id):
    db().execute("UPDATE posts SET published=1-published WHERE id=?", (id,)); db().commit()
    return redirect(url_for("admin"))

@app.route("/delete/<int:id>", methods=["POST"])
@admin_only
def delete(id):
    db().execute("DELETE FROM posts WHERE id=?", (id,)); db().commit()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init(); app.run(debug=True)
