import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "database.db")

def seed_database():
    # Asegurarnos de que el directorio data/ existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Crear tabla de Clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            country TEXT,
            registration_date DATE
        )
    ''')

    # Crear tabla de Pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            total_amount REAL,
            status TEXT,
            order_date DATE,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        )
    ''')

    # Insertar datos dummy
    customers = [
        ('Ana Garcia', 'ana@email.com', 'Mexico', '2023-01-15'),
        ('John Smith', 'john@email.com', 'USA', '2023-02-20'),
        ('Carlos Ruiz', 'carlos@email.com', 'Spain', '2023-03-10')
    ]
    cursor.executemany('INSERT OR IGNORE INTO customers (name, email, country, registration_date) VALUES (?, ?, ?, ?)', customers)

    orders = [
        (1, 150.50, 'completed', '2023-04-01'),
        (1, 200.00, 'completed', '2023-05-15'),
        (2, 99.99, 'pending', '2023-06-10'),
        (3, 350.75, 'completed', '2023-07-22')
    ]
    cursor.executemany('INSERT OR IGNORE INTO orders (customer_id, total_amount, status, order_date) VALUES (?, ?, ?, ?)', orders)

    conn.commit()
    conn.close()
    print(f"✅ Base de datos creada exitosamente en {DB_PATH}")

if __name__ == "__main__":
    seed_database()