# MyDuka POS - Point of Sale System

A full-featured Flask-based Point of Sale (POS) system with comprehensive inventory and sales management capabilities.

## Features

- **User Authentication**: Secure registration and login with password hashing
- **Product Management**: Add, edit, and delete products with cost and price tracking
- **Stock Management**: Separate stock tracking with automatic updates on sales
- **Customer Management**: Maintain customer database with contact information
- **Sales Management**: Batch/multiple product sales with automatic stock deduction
- **Dashboard**: Real-time statistics, charts, and sales analytics
- **Printable Receipts**: Generate receipts for sales transactions
- **Responsive UI**: Bootstrap 5 styling for all devices

## Project Structure

```
myduka_pos/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── models.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── products.html
│   │   ├── stock.html
│   │   ├── sales.html
│   │   ├── customers.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── receipt.html
│   └── static/
│       └── css/
│           └── style.css
├── config.py
├── run.py
└── requirements.txt
```

## Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd myduka_pos
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the application**
   - Open your browser and navigate to: `http://localhost:5000`
   - Register a new account or login with existing credentials

## Usage

1. **Registration/Login**: Create an account or login to access the system
2. **Add Products**: Go to Products section and add products with cost and selling price
3. **Manage Stock**: Add stock entries for products in the Stock section
4. **Add Customers**: Register customers in the Customers section
5. **Make Sales**: Create sales transactions with multiple products in the Sales section
6. **View Dashboard**: Check statistics and analytics on the dashboard

## Database

The application uses SQLite by default. The database file (`myduka_pos.db`) will be created automatically on first run.

To use a different database, modify the `SQLALCHEMY_DATABASE_URI` in `config.py`.

## Security Notes

- Change the `SECRET_KEY` in `config.py` for production use
- Passwords are hashed using Werkzeug's password hashing
- All routes are protected with Flask-Login authentication

## Technologies Used

- Flask 3.0.0
- Flask-SQLAlchemy
- Flask-Login
- Bootstrap 5
- Chart.js
- SQLite

## License

This project is open source and available for personal and commercial use.

