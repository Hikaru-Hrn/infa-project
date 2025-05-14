import sqlite3
from datetime import datetime
from cryptography.fernet import Fernet
import hashlib, os
KEY_PATH = "secret.key"
if not os.path.exists(KEY_PATH):
    raise RuntimeError("Ключ шифрования не найден! Запустите generate_key.py")
with open(KEY_PATH, "rb") as f:
    F = Fernet(f.read())

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
    (1, 1, "винтовка мосина обр. 1891/30 г.", 12000, 130),
    (2, 1, "m1903a1 usmc springfield", 11500, 34),
    (3, 1, "mauser 98k", 13000, 57),
    (4, 2, "свт-38", 15430, 71),
    (5, 2, "m1 garand", 16999, 23),
    (6, 2, "gewehr 43", 14799, 15),
    (7, 3, "ппш-41", 9879, 98),
    (8, 3, "m1928A1 thompson", 10199, 82),
    (9, 3, "mp-40", 9543, 51),
    (10, 4, "тт", 5201, 235),
    (11, 4, "mauser c96", 5023, 198),
    (12, 5, "дп-27", 17541, 34),
    (13, 5, "bren mk. 1", 18542, 54),
    (14, 5, "mg 34", 14056, 9),
    (15, 6, "снайперская винтовка мосина обр. 1891/30", 15000, 3),
    (16, 6, "снайперская m1903a1 usmc springfield", 13400, 5),
    (17, 6, "снайперская mauser 98k", 15678, 4)
]


def create_tables():
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS balance_table(
            balance INTEGER NOT NULL
        );"""
    )
    cursor.execute(
        """INSERT INTO balance_table(balance) VALUES(1000000)"""
    )
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
            id INTEGER PRIMARY KEY,
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
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS addings (
                id INTEGER PRIMARY KEY,
                adding_date TEXT NOT NULL,
                total_amount REAL NOT NULL
        );"""
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS add_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adding_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (adding_id) REFERENCES addings (id),
            FOREIGN KEY (product_id) REFERENCES products (id)
        );
        """
    )
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS sellers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        );"""
    )
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                age INTEGER NOT NULL,
                phone TEXT NOT NULL,
                passport_encrypted BLOB NOT NULL
            );
        """)
    # добавляем поле customer_id в sales, если его ещё нет
    cursor.execute("PRAGMA table_info(sales);")
    cols = [col[1] for col in cursor.fetchall()]
    if "customer_id" not in cols:
        cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INTEGER REFERENCES customers(id);")
    connection.commit()


def add_categories(categories):

    cursor.executemany("INSERT OR IGNORE INTO categories (id, name) VALUES (?, ?)", categories)
    connection.commit()

def select_income():
    res = cursor.execute("SELECT SUM(total_amount) FROM sales WHERE sale_date = ?",
                         (datetime.now().strftime('%Y-%m-%d'),)).fetchone()[0]
    return res if res else 0  # Возвращает сумму всех продаж за день

def select_costs():
    res = cursor.execute("SELECT SUM(total_amount) FROM addings WHERE adding_date = ?",
                         (datetime.now().strftime('%Y-%m-%d'),)).fetchone()[0]
    return res if res else 0  # Возвращает сумму всех закупок за день

def select_balance():
    i = select_income()
    c = select_costs()
    cursor.execute("UPDATE balance_table SET balance = ?", (i - c,))  # Полная перезапись баланса
    connection.commit()
    return i - c

def add_products(products):

    cursor.executemany("INSERT OR IGNORE INTO products "
                      "(id, category_id, name, price, quantity) VALUES (?, ?, ?, ?, ?)", products)
    connection.commit()

def add_product(new_prod_id, new_prod_categ_id, product_name, price, quantity):
    cursor.execute("INSERT INTO products(id, category_id, name, price, quantity) VALUES(?,?,?,?,?)",
                   (new_prod_id, new_prod_categ_id, product_name, price, quantity))

def get_product_info(product_id):
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    return cursor.fetchone()

def get_names(tablename):
    res = cursor.execute(f"SELECT name FROM {tablename}")
    return [i[0] for i in res]

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


def get_categ_id_by_name(categ_name):
    res = cursor.execute("""SELECT c.id FROM categories c
                                    JOIN products pr ON c.id = pr.category_id
                                    WHERE name = ?""", (categ_name,)).fetchone()[0]
    return res

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


def update_add_items(sale_id, product_id, quantity, price):
    cursor.execute('INSERT INTO add_items(adding_id, product_id, quantity, price) VALUES(?,?,?,?)',
                   (sale_id, product_id, quantity, price))


def add_products_to_store(add_items):
    if not add_items:
        raise ValueError("Список товаров для добавления пуст")

    try:
        adding_date = datetime.now().strftime('%Y-%m-%d')
        prod_names = [i.lower().strip() for i in get_names("products")]
        categ_names = [j.strip() for j in get_names("categories")]

        total_amount = sum(item[2] * item[3] for item in add_items)

        cursor.execute('INSERT INTO addings(adding_date, total_amount) VALUES(?,?)',
                       (adding_date, total_amount))
        cursor.execute('UPDATE balance_table SET balance = balance - ?', (total_amount,))
        sale_id = cursor.lastrowid

        for item in add_items:
            product_name = item[0].lower().strip()
            product_category = item[1].strip().capitalize()
            quantity = int(item[2])
            price = int(item[3])
            sell_price = int(item[4])

            if quantity <= 0 or price <= 0:
                raise ValueError("Количество и цена должны быть положительными числами")

            # Ищем товар с учётом категории
            cursor.execute("""
                SELECT p.id 
                FROM products p 
                JOIN categories c ON p.category_id = c.id 
                WHERE LOWER(TRIM(p.name)) = ? AND TRIM(c.name) = ?
            """, (product_name, product_category))

            product_info = cursor.fetchone()

            if product_info is None:
                # Товара нет - создаём новый
                new_prod_id = cursor.execute("SELECT MAX(id) + 1 FROM products").fetchone()[0]
                if product_category in categ_names:
                    new_prod_categ_id = get_categ_id_by_name(product_category)
                else:
                    new_prod_categ_id = cursor.execute("SELECT MAX(id) + 1 FROM categories").fetchone()[0]
                    cursor.execute("INSERT INTO categories(id, name) VALUES(?,?)",
                                   (new_prod_categ_id, product_category))

                add_product(new_prod_id, new_prod_categ_id, product_name, sell_price, quantity)
                update_add_items(sale_id, new_prod_id, quantity, price)
            else:
                # Товар есть - обновляем количество
                product_id = product_info[0]
                update_add_items(sale_id, product_id, quantity, price)
                cursor.execute('UPDATE products SET quantity = quantity + ? WHERE id = ?',
                               (quantity, product_id))

        connection.commit()
    except Exception as e:
        connection.rollback()
        raise e


def hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100_000)
    return pwd_hash.hex(), salt.hex()

def register_seller(full_name: str, age: int, phone: str, username: str, password: str):
    pwd_hash, salt = hash_password(password)
    cursor.execute(
        "INSERT INTO sellers (full_name, age, phone, username, password_hash, salt) VALUES (?, ?, ?, ?, ?, ?)",
        (full_name, age, phone, username, pwd_hash, salt)
    )
    connection.commit()

def verify_seller(username: str, password: str) -> bool:
    row = cursor.execute(
        "SELECT password_hash, salt FROM sellers WHERE username = ?", (username,)
    ).fetchone()
    if not row:
        return False
    stored_hash, salt_hex = row
    calc_hash, _ = hash_password(password, bytes.fromhex(salt_hex))
    return calc_hash == stored_hash

def add_customer_and_get_id(full_name: str, age: int, phone: str, passport_plain: str) -> int:
    """
    Шифрует паспорт и сохраняет данные клиента, возвращает его ID.
    """
    passport_enc = F.encrypt(passport_plain.encode())
    cursor.execute(
        "INSERT INTO customers (full_name, age, phone, passport_encrypted) VALUES (?, ?, ?, ?)",
        (full_name, age, phone, passport_enc)
    )
    connection.commit()
    return cursor.lastrowid

def create_sale(sale_items, customer_id=None):

    sale_date = datetime.now().strftime('%Y-%m-%d')
    total_amount = sum(item[2] * item[1] for item in sale_items)
    cursor.execute(
        'INSERT INTO sales(sale_date, total_amount, customer_id) VALUES (?, ?, ?)',
        (sale_date, total_amount, customer_id)
    )
    sale_id = cursor.lastrowid
    for prod_id, price, quantity in sale_items:
        cursor.execute(
            'INSERT INTO sale_items(sale_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (sale_id, prod_id, quantity, price)
        )
    connection.commit()
