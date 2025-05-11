import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QScrollArea,
    QMessageBox, QDialog, QCompleter
)

import re
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from database import *


class CartDialog(QDialog):
    def __init__(self, cart, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Корзина")
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

        checkout_btn = QPushButton("Оформить покупку")
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
            self.cart.pop(index)
            self.update_cart_display()


class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавление товара(ов) на склад")
        self.setFixedSize(500, 400)

        self.products_for_add = []
        self.products_names = get_names("products")
        self.categories_names = get_names("categories")

        layout = QVBoxLayout()
        categ_layout = QHBoxLayout()
        categ_label = QLabel("Введите категроию:")
        self.categ_input = QLineEdit()
        categ_completer = QCompleter(self.categories_names)
        categ_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        categ_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.categ_input.setCompleter(categ_completer)
        categ_layout.addWidget(categ_label)
        categ_layout.addWidget(self.categ_input)
        layout.addLayout(categ_layout)
        prod_layout = QHBoxLayout()
        prod_label = QLabel("Введите название товара:")
        self.prod_input = QLineEdit()
        prod_completer = QCompleter(self.products_names)
        prod_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        prod_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.prod_input.setCompleter(prod_completer)
        prod_layout.addWidget(prod_label)
        prod_layout.addWidget(self.prod_input)
        layout.addLayout(prod_layout)
        quantity_layout = QHBoxLayout()
        quantity_label = QLabel("Введите количество:")
        self.quantity_input = QLineEdit()
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_input)
        layout.addLayout(quantity_layout)
        price_layout = QHBoxLayout()
        price_label = QLabel("Закупочная цена:")
        self.price_input = QLineEdit()
        price_layout.addWidget(price_label)
        price_layout.addWidget(self.price_input)
        layout.addLayout(price_layout)
        buttons = QHBoxLayout()
        back = QPushButton("Назад")
        add_btn = QPushButton("Добавить в список добавляемых")
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


    def add_to_products_to_add(self):
        try:
            prod_name = self.prod_input.text()
            categ_name = self.categ_input.text()
            quantity = self.quantity_input.text()
            price = self.price_input.text()
            self.products_for_add.append((prod_name, categ_name, int(quantity), int(price)))
            QMessageBox.information(self, "Успех", "Товар добавлен в список добавляемых")
            self.prod_input.clear()
            self.categ_input.clear()
            self.quantity_input.clear()
            self.price_input.clear()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить товар в список добавляемых: {str(e)}")

    def add_checkout(self):
        try:
            sale_items = [(item[0], item[1], item[2], item[3]) for item in self.products_for_add]

            add_products_to_store(sale_items)
            self.products_for_add = []
            QMessageBox.information(self, "Успех", "Товары успешно добавлены на склад")
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
        self.setWindowTitle("Корзина")
        self.setFixedSize(500, 400)
        self.add_products = products_for_add
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

        add_products_btn = QPushButton("Добавить товары на склад")
        add_products_btn.clicked.connect(self.accept)
        layout.addWidget(add_products_btn)

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
        for i, (prod_name, categ_name, price, quantity) in enumerate(self.add_products):
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_label = QLabel(f"{prod_name} - {price} руб. x {quantity} = {price * quantity} руб.")
            item_layout.addWidget(item_label)
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            item_layout.addWidget(delete_btn)
            self.scroll_layout.addWidget(item_widget)
            self.item_widgets.append(item_widget)

    def remove_item(self, index):
        if 0 <= index < len(self.add_products):
            self.add_products.pop(index)
            self.update_cart_display()




class HistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("История покупок")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout()

        count_layout = QHBoxLayout()
        count_label = QLabel("Количество покупок для отображения:")
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
                sale_id, sale_date, total_amount = sale

                sale_label = QLabel(f"Покупка #{sale_id} от {sale_date} - Итого: {total_amount} руб.")
                self.scroll_layout.addWidget(sale_label)

                self.scroll_layout.addWidget(QLabel("─" * 50))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить историю: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Магазин оружия)")
        self.setFixedSize(500, 300)

        try:
            create_tables()
            add_categories(CATEGORIES)
            add_products(PRODUCTS)
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
        self.category_combo.addItems([cat[1] for cat in CATEGORIES])
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
        self.quantity_input.setValidator(QtGui.QIntValidator(1, 999))
        quantity_layout.addWidget(quantity_label)
        quantity_layout.addWidget(self.quantity_input)
        layout.addLayout(quantity_layout)

        buttons_layout_1, buttons_layout_2 = QHBoxLayout(), QHBoxLayout()

        add_to_cart_btn = QPushButton("Добавить в корзину")
        add_to_cart_btn.clicked.connect(self.add_to_cart)
        buttons_layout_1.addWidget(add_to_cart_btn)

        cart_btn = QPushButton("Корзина")
        cart_btn.clicked.connect(self.show_cart)
        buttons_layout_1.addWidget(cart_btn)

        history_btn = QPushButton("История покупок")
        history_btn.clicked.connect(self.show_history)
        buttons_layout_1.addWidget(history_btn)

        add_to_store_btn = QPushButton("Добавить на склад")
        add_to_store_btn.clicked.connect(self.show_add_products_dialog)
        buttons_layout_2.addWidget(add_to_store_btn)

        layout.addLayout(buttons_layout_1)
        layout.addLayout(buttons_layout_2)

        self.main_widget.setLayout(layout)

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
            QMessageBox.information(self, "Успех", "Товар добавлен в корзину")
            self.quantity_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить товар в корзину: {str(e)}")

    # def add_to_store(self):
    #     try:
    #         product_name = self.product_combo.currentText()
    #         quantity_text = self.quantity_input.text()
    #
    #         if not quantity_text:
    #             QMessageBox.warning(self, "Ошибка", "Введите количество товара")
    #             return
    #
    #         quantity = int(quantity_text)
    #
    #         if not product_name:
    #             QMessageBox.warning(self, "Ошибка", "Товар не найден в базе данных")
    #             return
    #
    #         add_product_to_store(product_name, quantity)
    #         QMessageBox.information(self, "Успех", "Товар добавлен на склад")
    #         self.quantity_input.clear()
    #     except Exception as e:
    #         QMessageBox.critical(self, "Ошибка", f"Не удалось добавить товар на склад: {str(e)}")

    def show_cart(self):
        if not self.cart:
            QMessageBox.information(self, "Корзина", "Корзина пуста")
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
        try:
            sale_items = [(item[0], item[2], item[3]) for item in self.cart]

            create_sale(sale_items)
            self.cart = []
            QMessageBox.information(self, "Успех", "Продажа оформлена успешно")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось оформить продажу: {str(e)}")

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
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def open_register(self):
        dlg = RegisterDialog(self)
        dlg.exec()

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
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

