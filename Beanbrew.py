
import os
import sys
import json
import sqlite3
import datetime
import hashlib
import uuid
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# Initialize rich console for better CLI output
console = Console()

# Database initialization
def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect('beanbrew.db')
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        cost REAL NOT NULL,
        inventory INTEGER NOT NULL
    )
    ''')
    
    # Create orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        order_time TIMESTAMP NOT NULL,
        total REAL NOT NULL,
        payment_method TEXT NOT NULL,
        customer_id INTEGER
    )
    ''')
    
    # Create order_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        customizations TEXT,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    ''')
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT NOT NULL
    )
    ''')
    
    # Create customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        phone TEXT,
        points INTEGER DEFAULT 0,
        join_date TIMESTAMP NOT NULL
    )
    ''')
    
    # Create inventory_log table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        quantity_change INTEGER NOT NULL,
        reason TEXT NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def insert_sample_data():
    """Insert sample data for testing."""
    conn = sqlite3.connect('beanbrew.db')
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] > 0:
        return
    
    # Sample products
    products = [
        # Coffee
        ('Espresso', 'Coffee', 2.50, 0.70, 1000),
        ('Americano', 'Coffee', 3.00, 0.80, 1000),
        ('Cappuccino', 'Coffee', 3.50, 1.10, 1000),
        ('Latte', 'Coffee', 3.75, 1.20, 1000),
        ('Mocha', 'Coffee', 4.25, 1.50, 1000),
        ('Cold Brew', 'Coffee', 4.00, 1.30, 500),
        
        # Tea
        ('Green Tea', 'Tea', 2.75, 0.60, 500),
        ('English Breakfast', 'Tea', 2.75, 0.60, 500),
        ('Herbal Tea', 'Tea', 2.75, 0.60, 500),
        
        # Food
        ('Croissant', 'Bakery', 2.50, 1.00, 50),
        ('Chocolate Muffin', 'Bakery', 3.25, 1.20, 40),
        ('Bagel with Cream Cheese', 'Bakery', 3.50, 1.40, 35),
        ('Avocado Toast', 'Food', 6.50, 2.50, 20),
        ('Grilled Cheese Sandwich', 'Food', 5.75, 2.20, 25),
        
        # Merchandise
        ('Bean Brew Mug', 'Merchandise', 12.00, 5.00, 30),
        ('Whole Bean Coffee 12oz', 'Merchandise', 14.50, 6.00, 40)
    ]
    
    cursor.executemany("INSERT INTO products (name, category, price, cost, inventory) VALUES (?, ?, ?, ?, ?)", products)
    
    # Sample user (admin/admin)
    admin_password = hashlib.sha256("admin".encode()).hexdigest()
    cursor.execute("INSERT INTO users (username, password_hash, role, name) VALUES (?, ?, ?, ?)", 
                   ('admin', admin_password, 'admin', 'Admin User'))
    
    # Sample customers
    customers = [
        ('John Smith', 'john@example.com', '555-1234', 120, datetime.datetime.now().isoformat()),
        ('Sarah Johnson', 'sarah@example.com', '555-5678', 85, datetime.datetime.now().isoformat())
    ]
    
    cursor.executemany("INSERT INTO customers (name, email, phone, points, join_date) VALUES (?, ?, ?, ?, ?)", customers)
    
    conn.commit()
    conn.close()

class Authentication:
    """User authentication and management."""
    
    @staticmethod
    def login(username, password):
        """Authenticate a user."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("SELECT id, username, role, name FROM users WHERE username = ? AND password_hash = ?", 
                      (username, password_hash))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return {
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'name': user[3]
            }
        return None
    
    @staticmethod
    def create_user(username, password, role, name):
        """Create a new user."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            cursor.execute("INSERT INTO users (username, password_hash, role, name) VALUES (?, ?, ?, ?)",
                          (username, password_hash, role, name))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False


class InventoryManager:
    """Manages inventory and product information."""
    
    @staticmethod
    def get_all_products():
        """Get all products."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, category, price, inventory FROM products ORDER BY category, name")
        products = cursor.fetchall()
        
        conn.close()
        return products
    
    @staticmethod
    def get_products_by_category(category):
        """Get products filtered by category."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, category, price, inventory FROM products WHERE category = ? ORDER BY name",
                      (category,))
        products = cursor.fetchall()
        
        conn.close()
        return products
    
    @staticmethod
    def update_inventory(product_id, quantity_change, reason, user_id):
        """Update product inventory and log the change."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT inventory FROM products WHERE id = ?", (product_id,))
        current_inventory = cursor.fetchone()[0]
        
        new_inventory = current_inventory + quantity_change
        if new_inventory < 0:
            conn.close()
            return False, "Insufficient inventory"
        
        cursor.execute("UPDATE products SET inventory = ? WHERE id = ?", (new_inventory, product_id))
        
        # Log the inventory change
        cursor.execute("""
        INSERT INTO inventory_log (product_id, quantity_change, reason, timestamp, user_id) 
        VALUES (?, ?, ?, ?, ?)
        """, (product_id, quantity_change, reason, datetime.datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        return True, "Inventory updated successfully"
    
    @staticmethod
    def add_product(name, category, price, cost, inventory):
        """Add a new product."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO products (name, category, price, cost, inventory) 
        VALUES (?, ?, ?, ?, ?)
        """, (name, category, price, cost, inventory))
        
        conn.commit()
        conn.close()
        return True


class SalesProcessor:
    """Processes sales transactions."""
    
    @staticmethod
    def create_order(items, payment_method, customer_id=None):
        """
        Create a new order.
        
        Args:
            items: List of dictionaries with product_id, quantity, and customizations
            payment_method: String payment method (cash, credit, etc.)
            customer_id: Optional customer ID for loyalty tracking
            
        Returns:
            tuple: (success boolean, order_id or error message)
        """
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        try:
            # Calculate order total
            total = 0
            for item in items:
                cursor.execute("SELECT price FROM products WHERE id = ?", (item['product_id'],))
                price = cursor.fetchone()[0]
                total += price * item['quantity']
            
            # Create order
            cursor.execute("""
            INSERT INTO orders (order_time, total, payment_method, customer_id) 
            VALUES (?, ?, ?, ?)
            """, (datetime.datetime.now().isoformat(), total, payment_method, customer_id))
            
            order_id = cursor.lastrowid
            
            # Add order items
            for item in items:
                cursor.execute("SELECT price FROM products WHERE id = ?", (item['product_id'],))
                price = cursor.fetchone()[0]
                
                cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price, customizations) 
                VALUES (?, ?, ?, ?, ?)
                """, (order_id, item['product_id'], item['quantity'], price, 
                      json.dumps(item.get('customizations', {}))))
                
                # Update inventory
                cursor.execute("UPDATE products SET inventory = inventory - ? WHERE id = ?", 
                             (item['quantity'], item['product_id']))
            
            # Update customer loyalty points if applicable
            if customer_id:
                points_earned = int(total)
                cursor.execute("UPDATE customers SET points = points + ? WHERE id = ?", 
                             (points_earned, customer_id))
            
            conn.commit()
            conn.close()
            return True, order_id
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, str(e)
    
    @staticmethod
    def get_receipt(order_id):
        """Generate receipt data for an order."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT orders.id, orders.order_time, orders.total, orders.payment_method,
               customers.name, customers.email
        FROM orders
        LEFT JOIN customers ON orders.customer_id = customers.id
        WHERE orders.id = ?
        """, (order_id,))
        
        order = cursor.fetchone()
        if not order:
            conn.close()
            return None
        
        order_data = {
            'order_id': order[0],
            'order_time': order[1],
            'total': order[2],
            'payment_method': order[3],
            'customer_name': order[4],
            'customer_email': order[5],
            'items': []
        }
        
        cursor.execute("""
        SELECT order_items.quantity, products.name, order_items.price, order_items.customizations
        FROM order_items
        JOIN products ON order_items.product_id = products.id
        WHERE order_items.order_id = ?
        """, (order_id,))
        
        items = cursor.fetchall()
        for item in items:
            customizations = json.loads(item[3] or '{}')
            order_data['items'].append({
                'quantity': item[0],
                'name': item[1],
                'price': item[2],
                'customizations': customizations,
                'subtotal': item[0] * item[2]
            })
        
        conn.close()
        return order_data


class CustomerManager:
    """Manages customer information and loyalty program."""
    
    @staticmethod
    def get_all_customers():
        """Get all customers."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, email, phone, points FROM customers ORDER BY name")
        customers = cursor.fetchall()
        
        conn.close()
        return customers
    
    @staticmethod
    def find_customer(search_term):
        """Find a customer by name, email, or phone."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        search_pattern = f"%{search_term}%"
        cursor.execute("""
        SELECT id, name, email, phone, points 
        FROM customers 
        WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
        ORDER BY name
        """, (search_pattern, search_pattern, search_pattern))
        
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    @staticmethod
    def add_customer(name, email=None, phone=None):
        """Add a new customer."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
            INSERT INTO customers (name, email, phone, join_date) 
            VALUES (?, ?, ?, ?)
            """, (name, email, phone, datetime.datetime.now().isoformat()))
            
            customer_id = cursor.lastrowid
            conn.commit()
            conn.close()
            return True, customer_id
        except sqlite3.IntegrityError:
            conn.close()
            return False, "Email already exists"
    
    @staticmethod
    def redeem_points(customer_id, points):
        """Redeem loyalty points."""
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT points FROM customers WHERE id = ?", (customer_id,))
        current_points = cursor.fetchone()[0]
        
        if current_points < points:
            conn.close()
            return False, "Insufficient points"
        
        cursor.execute("UPDATE customers SET points = points - ? WHERE id = ?", 
                     (points, customer_id))
        
        conn.commit()
        conn.close()
        return True, "Points redeemed successfully"


class ReportGenerator:
    """Generates business reports."""
    
    @staticmethod
    def daily_sales_report(date=None):
        """Generate a daily sales report."""
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect('beanbrew.db')
        cursor = conn.cursor()
        
        date_pattern = f"{date}%"
        cursor.execute("""
        SELECT COUNT(*), SUM(total) 
        FROM orders 
        WHERE order_time LIKE ?
        """, (date_pattern,))
        
        result = cursor.fetchone()
        order_count = result[0] or 0
        total_sales = result[1] or 0
        
        cursor.execute("""
        SELECT products.category, SUM(order_items.quantity), SUM(order_items.quantity * order_items.price)
        FROM order_items
        JOIN orders ON order_items.order_id = orders.id
        JOIN products ON order_items.product_id = products.id
        WHERE orders.order_time LIKE ?
        GROUP BY products.category
        ORDER BY SUM(order_items.quantity * order_items.price) DESC
        """, (date_pattern,))
        
        category_sales = cursor.fetchall()
        
        cursor.execute("""
        SELECT products.name, SUM(order_items.quantity), SUM(order_items.quantity * order_items.price)
        FROM order_items
        JOIN orders ON order_items.order_id = orders.id
        JOIN products ON order_items.product_id = products.id
        WHERE orders.order_time LIKE ?
        GROUP BY products.name
        ORDER BY SUM(order_items.quantity) DESC
        LIMIT 10
        """, (date_pattern,))
        
        top_products = cursor.fetchall()
        
        conn.close()
        
        return {
            'date': date,
            'order_count': order_count,
            'total_sales': total_sales,
            'category_sales': category_sales,
            'top_products': top_products
        }


# CLI Commands using Click
@click.group()
def cli():
    """Bean Brew: Coffee Shop Management CLI"""
    pass


@cli.command()
def setup():
    """Initialize the database and add sample data."""
    console.print(Panel("[bold blue]Bean Brew CLI Setup[/bold blue]", box=box.ROUNDED))
    
    console.print("Initializing database...", end="")
    init_db()
    console.print("[green]Done![/green]")
    
    console.print("Adding sample data...", end="")
    insert_sample_data()
    console.print("[green]Done![/green]")
    
    console.print("\n[green]Setup complete![/green]")
    console.print("\nDefault admin credentials:")
    console.print("  Username: [bold]admin[/bold]")
    console.print("  Password: [bold]admin[/bold]")
    console.print("\n[yellow]Please change the default password immediately.[/yellow]")


@cli.command()
@click.option('--username', prompt=True, help='Admin username')
@click.option('--password', prompt=True, hide_input=True, help='Admin password')
@click.option('--name', prompt=True, help='Admin display name')
def create_admin(username, password, name):
    """Create a new admin user."""
    result = Authentication.create_user(username, password, 'admin', name)
    if result:
        console.print("[green]Admin user created successfully![/green]")
    else:
        console.print("[red]Username already exists![/red]")


@cli.command()
@click.option('--username', prompt=True, help='Username')
@click.option('--password', prompt=True, hide_input=True, help='Password')
def login(username, password):
    """Log in to the system."""
    user = Authentication.login(username, password)
    if user:
        console.print(f"[green]Welcome, {user['name']}![/green]")
        console.print(f"Role: {user['role']}")
        # In a real application, we would store the user session
    else:
        console.print("[red]Invalid username or password![/red]")


@cli.command()
def inventory():
    """Display current inventory."""
    products = InventoryManager.get_all_products()
    
    table = Table(title="Current Inventory")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Price", justify="right")
    table.add_column("Inventory", justify="right")
    
    for product in products:
        table.add_row(
            str(product[0]),
            product[1],
            product[2],
            f"${product[3]:.2f}",
            str(product[4])
        )
    
    console.print(table)


@cli.command()
@click.option('--name', prompt=True, help='Product name')
@click.option('--category', prompt=True, help='Product category')
@click.option('--price', prompt=True, type=float, help='Product price')
@click.option('--cost', prompt=True, type=float, help='Product cost')
@click.option('--inventory', prompt=True, type=int, help='Initial inventory')
def add_product(name, category, price, cost, inventory):
    """Add a new product."""
    result = InventoryManager.add_product(name, category, price, cost, inventory)
    if result:
        console.print(f"[green]Product '{name}' added successfully![/green]")
    else:
        console.print("[red]Failed to add product![/red]")


@cli.command()
def customers():
    """Display customer list."""
    customers = CustomerManager.get_all_customers()
    
    table = Table(title="Customer List")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Phone")
    table.add_column("Loyalty Points", justify="right")
    
    for customer in customers:
        table.add_row(
            str(customer[0]),
            customer[1],
            customer[2] or "-",
            customer[3] or "-",
            str(customer[4])
        )
    
    console.print(table)


@cli.command()
@click.option('--name', prompt=True, help='Customer name')
@click.option('--email', prompt=True, help='Customer email')
@click.option('--phone', prompt=True, help='Customer phone')
def add_customer(name, email, phone):
    """Add a new customer."""
    result, customer_id = CustomerManager.add_customer(name, email, phone)
    if result:
        console.print(f"[green]Customer '{name}' added successfully! ID: {customer_id}[/green]")
    else:
        console.print(f"[red]Failed to add customer: {customer_id}[/red]")


@cli.command()
@click.option('--date', help='Report date (YYYY-MM-DD)')
def daily_report(date=None):
    """Generate a daily sales report."""
    report = ReportGenerator.daily_sales_report(date)
    
    console.print(Panel(f"[bold blue]Daily Sales Report: {report['date']}[/bold blue]", box=box.ROUNDED))
    console.print(f"Orders: {report['order_count']}")
    console.print(f"Total Sales: ${report['total_sales']:.2f}")
    
    if report['category_sales']:
        console.print("\n[bold]Sales by Category:[/bold]")
        table = Table()
        table.add_column("Category")
        table.add_column("Quantity", justify="right")
        table.add_column("Sales", justify="right")
        
        for category in report['category_sales']:
            table.add_row(
                category[0],
                str(category[1]),
                f"${category[2]:.2f}"
            )
        
        console.print(table)
    
    if report['top_products']:
        console.print("\n[bold]Top Products:[/bold]")
        table = Table()
        table.add_column("Product")
        table.add_column("Quantity", justify="right")
        table.add_column("Sales", justify="right")
        
        for product in report['top_products']:
            table.add_row(
                product[0],
                str(product[1]),
                f"${product[2]:.2f}"
            )
        
        console.print(table)


@cli.command()
@click.argument('search_term')
def find_customer(search_term):
    """Find a customer by name, email, or phone."""
    customers = CustomerManager.find_customer(search_term)
    
    if not customers:
        console.print("[yellow]No customers found![/yellow]")
        return
    
    table = Table(title=f"Search Results for '{search_term}'")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Email")
    table.add_column("Phone")
    table.add_column("Loyalty Points", justify="right")
    
    for customer in customers:
        table.add_row(
            str(customer[0]),
            customer[1],
            customer[2] or "-",
            customer[3] or "-",
            str(customer[4])
        )
    
    console.print(table)


@cli.command()
def new_order():
    """Create a new order interactively."""
    console.print(Panel("[bold blue]New Order[/bold blue]", box=box.ROUNDED))
    
    # Display product list
    products = InventoryManager.get_all_products()
    table = Table(title="Available Products")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Category")
    table.add_column("Price", justify="right")
    
    for product in products:
        table.add_row(
            str(product[0]),
            product[1],
            product[2],
            f"${product[3]:.2f}"
        )
    
    console.print(table)
    
    # Build order
    items = []
    total = 0
    adding_items = True
    
    while adding_items:
        product_id = click.prompt("Enter product ID (0 to finish)", type=int)
        if product_id == 0:
            adding_items = False
            continue
        
        # Check if product exists
        product = None
        for p in products:
            if p[0] == product_id:
                product = p
                break
        
        if not product:
            console.print("[red]Invalid product ID![/red]")
            continue
        
        quantity = click.prompt("Quantity", type=int, default=1)
        if quantity <= 0:
            console.print("[red]Invalid quantity![/red]")
            continue
        
        # Add item to order
        item = {
            'product_id': product_id,
            'quantity': quantity,
            'customizations': {}
        }
        
        # Ask for customizations
        if click.confirm("Add customizations?"):
            customization = click.prompt("Enter customization (e.g. 'Milk: Oat')")
            if customization:
                key, value = customization.split(':', 1)
                item['customizations'][key.strip()] = value.strip()
        
        items.append(item)
        subtotal = product[3] * quantity
        total += subtotal
        console.print(f"Added {quantity} x {product[1]} (${subtotal:.2f})")
    
    if not items:
        console.print("[yellow]Order cancelled - no items added![/yellow]")
        return
    
    # Order summary
    console.print(Panel(f"[bold]Order Summary - Total: ${total:.2f}[/bold]", box=box.ROUNDED))
    
    # Customer information
    customer_id = None
    if click.confirm("Add customer for loyalty points?"):
        search_term = click.prompt("Search for customer (name, email, or phone)")
        customers = CustomerManager.find_customer(search_term)
        
        if customers:
            table = Table(title=f"Matching Customers")
            table.add_column("ID", justify="right")
            table.add_column("Name")
            table.add_column("Email")
            table.add_column("Points", justify="right")
            
            for customer in customers:
                table.add_row(
                    str(customer[0]),
                    customer[1],
                    customer[2] or "-",
                    str(customer[4])
                )
            
            console.print(table)
            customer_id = click.prompt("Enter customer ID (0 to skip)", type=int, default=0)
            if customer_id == 0:
                customer_id = None
        else:
            console.print("[yellow]No customers found![/yellow]")
            if click.confirm("Create new customer?"):
                name = click.prompt("Name")
                email = click.prompt("Email", default="")
                phone = click.prompt("Phone", default="")
                
                result, new_id = CustomerManager.add_customer(name, email or None, phone or None)
                if result:
                    console.print(f"[green]Customer created successfully![/green]")
                    customer_id = new_id
                else:
                    console.print(f"[red]Failed to create customer: {new_id}[/red]")
    
    # Payment method
    payment_options = ['Cash', 'Credit Card', 'Debit Card', 'Mobile Payment']
    for i, option in enumerate(payment_options, 1):
        console.print(f"{i}. {option}")
    
    payment_choice = click.prompt("Select payment method", type=int, default=1)
    payment_method = payment_options[payment_choice - 1]
    
    # Process order
    success, result = SalesProcessor.create_order(items, payment_method, customer_id)
    
    if success:
        order_id = result
        console.print(f"[green]Order #{order_id} created successfully![/green]")
        
        # Print receipt
        receipt = SalesProcessor.get_receipt(order_id)
        if receipt:
            console.print(Panel(f"[bold blue]Receipt: Order #{receipt['order_id']}[/bold blue]", box=box.ROUNDED))
            
            if receipt['customer_name']:
                console.print(f"Customer: {receipt['customer_name']}")
            
            console.print(f"Date: {receipt['order_time']}")
            console.print(f"Payment: {receipt['payment_method']}")
            
            table = Table()
            table.add_column("Qty", justify="right")
            table.add_column("Item")
            table.add_column("Price", justify="right")
            table.add_column("Subtotal", justify="right")
            
            for item in receipt['items']:
                customizations_str = ""
                if item['customizations']:
                    customizations = []
                    for key, value in item['customizations'].items():
                        customizations.append(f"{key}: {value}")
                    if customizations:
                        customizations_str = f" ({', '.join(customizations)})"
                
                table.add_row(
                    str(item['quantity']),
                    f"{item['name']}{customizations_str}",
                    f"${item['price']:.2f}",
                    f"${item['subtotal']:.2f}"
                )
            
            console.print(table
