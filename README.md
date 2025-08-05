# Snackwatch 🍿

A live snack store management system built with Flask. Perfect for office snack bars, events, or small retail operations.

## Features

- 🛒 **Customer Interface**: Browse snacks, add to cart, place orders
- 🔧 **Admin Panel**: Manage orders, update stock, toggle store status
- 📱 **Responsive**: Works on desktop and mobile devices
- 🛡️ **Secure**: Environment-based configuration, input validation

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/your-username/Snackwatch.git
   cd Snackwatch
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Run the application**:
   ```bash
   python app/app.py
   ```

4. **Access the application**:
   - **Store**: http://localhost:5000
   - **Admin**: http://localhost:5000/admin (use password from .env)

## Configuration

Create a `.env` file from `.env.example` and update:

- `FLASK_SECRET_KEY`: Change this for security
- `ADMIN_PASSWORD`: Set your admin password
- `FLASK_ENV`: Set to `production` for production use

## Usage

### For Customers
1. Browse available snacks
2. Add items to cart
3. Checkout with name and pickup preference

### For Admins
1. Login at `/admin`
2. View and complete orders
3. Manage stock levels at `/admin/stock`
4. Toggle store open/closed status

## License

MIT License - feel free to use and modify!
