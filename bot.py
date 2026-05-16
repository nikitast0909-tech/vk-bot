import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import json
import os
from datetime import datetime

TOKEN = 'vk1.a.d5Q_QeEq9Xyr-hE5dXMrpCxZt68Wn6onJ14mFxol-t6g4kN-GG2zNqcITO2_wCX5y5Kx9Ktuh7KV-E4zdxPzZfAgp3nuH_EL5-_ZXO_58CO-Mr2nmG6SC0Bv6-PCKoLbWvyj98MKgGDsmnxXvD-sGUmqeLqT0_s7qeKGc7VIiLmvGZs-ANTwREF_MSCpsX_4jLHrt4KmL76QjRxEff0H5Q'

# Файлы для хранения данных
PRODUCTS_FILE = 'products.json'
USERS_FILE = 'users.json'

def load_data(filename, default):
    """Загружает данные из JSON файла"""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default

def save_data(filename, data):
    """Сохраняет данные в JSON файл"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_product_buttons():
    """Кнопки для меню"""
    keyboard = {
        "one_time": False,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "label": "📋 Все подики",
                    "payload": "{\"button\": \"list\"}"
                },
                "color": "primary"
            }],
            [{
                "action": {
                    "type": "text",
                    "label": "➕ Добавить подик",
                    "payload": "{\"button\": \"add\"}"
                },
                "color": "positive"
            }],
            [{
                "action": {
                    "type": "text",
                    "label": "👤 Мой профиль",
                    "payload": "{\"button\": \"profile\"}"
                },
                "color": "secondary"
            }],
            [{
                "action": {
                    "type": "text",
                    "label": "❌ Мои объявления",
                    "payload": "{\"button\": \"my_ads\"}"
                },
                "color": "negative"
            }]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def create_back_button():
    """Кнопка назад"""
    keyboard = {
        "one_time": False,
        "buttons": [
            [{
                "action": {
                    "type": "text",
                    "label": "◀️ Назад",
                    "payload": "{\"button\": \"back\"}"
                },
                "color": "secondary"
            }]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    
    # Словарь для временного хранения данных при добавлении товара
    temp_products = {}
    
    print("Бот-барахолка запущен!")
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = str(event.user_id)
            msg = event.text.lower().strip()
            original_msg = event.text.strip()
            
            # Загружаем данные
            products = load_data(PRODUCTS_FILE, {})
            users = load_data(USERS_FILE, {})
            
            # Инициализируем пользователя, если новый
            if user_id not in users:
                users[user_id] = {
                    "name": f"User_{user_id}",
                    "sales": 0,
                    "rating": 0
                }
                save_data(USERS_FILE, users)
            
            # Обработка добавления товара (шаг 1)
            if user_id in temp_products and 'step' in temp_products[user_id]:
                step_data = temp_products[user_id]
                
                if step_data['step'] == 'wait_name':
                    temp_products[user_id]['name'] = original_msg
                    temp_products[user_id]['step'] = 'wait_price'
                    vk.messages.send(
                        user_id=event.user_id,
                        message="💰 Введите цену (только цифры):\nПример: 500",
                        random_id=0,
                        keyboard=create_back_button()
                    )
                    continue
                    
                elif step_data['step'] == 'wait_price':
                    if original_msg.isdigit():
                        temp_products[user_id]['price'] = int(original_msg)
                        temp_products[user_id]['step'] = 'wait_desc'
                        vk.messages.send(
                            user_id=event.user_id,
                            message="📝 Введите описание подика (не больше 500 символов):",
                            random_id=0,
                            keyboard=create_back_button()
                        )
                    else:
                        vk.messages.send(
                            user_id=event.user_id,
                            message="❌ Введите число! Например: 500",
                            random_id=0
                        )
                    continue
                    
                elif step_data['step'] == 'wait_desc':
                    # Создаем объявление
                    product_id = str(len(products) + 1)
                    products[product_id] = {
                        "id": product_id,
                        "seller_id": user_id,
                        "name": step_data['name'],
                        "price": step_data['price'],
                        "description": original_msg[:500],
                        "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "status": "active"
                    }
                    save_data(PRODUCTS_FILE, products)
                    
                    # Очищаем временные данные
                    del temp_products[user_id]
                    
                    vk.messages.send(
                        user_id=event.user_id,
                        message="✅ Подик успешно добавлен!\n\n" + 
                                f"📌 Название: {step_data['name']}\n" +
                                f"💰 Цена: {step_data['price']} руб.\n" +
                                f"📝 Описание: {original_msg[:100]}",
                        random_id=0,
                        keyboard=create_product_buttons()
                    )
                    continue
            
            # Главное меню
            if msg == "начать" or msg == "старт" or msg == "меню":
                vk.messages.send(
                    user_id=event.user_id,
                    message="🛍️ Добро пожаловать в барахолку подиков!\n\n"
                            "📋 Все подики - посмотреть все объявления\n"
                            "➕ Добавить подик - выставить товар на продажу\n"
                            "👤 Мой профиль - статистика и продажи\n"
                            "❌ Мои объявления - управлять своими товарами\n\n"
                            "Просто напиши команду или нажми на кнопку!",
                    random_id=0,
                    keyboard=create_product_buttons()
                )
            
            # Все подики
            elif msg == "все подики" or msg == "📋 все подики":
                active_products = {k: v for k, v in products.items() if v['status'] == 'active'}
                
                if not active_products:
                    vk.messages.send(
                        user_id=event.user_id,
                        message="😢 Пока нет ни одного объявления. Добавь первым!",
                        random_id=0,
                        keyboard=create_product_buttons()
                    )
                else:
                    for pid, product in list(active_products.items())[:5]:  # Показываем по 5
                        message = f"📦 {product['name']}\n" \
                                  f"💰 {product['price']} руб.\n" \
                                  f"📝 {product['description'][:100]}\n" \
                                  f"👤 Продавец: @id{product['seller_id']}\n" \
                                  f"🆔 ID: {pid}\n\n" \
                                  f"Чтобы купить, напишите: Купить {pid}"
                        
                        vk.messages.send(
                            user_id=event.user_id,
                            message=message,
                            random_id=0
                        )
                    
                    if len(active_products) > 5:
                        vk.messages.send(
                            user_id=event.user_id,
                            message=f"📊 Всего объявлений: {len(active_products)}\n"
                                    "Показаны последние 5. Используй поиск для других.",
                            random_id=0
                        )
            
            # Добавить подик
            elif msg == "добавить подик" or msg == "➕ добавить подик":
                temp_products[user_id] = {'step': 'wait_name'}
                vk.messages.send(
                    user_id=event.user_id,
                    message="🆕 Создание объявления\n\n"
                            "Введите НАЗВАНИЕ подика:",
                    random_id=0,
                    keyboard=create_back_button()
                )
            
            # Мой профиль
            elif msg == "мой профиль" or msg == "👤 мой профиль":
                user_products = [p for p in products.values() if p['seller_id'] == user_id and p['status'] == 'active']
                sold_products = [p for p in products.values() if p['seller_id'] == user_id and p['status'] == 'sold']
                
                profile_text = f"👤 ВАШ ПРОФИЛЬ\n\n" \
                               f"🆔 ID: {user_id}\n" \
                               f"📦 Активных объявлений: {len(user_products)}\n" \
                               f"✅ Продано вещей: {len(sold_products)}\n" \
                               f"⭐ Рейтинг: {users[user_id]['rating']}★\n\n" \
                               f"Чтобы добавить товар - нажми 'Добавить подик'"
                
                vk.messages.send(
                    user_id=event.user_id,
                    message=profile_text,
                    random_id=0,
                    keyboard=create_product_buttons()
                )
            
            # Мои объявления
            elif msg == "мои объявления" or msg == "❌ мои объявления":
                my_products = {k: v for k, v in products.items() if v['seller_id'] == user_id and v['status'] == 'active'}
                
                if not my_products:
                    vk.messages.send(
                        user_id=event.user_id,
                        message="😢 У вас пока нет активных объявлений.\n"
                                "Нажмите 'Добавить подик' чтобы создать!",
                        random_id=0,
                        keyboard=create_product_buttons()
                    )
                else:
                    message = "🗑️ ВАШИ ОБЪЯВЛЕНИЯ:\n\n"
                    for pid, product in my_products.items():
                        message += f"🔹 ID: {pid} | {product['name']} - {product['price']} руб.\n"
                        message += f"   Для удаления напишите: Удалить {pid}\n\n"
                    
                    message += "Чтобы удалить объявление - напиши: Удалить [ID]"
                    
                    vk.messages.send(
                        user_id=event.user_id,
                        message=message[:4000],
                        random_id=0,
                        keyboard=create_product_buttons()
                    )
            
            # Купить товар
            elif msg.startswith("купить "):
                product_id = msg.split()[1]
                if product_id in products and products[product_id]['status'] == 'active':
                    product = products[product_id]
                    seller_id = product['seller_id']
                    
                    if seller_id == user_id:
                        vk.messages.send(
                            user_id=event.user_id,
                            message="❌ Нельзя купить свой же товар!",
                            random_id=0
                        )
                    else:
                        # Обновляем статус
                        products[product_id]['status'] = 'sold'
                        save_data(PRODUCTS_FILE, products)
                        
                        # Обновляем статистику продавца
                        users[seller_id]['sales'] = users[seller_id].get('sales', 0) + 1
                        users[seller_id]['rating'] = min(5, users[seller_id]['rating'] + 0.5)
                        save_data(USERS_FILE, users)
                        
                        vk.messages.send(
                            user_id=event.user_id,
                            message=f"✅ Поздравляем с покупкой!\n\n"
                                    f"Товар: {product['name']}\n"
                                    f"Цена: {product['price']} руб.\n\n"
                                    f"Свяжитесь с продавцом: @id{seller_id}",
                            random_id=0
                        )
                        
                        # Уведомляем продавца
                        vk.messages.send(
                            user_id=int(seller_id),
                            message=f"🎉 Ваш товар '{product['name']}' купили!\n"
                                    f"Цена: {product['price']} руб.",
                            random_id=0
                        )
                else:
                    vk.messages.send(
                        user_id=event.user_id,
                        message="❌ Товар не найден или уже продан!",
                        random_id=0
                    )
            
            # Удалить товар
            elif msg.startswith("удалить "):
                product_id = msg.split()[1]
                if product_id in products and products[product_id]['seller_id'] == user_id:
                    product_name = products[product_id]['name']
                    del products[product_id]
                    save_data(PRODUCTS_FILE, products)
                    
                    vk.messages.send(
                        user_id=event.user_id,
                        message=f"✅ Объявление '{product_name}' удалено!",
                        random_id=0,
                        keyboard=create_product_buttons()
                    )
                else:
                    vk.messages.send(
                        user_id=event.user_id,
                        message="❌ Объявление не найдено или это не ваше объявление!",
                        random_id=0
                    )
            
            # Назад
            elif msg == "назад" or msg == "◀️ назад":
                if user_id in temp_products:
                    del temp_products[user_id]
                
                vk.messages.send(
                    user_id=event.user_id,
                    message="◀️ Возврат в главное меню",
                    random_id=0,
                    keyboard=create_product_buttons()
                )
            
            # Помощь
            elif msg == "помощь":
                help_text = "📚 КОМАНДЫ БОТА:\n\n" \
                           "📋 Все подики - просмотр всех товаров\n" \
                           "➕ Добавить подик - создать объявление\n" \
                           "👤 Мой профиль - моя статистика\n" \
                           "❌ Мои объявления - удалить товар\n" \
                           "Купить [ID] - купить товар\n" \
                           "Удалить [ID] - удалить свое объявление\n" \
                           "Помощь - это сообщение\n" \
                           "Меню - вернуться в главное меню"
                
                vk.messages.send(
                    user_id=event.user_id,
                    message=help_text,
                    random_id=0,
                    keyboard=create_product_buttons()
                )
            
            # Неизвестная команда
            else:
                vk.messages.send(
                    user_id=event.user_id,
                    message="❓ Неизвестная команда.\n"
                            "Напишите 'Меню' для просмотра доступных команд "
                            "или 'Помощь' для справки.",
                    random_id=0
                )

if __name__ == '__main__':
    main()