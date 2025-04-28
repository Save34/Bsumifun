import sqlite3
import os
import json
import datetime
import random
from pathlib import Path

class OrdersDatabase:
    def __init__(self, db_file='orders.db'):
        """Инициализация базы данных заказов"""
        self.db_file = db_file
        self.connection = None
        self.create_database()
    
    def connect(self):
        """Подключение к базе данных"""
        self.connection = sqlite3.connect(self.db_file)
        self.connection.row_factory = sqlite3.Row
        return self.connection
    
    def create_database(self):
        """Создание структуры базы данных"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Создаем таблицу для хранения заказов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            price INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT DEFAULT 'new'
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_order(self, name, phone, quantity=1):
        """Добавление нового заказа в базу данных"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Генерируем уникальный ID заказа
        order_id = self.generate_order_id()
        
        # Рассчитываем цену заказа
        if quantity == 1:
            price = 890
        elif quantity == 3:
            price = 1800
        else:
            price = quantity * 890
        
        # Текущая дата и время
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            cursor.execute('''
            INSERT INTO orders (order_id, name, phone, quantity, price, date)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (order_id, name, phone, quantity, price, date))
            
            conn.commit()
            return {"success": True, "order_id": order_id}
        except sqlite3.Error as e:
            return {"success": False, "message": str(e)}
        finally:
            conn.close()
    
    def get_orders(self):
        """Получение списка всех заказов"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM orders ORDER BY date DESC
        ''')
        
        rows = cursor.fetchall()
        orders = []
        
        for row in rows:
            orders.append(dict(row))
        
        conn.close()
        return orders
    
    def generate_order_id(self):
        """Генерация уникального ID заказа в формате SUMIFUN-YYYYMMDDHHmmss-XXX"""
        now = datetime.datetime.now()
        date_part = now.strftime("%Y%m%d%H%M%S")
        random_part = random.randint(100, 999)
        return f"SUMIFUN-{date_part}-{random_part}"
    
    def update_order_status(self, order_id, status):
        """Обновление статуса заказа"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE orders 
            SET status = ? 
            WHERE order_id = ?
            ''', (status, order_id))
            
            conn.commit()
            return {"success": True, "message": f"Статус заказа {order_id} обновлен на {status}"}
        except sqlite3.Error as e:
            return {"success": False, "message": str(e)}
        finally:
            conn.close()
    
    def search_orders(self, query):
        """Поиск заказов по имени, телефону или ID"""
        conn = self.connect()
        cursor = conn.cursor()
        
        search_param = f"%{query}%"
        
        cursor.execute('''
        SELECT * FROM orders 
        WHERE order_id LIKE ? OR name LIKE ? OR phone LIKE ?
        ORDER BY date DESC
        ''', (search_param, search_param, search_param))
        
        rows = cursor.fetchall()
        orders = []
        
        for row in rows:
            orders.append(dict(row))
        
        conn.close()
        return orders
    
    def export_orders_to_json(self, filename='orders_export.json'):
        """Экспорт заказов в JSON файл"""
        orders = self.get_orders()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": f"Экспортировано {len(orders)} заказов в файл {filename}"}
    
    def import_orders_from_json(self, filename='orders_export.json'):
        """Импорт заказов из JSON файла"""
        if not os.path.exists(filename):
            return {"success": False, "message": f"Файл {filename} не найден"}
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                orders = json.load(f)
            
            conn = self.connect()
            cursor = conn.cursor()
            
            imported_count = 0
            for order in orders:
                try:
                    cursor.execute('''
                    INSERT OR IGNORE INTO orders 
                    (order_id, name, phone, quantity, price, date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        order['order_id'], 
                        order['name'], 
                        order['phone'], 
                        order.get('quantity', 1), 
                        order.get('price', 890), 
                        order['date'], 
                        order.get('status', 'new')
                    ))
                    
                    if cursor.rowcount > 0:
                        imported_count += 1
                except sqlite3.Error as e:
                    print(f"Ошибка импорта заказа {order.get('order_id')}: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": f"Импортировано {imported_count} заказов из {len(orders)}"}
        
        except Exception as e:
            return {"success": False, "message": f"Ошибка импорта: {str(e)}"}


# Создаем функцию для импорта примеров заказов
def import_mock_orders():
    """Импорт примеров заказов в базу данных"""
    mock_orders = [
        {
            "order_id": "SUMIFUN-20230101120000-123",
            "name": "Иван Иванов",
            "phone": "+7 (123) 456-7890",
            "quantity": 1,
            "price": 890,
            "date": "2023-01-01 12:00:00",
            "status": "completed"
        },
        {
            "order_id": "SUMIFUN-20230102130000-456",
            "name": "Петр Петров",
            "phone": "+7 (987) 654-3210",
            "quantity": 3,
            "price": 1800,
            "date": "2023-01-02 13:00:00",
            "status": "completed"
        }
    ]
    
    db = OrdersDatabase()
    conn = db.connect()
    cursor = conn.cursor()
    
    for order in mock_orders:
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO orders 
            (order_id, name, phone, quantity, price, date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                order['order_id'], 
                order['name'], 
                order['phone'], 
                order['quantity'], 
                order['price'], 
                order['date'], 
                order['status']
            ))
        except sqlite3.Error as e:
            print(f"Ошибка импорта заказа {order['order_id']}: {str(e)}")
    
    conn.commit()
    conn.close()
    print("Примеры заказов импортированы успешно")


if __name__ == "__main__":
    # Проверяем, существует ли база данных
    db_file = 'orders.db'
    db_exists = os.path.exists(db_file)
    
    # Создаем базу данных
    db = OrdersDatabase(db_file)
    
    # Если база данных только что создана, импортируем примеры заказов
    if not db_exists:
        import_mock_orders()
        print(f"База данных создана в файле: {os.path.abspath(db_file)}")
    else:
        print(f"База данных уже существует: {os.path.abspath(db_file)}")
    
    # Выводим общее количество заказов
    orders = db.get_orders()
    print(f"Всего заказов в базе: {len(orders)}") 