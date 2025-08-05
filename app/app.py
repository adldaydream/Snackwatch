from flask import Flask, render_template, request, jsonify, redirect, session
from datetime import datetime
import json
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key_change_this')

BASE_DIR = os.path.dirname(__file__)
STOCK_FILE = os.path.join(BASE_DIR, 'stock.json')
ORDERS_FILE = os.path.join(BASE_DIR, 'orders.json')

STORE_OPEN = True  # In-memory store open flag
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# --- Utility ---

def sanitize_input(text, max_length=100):
    """Sanitize user input to prevent XSS and limit length"""
    if not text:
        return ""
    # Remove HTML tags and limit length
    text = re.sub('<[^<]+?>', '', str(text))
    return text.strip()[:max_length]

def validate_quantity(quantity):
    """Validate quantity is a positive integer"""
    try:
        qty = int(quantity)
        return max(0, min(qty, 99))  # Cap at 99 items
    except (ValueError, TypeError):
        return 0

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

    # Handle both single item and multiple items (cart) orders
    data = request.get_json() if request.is_json else request.form
    
    name = sanitize_input(data.get('name'), 50)
    pickup_method = sanitize_input(data.get('pickup_method', 'Pickup'), 20)
    
    if not name or len(name.strip()) < 1:
        return jsonify(success=False, message="Please provide a valid name"), 400

    # Validate pickup method
    if pickup_method not in ['Pickup', 'Delivery']:
        pickup_method = 'Pickup'

    # Handle multiple items from cart
    if 'cart' in data:
        cart = data.get('cart')
        if not cart or not isinstance(cart, dict):
            return jsonify(success=False, message="Invalid cart data"), 400
        
        # Validate cart items and quantities
        validated_cart = {}
        stock = load_stock()
        
        for item, quantity in cart.items():
            item = sanitize_input(item, 50)
            quantity = validate_quantity(quantity)
            
            if not item or quantity <= 0:
                continue
                
            if item not in stock:
                return jsonify(success=False, message=f"Item '{item}' not found"), 400
                
            if stock[item]['stock'] < quantity:
                return jsonify(success=False, message=f"Insufficient stock for {item}"), 400
                
            validated_cart[item] = quantity
        
        if not validated_cart:
            return jsonify(success=False, message="No valid items in cart"), 400
        
        # Reserve stock for all items
        for item, quantity in validated_cart.items():
            stock[item]['stock'] -= quantity
        save_stock(stock)

        # Create orders for each item
        orders = load_orders()
        order_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for item, quantity in validated_cart.items():
            for _ in range(quantity):
                orders.append({
                    "item": item,
                    "name": name,
                    "pickup_method": pickup_method,
                    "time": order_time,
                    "delivered": False
                })
        save_orders(orders)
        
    else:
        # Handle single item (legacy support)
        item = sanitize_input(data.get('item'), 50)
        if not item:
            return jsonify(success=False, message="Missing item"), 400

        stock = load_stock()
        if item not in stock:
            return jsonify(success=False, message="Item not found"), 400
            
        if stock[item]['stock'] <= 0:
            return jsonify(success=False, message="Item out of stock"), 400

        # Reserve stock immediately when order is placed
        stock[item]['stock'] -= 1
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

    # Stock was already decremented when order was placed, just mark as delivered
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
        if pin == ADMIN_PASSWORD:
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
