import sqlite3
from datetime import datetime

# Database setup
def setup_database():
    conn = sqlite3.connect("bean_brew.db")
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Functions
def add_menu_item():
    name = input("Enter item name: ")
    price = float(input("Enter item price: "))
    conn = sqlite3.connect("bean_brew.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO menu (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    conn.close()
    print(f"{name} added to menu.")

def view_menu():
    conn = sqlite3.connect("bean_brew.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu")
    rows = cursor.fetchall()
    print("Menu Items:")
    for row in rows:
        print(f"{row[0]}. {row[1]} - ${row[2]:.2f}")
    conn.close()

def add_inventory_item():
    item_name = input("Enter inventory item name: ")
    quantity = int(input("Enter quantity: "))
    conn = sqlite3.connect("bean_brew.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory (item_name, quantity) VALUES (?, ?)", (item_name, quantity))
    conn.commit()
    conn.close()
    print(f"{item_name} added to inventory.")

def view_inventory():
    conn = sqlite3.connect("bean_brew.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    rows = cursor.fetchall()
    print("Inventory:")
    for row in rows:
        print(f"{row[0]}. {row[1]} - Quantity: {row[2]}")
    conn.close()

def process_sale():
    item_id = int(input("Enter menu item ID: "))
    quantity = int(input("Enter quantity: "))
    conn = sqlite3.connect("bean_brew.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, price FROM menu WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    if item:
        item_name, price = item
        total_price = price * quantity
        cursor.execute("INSERT INTO sales (item_name, quantity, total_price, date) VALUES (?, ?, ?, ?)",
                       (item_name, quantity, total_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        print(f"Sold {quantity} of {item_name} for ${total_price:.2f}")
    else:
        print("Item not found in menu.")
    conn.close()

def generate_sales_report():
    conn = sqlite3.connect("bean_brew.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales")
    rows = cursor.fetchall()
    print("Sales Report:")
    for row in rows:
        print(f"ID: {row[0]}, Item: {row[1]}, Quantity: {row[2]}, Total: ${row[3]:.2f}, Date: {row[4]}")
    conn.close()

# Main CLI loop
def main():
    setup_database()
    while True:
        print("\nBean Brew CLI")
        print("1. Add Menu Item")
        print("2. View Menu")
        print("3. Add Inventory Item")
        print("4. View Inventory")
        print("5. Process Sale")
        print("6. Generate Sales Report")
        print("7. Exit")
        choice = input("Enter your choice: ")
        
        if choice == "1":
            add_menu_item()
        elif choice == "2":
            view_menu()
        elif choice == "3":
            add_inventory_item()
        elif choice == "4":
            view_inventory()
        elif choice == "5":
            process_sale()
        elif choice == "6":
            generate_sales_report()
        elif choice == "7":
            print("Exiting Bean Brew CLI. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
