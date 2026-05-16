import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import sys

# ТОКЕН ВК (ваш)
TOKEN = 'vk1.a.d5Q_QeEq9Xyr-hE5dXMrpCxZt68Wn6onJ14mFxol-t6g4kN-GG2zNqcITO2_wCX5y5Kx9Ktuh7KV-E4zdxPzZfAgp3nuH_EL5-_ZXO_58CO-Mr2nmG6SC0Bv6-PCKoLbWvyj98MKgGDsmnxXvD-sGUmqeLqT0_s7qeKGc7VIiLmvGZs-ANTwREF_MSCpsX_4jLHrt4KmL76QjRxEff0H5Q'

def main():
    # Авторизуемся как сообщество
    vk_session = vk_api.VkApi(token=TOKEN)
    
    # Работа с сообщениями
    longpoll = VkLongPoll(vk_session)
    vk = vk_session.get_api()
    
    print("Бот запущен и ждет сообщений...")
    
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            # Получаем текст сообщения
            msg = event.text.lower()
            user_id = event.user_id
            
            if msg == "привет":
                vk.messages.send(
                    user_id=user_id,
                    message="Привет!",
                    random_id=0
                )
                print(f"Отвечено Привет пользователю {user_id}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nБот остановлен")
        sys.exit()