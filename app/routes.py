from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime
from app.models import db, User, Product, Stock, Customer, Sale, SaleItem
from sqlalchemy import func, desc

def register_routes(app):
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return render_template('landing.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            # Validation
            if not username or not email or not password:
                flash('All fields are required.', 'danger')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html')
            
            if User.query.filter_by(username=username).first():
                flash('Username already exists.', 'danger')
                return render_template('register.html')
            
            if User.query.filter_by(email=email).first():
                flash('Email already exists.', 'danger')
                return render_template('register.html')
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Please enter username and password.', 'danger')
                return render_template('login.html')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        from datetime import datetime, date, timedelta
        
        # Total Sales
        total_sales = db.session.query(func.sum(Sale.total_amount)).scalar() or 0
        
        # Total Profit
        total_profit = db.session.query(func.sum(Sale.total_profit)).scalar() or 0
        
        # Total Stock (sum of all stock quantities)
        total_stock = db.session.query(func.sum(Stock.quantity)).scalar() or 0
        
        # Business Worth - Calculate inventory value
        # Inventory value at cost (what we invested)
        inventory_value_at_cost = 0
        # Inventory value at selling price (potential revenue)
        inventory_value_at_price = 0
        
        products_with_inventory = Product.query.all()
        for product in products_with_inventory:
            stock_quantity = product.get_total_stock()
            inventory_value_at_cost += product.cost * stock_quantity
            inventory_value_at_price += product.price * stock_quantity
        
        # Total business worth = Inventory at cost + Total profit earned
        business_worth = inventory_value_at_cost + total_profit
        # Potential business worth if all inventory is sold
        potential_business_worth = inventory_value_at_price
        
        # Daily Sales - Today
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = datetime.combine(date.today(), datetime.max.time())
        
        daily_sales_amount = db.session.query(func.sum(Sale.total_amount)).filter(
            Sale.created_at >= today_start,
            Sale.created_at <= today_end
        ).scalar() or 0
        
        daily_profit = db.session.query(func.sum(Sale.total_profit)).filter(
            Sale.created_at >= today_start,
            Sale.created_at <= today_end
        ).scalar() or 0
        
        daily_sales_count = Sale.query.filter(
            Sale.created_at >= today_start,
            Sale.created_at <= today_end
        ).count()
        
        # Sales for the last 7 days for chart
        seven_days_ago = today_start - timedelta(days=6)
        daily_sales_data = db.session.query(
            func.date(Sale.created_at).label('sale_date'),
            func.sum(Sale.total_amount).label('daily_total')
        ).filter(
            Sale.created_at >= seven_days_ago
        ).group_by(func.date(Sale.created_at)).order_by('sale_date').all()
        
        # Format for chart (fill missing days with 0)
        chart_labels = []
        chart_data = []
        current_date = seven_days_ago.date()
        today_date = date.today()
        
        # Create a dictionary from query results
        sales_dict = {str(item.sale_date): float(item.daily_total or 0) for item in daily_sales_data}
        
        while current_date <= today_date:
            date_str = str(current_date)
            chart_labels.append(current_date.strftime('%b %d'))
            chart_data.append(float(sales_dict.get(date_str, 0)))
            current_date += timedelta(days=1)
        
        # Today's sales list
        today_sales = Sale.query.filter(
            Sale.created_at >= today_start,
            Sale.created_at <= today_end
        ).order_by(desc(Sale.created_at)).all()
        
        # Top selling products
        top_products = db.session.query(
            Product.id,
            Product.name,
            func.sum(SaleItem.quantity).label('total_sold')
        ).join(SaleItem).group_by(Product.id, Product.name).order_by(desc('total_sold')).limit(5).all()
        
        # Sales per product for chart
        sales_per_product_query = db.session.query(
            Product.name,
            func.sum(SaleItem.quantity * SaleItem.unit_price).label('total_revenue')
        ).join(SaleItem).group_by(Product.id, Product.name).all()
        
        # Convert to list of lists for JSON serialization
        sales_per_product = [[item[0], float(item[1] or 0)] for item in sales_per_product_query]
        
        # Recent sales
        recent_sales = Sale.query.order_by(desc(Sale.created_at)).limit(5).all()
        
        return render_template('dashboard.html',
                             total_sales=total_sales,
                             total_profit=total_profit,
                             total_stock=total_stock,
                             daily_sales_amount=daily_sales_amount,
                             daily_profit=daily_profit,
                             daily_sales_count=daily_sales_count,
                             today_sales=today_sales,
                             chart_labels=chart_labels,
                             chart_data=chart_data,
                             top_products=top_products,
                             sales_per_product=sales_per_product,
                             recent_sales=recent_sales,
                             business_worth=business_worth,
                             inventory_value_at_cost=inventory_value_at_cost,
                             inventory_value_at_price=inventory_value_at_price,
                             potential_business_worth=potential_business_worth)
    
    # Product Routes
    @app.route('/products')
    @login_required
    def products():
        products = Product.query.all()
        products_with_stock = []
        for product in products:
            total_stock = product.get_total_stock()
            products_with_stock.append({
                'product': product,
                'stock': total_stock
            })
        return render_template('products.html', products_with_stock=products_with_stock)
    
    @app.route('/products/add', methods=['POST'])
    @login_required
    def add_product():
        try:
            name = request.form.get('name')
            cost = float(request.form.get('cost'))
            price = float(request.form.get('price'))
            
            if not name or cost < 0 or price < 0:
                flash('Invalid input. All fields required and values must be non-negative.', 'danger')
                return redirect(url_for('products'))
            
            if price < cost:
                flash('Price must be greater than or equal to cost.', 'warning')
            
            product = Product(name=name, cost=cost, price=price)
            db.session.add(product)
            db.session.commit()
            
            flash('Product added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
        
        return redirect(url_for('products'))
    
    @app.route('/products/edit/<int:id>', methods=['POST'])
    @login_required
    def edit_product(id):
        try:
            product = Product.query.get_or_404(id)
            product.name = request.form.get('name')
            product.cost = float(request.form.get('cost'))
            product.price = float(request.form.get('price'))
            
            if product.cost < 0 or product.price < 0:
                flash('Cost and price must be non-negative.', 'danger')
                return redirect(url_for('products'))
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
        
        return redirect(url_for('products'))
    
    @app.route('/products/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_product(id):
        try:
            product = Product.query.get_or_404(id)
            db.session.delete(product)
            db.session.commit()
            flash('Product deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting product: {str(e)}', 'danger')
        
        return redirect(url_for('products'))
    
    # Stock Routes
    @app.route('/stock')
    @login_required
    def stock():
        stock_items = Stock.query.join(Product).order_by(Stock.restock_date.desc()).all()
        products = Product.query.all()
        products_with_stock = []
        for product in products:
            total_stock = product.get_total_stock()
            products_with_stock.append({
                'product': product,
                'stock': total_stock
            })
        return render_template('stock.html', stock_items=stock_items, products_with_stock=products_with_stock)
    
    @app.route('/stock/add', methods=['POST'])
    @login_required
    def add_stock():
        try:
            product_id = int(request.form.get('product_id'))
            quantity = int(request.form.get('quantity'))
            
            if quantity <= 0:
                flash('Quantity must be greater than 0.', 'danger')
                return redirect(url_for('stock'))
            
            product = Product.query.get_or_404(product_id)
            
            stock_item = Stock(product_id=product_id, quantity=quantity)
            db.session.add(stock_item)
            db.session.commit()
            
            flash('Stock added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding stock: {str(e)}', 'danger')
        
        return redirect(url_for('stock'))
    
    @app.route('/stock/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_stock(id):
        try:
            stock_item = Stock.query.get_or_404(id)
            db.session.delete(stock_item)
            db.session.commit()
            flash('Stock entry deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting stock: {str(e)}', 'danger')
        
        return redirect(url_for('stock'))
    
    # Customer Routes
    @app.route('/customers')
    @login_required
    def customers():
        customers = Customer.query.order_by(Customer.created_at.desc()).all()
        return render_template('customers.html', customers=customers)
    
    @app.route('/customers/add', methods=['POST'])
    @login_required
    def add_customer():
        try:
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            
            if not name:
                flash('Name is required.', 'danger')
                return redirect(url_for('customers'))
            
            if email and '@' not in email:
                flash('Invalid email format.', 'danger')
                return redirect(url_for('customers'))
            
            customer = Customer(name=name, phone=phone, email=email)
            db.session.add(customer)
            db.session.commit()
            
            flash('Customer added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'danger')
        
        return redirect(url_for('customers'))
    
    @app.route('/customers/edit/<int:id>', methods=['POST'])
    @login_required
    def edit_customer(id):
        try:
            customer = Customer.query.get_or_404(id)
            customer.name = request.form.get('name')
            customer.phone = request.form.get('phone')
            customer.email = request.form.get('email')
            
            if not customer.name:
                flash('Name is required.', 'danger')
                return redirect(url_for('customers'))
            
            if customer.email and '@' not in customer.email:
                flash('Invalid email format.', 'danger')
                return redirect(url_for('customers'))
            
            db.session.commit()
            flash('Customer updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating customer: {str(e)}', 'danger')
        
        return redirect(url_for('customers'))
    
    @app.route('/customers/delete/<int:id>', methods=['POST'])
    @login_required
    def delete_customer(id):
        try:
            customer = Customer.query.get_or_404(id)
            db.session.delete(customer)
            db.session.commit()
            flash('Customer deleted successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting customer: {str(e)}', 'danger')
        
        return redirect(url_for('customers'))
    
    # Sales Routes
    @app.route('/sales')
    @login_required
    def sales():
        sales_list = Sale.query.order_by(desc(Sale.created_at)).all()
        return render_template('sales.html', sales_list=sales_list)
    
    @app.route('/sales/add', methods=['POST'])
    @login_required
    def add_sale():
        try:
            data = request.get_json()
            customer_id = data.get('customer_id') if data.get('customer_id') else None
            items = data.get('items', [])
            
            if not items:
                return jsonify({'success': False, 'message': 'No items in sale.'}), 400
            
            # Validate stock and calculate totals
            total_amount = 0
            total_profit = 0
            sale_items_data = []
            
            for item in items:
                product_id = int(item['product_id'])
                quantity = int(item['quantity'])
                
                if quantity <= 0:
                    return jsonify({'success': False, 'message': f'Invalid quantity for product {product_id}.'}), 400
                
                product = Product.query.get_or_404(product_id)
                available_stock = product.get_total_stock()
                
                if quantity > available_stock:
                    return jsonify({'success': False, 'message': f'Insufficient stock for {product.name}. Available: {available_stock}'}), 400
                
                unit_price = product.price
                total_price = unit_price * quantity
                profit = (product.price - product.cost) * quantity
                
                total_amount += total_price
                total_profit += profit
                
                sale_items_data.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
            
            # Create sale
            sale = Sale(customer_id=customer_id, total_amount=total_amount, total_profit=total_profit)
            db.session.add(sale)
            db.session.flush()  # Get sale.id
            
            # Create sale items and update stock
            for item_data in sale_items_data:
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=item_data['product'].id,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['total_price']
                )
                db.session.add(sale_item)
                
                # Decrease stock (FIFO - First In First Out)
                remaining = item_data['quantity']
                stock_entries = Stock.query.filter_by(product_id=item_data['product'].id).order_by(Stock.restock_date.asc()).all()
                
                for stock_entry in stock_entries:
                    if remaining <= 0:
                        break
                    if stock_entry.quantity <= remaining:
                        remaining -= stock_entry.quantity
                        db.session.delete(stock_entry)
                    else:
                        stock_entry.quantity -= remaining
                        remaining = 0
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Sale completed successfully!',
                'sale_id': sale.id
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    @app.route('/sales/<int:id>/receipt')
    @login_required
    def sale_receipt(id):
        sale = Sale.query.get_or_404(id)
        return render_template('receipt.html', sale=sale)
    
    @app.route('/api/products')
    @login_required
    def api_products():
        products = Product.query.all()
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'cost': product.cost,
                'stock': product.get_total_stock()
            })
        return jsonify(products_data)
    
    @app.route('/api/customers')
    @login_required
    def api_customers():
        customers = Customer.query.all()
        customers_data = []
        for customer in customers:
            customers_data.append({
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email
            })
        return jsonify(customers_data)

