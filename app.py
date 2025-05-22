from flask import Flask, redirect, url_for, request, flash, render_template, session, jsonify
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, Text, ForeignKey, Float, DateTime, Boolean, Numeric
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

# Base configuration
app = Flask(__name__)
bootstrap = Bootstrap5(app)

app.config['SECRET_KEY'] = 'rseceret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restautant_pos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add datetime now function to templates
@app.context_processor
def utility_processor():
    def now():
        return datetime.now()
    return dict(now=now)

# Database setup - use standard SQLAlchemy setup
db = SQLAlchemy(app)

# Models
class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Use string reference for relationship to avoid circular imports
    users = db.relationship('User', back_populates='role')
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    active = db.Column(db.Boolean, default=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    last_login = db.Column(db.DateTime, default=datetime.now)
    
    role = db.relationship('Role', back_populates='users')
    orders = db.relationship('Order', back_populates='user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, default=0)
    
    menu_items = db.relationship('MenuItem', back_populates='category')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    available = db.Column(db.Boolean, default=True)
    
    category = db.relationship('Category', back_populates='menu_items')
    order_items = db.relationship('OrderItem', back_populates='menu_item')
    recipe_items = db.relationship('RecipeItem', back_populates='menu_item')
    
    @property
    def margin(self):
        if self.price > 0 and self.cost > 0:
            return round(((self.price - self.cost) / self.price) * 100)
        return 0
    
    def __repr__(self):
        return f'<MenuItem {self.name}>'

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    current_quantity = db.Column(db.Float, default=0)
    unit = db.Column(db.String(20), nullable=False)
    min_quantity = db.Column(db.Float, default=0)
    max_quantity = db.Column(db.Float, default=0)
    
    recipe_items = db.relationship('RecipeItem', back_populates='ingredient')
    supplier_items = db.relationship('SupplierItem', back_populates='ingredient')
    
    @property
    def status(self):
        if self.current_quantity < self.min_quantity:
            return "LOW"
        else:
            return "OK"
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'

class RecipeItem(db.Model):
    __tablename__ = 'recipe_items'
    
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'))
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'))
    quantity = db.Column(db.Float, nullable=False)
    
    menu_item = db.relationship('MenuItem', back_populates='recipe_items')
    ingredient = db.relationship('Ingredient', back_populates='recipe_items')
    
    def __repr__(self):
        return f'<RecipeItem {self.menu_item.name} - {self.ingredient.name}>'

class Table(db.Model):
    __tablename__ = 'tables'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    seats = db.Column(db.Integer, default=2)
    occupied = db.Column(db.Boolean, default=False)
    
    orders = db.relationship('Order', back_populates='table')
    
    def __repr__(self):
        return f'<Table {self.name}>'

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='open')  # open, in_progress, ready, completed, paid
    total_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    table = db.relationship('Table', back_populates='orders')
    user = db.relationship('User', back_populates='orders')
    order_items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payment = db.relationship('Payment', back_populates='order', uselist=False)
    
    def calculate_total(self):
        self.total_amount = sum(item.subtotal for item in self.order_items)
        return self.total_amount
    
    def __repr__(self):
        return f'<Order #{self.id}>'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    order = db.relationship('Order', back_populates='order_items')
    menu_item = db.relationship('MenuItem', back_populates='order_items')
    
    @property
    def subtotal(self):
        return self.price * self.quantity
    
    def __repr__(self):
        return f'<OrderItem {self.menu_item.name} x{self.quantity}>'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), unique=True)
    amount = db.Column(db.Float, nullable=False)
    payment_type = db.Column(db.String(20), nullable=False)  # cash, credit, debit
    payment_status = db.Column(db.String(20), default='pending')  # pending, completed
    payment_date = db.Column(db.DateTime, default=datetime.now)
    
    order = db.relationship('Order', back_populates='payment')
    
    def __repr__(self):
        return f'<Payment ${self.amount} for Order #{self.order_id}>'

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    address = db.Column(db.Text, nullable=True)
    last_order = db.Column(db.DateTime, nullable=True)
    
    supplier_items = db.relationship('SupplierItem', back_populates='supplier')
    
    def __repr__(self):
        return f'<Supplier {self.name}>'

class SupplierItem(db.Model):
    __tablename__ = 'supplier_items'
    
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'))
    
    supplier = db.relationship('Supplier', back_populates='supplier_items')
    ingredient = db.relationship('Ingredient', back_populates='supplier_items')
    
    def __repr__(self):
        return f'<SupplierItem {self.supplier.name} - {self.ingredient.name}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.now()
            db.session.commit()
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated and current_user.role.name != 'admin':
        flash('Only administrators can register new users', 'warning')
        return redirect(url_for('dashboard'))
    
    roles = Role.query.all()
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role_id = request.form.get('role')
        
        # Validation
        user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
        if user_exists:
            flash('Username or email already exists', 'danger')
            return render_template('register.html', roles=roles)
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html', roles=roles)
        
        # Create new user
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            phone=phone,
            role_id=role_id
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('User registered successfully', 'success')
        return redirect(url_for('users'))
    
    return render_template('register.html', roles=roles)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role_name = current_user.role.name
    
    if role_name == 'waiter':
        tables = Table.query.all()
        open_orders = Order.query.filter_by(status='open').count()
        active_orders = Order.query.filter(Order.status.in_(['open', 'in_progress', 'ready'])).all()
        categories = Category.query.order_by(Category.display_order).all()
        
        # Add a status color property to each order
        for order in active_orders:
            if order.status == 'open':
                order.status_color = 'primary'
            elif order.status == 'in_progress':
                order.status_color = 'warning'
            elif order.status == 'ready':
                order.status_color = 'success'
            else:
                order.status_color = 'secondary'
        
        return render_template('waiter_dashboard.html', tables=tables, open_orders=open_orders, 
                              active_orders=active_orders, categories=categories)
    
    elif role_name == 'chef' or role_name == 'kitchen':
        pending_orders = Order.query.filter(Order.status.in_(['open', 'in_progress'])).all()
        return render_template('kitchen_dashboard.html', pending_orders=pending_orders)
    
    elif role_name == 'manager' or role_name == 'admin':
        today = datetime.now().date()
        today_sales = db.session.query(Payment).filter(Payment.payment_date >= today).all()
        total_sales = sum(payment.amount for payment in today_sales)
        
        low_stock_items = Ingredient.query.filter(Ingredient.current_quantity < Ingredient.min_quantity).count()
        
        return render_template('manager_dashboard.html', 
                               total_sales=total_sales,
                               low_stock_items=low_stock_items)
    
    else:  # cashier
        # Get orders ready for payment
        open_orders = Order.query.filter(Order.status.in_(['ready', 'completed'])).all()
        
        # Get tables
        tables = Table.query.all()
        
        # Get menu items by category
        categories = Category.query.order_by(Category.display_order).all()
        menu_items = MenuItem.query.filter_by(available=True).all()
        
        # Create a dictionary of menu items by category for easy access in the template
        menu_by_category = {}
        for category in categories:
            menu_by_category[category.id] = [item for item in menu_items if item.category_id == category.id]
            
        # Get default selected order if available
        selected_order = None
        if open_orders:
            selected_order = open_orders[0]
            
        return render_template('cashier_dashboard.html', 
                               open_orders=open_orders,
                               tables=tables,
                               categories=categories,
                               menu_by_category=menu_by_category,
                               menu_items=menu_items,
                               selected_order=selected_order)

# User Management Routes
@app.route('/users')
@login_required
def users():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role.name != 'admin':
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    roles = Role.query.all()
    
    if request.method == 'POST':
        return redirect(url_for('users'))
    
    return render_template('add_user.html', roles=roles)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if current_user.role.name != 'admin':
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.role_id = request.form.get('role')
        user.active = 'active' in request.form
        
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('users'))
    
    return render_template('edit_user.html', user=user, roles=roles)

@app.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    if current_user.role.name != 'admin':
        flash('Permission denied', 'danger')
        return redirect(url_for('users'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deactivating your own account
    if user.id == current_user.id:
        flash('You cannot deactivate your own account', 'danger')
        return redirect(url_for('users'))
    
    # Toggle active status
    user.active = not user.active
    db.session.commit()
    
    status_message = 'activated' if user.active else 'deactivated'
    flash(f'User {user.full_name} {status_message} successfully', 'success')
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
def reset_user_password(user_id):
    if current_user.role.name != 'admin':
        flash('Permission denied', 'danger')
        return redirect(url_for('users'))
    
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not new_password or not confirm_password:
        flash('Both password fields are required', 'danger')
        return redirect(url_for('users'))
    
    if new_password != confirm_password:
        flash('Passwords do not match', 'danger')
        return redirect(url_for('users'))
    
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'Password for {user.full_name} reset successfully', 'success')
    return redirect(url_for('users'))

# Menu Management Routes
@app.route('/menu')
@login_required
def menu():
    categories = Category.query.order_by(Category.display_order).all()
    menu_items = MenuItem.query.all()
    return render_template('menu.html', categories=categories, menu_items=menu_items)

@app.route('/menu/add', methods=['GET', 'POST'])
@login_required
def add_menu_item():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('menu'))
    
    categories = Category.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        cost = request.form.get('cost')
        category_id = request.form.get('category_id')
        available = 'available' in request.form
        
        menu_item = MenuItem(
            name=name,
            description=description,
            price=price,
            cost=cost,
            category_id=category_id,
            available=available
        )
        
        db.session.add(menu_item)
        db.session.commit()
        
        flash('Menu item added successfully', 'success')
        return redirect(url_for('menu'))
    
    return render_template('add_menu_item.html', categories=categories)

@app.route('/menu/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_menu_item(item_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('menu'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    categories = Category.query.all()
    
    if request.method == 'POST':
        menu_item.name = request.form.get('name')
        menu_item.description = request.form.get('description')
        menu_item.price = request.form.get('price')
        menu_item.cost = request.form.get('cost')
        menu_item.category_id = request.form.get('category_id')
        menu_item.available = 'available' in request.form
        
        db.session.commit()
        flash('Menu item updated successfully', 'success')
        return redirect(url_for('menu'))
    
    return render_template('edit_menu_item.html', menu_item=menu_item, categories=categories)

@app.route('/menu/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_menu_item(item_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('menu'))
    
    menu_item = MenuItem.query.get_or_404(item_id)
    
    try:
        # Check if the menu item has associated order items before deleting
        if not menu_item.order_items:
            # Delete associated recipe items first
            RecipeItem.query.filter_by(menu_item_id=item_id).delete()
            
            # Delete the menu item
            db.session.delete(menu_item)
            db.session.commit()
            flash(f'{menu_item.name} deleted successfully', 'success')
        else:
            flash(f'Cannot delete {menu_item.name} as it has associated orders', 'danger')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting menu item: {str(e)}', 'danger')
    
    return redirect(url_for('menu'))

@app.route('/categories')
@login_required
def categories():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    categories = Category.query.order_by(Category.display_order).all()
    return render_template('categories.html', categories=categories)

@app.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('categories'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        display_order = request.form.get('display_order', 0)
        
        category = Category(
            name=name,
            description=description,
            display_order=display_order
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully', 'success')
        return redirect(url_for('categories'))
    
    return render_template('add_category.html')

@app.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('categories'))
    
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.display_order = request.form.get('display_order')
        
        db.session.commit()
        flash('Category updated successfully', 'success')
        return redirect(url_for('categories'))
    
    return render_template('edit_category.html', category=category)

@app.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('categories'))
    
    category = Category.query.get_or_404(category_id)
    
    try:
        # Delete all menu items in this category
        menu_items = MenuItem.query.filter_by(category_id=category_id).all()
        
        # First delete associated recipe items for each menu item
        for item in menu_items:
            RecipeItem.query.filter_by(menu_item_id=item.id).delete()
        
        # Then delete the menu items
        for item in menu_items:
            db.session.delete(item)
        
        # Finally delete the category
        db.session.delete(category)
        db.session.commit()
        
        flash(f'Category "{category.name}" and all its menu items have been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')
    
    return redirect(url_for('categories'))

@app.route('/suppliers')
@login_required
def suppliers():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('suppliers'))
    
    ingredients = Ingredient.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        ingredient_ids = request.form.getlist('ingredients')
        
        # Create new supplier
        supplier = Supplier(
            name=name,
            contact=contact,
            phone=phone,
            email=email,
            address=address
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        # Associate with ingredients
        for ingredient_id in ingredient_ids:
            supplier_item = SupplierItem(
                supplier_id=supplier.id,
                ingredient_id=ingredient_id
            )
            db.session.add(supplier_item)
        
        db.session.commit()
        flash('Supplier added successfully', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('add_supplier.html', ingredients=ingredients)

@app.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('suppliers'))
    
    supplier = Supplier.query.get_or_404(supplier_id)
    ingredients = Ingredient.query.all()
    
    if request.method == 'POST':
        supplier.name = request.form.get('name')
        supplier.contact = request.form.get('contact')
        supplier.phone = request.form.get('phone')
        supplier.email = request.form.get('email')
        supplier.address = request.form.get('address')
        
        # Update ingredients
        ingredient_ids = request.form.getlist('ingredients')
        
        # Remove existing ingredient connections
        SupplierItem.query.filter_by(supplier_id=supplier_id).delete()
        
        # Add new connections
        for ingredient_id in ingredient_ids:
            supplier_item = SupplierItem(
                supplier_id=supplier.id,
                ingredient_id=ingredient_id
            )
            db.session.add(supplier_item)
        
        db.session.commit()
        flash('Supplier updated successfully', 'success')
        return redirect(url_for('suppliers'))
    
    return render_template('edit_supplier.html', supplier=supplier, ingredients=ingredients)

@app.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('suppliers'))
    
    supplier = Supplier.query.get_or_404(supplier_id)
    
    try:
        # Delete all supplier-ingredient connections
        SupplierItem.query.filter_by(supplier_id=supplier_id).delete()
        
        # Delete the supplier
        db.session.delete(supplier)
        db.session.commit()
        
        flash(f'Supplier "{supplier.name}" has been deleted', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'danger')
    
    return redirect(url_for('suppliers'))

@app.route('/suppliers/<int:supplier_id>/order', methods=['POST'])
@login_required
def place_supplier_order(supplier_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('suppliers'))
    
    supplier = Supplier.query.get_or_404(supplier_id)
    
    if request.method == 'POST':
        ingredient_ids = request.form.getlist('ingredient_ids[]')
        quantities = request.form.getlist('quantities[]')
        notes = request.form.get('notes', '')
        
        if not ingredient_ids:
            flash('No ingredients were selected', 'warning')
            return redirect(url_for('suppliers'))
        
        # Update supplier's last order date
        supplier.last_order = datetime.now()
        
        # Process each ingredient
        ordered_items = 0
        for i, ingredient_id in enumerate(ingredient_ids):
            if i < len(quantities):
                quantity = float(quantities[i] or 0)
                if quantity > 0:
                    # Get the ingredient
                    ingredient = Ingredient.query.get(ingredient_id)
                    if ingredient:
                        # Update ingredient quantity
                        ingredient.current_quantity += quantity
                        ordered_items += 1
        
        db.session.commit()
        
        if ordered_items > 0:
            flash(f'Order placed successfully with {supplier.name} for {ordered_items} ingredient(s)', 'success')
        else:
            flash('No valid quantities were provided for the order', 'warning')
    
    return redirect(url_for('suppliers'))

@app.route('/ingredients')
@login_required
def ingredients():
    if current_user.role.name not in ['admin', 'manager', 'chef']:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    ingredients = Ingredient.query.all()
    return render_template('ingredients.html', ingredients=ingredients)

@app.route('/ingredients/add', methods=['GET', 'POST'])
@login_required
def add_ingredient():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('ingredients'))
    
    suppliers = Supplier.query.all()
    
    if request.method == 'POST':
        name = request.form.get('name')
        current_quantity = float(request.form.get('current_quantity', 0))
        unit = request.form.get('unit')
        min_quantity = float(request.form.get('min_quantity', 0))
        max_quantity = float(request.form.get('max_quantity', 0))
        supplier_ids = request.form.getlist('suppliers')
        
        # Create new ingredient
        ingredient = Ingredient(
            name=name,
            current_quantity=current_quantity,
            unit=unit,
            min_quantity=min_quantity,
            max_quantity=max_quantity
        )
        
        db.session.add(ingredient)
        db.session.commit()
        
        # Associate with suppliers
        for supplier_id in supplier_ids:
            supplier_item = SupplierItem(
                supplier_id=supplier_id,
                ingredient_id=ingredient.id
            )
            db.session.add(supplier_item)
        
        db.session.commit()
        flash('Ingredient added successfully', 'success')
        return redirect(url_for('ingredients'))
    
    return render_template('add_ingredient.html', suppliers=suppliers)

@app.route('/ingredients/<int:ingredient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ingredient(ingredient_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('ingredients'))
    
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    suppliers = Supplier.query.all()
    
    if request.method == 'POST':
        ingredient.name = request.form.get('name')
        ingredient.current_quantity = float(request.form.get('current_quantity', 0))
        ingredient.unit = request.form.get('unit')
        ingredient.min_quantity = float(request.form.get('min_quantity', 0))
        ingredient.max_quantity = float(request.form.get('max_quantity', 0))
        
        # Update suppliers
        supplier_ids = request.form.getlist('suppliers')
        
        # Remove existing supplier connections
        SupplierItem.query.filter_by(ingredient_id=ingredient_id).delete()
        
        # Add new connections
        for supplier_id in supplier_ids:
            supplier_item = SupplierItem(
                supplier_id=supplier_id,
                ingredient_id=ingredient.id
            )
            db.session.add(supplier_item)
        
        db.session.commit()
        flash('Ingredient updated successfully', 'success')
        return redirect(url_for('ingredients'))
    
    return render_template('edit_ingredient.html', ingredient=ingredient, suppliers=suppliers)

@app.route('/ingredients/<int:ingredient_id>/adjust', methods=['POST'])
@login_required
def adjust_ingredient_stock(ingredient_id):
    if current_user.role.name not in ['admin', 'manager', 'chef']:
        flash('Permission denied', 'danger')
        return redirect(url_for('ingredients'))
    
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    if request.method == 'POST':
        quantity = float(request.form.get('quantity', 0))
        adjustment_type = request.form.get('adjustment_type')
        reason = request.form.get('reason', '')
        
        if adjustment_type == 'add':
            ingredient.current_quantity += quantity
        elif adjustment_type == 'remove':
            if quantity > ingredient.current_quantity:
                flash(f'Cannot remove {quantity} {ingredient.unit} from stock. Current quantity is {ingredient.current_quantity} {ingredient.unit}', 'danger')
                return redirect(url_for('ingredients'))
            ingredient.current_quantity -= quantity
        elif adjustment_type == 'set':
            ingredient.current_quantity = quantity
        
        db.session.commit()
        flash(f'Stock for {ingredient.name} has been adjusted successfully', 'success')
    
    return redirect(url_for('ingredients'))

@app.route('/ingredients/<int:ingredient_id>/order', methods=['POST'])
@login_required
def order_ingredient(ingredient_id):
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('ingredients'))
    
    ingredient = Ingredient.query.get_or_404(ingredient_id)
    
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        quantity = float(request.form.get('quantity', 0))
        notes = request.form.get('notes', '')
        
        supplier = Supplier.query.get_or_404(supplier_id)
        supplier.last_order = datetime.now()
        
        # In a real system, you would create an order record
        # For now, just update the ingredient quantity
        ingredient.current_quantity += quantity
        
        db.session.commit()
        flash(f'Order for {quantity} {ingredient.unit} of {ingredient.name} from {supplier.name} has been placed', 'success')
    
    return redirect(url_for('ingredients'))

@app.route('/reports')
@login_required
def reports():
    if current_user.role.name not in ['admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('reports.html')

# Order Management Routes for Waiters
@app.route('/orders/create', methods=['POST'])
@login_required
def create_order():
    if current_user.role.name != 'waiter':
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    table_id = request.form.get('table_id')
    item_ids = request.form.getlist('item_ids[]')
    quantities = request.form.getlist('quantities[]')
    notes = request.form.getlist('notes[]')
    
    if not table_id or not item_ids:
        flash('Invalid order data', 'danger')
        return redirect(url_for('dashboard'))
    
    # Create new order
    order = Order(
        table_id=table_id,
        user_id=current_user.id,
        status='open',
        created_at=datetime.now()
    )
    
    db.session.add(order)
    db.session.commit()
    
    # Add order items
    for i, item_id in enumerate(item_ids):
        if i < len(quantities):
            quantity = int(quantities[i])
            menu_item = MenuItem.query.get_or_404(item_id)
            
            if quantity > 0:
                note = notes[i] if i < len(notes) else ''
                
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item_id,
                    quantity=quantity,
                    price=menu_item.price,
                    notes=note
                )
                db.session.add(order_item)
    
    # Update table status
    table = Table.query.get_or_404(table_id)
    table.occupied = True
    
    # Calculate the order total
    order.calculate_total()
    
    db.session.commit()
    
    flash('Order created successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/orders/modify', methods=['POST'])
@login_required
def modify_order():
    if current_user.role.name != 'waiter':
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    order_id = request.form.get('order_id')
    item_ids = request.form.getlist('item_ids[]')
    item_quantities = request.form.getlist('item_quantities[]')
    
    if not order_id or not item_ids:
        flash('Invalid order data', 'danger')
        return redirect(url_for('dashboard'))
    
    order = Order.query.get_or_404(order_id)
    
    # Update existing items or remove if quantity is 0
    for i, item_id in enumerate(item_ids):
        if i < len(item_quantities):
            quantity = int(item_quantities[i])
            
            # Find the order item
            order_item = OrderItem.query.filter_by(
                order_id=order_id, 
                menu_item_id=item_id
            ).first()
            
            if order_item:
                if quantity <= 0:
                    # Remove the item if quantity is 0
                    db.session.delete(order_item)
                else:
                    # Update the quantity
                    order_item.quantity = quantity
    
    # Calculate the updated total
    order.calculate_total()
    db.session.commit()
    
    flash('Order modified successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/orders/request-bill', methods=['POST'])
@login_required
def request_bill():
    if current_user.role.name != 'waiter':
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    order_id = request.form.get('order_id')
    
    if not order_id:
        flash('Invalid order data', 'danger')
        return redirect(url_for('dashboard'))
    
    order = Order.query.get_or_404(order_id)
    
    # Update order status to mark it's ready for payment
    order.status = 'completed'
    db.session.commit()
    
    flash('Bill requested successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/orders/<int:order_id>/details')
@login_required
def get_order_details(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Define status color
    status_color = 'secondary'
    if order.status == 'open':
        status_color = 'primary'
    elif order.status == 'in_progress':
        status_color = 'warning'
    elif order.status == 'ready':
        status_color = 'success'
    
    # Build the response data
    data = {
        'id': order.id,
        'table_id': order.table_id,
        'table_name': order.table.name,
        'status': order.status,
        'status_color': status_color,
        'total': order.total_amount,
        'created_time': order.created_at.strftime('%Y-%m-%d %H:%M'),
        'items': []
    }
    
    for item in order.order_items:
        data['items'].append({
            'id': item.menu_item_id,
            'name': item.menu_item.name,
            'price': item.price,
            'quantity': item.quantity,
            'notes': item.notes,
            'subtotal': item.subtotal
        })
    
    return jsonify(data)

# Kitchen Management Routes
@app.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    if current_user.role.name not in ['chef', 'kitchen']:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    
    # Validate that the status change is allowed
    if new_status in ['in_progress', 'ready']:
        if (order.status == 'open' and new_status == 'in_progress') or \
           (order.status == 'in_progress' and new_status == 'ready'):
            order.status = new_status
            order.updated_at = datetime.now()
            db.session.commit()
            flash(f'Order #{order.id} status updated to {new_status}', 'success')
        else:
            flash(f'Invalid status change from {order.status} to {new_status}', 'danger')
    else:
        flash('Invalid status', 'danger')
    
    return redirect(url_for('dashboard'))

# Cashier Management Routes
@app.route('/orders/<int:order_id>/payment', methods=['GET', 'POST'])
@login_required
def process_payment(order_id):
    if current_user.role.name not in ['cashier', 'admin', 'manager']:
        flash('Permission denied', 'danger')
        return redirect(url_for('dashboard'))
    
    order = Order.query.get_or_404(order_id)
    
    # Check if payment already exists
    if order.payment:
        flash('Payment for this order has already been processed', 'warning')
        return redirect(url_for('dashboard'))
    
    # Check if order is in a payable state
    if order.status not in ['ready', 'completed']:
        flash('Order is not ready for payment', 'warning')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        payment_type = request.form.get('payment_type')
        amount = float(request.form.get('amount', order.total_amount))
        
        # Create payment record
        payment = Payment(
            order_id=order.id,
            amount=amount,
            payment_type=payment_type,
            payment_status='completed',
            payment_date=datetime.now()
        )
        
        db.session.add(payment)
        
        # Update order status to paid
        order.status = 'paid'
        
        # Free up the table
        if order.table:
            order.table.occupied = False
        
        db.session.commit()
        flash(f'Payment processed successfully for Order #{order.id}', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('process_payment.html', order=order)

# API Endpoints
@app.route('/api/menu-items')
@login_required
def api_menu_items():
    category_id = request.args.get('category_id', type=int)
    
    if category_id:
        menu_items = MenuItem.query.filter_by(category_id=category_id, available=True).all()
    else:
        menu_items = MenuItem.query.filter_by(available=True).all()
    
    items_data = []
    for item in menu_items:
        items_data.append({
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'description': item.description
        })
    
    return jsonify({'items': items_data})

if __name__ == '__main__':
    app.run(debug=True)