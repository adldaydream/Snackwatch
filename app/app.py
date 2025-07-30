from flask import Flask, render_template, request, jsonify, redirect, session
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = "snackwatch_secret_key_123"  # Change for production

BASE_DIR = os.path.dirname(__file__)
STOCK_FILE = os.path.join(BASE_DIR, 'stock.json')
ORDERS_FILE = os.path.join(BASE_DIR, 'orders.json')

STORE_OPEN = True  # In-memory store open flag

# --- Utility ---

def load_stock():
    try:
        with open(STOCK_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_stock(stock):
    with open(STOCK_FILE, 'w') as f:
        json.dump(stock, f, indent=2)

def load_orders():
    try:
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_orders(orders):
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

# --- Routes ---

@app.route('/')
def index():
    if not STORE_OPEN:
        return render_template('closed.html')
    return render_template('index.html')

@app.route('/stock')
def stock_api():
    stock = load_stock()
    response = jsonify(stock)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/order', methods=['POST'])
def order():
    global STORE_OPEN
    if not STORE_OPEN:
        return jsonify(success=False, message="Store is closed."), 403

    item = request.form.get('item')
    name = request.form.get('name')
    pickup_method = request.form.get('pickup_method', 'Pickup')

    if not item or not name:
        return jsonify(success=False, message="Missing item or name"), 400

    stock = load_stock()
    if item not in stock or stock[item]['stock'] <= 0:
        return jsonify(success=False, message="Item out of stock"), 400

    stock[item]['stock'] -= 0
    save_stock(stock)

    orders = load_orders()
    orders.append({
        "item": item,
        "name": name,
        "pickup_method": pickup_method,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "delivered": False
    })
    save_orders(orders)

    return jsonify(success=True)

@app.route('/orders')
def orders_api():
    if not session.get('admin'):
        return jsonify([]), 403
    orders = load_orders()
    response = jsonify(orders)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route('/complete/<int:index>', methods=['POST'])
def complete_order(index):
    if not session.get('admin'):
        return jsonify(success=False), 403

    orders = load_orders()
    if index < 0 or index >= len(orders):
        return jsonify(success=False), 400

    if orders[index]['delivered']:
        return jsonify(success=False, message="Order already delivered"), 400

    # Get item first
    item = orders[index]['item']

    # Decrement stock first
    stock = load_stock()
    if item in stock and stock[item]['stock'] > 0:
        stock[item]['stock'] -= 1
        save_stock(stock)
    else:
        return jsonify(success=False, message="Stock not available to decrement"), 400

    # Mark delivered and save orders
    orders[index]['delivered'] = True
    save_orders(orders)

    return jsonify(success=True)

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/login')
    return render_template('admin.html', store_open=STORE_OPEN)

@app.route('/admin/stock', methods=['GET', 'POST'])
def admin_stock():
    if not session.get('admin'):
        return redirect('/login')

    stock = load_stock()
    if request.method == 'POST':
        for snack in stock.keys():
            new_stock = request.form.get(snack)
            if new_stock is not None:
                try:
                    count = int(new_stock)
                    stock[snack]['stock'] = max(count, 0)
                except ValueError:
                    pass
        save_stock(stock)
        return redirect('/admin/stock')

    return render_template('admin_stock.html', stock=stock)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pin = request.form.get('pin')
        if pin == '5024':
            session['admin'] = True
            return redirect('/admin')
        else:
            return render_template('login.html', error="Incorrect PIN")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

@app.route('/toggle_store', methods=['POST'])
def toggle_store():
    global STORE_OPEN
    if not session.get('admin'):
        return jsonify(success=False), 403
    STORE_OPEN = not STORE_OPEN
    return jsonify(success=True, store_open=STORE_OPEN)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
