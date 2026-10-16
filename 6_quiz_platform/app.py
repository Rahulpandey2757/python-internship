"""Task 6: Online Quiz Platform (Flask + SQLite). Run: pip install flask && python app.py"""
import os, sqlite3
from flask import Flask, g, redirect, render_template_string, request, url_for, abort
from jinja2 import DictLoader

app = Flask(__name__)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quiz.db")

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
    c.executescript("""
    CREATE TABLE IF NOT EXISTS quizzes(id INTEGER PRIMARY KEY, title TEXT, description TEXT);
    CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY, quiz_id INTEGER, text TEXT,
        a TEXT, b TEXT, c TEXT, d TEXT, correct TEXT);
    CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY, quiz_id INTEGER, name TEXT, score INTEGER, total INTEGER);
    """)
    if not c.execute("SELECT 1 FROM quizzes").fetchone():
        c.execute("INSERT INTO quizzes VALUES(1,'Python Basics','Test your Python knowledge')")
        qs = [("Which keyword defines a function?", "func", "def", "function", "lambda", "B"),
              ("Which type is immutable?", "list", "dict", "tuple", "set", "C"),
              ("What does len('abc') return?", "2", "3", "4", "Error", "B"),
              ("Which symbol starts a comment?", "//", "#", "--", "/*", "B")]
        c.executemany("INSERT INTO questions(quiz_id,text,a,b,c,d,correct) VALUES(1,?,?,?,?,?,?)", qs)
    c.commit(); c.close()

BASE = """<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>QuizHub</title><style>
body{font-family:Arial;background:#eef3fb;margin:0}nav{background:#3f51b5;padding:14px 24px}
nav a{color:#fff;text-decoration:none;margin-right:18px}main{max-width:700px;margin:24px auto;padding:0 16px}
.card{background:#fff;padding:18px 22px;margin-bottom:14px;border-radius:8px;box-shadow:0 1px 3px #0002}
input[type=text],textarea{width:100%;padding:8px;margin:6px 0 12px;box-sizing:border-box}
button,.btn{background:#3f51b5;color:#fff;border:0;padding:9px 18px;border-radius:4px;cursor:pointer;text-decoration:none}
label.opt{display:block;padding:6px 0}.ok{color:#2e7d32}.bad{color:#c62828}table{width:100%;border-collapse:collapse}td,th{padding:6px;border-bottom:1px solid #ddd;text-align:left}
</style></head><body><nav><a href="/">🧠 QuizHub</a><a href="/">Quizzes</a><a href="/create">Create quiz</a></nav><main>{% block body %}{% endblock %}</main></body></html>"""

HOME = """{% extends 'base' %}{% block body %}<h1>Available quizzes</h1>
{% for q in quizzes %}<div class=card><h2>{{ q.title }}</h2><p>{{ q.description }}</p>
<a class=btn href="{{ url_for('take', id=q.id) }}">Start</a> <a href="{{ url_for('board', id=q.id) }}">Leaderboard</a></div>{% endfor %}{% endblock %}"""

TAKE = """{% extends 'base' %}{% block body %}<h1>{{ quiz.title }}</h1><form method=post>
<div class=card>Your name: <input type=text name=name required></div>
{% for q in questions %}<div class=card><b>{{ loop.index }}. {{ q.text }}</b>
{% for k in 'abcd' %}<label class=opt><input type=radio name="q{{ q.id }}" value="{{ k.upper() }}" required> {{ q[k] }}</label>{% endfor %}</div>{% endfor %}
<button>Submit</button></form>{% endblock %}"""

RESULT = """{% extends 'base' %}{% block body %}<div class=card><h1>{{ name }}, you scored {{ score }}/{{ total }} ({{ pct }}%)</h1></div>
{% for r in review %}<div class=card><b>{{ r.q.text }}</b><br>
{% if r.ok %}<span class=ok>✔ Correct: {{ r.q[r.q.correct.lower()] }}</span>{% else %}
<span class=bad>✘ You chose {{ r.chosen }}: {{ r.q[r.chosen.lower()] }}</span><br><span class=ok>Correct: {{ r.q[r.q.correct.lower()] }}</span>{% endif %}</div>{% endfor %}
<a class=btn href="{{ url_for('board', id=quiz.id) }}">Leaderboard</a> <a href="{{ url_for('take', id=quiz.id) }}">Retry</a>{% endblock %}"""

BOARD = """{% extends 'base' %}{% block body %}<h1>{{ quiz.title }} - Leaderboard</h1><div class=card><table>
<tr><th>#</th><th>Name</th><th>Score</th></tr>{% for r in rows %}<tr><td>{{ loop.index }}</td><td>{{ r.name }}</td><td>{{ r.score }}/{{ r.total }}</td></tr>
{% else %}<tr><td colspan=3>No attempts yet.</td></tr>{% endfor %}</table></div>{% endblock %}"""

CREATE = """{% extends 'base' %}{% block body %}<h1>Create a quiz</h1>{% if error %}<p class=bad>{{ error }}</p>{% endif %}
<form method=post><div class=card><label>Title</label><input type=text name=title required value="{{ title }}">
<label>Description</label><input type=text name=description value="{{ description }}">
<label>Questions - one per line: <code>Question | A | B | C | D | correct letter</code></label>
<textarea name=questions rows=8 required placeholder="Capital of France? | Rome | Paris | Madrid | Berlin | B">{{ questions }}</textarea>
<button>Create</button></div></form>{% endblock %}"""

app.jinja_loader = DictLoader({"base": BASE, "home": HOME, "take": TAKE, "result": RESULT, "board": BOARD, "create": CREATE})

def render(_tpl, **kw):
    return render_template_string(app.jinja_loader.get_source(app.jinja_env, _tpl)[0], **kw)

def get_quiz(id):
    return db().execute("SELECT * FROM quizzes WHERE id=?", (id,)).fetchone() or abort(404)

@app.route("/")
def home(): return render("home", quizzes=db().execute("SELECT * FROM quizzes").fetchall())

@app.route("/quiz/<int:id>", methods=["GET", "POST"])
def take(id):
    quiz = get_quiz(id)
    qs = db().execute("SELECT * FROM questions WHERE quiz_id=?", (id,)).fetchall()
    if request.method == "GET": return render("take", quiz=quiz, questions=qs)
    score, review = 0, []
    for q in qs:
        chosen = request.form.get(f"q{q['id']}", "")
        ok = chosen == q["correct"]; score += ok
        review.append({"q": q, "chosen": chosen or "A", "ok": ok})
    name = request.form["name"].strip()[:30] or "Anonymous"
    db().execute("INSERT INTO results(quiz_id,name,score,total) VALUES(?,?,?,?)", (id, name, score, len(qs)))
    db().commit()
    return render("result", quiz=quiz, name=name, score=score, total=len(qs),
                  pct=round(100 * score / max(len(qs), 1)), review=review)

@app.route("/leaderboard/<int:id>")
def board(id):
    rows = db().execute("SELECT * FROM results WHERE quiz_id=? ORDER BY score DESC, id LIMIT 20", (id,)).fetchall()
    return render("board", quiz=get_quiz(id), rows=rows)

@app.route("/create", methods=["GET", "POST"])
def create():
    ctx = dict(error=None, title="", description="", questions="")
    if request.method == "POST":
        ctx.update(title=request.form["title"], description=request.form["description"], questions=request.form["questions"])
        parsed = []
        for n, line in enumerate(filter(None, (l.strip() for l in ctx["questions"].splitlines())), 1):
            p = [x.strip() for x in line.split("|")]
            if len(p) != 6 or p[5].upper() not in "ABCD" or len(p[5]) != 1:
                ctx["error"] = f"Line {n} must be: Question | A | B | C | D | correct letter"; break
            parsed.append((*p[:5], p[5].upper()))
        else:
            cur = db().execute("INSERT INTO quizzes(title,description) VALUES(?,?)", (ctx["title"], ctx["description"]))
            db().executemany("INSERT INTO questions(quiz_id,text,a,b,c,d,correct) VALUES(?,?,?,?,?,?,?)",
                             [(cur.lastrowid, *q) for q in parsed])
            db().commit(); return redirect(url_for("home"))
    return render("create", **ctx)

if __name__ == "__main__":
    init(); app.run(debug=True)
