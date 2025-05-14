import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QScrollArea,
    QMessageBox, QDialog, QCompleter, QFormLayout, QDialogButtonBox,
)

from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from database import *
import re


class CartDialog(QDialog):
    def __init__(self, cart, parent=None):
        super().__init__(parent)
        self.setWindowTitle("К продаже")
        self.setFixedSize(500, 400)
        self.cart = cart
        self.item_widgets = []  # Список для хранения виджетов товаров

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        self.update_cart_display()

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        checkout_btn = QPushButton("Оформить продажу")
        checkout_btn.clicked.connect(self.accept)
        layout.addWidget(checkout_btn)

        back_btn = QPushButton("Вернуться назад")
        back_btn.clicked.connect(self.reject)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def update_cart_display(self):
        for widget in self.item_widgets:
            widget.setParent(None)
        self.item_widgets.clear()
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)
        for i, (product_id, name, price, quantity) in enumerate(self.cart):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_label = QLabel(f"{name} - {price} руб. x {quantity} = {price * quantity} руб.")
            item_layout.addWidget(item_label)
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            item_layout.addWidget(delete_btn)
            self.scroll_layout.addWidget(item_widget)
            self.item_widgets.append(item_widget)

    def remove_item(self, index):
        if 0 <= index < len(self.cart):
            cursor.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (self.cart[index][3], self.cart[index][0]))
            self.cart.pop(index)
            self.update_cart_display()


class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление товара(ов) на склад")
        self.setFixedSize(500, 400)

        self.products_for_add = []
        self.categories_names = get_names("categories")
        self.current_products_names = []

        layout = QVBoxLayout()
        self.products = get_names("products")

        # Категория
        categ_layout = QHBoxLayout()
        categ_label = QLabel("Введите категорию:")
        self.categ_input = QLineEdit()
        categ_completer = QCompleter(self.categories_names)
        categ_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        categ_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.categ_input.setCompleter(categ_completer)
        self.categ_input.textChanged.connect(self.update_products_completer)
        categ_layout.addWidget(categ_label)
        categ_layout.addWidget(self.categ_input)
        layout.addLayout(categ_layout)

        # Товар
        prod_layout = QHBoxLayout()
        prod_label = QLabel("Введите название товара:")
        self.prod_input = QLineEdit()
        self.prod_completer = QCompleter([])
        self.prod_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.prod_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.prod_input.setCompleter(self.prod_completer)
        self.prod_input.textChanged.connect(self.update_price_fields)
        prod_layout.addWidget(prod_label)
        prod_layout.addWidget(self.prod_input)
        layout.addLayout(prod_layout)

        # Количество
        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Введите количество:")
        self.quantity_input = QLineEdit()
        self.quantity_input.setValidator(QtGui.QIntValidator(1, 9999))
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_input)
        layout.addLayout(quantity_layout)

        # Цена
        price_layout = QHBoxLayout()
        price_label = QLabel("Закупочная цена:")
        self.price_input = QLineEdit()
        self.price_input.setValidator(QtGui.QIntValidator(1, 999999999))
        price_layout.addWidget(price_label)
        price_layout.addWidget(self.price_input)
        layout.addLayout(price_layout)

        sell_price_layout = QHBoxLayout()
        sell_price_label = QLabel("Цена для продажи:")
        self.sell_price_input = QLineEdit()
        self.sell_price_input.setValidator(QtGui.QIntValidator(1, 999999999))
        sell_price_layout.addWidget(sell_price_label)
        sell_price_layout.addWidget(self.sell_price_input)
        layout.addLayout(sell_price_layout)

        # Кнопки
        buttons = QHBoxLayout()
        back = QPushButton("Назад")
        add_btn = QPushButton("Добавить в список")
        buttons2 = QHBoxLayout()
        show_pr_list_btn = QPushButton("Посмотреть список добавляемых товаров")
        back.clicked.connect(self.reject)
        buttons.addWidget(back)
        add_btn.clicked.connect(self.add_to_products_to_add)
        buttons.addWidget(add_btn)
        show_pr_list_btn.clicked.connect(self.show_add_list)
        buttons2.addWidget(show_pr_list_btn)
        layout.addLayout(buttons)
        layout.addLayout(buttons2)
        self.setLayout(layout)

    def update_products_completer(self):
        """Обновляет список товаров для автодополнения на основе выбранной категории"""
        category = self.categ_input.text().strip().capitalize()
        if category in self.categories_names:
            try:
                self.current_products_names = [i[0] for i in get_products_by_category(category)]
                self.prod_completer.model().setStringList(self.current_products_names)
            except Exception as e:
                print(f"Ошибка при обновлении списка товаров: {e}")
                self.current_products_names = []
                self.prod_completer.model().setStringList([])
        else:
            self.current_products_names = []
            self.prod_completer.model().setStringList([])

    def update_price_fields(self):
        """Обновляет поля цен, если товар уже существует"""
        category = self.categ_input.text().strip().capitalize()
        product_name = self.prod_input.text().strip().lower()

        if category in self.categories_names and product_name in self.current_products_names:
            try:
                c_id = cursor.execute("SELECT id FROM categories WHERE name = ?", (category,)).fetchone()[0]
                product_info = cursor.execute(
                    "SELECT price FROM products WHERE name = ? AND category_id = ?",
                    (product_name, c_id)
                ).fetchone()

                if product_info:
                    print(product_info)
                    self.sell_price_input.setText(str(int(product_info[0])))
            except Exception as e:
                print(f"Ошибка при получении информации о товаре: {e}")

    def add_to_products_to_add(self):
        try:
            prod_name = self.prod_input.text().strip()
            categ_name = self.categ_input.text().strip().capitalize()
            quantity_text = self.quantity_input.text().strip()
            price_text = self.price_input.text().strip()
            sell_price_text = self.sell_price_input.text().strip()

            if not all([prod_name, categ_name, quantity_text, price_text, sell_price_text]):
                QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены")
                return

            quantity = int(quantity_text)
            price = int(price_text)
            sell_price = int(sell_price_text)

            if quantity <= 0 or price <= 0 or sell_price <= 0:
                QMessageBox.warning(self, "Ошибка", "Количество и цены должны быть положительными числами")
                return

            accept_adding = QMessageBox()
            accept_adding.setWindowTitle("Подтверждение")
            accept_adding.setText(
                f"Вы уверены, что хотите добавить в список товар {prod_name} категории {categ_name} "
                f"в количестве {quantity} шт. по закупочной цене {price} и цене на продажу {sell_price} за шт.?"
            )
            accept_adding.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            answer = accept_adding.exec()

            if answer == QMessageBox.StandardButton.Yes:
                self.products_for_add.append((prod_name, categ_name, quantity, price, sell_price))
                QMessageBox.information(self, "Успех", "Товар добавлен в список")
                self.prod_input.clear()
                self.quantity_input.clear()
                self.price_input.clear()
                self.sell_price_input.clear()

        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Количество и цены должны быть целыми числами")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить товар в список: {str(e)}")

    def add_checkout(self):
        try:
            if not self.products_for_add:
                QMessageBox.warning(self, "Ошибка", "Нет товаров для добавления")
                return

            add_products_to_store(self.products_for_add)
            self.products_for_add = []
            QMessageBox.information(self, "Успех", "Товары успешно добавлены на склад")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить товары на склад: {str(e)}")

    def show_add_list(self):
        if not self.products_for_add:
            QMessageBox.information(self, "Список добавляемых товаров", "Нет товаров для добавления")
            return

        try:
            dialog = AddProductsListDialog(self.products_for_add, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.add_checkout()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть корзину: {str(e)}")


class AddProductsListDialog(QDialog):
    def __init__(self, products_for_add, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Список добавляемых товаров")
        self.setFixedSize(500, 400)
        self.add_products = products_for_add.copy()
        self.item_widgets = []

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        self.update_cart_display()

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        buttons_layout = QHBoxLayout()

        add_products_btn = QPushButton("Добавить товары на склад")
        add_products_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(add_products_btn)

        back_btn = QPushButton("Вернуться назад")
        back_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(back_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def update_cart_display(self):
        # Очищаем предыдущие виджеты
        for i in reversed(range(self.scroll_layout.count())):
            self.scroll_layout.itemAt(i).widget().setParent(None)

        for i, (prod_name, categ_name, quantity, price, sell_price) in enumerate(self.add_products):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)

            item_label = QLabel(f"{prod_name} - {price} руб. x {quantity} = {price * quantity} руб.")
            item_layout.addWidget(item_label, stretch=1)

            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            item_layout.addWidget(delete_btn)

            self.scroll_layout.addWidget(item_widget)

    def remove_item(self, index):
        if 0 <= index < len(self.add_products):
            self.add_products.pop(index)
            self.update_cart_display()


class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История продаж")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout()

        count_layout = QHBoxLayout()
        count_label = QLabel("Количество продаж для отображения:")
        self.count_input = QLineEdit()
        self.count_input.setValidator(QtGui.QIntValidator(1, 999))
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_input)
        layout.addLayout(count_layout)

        show_btn = QPushButton("Показать")
        show_btn.clicked.connect(self.display_history)
        layout.addWidget(show_btn)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout()
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        back_btn = QPushButton("Вернуться назад")
        back_btn.clicked.connect(self.reject)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def display_history(self):
        try:
            count_text = self.count_input.text()

            if not count_text:
                QMessageBox.warning(self, "Ошибка", "Введите количество покупок")
                return

            count = int(count_text)

            for i in reversed(range(self.scroll_layout.count())):
                widget = self.scroll_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            sales = get_info_from_table('sales', count)

            if not sales:
                self.scroll_layout.addWidget(QLabel("Нет данных о покупках"))
                return

            for sale in sales:
                sale_id, sale_date, total_amount, customer, seller = sale

                sale_label = QLabel(f"Покупка #{sale_id} от {sale_date} - Итого: {total_amount} руб. Покупатель: {customer}. Продавец: {seller}")
                self.scroll_layout.addWidget(sale_label)

                self.scroll_layout.addWidget(QLabel("─" * 50))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self, seller_login=None):
        super().__init__()
        self.s_id = get_seller_id(seller_login)
        self.setWindowTitle("Магазин оружия")
        self.setFixedSize(500, 400)
        try:
            create_tables()
            add_categories(CATEGORIES)
            add_products(PRODUCTS)
            # Initialize balance for the seller if not exists
            update_balance(self.s_id, 0.0)  # Set initial balance to 0.0
        except Exception as e:
            QMessageBox.critical(self, "Ошибка базы данных", f"Не удалось инициализировать БД: {str(e)}")
            sys.exit(1)
        self.cart = []
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.init_main_ui()

    def init_main_ui(self):
        layout = QVBoxLayout()

        category_layout = QHBoxLayout()
        category_label = QLabel("Выберите категорию:")
        self.category_combo = QComboBox()
        self.category_combo.addItems(get_names("categories"))
        self.category_combo.currentTextChanged.connect(self.update_products_combo)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)

        product_layout = QHBoxLayout()
        product_label = QLabel("Выберите товар:")
        self.product_combo = QComboBox()
        self.update_products_combo()
        product_layout.addWidget(product_label)
        product_layout.addWidget(self.product_combo)
        layout.addLayout(product_layout)

        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Введите количество:")
        self.quantity_input = QLineEdit()
        self.quantity_input.setValidator(QtGui.QIntValidator(1, 9999))
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_input)
        layout.addLayout(quantity_layout)

        buttons_layout_1, buttons_layout_2 = QHBoxLayout(), QHBoxLayout()

        add_to_cart_btn = QPushButton("Добавить к продаже")
        add_to_cart_btn.clicked.connect(self.add_to_cart)
        buttons_layout_1.addWidget(add_to_cart_btn)

        cart_btn = QPushButton("Товары к продаже")
        cart_btn.clicked.connect(self.show_cart)
        buttons_layout_1.addWidget(cart_btn)

        history_btn = QPushButton("История продаж")
        history_btn.clicked.connect(self.show_history)
        buttons_layout_1.addWidget(history_btn)

        add_to_store_btn = QPushButton("Добавить на склад")
        add_to_store_btn.clicked.connect(self.show_add_products_dialog)
        buttons_layout_2.addWidget(add_to_store_btn)

        update_categories_btn = QPushButton("Обновить данные")
        update_categories_btn.clicked.connect(self.update_info)
        buttons_layout_2.addWidget(update_categories_btn)

        income_layout, costs_layout, balance_layout = QHBoxLayout(), QHBoxLayout(), QHBoxLayout()

        self.income_value = QLabel()
        self.income_value.setText(str(select_income()))
        self.costs_value = QLabel()
        self.costs_value.setText(str(select_costs()))
        self.balance_value = QLabel()
        self.balance_value.setText(str(select_balance(self.s_id)))
        income_label = QLabel("Получено:")
        income_layout.addWidget(income_label)
        income_layout.addWidget(self.income_value)
        costs_label = QLabel("Потрачено:")
        costs_layout.addWidget(costs_label)
        costs_layout.addWidget(self.costs_value)
        balance_label = QLabel("ИТОГО:")
        balance_layout.addWidget(balance_label)
        balance_layout.addWidget(self.balance_value)
        layout.addLayout(buttons_layout_1)
        layout.addLayout(buttons_layout_2)
        layout.addLayout(income_layout)
        layout.addLayout(costs_layout)
        layout.addLayout(balance_layout)
        layout.setSpacing(30)

        self.main_widget.setLayout(layout)

    def update_info(self):
        try:
            self.category_combo.clear()
            self.category_combo.addItems(get_names("categories"))
            self.update_products_combo()
            self.income_value.setText(str(select_income()))  # Сумма всех продаж
            self.costs_value.setText(str(select_costs()))  # Сумма всех закупок
            self.balance_value.setText(str(select_balance(self.s_id)))  # Обновленный баланс
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить данные: {str(e)}")

    def update_products_combo(self):
        """Обновляет список товаров при изменении категории"""
        try:
            category = self.category_combo.currentText()
            products = get_products_by_category(category)
            self.product_combo.clear()
            self.product_combo.addItems([product[0] for product in products])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить товары: {str(e)}")

    def add_to_cart(self):
        """Добавляет выбранный товар в корзину"""
        try:
            product_name = self.product_combo.currentText()
            quantity_text = self.quantity_input.text()

            if not quantity_text:
                QMessageBox.warning(self, "Ошибка", "Введите количество товара")
                return

            quantity = int(quantity_text)
            product_info = get_id_price_by_name(product_name)

            if not product_info:
                QMessageBox.warning(self, "Ошибка", "Товар не найден в базе данных")
                return

            product_id, price = product_info
            available_quantity = get_quantity_by_id(product_id)

            if quantity > available_quantity:
                QMessageBox.warning(self, "Ошибка", f"Недостаточно товара на складе. Доступно: {available_quantity}")
                return

            self.cart.append((product_id, product_name, price, quantity))
            cursor.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
            QMessageBox.information(self, "Успех", "Товар добавлен к продаже")
            self.quantity_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить товар к продаже: {str(e)}")

    def show_cart(self):
        if not self.cart:
            QMessageBox.information(self, "К продаже", "Нет товаров к продаже")
            return

        try:
            dialog = CartDialog(self.cart, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.checkout()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть корзину: {str(e)}")

    def show_add_products_dialog(self):
        try:
            dialog = AddProductDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть окно добавления товара(ов): {str(e)}")

    def checkout(self):
        dlg = CustomerDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            for item in self.cart:
                cursor.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?",
                               (item[3], item[0]))
            connection.commit()
            return  # покупка отменена
        # все поля валидны
        customer_id = add_customer_and_get_id(
            full_name=dlg.name_input.text().strip(),
            age=int(dlg.age_input.text()),
            phone=dlg.phone_input.text().strip(),
            passport_plain=dlg.passport_input.text().strip().replace(" ", "")
        )
        try:
            create_sale([(item[0], item[2], item[3]) for item in self.cart], customer_id=customer_id,
                        seller_id=self.s_id)
            total_amount = sum(item[2] * item[3] for item in self.cart)  # Calculate total sale amount
            current_balance = select_balance(self.s_id)
            new_balance = current_balance + total_amount  # Update balance
            update_balance(self.s_id, new_balance)  # Update balance in the database
            self.cart = []
            QMessageBox.information(self, "Успех", "Продажа оформлена успешно")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось оформить продажу: {e}")

    def show_history(self):
        try:
            dialog = HistoryDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть историю покупок: {str(e)}")

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Регистрация продавца")
        self.setFixedSize(400, 300)
        layout = QVBoxLayout()

        # ФИО
        self.name_input = QLineEdit()
        layout.addWidget(QLabel("ФИО:"))
        layout.addWidget(self.name_input)

        # Возраст
        self.age_input = QLineEdit()
        self.age_input.setValidator(QtGui.QIntValidator(16, 99))
        layout.addWidget(QLabel("Возраст:"))
        layout.addWidget(self.age_input)

        # Телефон
        self.phone_input = QLineEdit()
        layout.addWidget(QLabel("Телефон:"))
        layout.addWidget(self.phone_input)

        # Логин
        self.username_input = QLineEdit()
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.username_input)

        # Пароль
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)

        # Кнопка регистрации
        btn = QPushButton("Зарегистрироваться")
        btn.clicked.connect(self.attempt_register)
        layout.addWidget(btn)

        self.setLayout(layout)

    def attempt_register(self):
        from database import register_seller

        # Собираем поля
        full_name = self.name_input.text().strip()
        age_text  = self.age_input.text().strip()
        phone     = self.phone_input.text().strip()
        username  = self.username_input.text().strip()
        password  = self.password_input.text()

        # Проверка ФИО
        if not re.fullmatch(r'[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+', full_name):
            QMessageBox.warning(self, "Ошибка", "ФИО должно состоять ровно из трёх слов, каждое с заглавной буквы и разделено пробелами")
            return

        # Проверка возраста
        try:
            age = int(age_text)
            if age < 18:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Возраст должен быть числом и не менее 18 лет")
            return

        # Проверка телефона
        if not re.fullmatch(r'(8\d{10}|\+7\d{10})', phone):
            QMessageBox.warning(self, "Ошибка", "Номер телефона должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX")
            return

        # Логин и пароль: только латиница и цифры
        if not re.fullmatch(r'[A-Za-z0-9]+', username):
            QMessageBox.warning(self, "Ошибка", "Логин может содержать только английские буквы и цифры")
            return
        if not re.fullmatch(r'[A-Za-z0-9]+', password):
            QMessageBox.warning(self, "Ошибка", "Пароль может содержать только английские буквы и цифры")
            return

        # Попытка регистрации
        try:
            register_seller(full_name, age, phone, username, password)
            QMessageBox.information(self, "Успех", "Продавец успешно зарегистрирован")
            self.accept()
        except sqlite3.IntegrityError as e:
            # ловим уникальность логина
            if "UNIQUE constraint failed: sellers.username" in str(e):
                QMessageBox.warning(self, "Ошибка", "Логин уже существует, выберите другой")
            else:
                QMessageBox.critical(self, "Ошибка регистрации", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка регистрации", str(e))

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Вход продавца")
        self.setFixedSize(300, 200)

        self.seller_login = ""

        layout = QVBoxLayout()

        self.login_input = QLineEdit()
        layout.addWidget(QLabel("Логин:"))
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_input)

        btn_layout = QHBoxLayout()
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.try_login)
        btn_layout.addWidget(login_btn)

        register_btn = QPushButton("Регистрация")
        register_btn.clicked.connect(self.open_register)
        btn_layout.addWidget(register_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def try_login(self):
        from database import verify_seller
        username = self.login_input.text().strip()
        password = self.password_input.text()
        if verify_seller(username, password):
            QMessageBox.information(self, "Успех", "Вход выполнен")
            self.seller_login = username
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def open_register(self):
        dlg = RegisterDialog(self)
        dlg.exec()

class CustomerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Данные покупателя")
        self.setFixedSize(300, 250)

        form = QFormLayout(self)

        self.name_input = QLineEdit(); form.addRow("ФИО:", self.name_input)
        self.age_input = QLineEdit();
        self.age_input.setValidator(QtGui.QIntValidator(18, 120))
        form.addRow("Возраст:", self.age_input)
        self.phone_input = QLineEdit(); form.addRow("Телефон:", self.phone_input)
        self.passport_input = QLineEdit(); form.addRow("Паспорт (серия и номер):", self.passport_input)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.validate_and_accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def validate_and_accept(self):
        # ФИО: 3 слова
        if not re.fullmatch(r'[А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+', self.name_input.text().strip()):
            QMessageBox.warning(self, "Ошибка", "ФИО: три слова, каждое с заглавной буквы")
            return

        # Возраст: число и не менее 18
        age_text = self.age_input.text().strip()
        try:
            age = int(age_text)
            if age < 18:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Возраст должен быть числом и не менее 18 лет")
            return

        # Телефон
        if not re.fullmatch(r'(8\d{10}|\+7\d{10})', self.phone_input.text().strip()):
            QMessageBox.warning(self, "Ошибка", "Телефон: формат 8XXXXXXXXXX или +7XXXXXXXXXX")
            return

        # Паспорт: две буквы + 6 цифр или 4 цифры + 6 цифр
        if not re.fullmatch(r'([А-ЯЁ]{2}\d{6}|\d{4}\s?\d{6})', self.passport_input.text().strip()):
            QMessageBox.warning(self, "Ошибка", "Паспорт: серия и номер в формате XX123456 или 1234 123456")
            return

        # Всё ок, принимаем
        self.accept()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)

        # Передача в БД
        create_tables()
        add_categories(CATEGORIES)
        add_products(PRODUCTS)

        # Окно входа
        from main import LoginDialog
        login = LoginDialog()
        if login.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

        # После успешного входа – главное окно
        window = MainWindow(login.seller_login)
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)