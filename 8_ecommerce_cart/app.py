"""Task 8: E-commerce Shopping Cart (Flask + SQLite). Run: pip install flask && python app.py

SECURITY NOTE: Payment here is a SIMULATION. Card numbers are validated (Luhn) but never stored or logged.
For real payments, integrate a provider such as Stripe Checkout or Razorpay so card data never touches your server."""
import os, sqlite3, uuid
from flask import Flask, g, redirect, render_template_string, request, session, url_for, flash, abort
from jinja2 import DictLoader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shop.db")

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
    CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT, price REAL, stock INTEGER, emoji TEXT, description TEXT);
    CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, name TEXT, email TEXT, address TEXT, total REAL);
    CREATE TABLE IF NOT EXISTS order_items(order_id TEXT, product_id INTEGER, qty INTEGER, price REAL);""")
    if not c.execute("SELECT 1 FROM products").fetchone():
        c.executemany("INSERT INTO products(name,price,stock,emoji,description) VALUES(?,?,?,?,?)", [
            ("Wireless Mouse", 599, 25, "🖱", "Ergonomic 2.4GHz wireless mouse"),
            ("Mechanical Keyboard", 2499, 10, "⌨", "Blue-switch keyboard with backlight"),
            ("USB-C Hub", 1299, 15, "🔌", "7-in-1 hub with HDMI and card reader"),
            ("Laptop Stand", 899, 20, "💻", "Foldable aluminium stand"),
            ("Headphones", 1999, 12, "🎧", "Over-ear with noise isolation"),
            ("Webcam HD", 1499, 8, "📷", "1080p webcam with mic")])
    c.commit(); c.close()

BASE = """<!doctype html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>ShopEasy</title><style>
body{font-family:Arial;background:#fafafa;margin:0}nav{background:#232f3e;padding:14px 24px;display:flex}
nav a{color:#fff;text-decoration:none;margin-left:18px}nav .brand{margin:0 auto 0 0;font-size:1.2em;font-weight:bold}
main{max-width:900px;margin:24px auto;padding:0 16px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px}
.card{background:#fff;padding:18px;border-radius:8px;box-shadow:0 1px 3px #0002}.emoji{font-size:48px}
button,.btn{background:#ff9900;border:0;padding:8px 16px;border-radius:4px;cursor:pointer;text-decoration:none;color:#000}
input{padding:8px;margin:4px 0 12px;width:100%;box-sizing:border-box}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #ddd;text-align:left}
.flash{background:#fff3cd;padding:10px;border-radius:4px;margin-bottom:12px}.price{font-weight:bold;color:#b12704}input.qty{width:60px;margin:0}
</style></head><body><nav><a class=brand href="/">🛒 ShopEasy</a><a href="/">Products</a><a href="/cart">Cart ({{ cart_count }})</a></nav>
<main>{% for m in get_flashed_messages() %}<div class=flash>{{ m }}</div>{% endfor %}{% block body %}{% endblock %}</main></body></html>"""

HOME = """{% extends 'base' %}{% block body %}<h1>Products</h1><div class=grid>{% for p in products %}<div class=card>
<div class=emoji>{{ p.emoji }}</div><h3>{{ p.name }}</h3><p>{{ p.description }}</p><p class=price>₹{{ '%.0f'|format(p.price) }}</p>
{% if p.stock > 0 %}<form method=post action="{{ url_for('add', id=p.id) }}"><button>Add to cart</button></form>{% else %}<b>Out of stock</b>{% endif %}
</div>{% endfor %}</div>{% endblock %}"""

CART = """{% extends 'base' %}{% block body %}<h1>Your cart</h1>{% if items %}<form method=post action="{{ url_for('update') }}"><table>
<tr><th>Item</th><th>Price</th><th>Qty</th><th>Subtotal</th><th></th></tr>{% for i in items %}<tr><td>{{ i.p.emoji }} {{ i.p.name }}</td>
<td>₹{{ '%.0f'|format(i.p.price) }}</td><td><input class=qty type=number min=0 max="{{ i.p.stock }}" name="qty{{ i.p.id }}" value="{{ i.qty }}"></td>
<td>₹{{ '%.0f'|format(i.sub) }}</td><td><a href="{{ url_for('remove', id=i.p.id) }}">Remove</a></td></tr>{% endfor %}
<tr><th colspan=3>Total</th><th colspan=2 class=price>₹{{ '%.0f'|format(total) }}</th></tr></table><br>
<button>Update cart</button> <a class=btn href="{{ url_for('checkout') }}">Checkout →</a></form>
{% else %}<p>Your cart is empty. <a href="/">Browse products</a></p>{% endif %}{% endblock %}"""

CHECKOUT = """{% extends 'base' %}{% block body %}<h1>Checkout - ₹{{ '%.0f'|format(total) }}</h1><form method=post class=card autocomplete=off>
<label>Full name</label><input name=name required><label>Email</label><input type=email name=email required>
<label>Shipping address</label><input name=address required>
<label>Card number (demo: 4242 4242 4242 4242)</label><input name=card required inputmode=numeric>
<label>Expiry (MM/YY)</label><input name=exp required placeholder="12/30"><label>CVV</label><input name=cvv required type=password maxlength=4>
<button>Pay now (simulated)</button></form>{% endblock %}"""

SUCCESS = """{% extends 'base' %}{% block body %}<div class=card><h1>✅ Order confirmed</h1><p>Thanks {{ o.name }}! Order <b>{{ o.id }}</b> - total ₹{{ '%.0f'|format(o.total) }}.</p>
<p>A confirmation would be sent to {{ o.email }}.</p><a class=btn href="/">Continue shopping</a></div>{% endblock %}"""

app.jinja_loader = DictLoader({"base": BASE, "home": HOME, "cart": CART, "checkout": CHECKOUT, "success": SUCCESS})

def render(_tpl, **kw):
    return render_template_string(app.jinja_loader.get_source(app.jinja_env, _tpl)[0], **kw)

@app.context_processor
def inject():
    return {"cart_count": sum(session.get("cart", {}).values())}

def cart_items():
    items, total = [], 0
    for pid, qty in session.get("cart", {}).items():
        p = db().execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if p: items.append({"p": p, "qty": qty, "sub": p["price"] * qty}); total += p["price"] * qty
    return items, total

def luhn(num):
    digits = [int(d) for d in num][::-1]
    return len(digits) >= 13 and (sum(digits[0::2]) + sum(sum(divmod(2 * d, 10)) for d in digits[1::2])) % 10 == 0

@app.route("/")
def home(): return render("home", products=db().execute("SELECT * FROM products").fetchall())

@app.route("/add/<int:id>", methods=["POST"])
def add(id):
    p = db().execute("SELECT * FROM products WHERE id=?", (id,)).fetchone() or abort(404)
    cart = session.setdefault("cart", {})
    if cart.get(str(id), 0) < p["stock"]:
        cart[str(id)] = cart.get(str(id), 0) + 1; flash(f"Added {p['name']} to cart.")
    else: flash("No more stock available.")
    session.modified = True
    return redirect(request.referrer or url_for("home"))

@app.route("/cart")
def cart():
    items, total = cart_items(); return render("cart", items=items, total=total)

@app.route("/update", methods=["POST"])
def update():
    cart = session.get("cart", {})
    for pid in list(cart):
        try: q = int(request.form.get(f"qty{pid}", cart[pid]))
        except ValueError: continue
        p = db().execute("SELECT stock FROM products WHERE id=?", (pid,)).fetchone()
        if q <= 0 or not p: cart.pop(pid)
        else: cart[pid] = min(q, p["stock"])
    session.modified = True
    return redirect(url_for("cart"))

@app.route("/remove/<id>")
def remove(id):
    session.get("cart", {}).pop(id, None); session.modified = True
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total = cart_items()
    if not items: return redirect(url_for("cart"))
    if request.method == "POST":
        card = request.form["card"].replace(" ", "")
        if not (card.isdigit() and luhn(card)):
            flash("Payment failed: invalid card number."); return render("checkout", total=total)
        oid = uuid.uuid4().hex[:8].upper()
        db().execute("INSERT INTO orders VALUES(?,?,?,?,?)", (oid, request.form["name"], request.form["email"], request.form["address"], total))
        for i in items:
            db().execute("INSERT INTO order_items VALUES(?,?,?,?)", (oid, i["p"]["id"], i["qty"], i["p"]["price"]))
            db().execute("UPDATE products SET stock=stock-? WHERE id=?", (i["qty"], i["p"]["id"]))
        db().commit(); session.pop("cart", None)   # card data is discarded here, never stored
        return redirect(url_for("success", oid=oid))
    return render("checkout", total=total)

@app.route("/success/<oid>")
def success(oid):
    o = db().execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone() or abort(404)
    return render("success", o=o)

if __name__ == "__main__":
    init(); app.run(debug=True)
