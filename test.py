from database import *
prod_names = [i[0].lower() for i in cursor.execute("""SELECT name FROM products""")]
categ_names = [j[0].lower() for j in cursor.execute("""SELECT name FROM categories""")]
a = [i[0] for i in get_products_by_category("Винтовка")]
b = select_costs()
if any(b):
    print(1)
else:
    print(0)
