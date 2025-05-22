from app import app, db, Role, User, Category, MenuItem, Ingredient, RecipeItem, Supplier, SupplierItem, Table
from werkzeug.security import generate_password_hash
from datetime import datetime

def populate_database():
    print("Starting database population...")
    
    with app.app_context():
        # Create roles if they don't exist
        roles = {
            'admin': 'Administrator with full access',
            'manager': 'Restaurant manager with access to most features',
            'waiter': 'Waiter who takes orders',
            'chef': 'Kitchen staff who prepares food',
            'cashier': 'Staff who handles payments'
        }
        
        role_objects = {}
        for role_name, description in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, description=description)
                db.session.add(role)
                print(f"Added role: {role_name}")
            role_objects[role_name] = role
        
        db.session.commit()
        
        # Create sample users for each role
        sample_users = [
            {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'first_name': 'Admin', 'last_name': 'User', 'email': 'admin@restaurant.com'},
            {'username': 'manager', 'password': 'manager123', 'role': 'manager', 'first_name': 'Mike', 'last_name': 'Johnson', 'email': 'mike@restaurant.com'},
            {'username': 'waiter1', 'password': 'waiter123', 'role': 'waiter', 'first_name': 'William', 'last_name': 'Smith', 'email': 'william@restaurant.com'},
            {'username': 'waiter2', 'password': 'waiter123', 'role': 'waiter', 'first_name': 'Sarah', 'last_name': 'Davis', 'email': 'sarah@restaurant.com'},
            {'username': 'chef1', 'password': 'chef123', 'role': 'chef', 'first_name': 'Carlos', 'last_name': 'Rodriguez', 'email': 'carlos@restaurant.com'},
            {'username': 'chef2', 'password': 'chef123', 'role': 'chef', 'first_name': 'Maria', 'last_name': 'Garcia', 'email': 'maria@restaurant.com'},
            {'username': 'cashier1', 'password': 'cashier123', 'role': 'cashier', 'first_name': 'Chris', 'last_name': 'Lee', 'email': 'chris@restaurant.com'},
        ]
        
        for user_data in sample_users:
            # Skip if user already exists
            if User.query.filter_by(username=user_data['username']).first():
                print(f"User {user_data['username']} already exists, skipping")
                continue
                
            role = Role.query.filter_by(name=user_data['role']).first()
            user = User(
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                email=user_data['email'],
                role_id=role.id,
                active=True,
                phone='555-' + ''.join([str(i) for i in range(7)])
            )
            user.password_hash = generate_password_hash(user_data['password'])
            db.session.add(user)
            print(f"Added user: {user.username} ({user_data['role']})")
        
        db.session.commit()
        
        # Ensure categories exist
        categories = {
            'Starters': {'display_order': 0},
            'Main Dishes': {'display_order': 1},
            'Sides': {'display_order': 2},
            'Drinks': {'display_order': 3},
            'Desserts': {'display_order': 4}
        }
        
        category_objects = {}
        for cat_name, cat_data in categories.items():
            category = Category.query.filter_by(name=cat_name).first()
            if not category:
                category = Category(name=cat_name, display_order=cat_data['display_order'])
                db.session.add(category)
                print(f"Added category: {cat_name}")
            category_objects[cat_name] = category
        
        db.session.commit()
        
        # Add menu items
        menu_items = [
            # Starters
            {'name': 'Bruschetta', 'description': 'Toasted bread topped with tomatoes, garlic, and basil', 'price': 8.99, 'cost': 2.50, 'category': 'Starters', 'available': True},
            {'name': 'Mozzarella Sticks', 'description': 'Breaded and fried mozzarella cheese sticks', 'price': 7.99, 'cost': 3.00, 'category': 'Starters', 'available': True},
            {'name': 'Garlic Bread', 'description': 'Toasted bread with garlic butter', 'price': 5.99, 'cost': 1.50, 'category': 'Starters', 'available': True},
            {'name': 'Calamari', 'description': 'Fried squid rings with marinara sauce', 'price': 10.99, 'cost': 4.50, 'category': 'Starters', 'available': True},
            
            # Main Dishes
            {'name': 'Margherita Pizza', 'description': 'Classic pizza with tomato sauce, mozzarella, and basil', 'price': 14.99, 'cost': 5.00, 'category': 'Main Dishes', 'available': True},
            {'name': 'Pepperoni Pizza', 'description': 'Pizza with tomato sauce, mozzarella, and pepperoni', 'price': 16.99, 'cost': 6.00, 'category': 'Main Dishes', 'available': True},
            {'name': 'Spaghetti Bolognese', 'description': 'Pasta with meat sauce', 'price': 13.99, 'cost': 4.50, 'category': 'Main Dishes', 'available': True},
            {'name': 'Chicken Alfredo', 'description': 'Fettuccine pasta with creamy alfredo sauce and grilled chicken', 'price': 15.99, 'cost': 5.50, 'category': 'Main Dishes', 'available': True},
            {'name': 'Grilled Salmon', 'description': 'Salmon fillet with vegetables and lemon butter sauce', 'price': 19.99, 'cost': 8.00, 'category': 'Main Dishes', 'available': True},
            {'name': 'Beef Burger', 'description': 'Beef patty with lettuce, tomato, cheese, and special sauce', 'price': 12.99, 'cost': 4.00, 'category': 'Main Dishes', 'available': True},
            
            # Sides
            {'name': 'French Fries', 'description': 'Crispy fried potatoes', 'price': 4.99, 'cost': 1.00, 'category': 'Sides', 'available': True},
            {'name': 'Onion Rings', 'description': 'Battered and fried onion rings', 'price': 5.99, 'cost': 1.50, 'category': 'Sides', 'available': True},
            {'name': 'Side Salad', 'description': 'Mixed greens with choice of dressing', 'price': 4.99, 'cost': 1.50, 'category': 'Sides', 'available': True},
            
            # Drinks
            {'name': 'Soda', 'description': 'Cola, Sprite, or Fanta', 'price': 2.99, 'cost': 0.50, 'category': 'Drinks', 'available': True},
            {'name': 'Iced Tea', 'description': 'Freshly brewed iced tea', 'price': 2.99, 'cost': 0.40, 'category': 'Drinks', 'available': True},
            {'name': 'Coffee', 'description': 'Regular or decaf coffee', 'price': 3.49, 'cost': 0.60, 'category': 'Drinks', 'available': True},
            {'name': 'Beer', 'description': 'Domestic or imported beer', 'price': 5.99, 'cost': 2.00, 'category': 'Drinks', 'available': True},
            {'name': 'Wine', 'description': 'Red or white wine', 'price': 7.99, 'cost': 3.00, 'category': 'Drinks', 'available': True},
            
            # Desserts
            {'name': 'Chocolate Cake', 'description': 'Rich chocolate cake with chocolate frosting', 'price': 6.99, 'cost': 2.00, 'category': 'Desserts', 'available': True},
            {'name': 'Cheesecake', 'description': 'Classic New York style cheesecake', 'price': 7.99, 'cost': 2.50, 'category': 'Desserts', 'available': True},
            {'name': 'Tiramisu', 'description': 'Italian coffee-flavored dessert', 'price': 8.99, 'cost': 3.00, 'category': 'Desserts', 'available': True},
            {'name': 'Ice Cream', 'description': 'Vanilla, chocolate, or strawberry', 'price': 4.99, 'cost': 1.50, 'category': 'Desserts', 'available': True},
        ]
        
        menu_item_objects = {}
        for item_data in menu_items:
            # Check if menu item already exists
            item = MenuItem.query.filter_by(name=item_data['name']).first()
            if not item:
                category = Category.query.filter_by(name=item_data['category']).first()
                item = MenuItem(
                    name=item_data['name'],
                    description=item_data['description'],
                    price=item_data['price'],
                    cost=item_data['cost'],
                    category_id=category.id,
                    available=item_data['available']
                )
                db.session.add(item)
                print(f"Added menu item: {item.name}")
            menu_item_objects[item_data['name']] = item
        
        db.session.commit()
        
        # Add ingredients
        ingredients = [
            {'name': 'Tomatoes', 'unit': 'kg', 'current_quantity': 10, 'min_quantity': 5, 'max_quantity': 20},
            {'name': 'Mozzarella Cheese', 'unit': 'kg', 'current_quantity': 8, 'min_quantity': 3, 'max_quantity': 15},
            {'name': 'Flour', 'unit': 'kg', 'current_quantity': 25, 'min_quantity': 10, 'max_quantity': 50},
            {'name': 'Bread', 'unit': 'loaf', 'current_quantity': 12, 'min_quantity': 5, 'max_quantity': 20},
            {'name': 'Garlic', 'unit': 'kg', 'current_quantity': 2, 'min_quantity': 1, 'max_quantity': 5},
            {'name': 'Basil', 'unit': 'bunch', 'current_quantity': 5, 'min_quantity': 2, 'max_quantity': 10},
            {'name': 'Ground Beef', 'unit': 'kg', 'current_quantity': 15, 'min_quantity': 5, 'max_quantity': 25},
            {'name': 'Chicken Breast', 'unit': 'kg', 'current_quantity': 12, 'min_quantity': 5, 'max_quantity': 20},
            {'name': 'Salmon', 'unit': 'kg', 'current_quantity': 8, 'min_quantity': 3, 'max_quantity': 15},
            {'name': 'Pasta', 'unit': 'kg', 'current_quantity': 20, 'min_quantity': 8, 'max_quantity': 30},
            {'name': 'Alfredo Sauce', 'unit': 'liter', 'current_quantity': 5, 'min_quantity': 2, 'max_quantity': 10},
            {'name': 'Pizza Sauce', 'unit': 'liter', 'current_quantity': 6, 'min_quantity': 3, 'max_quantity': 12},
            {'name': 'Pepperoni', 'unit': 'kg', 'current_quantity': 4, 'min_quantity': 2, 'max_quantity': 8},
            {'name': 'Potatoes', 'unit': 'kg', 'current_quantity': 25, 'min_quantity': 10, 'max_quantity': 50},
            {'name': 'Onions', 'unit': 'kg', 'current_quantity': 15, 'min_quantity': 5, 'max_quantity': 30},
            {'name': 'Lettuce', 'unit': 'kg', 'current_quantity': 6, 'min_quantity': 3, 'max_quantity': 12},
            {'name': 'Beef Patties', 'unit': 'kg', 'current_quantity': 10, 'min_quantity': 5, 'max_quantity': 20},
            {'name': 'Burger Buns', 'unit': 'pack', 'current_quantity': 8, 'min_quantity': 4, 'max_quantity': 16},
            {'name': 'Chocolate', 'unit': 'kg', 'current_quantity': 5, 'min_quantity': 2, 'max_quantity': 10},
            {'name': 'Cream Cheese', 'unit': 'kg', 'current_quantity': 3, 'min_quantity': 1, 'max_quantity': 6},
            {'name': 'Sugar', 'unit': 'kg', 'current_quantity': 20, 'min_quantity': 10, 'max_quantity': 40},
            {'name': 'Coffee Beans', 'unit': 'kg', 'current_quantity': 4, 'min_quantity': 2, 'max_quantity': 8},
            {'name': 'Soda Syrup', 'unit': 'liter', 'current_quantity': 15, 'min_quantity': 5, 'max_quantity': 30},
            {'name': 'Beer Kegs', 'unit': 'keg', 'current_quantity': 3, 'min_quantity': 1, 'max_quantity': 5},
            {'name': 'Wine Bottles', 'unit': 'bottle', 'current_quantity': 24, 'min_quantity': 12, 'max_quantity': 48},
        ]
        
        ingredient_objects = {}
        for ing_data in ingredients:
            # Check if ingredient already exists
            ingredient = Ingredient.query.filter_by(name=ing_data['name']).first()
            if not ingredient:
                ingredient = Ingredient(
                    name=ing_data['name'],
                    unit=ing_data['unit'],
                    current_quantity=ing_data['current_quantity'],
                    min_quantity=ing_data['min_quantity'],
                    max_quantity=ing_data['max_quantity']
                )
                db.session.add(ingredient)
                print(f"Added ingredient: {ingredient.name}")
            ingredient_objects[ing_data['name']] = ingredient
        
        db.session.commit()
        
        # Add suppliers
        suppliers_data = [
            {'name': 'Fresh Foods Inc.', 'contact': 'John Miller', 'phone': '555-123-4567', 'email': 'contact@freshfoods.com', 'address': '123 Produce Lane, Anytown, ST 12345'},
            {'name': 'Quality Meats', 'contact': 'Sarah Johnson', 'phone': '555-234-5678', 'email': 'orders@qualitymeats.com', 'address': '456 Butcher St, Meatville, ST 67890'},
            {'name': 'Seafood Direct', 'contact': 'Michael Brown', 'phone': '555-345-6789', 'email': 'sales@seafooddirect.com', 'address': '789 Ocean Ave, Fisher, ST 45678'},
            {'name': 'Bakery Supplies Co.', 'contact': 'Lisa Davis', 'phone': '555-456-7890', 'email': 'info@bakerysupplies.com', 'address': '321 Flour St, Breadville, ST 23456'},
            {'name': 'Beverage Distributors', 'contact': 'Robert Wilson', 'phone': '555-567-8901', 'email': 'orders@beveragedist.com', 'address': '654 Drink Blvd, Liquidtown, ST 78901'},
        ]
        
        supplier_objects = {}
        for supp_data in suppliers_data:
            # Check if supplier already exists
            supplier = Supplier.query.filter_by(name=supp_data['name']).first()
            if not supplier:
                supplier = Supplier(
                    name=supp_data['name'],
                    contact=supp_data['contact'],
                    phone=supp_data['phone'],
                    email=supp_data['email'],
                    address=supp_data['address']
                )
                db.session.add(supplier)
                print(f"Added supplier: {supplier.name}")
            supplier_objects[supp_data['name']] = supplier
        
        db.session.commit()
        
        # Add supplier-ingredient connections
        supplier_ingredients = [
            {'supplier': 'Fresh Foods Inc.', 'ingredients': ['Tomatoes', 'Garlic', 'Basil', 'Lettuce', 'Onions', 'Potatoes']},
            {'supplier': 'Quality Meats', 'ingredients': ['Ground Beef', 'Chicken Breast', 'Beef Patties', 'Pepperoni']},
            {'supplier': 'Seafood Direct', 'ingredients': ['Salmon']},
            {'supplier': 'Bakery Supplies Co.', 'ingredients': ['Flour', 'Bread', 'Burger Buns', 'Sugar', 'Chocolate', 'Cream Cheese']},
            {'supplier': 'Beverage Distributors', 'ingredients': ['Coffee Beans', 'Soda Syrup', 'Beer Kegs', 'Wine Bottles']},
        ]
        
        for si_link in supplier_ingredients:
            supplier = Supplier.query.filter_by(name=si_link['supplier']).first()
            for ing_name in si_link['ingredients']:
                ingredient = Ingredient.query.filter_by(name=ing_name).first()
                
                # Check if connection already exists
                existing = SupplierItem.query.filter_by(supplier_id=supplier.id, ingredient_id=ingredient.id).first()
                if not existing:
                    supplier_item = SupplierItem(
                        supplier_id=supplier.id,
                        ingredient_id=ingredient.id
                    )
                    db.session.add(supplier_item)
                    print(f"Linked supplier {supplier.name} with ingredient {ingredient.name}")
        
        db.session.commit()
        
        # Link menu items to ingredients (recipe items)
        recipes = [
            {'item': 'Bruschetta', 'ingredients': [('Bread', 0.1), ('Tomatoes', 0.15), ('Garlic', 0.02), ('Basil', 0.5)]},
            {'item': 'Garlic Bread', 'ingredients': [('Bread', 0.2), ('Garlic', 0.05)]},
            {'item': 'Margherita Pizza', 'ingredients': [('Flour', 0.3), ('Tomatoes', 0.2), ('Mozzarella Cheese', 0.2), ('Basil', 0.3)]},
            {'item': 'Pepperoni Pizza', 'ingredients': [('Flour', 0.3), ('Tomatoes', 0.15), ('Mozzarella Cheese', 0.2), ('Pepperoni', 0.1)]},
            {'item': 'Spaghetti Bolognese', 'ingredients': [('Pasta', 0.2), ('Ground Beef', 0.15), ('Tomatoes', 0.1), ('Onions', 0.05)]},
            {'item': 'Chicken Alfredo', 'ingredients': [('Pasta', 0.2), ('Chicken Breast', 0.2), ('Alfredo Sauce', 0.15)]},
            {'item': 'Grilled Salmon', 'ingredients': [('Salmon', 0.25), ('Lettuce', 0.1)]},
            {'item': 'Beef Burger', 'ingredients': [('Beef Patties', 0.2), ('Burger Buns', 1), ('Lettuce', 0.05), ('Tomatoes', 0.05), ('Onions', 0.03)]},
            {'item': 'French Fries', 'ingredients': [('Potatoes', 0.2)]},
            {'item': 'Onion Rings', 'ingredients': [('Onions', 0.15), ('Flour', 0.05)]},
            {'item': 'Chocolate Cake', 'ingredients': [('Flour', 0.1), ('Sugar', 0.15), ('Chocolate', 0.1)]},
            {'item': 'Cheesecake', 'ingredients': [('Cream Cheese', 0.15), ('Sugar', 0.1)]},
            {'item': 'Coffee', 'ingredients': [('Coffee Beans', 0.02)]},
            {'item': 'Soda', 'ingredients': [('Soda Syrup', 0.05)]},
            {'item': 'Beer', 'ingredients': [('Beer Kegs', 0.03)]},
            {'item': 'Wine', 'ingredients': [('Wine Bottles', 0.17)]},
        ]
        
        for recipe in recipes:
            menu_item = MenuItem.query.filter_by(name=recipe['item']).first()
            for ing_name, quantity in recipe['ingredients']:
                ingredient = Ingredient.query.filter_by(name=ing_name).first()
                
                # Check if recipe item already exists
                existing = RecipeItem.query.filter_by(menu_item_id=menu_item.id, ingredient_id=ingredient.id).first()
                if not existing:
                    recipe_item = RecipeItem(
                        menu_item_id=menu_item.id,
                        ingredient_id=ingredient.id,
                        quantity=quantity
                    )
                    db.session.add(recipe_item)
                    print(f"Added recipe: {quantity} {ingredient.unit} of {ingredient.name} for {menu_item.name}")
        
        db.session.commit()
        print("Database successfully populated!")

if __name__ == '__main__':
    populate_database() 