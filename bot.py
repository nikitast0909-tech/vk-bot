import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.upload import VkUpload
import json
import os
from datetime import datetime
import requests

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

def download_photo(url, path):
    """Скачивает фото по URL"""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
    except:
        pass
    return False

def get_main_keyboard():
    """Главная клавиатура с кнопками"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('📋 Все подики', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('➕ Добавить подик', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('👤 Мой профиль', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('❌ Мои объявления', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
    return keyboard

def get_back_keyboard():
    """Клавиатура с кнопкой назад"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.SECONDARY)
    return keyboard

def get_skip_keyboard():
    """Клавиатура с кнопкой пропустить фото"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('⏩ Пропустить фото', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard

def main():
    vk_session = vk_api.VkApi(token=TOKEN)
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    upload = VkUpload(vk_session)
    
    # Словарь для временного хранения данных при добавлении товара
    temp_products = {}
    
    print("Бот-барахолка с фото запущен!")
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            user_id = str(event.user_id)
            msg = event.text.lower().strip() if event.text else ""
            original_msg = event.text.strip() if event.text else ""
            
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
            
            # Обработка добавления товара (пошагово)
            if user_id in temp_products and 'step' in temp_products[user_id]:
                step_data = temp_products[user_id]
                
                # Шаг 1: Ожидание названия
                if step_data['step'] == 'wait_name':
                    temp_products[user_id]['name'] = original_msg
                    temp_products[user_id]['step'] = 'wait_price'
                    vk.messages.send(
                        user_id=event.user_id,
                        message="💰 Введите цену (только цифры):\nПример: 500",
                        random_id=0,
                        keyboard=get_back_keyboard().get_keyboard()
                    )
                    continue
                
                # Шаг 2: Ожидание цены
                elif step_data['step'] == 'wait_price':
                    if original_msg.isdigit():
                        temp_products[user_id]['price'] = int(original_msg)
                        temp_products[user_id]['step'] = 'wait_desc'
                        vk.messages.send(
                            user_id=event.user_id,
                            message="📝 Введите описание подика (не больше 500 символов):",
                            random_id=0,
                            keyboard=get_back_keyboard().get_keyboard()
                        )
                    else:
                        vk.messages.send(
                            user_id=event.user_id,
                            message="❌ Введите число! Например: 500",
                            random_id=0
                        )
                    continue
                
                # Шаг 3: Ожидание описания
                elif step_data['step'] == 'wait_desc':
                    temp_products[user_id]['description'] = original_msg[:500]
                    temp_products[user_id]['step'] = 'wait_photo'
                    vk.messages.send(
                        user_id=event.user_id,
                        message="📸 Теперь отправьте ФОТО товара (можно одно фото)\n"
                                "Или нажмите 'Пропустить фото', если фото не нужно",
                        random_id=0,
                        keyboard=get_skip_keyboard().get_keyboard()
                    )
                    continue
                
                # Шаг 4: Ожидание фото
                elif step_data['step'] == 'wait_photo':
                    photo_attachment = ""
                    has_photo = False
                    photo_url = None
                    
                    # Проверяем наличие фото в сообщении
                    if event.attachments:
                        for attachment in event.attachments:
                            if attachment['type'] == 'photo':
                                sizes = attachment['photo']['sizes']
                                if sizes:
                                    photo_url = sizes[-1]['url']
                                    has_photo = True
                                    break
                    
                    # Если пользователь нажал "Пропустить фото"
                    if original_msg in ["пропустить фото", "⏩ пропустить фото"]:
                        product_id = str(len(products) + 1)
                        products[product_id] = {
                            "id": product_id,
                            "seller_id": user_id,
                            "name": step_data['name'],
                            "price": step_data['price'],
                            "description": step_data['description'],
                            "photo": "",
                            "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                            "status": "active"
                        }
                        save_data(PRODUCTS_FILE, products)
                        
                        success_msg = f"✅ Подик успешно добавлен!\n\n" \
                                      f"📌 Название: {step_data['name']}\n" \
                                      f"💰 Цена: {step_data['price']} руб.\n" \
                                      f"📝 Описание: {step_data['description'][:100]}\n" \
                                      f"📸 Фото: не добавлено"
                        
                        vk.messages.send(
                            user_id=event.user_id,
                            message=success_msg,
                            random_id=0,
                            keyboard=get_main_keyboard().get_keyboard()
                        )
                        
                        del temp_products[user_id]
                        continue
                    
                    # Если есть фото
                    elif has_photo and photo_url:
                        temp_path = f"temp_photo_{user_id}.jpg"
                        if download_photo(photo_url, temp_path):
                            try:
                                photo_upload = upload.photo_messages(temp_path)[0]
                                photo_attachment = f"photo{photo_upload['owner_id']}_{photo_upload['id']}"
                                os.remove(temp_path)
                                
                                product_id = str(len(products) + 1)
                                products[product_id] = {
                                    "id": product_id,
                                    "seller_id": user_id,
                                    "name": step_data['name'],
                                    "price": step_data['price'],
                                    "description": step_data['description'],
                                    "photo": photo_attachment,
                                    "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
                                    "status": "active"
                                }
                                save_data(PRODUCTS_FILE, products)
                                
                                success_msg = f"✅ Подик успешно добавлен!\n\n" \
                                              f"📌 Название: {step_data['name']}\n" \
                                              f"💰 Цена: {step_data['price']} руб.\n" \
                                              f"📝 Описание: {step_data['description'][:100]}\n" \
                                              f"📸 Фото: добавлено"
                                
                                vk.messages.send(
                                    user_id=event.user_id,
                                    message=success_msg,
                                    random_id=0,
                                    attachment=photo_attachment,
                                    keyboard=get_main_keyboard().get_keyboard()
                                )
                                
                                del temp_products[user_id]
                                continue
                                
                            except Exception as e:
                                print(f"Ошибка загрузки фото: {e}")
                                vk.messages.send(
                                    user_id=event.user_id,
                                    message="❌ Ошибка при загрузке фото. Попробуйте другое фото или нажмите 'Пропустить фото'",
                                    random_id=0,
                                    keyboard=get_skip_keyboard().get_keyboard()
                                )
                                continue
                        else:
                            vk.messages.send(
                                user_id=event.user_id,
                                message="❌ Не удалось скачать фото. Попробуйте отправить другое фото или нажмите 'Пропустить фото'",
                                random_id=0,
                                keyboard=get_skip_keyboard().get_keyboard()
                            )
                            continue
                    
                    # Если нет фото и не нажата кнопка пропуска
                    else:
                        vk.messages.send(
                            user_id=event.user_id,
                            message="📸 Пожалуйста, отправьте ФОТО (одно фото)\n"
                                    "Или нажмите 'Пропустить фото'",
                            random_id=0,
                            keyboard=get_skip_keyboard().get_keyboard()
                        )
                        continue
                
                # Шаг 5: Если пользователь нажал "Назад" во время добавления
                elif msg == "◀️ назад" or original_msg == "◀️ назад":
                    del temp_products[user_id]
                    vk.messages.send(
                        user_id=event.user_id,
                        message="◀️ Создание объявления отменено",
                        random_id=0,
                        keyboard=get_main_keyboard().get_keyboard()
                    )
                    continue
            
            # Обработка команд из кнопок
            if msg in ["начать", "старт", "меню"] or msg == "◀️ назад":
                if user_id in temp_products:
                    del temp_products[user_id]
                
                vk.messages.send(
                    user_id=event.user_id,
                    message="🛍️ Добро пожаловать в барахолку подиков!\n\n"
                            "📋 Все подики - посмотреть все объявления\n"
                            "➕ Добавить подик - выставить товар на продажу\n"
                            "👤 Мой профиль - статистика и продажи\n"
                            "❌ Мои объявления - управлять своими товарами\n\n"
                            "Просто нажми на кнопку!",
                    random_id=0,
                    keyboard=get_main_keyboard().get_keyboard()
                )
            
            # Все подики
            elif msg == "все подики" or msg == "📋 все подики":
                active_products = {k: v for k, v in products.items() if v['status'] == 'active'}
                
                if not active_products:
                    vk.messages.send(
                        user_id=event.user_id,
                        message="😢 Пока нет ни одного объявления. Добавь первым!",
                        random_id=0,
                        keyboard=get_main_keyboard().get_keyboard()
                    )
                else:
                    for pid, product in list(active_products.items())[:5]:
                        message = f"📦 {product['name']}\n" \
                                  f"💰 {product['price']} руб.\n" \
                                  f"📝 {product['description'][:100]}\n" \
                                  f"👤 Продавец: @id{product['seller_id']}\n" \
                                  f"🆔 ID: {pid}\n\n" \
                                  f"Чтобы купить, напишите: Купить {pid}"
                        
                        if product.get('photo'):
                            vk.messages.send(
                                user_id=event.user_id,
                                message=message,
                                random_id=0,
                                attachment=product['photo']
                            )
                        else:
                            vk.messages.send(
                                user_id=event.user_id,
                                message=message,
                                random_id=0
                            )
                    
                    if len(active_products) > 5:
                        vk.messages.send(
                            user_id=event.user_id,
                            message=f"📊 Всего объявлений: {len(active_products)}\n"
                                    "Показаны последние 5.",
                            random_id=0
                        )
                    
                    vk.messages.send(
                        user_id=event.user_id,
                        message="Нажми на кнопку, чтобы продолжить:",
                        random_id=0,
                        keyboard=get_main_keyboard().get_keyboard()
                    )
            
            # Добавить подик
            elif msg == "добавить подик" or msg == "➕ добавить подик":
                temp_products[user_id] = {'step': 'wait_name'}
                vk.messages.send(
                    user_id=event.user_id,
                    message="🆕 Создание объявления\n\n"
                            "Введите НАЗВАНИЕ подика:",
                    random_id=0,
                    keyboard=get_back_keyboard().get_keyboard()
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
                    keyboard=get_main_keyboard().get_keyboard()
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
                        keyboard=get_main_keyboard().get_keyboard()
                    )
                else:
                    message = "🗑️ ВАШИ ОБЪЯВЛЕНИЯ:\n\n"
                    for pid, product in my_products.items():
                        message += f"🔹 ID: {pid} | {product['name']} - {product['price']} руб.\n"
                        if product.get('photo'):
                            message += f"   📸 С фото\n"
                        message += f"   Для удаления напишите: Удалить {pid}\n\n"
                    
                    message += "Чтобы удалить объявление - напиши: Удалить [ID]"
                    
                    vk.messages.send(
                        user_id=event.user_id,
                        message=message[:4000],
                        random_id=0,
                        keyboard=get_main_keyboard().get_keyboard()
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
                            random_id=0,
                            keyboard=get_main_keyboard().get_keyboard()
                        )
                    else:
                        products[product_id]['status'] = 'sold'
                        save_data(PRODUCTS_FILE, products)
                        
                        users[seller_id]['sales'] = users[seller_id].get('sales', 0) + 1
                        users[seller_id]['rating'] = min(5, users[seller_id]['rating'] + 0.5)
                        save_data(USERS_FILE, users)
                        
                        vk.messages.send(
                            user_id=event.user_id,
                            message=f"✅ Поздравляем с покупкой!\n\n"
                                    f"Товар: {product['name']}\n"
                                    f"Цена: {product['price']} руб.\n\n"
                                    f"Свяжитесь с продавцом: @id{seller_id}",
                            random_id=0,
                            keyboard=get_main_keyboard().get_keyboard()
                        )
                        
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
                        random_id=0,
                        keyboard=get_main_keyboard().get_keyboard()
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
                        keyboard=get_main_keyboard().get_keyboard()
                    )
                else:
                    vk.messages.send(
                        user_id=event.user_id,
                        message="❌ Объявление не найдено или это не ваше объявление!",
                        random_id=0,
                        keyboard=get_main_keyboard().get_keyboard()
                    )
            
            # Помощь
            elif msg == "помощь" or msg == "❓ помощь":
                help_text = "📚 КОМАНДЫ БОТА:\n\n" \
                           "📋 Все подики - просмотр всех товаров\n" \
                           "➕ Добавить подик - создать объявление\n" \
                           "👤 Мой профиль - моя статистика\n" \
                           "❌ Мои объявления - удалить товар\n" \
                           "Купить [ID] - купить товар\n" \
                           "Удалить [ID] - удалить свое объявление\n\n" \
                           "🆕 НОВИНКА: Можно добавлять фото к объявлениям!\n\n" \
                           "Просто нажимай на кнопки!"
                
                vk.messages.send(
                    user_id=event.user_id,
                    message=help_text,
                    random_id=0,
                    keyboard=get_main_keyboard().get_keyboard()
                )
            
            # Неизвестная команда
            elif msg and not msg.startswith("купить") and not msg.startswith("удалить") and msg not in ["", " "]:
                vk.messages.send(
                    user_id=event.user_id,
                    message="❓ Неизвестная команда.\n"
                            "Нажми на кнопку 'Помощь' или напиши 'Меню'",
                    random_id=0,
                    keyboard=get_main_keyboard().get_keyboard()
                )

if __name__ == '__main__':
    main()