from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS  # Добавляем поддержку CORS
import os
import datetime
import secrets
import traceback  # Для отслеживания ошибок
from orders_db import OrdersDatabase

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Включаем CORS для всех маршрутов
app.secret_key = secrets.token_hex(16)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=30)

# Инициализация базы данных
db = OrdersDatabase()

# Маршрут для главной страницы - перенаправление на существующий index.html
@app.route('/')
def index():
    return app.send_static_file('index.html')

# API для отправки заказа (заменяет send.php)
@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        # Получаем данные из формы
        name = request.form.get('name', '')
        phone = request.form.get('phone', '')
        quantity = int(request.form.get('quantity', 1))
        
        # Проверяем обязательные поля
        if not name or not phone:
            return jsonify({
                'success': False,
                'message': 'Пожалуйста, заполните имя и телефон'
            })
        
        # Добавляем заказ в базу данных
        result = db.add_order(name, phone, quantity)
        
        # Возвращаем результат
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Ошибка при создании заказа: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

# API для получения списка заказов (заменяет get_orders.php)
@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        # Проверка режима доступа (публичный или административный)
        admin_mode = request.args.get('admin') == 'true'
        
        if admin_mode:
            # Проверяем авторизацию для административного доступа
            if not session.get('auth'):
                return jsonify({
                    'success': False,
                    'message': 'Требуется авторизация',
                    'orders': []
                })
        else:
            # Проверка ключа для публичного доступа
            access_key = request.args.get('key', '')
            if access_key != 'sumifun2023':
                return jsonify({
                    'success': False,
                    'message': 'Неверный ключ доступа',
                    'orders': []
                })
        
        # Получаем список заказов из базы данных
        orders = db.get_orders()
        
        # Для публичного доступа маскируем номера телефонов
        if not admin_mode:
            for order in orders:
                phone = order['phone']
                if len(phone) > 4:
                    order['phone'] = '*' * (len(phone) - 4) + phone[-4:]
        
        # Возвращаем список заказов
        return jsonify({
            'success': True,
            'message': 'Заказы успешно загружены.',
            'orders': orders
        })
    except Exception as e:
        app.logger.error(f"Ошибка при получении заказов: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}',
            'orders': []
        })

# Маршрут для входа в административную панель
@app.route('/api/login', methods=['POST'])
def login():
    try:
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        # Проверяем учетные данные из файла orders_data.js
        # В реальной системе следует использовать более безопасный метод
        if username == 'admin' and password == 'sumifun2023':
            session['auth'] = True
            session['auth_time'] = datetime.datetime.now().timestamp()
            return jsonify({'success': True})
        else:
            return jsonify({
                'success': False,
                'message': 'Неверное имя пользователя или пароль'
            })
    except Exception as e:
        app.logger.error(f"Ошибка при входе: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

# Маршрут для выхода из административной панели
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.pop('auth', None)
        session.pop('auth_time', None)
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Ошибка при выходе: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

# Маршрут для просмотра заказов в административной панели
@app.route('/orders')
def orders_view():
    return app.send_static_file('orders_viewer.html')

# Маршрут для поиска заказов
@app.route('/api/orders/search', methods=['GET'])
def search_orders():
    try:
        # Проверяем авторизацию
        if not session.get('auth'):
            return jsonify({
                'success': False,
                'message': 'Требуется авторизация',
                'orders': []
            })
        
        # Получаем параметр поиска
        query = request.args.get('q', '')
        
        # Выполняем поиск в базе данных
        orders = db.search_orders(query)
        
        # Возвращаем результаты поиска
        return jsonify({
            'success': True,
            'message': f'Найдено {len(orders)} заказов',
            'orders': orders
        })
    except Exception as e:
        app.logger.error(f"Ошибка при поиске заказов: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}',
            'orders': []
        })

# Маршрут для изменения статуса заказа
@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    try:
        # Проверяем авторизацию
        if not session.get('auth'):
            return jsonify({
                'success': False,
                'message': 'Требуется авторизация'
            })
        
        # Получаем новый статус
        status = request.json.get('status', '')
        
        # Обновляем статус в базе данных
        result = db.update_order_status(order_id, status)
        
        # Возвращаем результат
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Ошибка при обновлении статуса: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

# Маршрут для экспорта заказов в JSON
@app.route('/api/orders/export', methods=['GET'])
def export_orders():
    try:
        # Проверяем авторизацию
        if not session.get('auth'):
            return jsonify({
                'success': False,
                'message': 'Требуется авторизация'
            })
        
        # Экспортируем заказы в JSON файл
        filename = f'orders_export_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        result = db.export_orders_to_json(filename)
        
        # Возвращаем результат
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Ошибка при экспорте заказов: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Ошибка сервера: {str(e)}'
        })

# Обработчик ошибки 404
@app.errorhandler(404)
def page_not_found(e):
    return app.send_static_file('index.html')

# Обработчик ошибки 500
@app.errorhandler(500)
def server_error(e):
    app.logger.error(f"Внутренняя ошибка сервера: {str(e)}")
    return jsonify({
        'success': False,
        'message': 'Внутренняя ошибка сервера'
    }), 500

if __name__ == '__main__':
    # Создаем директорию для экспорта заказов, если она не существует
    os.makedirs('exports', exist_ok=True)
    
    # Настраиваем логирование
    import logging
    if not app.debug:
        # Только если не в режиме отладки
        logging.basicConfig(filename='app.log', level=logging.ERROR,
                            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    
    # Запускаем приложение в режиме отладки
    app.run(debug=True, host='0.0.0.0', port=5001) 