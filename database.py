import sqlite3
from datetime import datetime

connection = sqlite3.connect("DB_shop_sells.db")
cursor = connection.cursor()

CATEGORIES = [
    (1, "Винтовка"),
    (2, "Самозарядная винтовка"),
    (3, "Пистолет-пулемёт"),
    (4, "Пистолет"),
    (5, "Пулемёт"),
    (6, "Снайперская винтовка")
]


PRODUCTS = [
    (1, 1, "Винтовка Мосина обр. 1891/30 г.", 12000, 130),
    (2, 1, "M1903A1 USMC Springfield", 11500, 34),
    (3, 1, "Mauser 98k", 13000, 57),
    (4, 2, "СВТ-38", 15430, 71),
    (5, 2, "M1 Garand", 16999, 23),
    (6, 2, "Gewehr 43", 14799, 15),
    (7, 3, "ППШ-41", 9879, 98),
    (8, 3, "M1928A1 Thompson", 10199, 82),
    (9, 3, "MP-40", 9543, 51),
    (10, 4, "ТТ", 5201, 235),
    (11, 4, "Mauser C96", 5023, 198),
    (12, 5, "ДП-27", 17541, 34),
    (13, 5, "Bren MK. 1", 18542, 54),
    (14, 5, "MG 34", 14056, 9),
    (15, 6, "Снайперская Винтовка Мосина обр. 1891/30", 15000, 3),
    (16, 6, "Снайперская M1903A1 USMC Springfield", 13400, 5),
    (17, 6, "Снайперская Mauser 98k", 15678, 4)
]

def create_tables():
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY NOT NULL UNIQUE,
            name TEXT NOT NULL
        );"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY NOT NULL UNIQUE,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        );"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            total_amount REAL NOT NULL
        );"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );"""
    )

def add_categories(categories):

    cursor.executemany("INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)", categories)
    connection.commit()

def add_products(products):

    cursor.executemany("INSERT OR IGNORE INTO products "
                      "(id, category_id, name, price, quantity) VALUES (?, ?, ?, ?, ?)", products)
    connection.commit()

def get_product_info(product_id):
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    return cursor.fetchone()

def get_products_by_category(category):
    cursor.execute("SELECT p.name FROM products p JOIN categories c ON c.id = p.category_id WHERE c.name = ?",
                   (category,))
    return cursor.fetchall()

def clear_table(tablename):
    cursor.execute(f"DELETE FROM {tablename}")

def get_info_from_table(tablename, limit=0):
    if limit:
        cursor.execute(f"SELECT * from {tablename} LIMIT {limit}")
    else:
        cursor.execute(f"SELECT * from {tablename}")
    return cursor.fetchall()

def get_quantity_by_id(product_id):
    cursor.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
    aq = cursor.fetchone()[0]
    return aq

def get_id_price_by_name(prod_name):
    cursor.execute("SELECT id, price FROM products WHERE name = ?", (prod_name,))
    return cursor.fetchone()

def get_sale_items_by_sale_id(sale_id):
    cursor.execute("""
                        SELECT p.name, si.quantity, si.price
                        FROM sale_items si
                        JOIN products p ON p.id = si.product_id
                        WHERE si.sale_id = ?
                    """, (sale_id,))
    return cursor.fetchall()


def create_sale(sale_items):
    sale_date = datetime.now().strftime('%Y-%m-%d')
    total_amount = sum(item[2] * item[1] for item in sale_items)
    cursor.execute('INSERT INTO sales(sale_date, total_amount) VALUES(?,?)',
                  (sale_date, total_amount))
    sale_id = cursor.execute("SELECT COUNT(id) FROM sales").fetchone()[0] + 1
    for item in sale_items:
        product_id = item[0]
        price = item[1]
        quantity = item[2]
    cursor.execute('INSERT INTO sale_items(sale_id, product_id, quantity, price) VALUES(?,?,?,?)',
                      (sale_id, product_id, quantity, price))
    cursor.execute('UPDATE products SET quantity = quantity - ? WHERE id = ?',
                      (quantity, product_id))
    connection.commit()