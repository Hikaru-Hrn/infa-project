import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QScrollArea,
    QMessageBox, QDialog
)

from PyQt6 import QtGui
from database import *


class CartDialog(QDialog):
    def __init__(self, cart, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Корзина")
        self.setFixedSize(500, 400)
        self.cart = cart

        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        for i, (product_id, name, price, quantity) in enumerate(self.cart):
            item_layout = QHBoxLayout()

            item_label = QLabel(f"{name} - {price} руб. x {quantity} = {price * quantity} руб.")
            item_layout.addWidget(item_label)

            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            item_layout.addWidget(delete_btn)

            scroll_layout.addLayout(item_layout)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        checkout_btn = QPushButton("Оформить покупку")
        checkout_btn.clicked.connect(self.accept)
        layout.addWidget(checkout_btn)

        back_btn = QPushButton("Вернуться назад")
        back_btn.clicked.connect(self.reject)
        layout.addWidget(back_btn)

        self.setLayout(layout)

    def remove_item(self, index):
        self.cart.pop(index)
        self.close()
        self.show()

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

        buttons_layout = QHBoxLayout()

        add_to_cart_btn = QPushButton("Добавить в корзину")
        add_to_cart_btn.clicked.connect(self.add_to_cart)
        buttons_layout.addWidget(add_to_cart_btn)

        add_to_store_btn = QPushButton("Добавить на склад")
        add_to_store_btn.clicked.connect(self.add_to_store)
        buttons_layout.addWidget(add_to_store_btn)

        cart_btn = QPushButton("Корзина")
        cart_btn.clicked.connect(self.show_cart)
        buttons_layout.addWidget(cart_btn)

        history_btn = QPushButton("История покупок")
        history_btn.clicked.connect(self.show_history)
        buttons_layout.addWidget(history_btn)

        layout.addLayout(buttons_layout)

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

    def add_to_store(self):
        try:
            product_name = self.product_combo.currentText()
            quantity_text = self.quantity_input.text()

            if not quantity_text:
                QMessageBox.warning(self, "Ошибка", "Введите количество товара")
                return

            quantity = int(quantity_text)

            if not product_name:
                QMessageBox.warning(self, "Ошибка", "Товар не найден в базе данных")
                return

            add_product_to_store(product_name, quantity)
            QMessageBox.information(self, "Успех", "Товар добавлен на склад")
            self.quantity_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить товар на склад: {str(e)}")

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

    def checkout(self):
        try:
            sale_items = [(item[0], item[2], item[3]) for item in self.cart]

            create_sale(sale_items)
            self.cart = []
            QMessageBox.information(self, "Успех", "Покупка оформлена успешно")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось оформить покупку: {str(e)}")

    def show_history(self):
        try:
            dialog = HistoryDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть историю покупок: {str(e)}")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Critical error: {str(e)}")
        sys.exit(1)


