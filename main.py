from collections import deque
from datetime import datetime, timedelta
import logging, time, json, telebot

# Настройки
API_TOKEN = ''
CHAT_ID = ''
ADMIN_ID = ""

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)
bot_message_ids = deque(maxlen=10)
sent_messages = {}

# Инициализация логирования
logging.basicConfig(level=logging.INFO)

# Глобальные переменные для данных из JSON
schedule_data = {}
zoomlink_data = {}

# Загрузка JSON-файлов (только при старте)
def load_json_files():
    global schedule_data, zoomlink_data
    try:
        with open('schedule.json', 'r', encoding='utf-8') as f:
            schedule_data = json.load(f)
        bot.send_message(ADMIN_ID, "Расписание загружено.")  # Уведомление об успешной загрузке
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Ошибка при загрузке schedule.json: {e}")

    try:
        with open('zoomLink.json', 'r', encoding='utf-8') as f:
            zoomlink_data = json.load(f)
        bot.send_message(ADMIN_ID, "Ссылки Zoom загружены.")  # Уведомление об успешной загрузке
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Ошибка при загрузке zoomLink.json: {e}")

# Функция определения текущей недели
def get_current_week_type():
    start_of_year = datetime(datetime.now().year, 9, 1)
    current_date = datetime.now()
    weeks_since_start = (current_date - start_of_year).days // 7
    return 'even' if weeks_since_start % 1 == 0 else 'odd'

# Отправка расписания
def send_daily_schedule():
    try:
        current_time = datetime.now()
        day_name = current_time.strftime('%A')
        lessons = schedule_data.get(day_name, [])

        if current_time.hour == 8 and current_time.minute == 0:
            subjects_list = '\n'.join([f"{lesson['subject']}" for lesson in lessons])
            message = (f"Розклад на сьогодні\n{subjects_list}")
            sent_message = bot.send_message(CHAT_ID, message, reply_to_message_id=4)
            bot_message_ids.append((CHAT_ID, sent_message.message_id))
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Ошибка при отправке расписания: {e}")

# Очистка старых сообщений
def clear_old_messages():
    try:
        current_time = datetime.now()
        if current_time.hour == 16 and current_time.minute == 0:
            for chat_id, message_id in bot_message_ids:
                try:
                    bot.delete_message(chat_id, message_id)
                except Exception as e:
                    bot.send_message(ADMIN_ID, f"Ошибка при удалении сообщения {message_id}: {e}")
            bot_message_ids.clear()
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Ошибка при очистке сообщений: {e}")

# Отправка Zoom-ссылок
def send_zoom_links():
    try:
        current_time = datetime.now()
        current_week_type = get_current_week_type()
        day_name = current_time.strftime('%A')
        lessons = schedule_data.get(day_name, [])

        for lesson in lessons:
            lesson_time = lesson.get('time', [])
            lesson_subject = lesson.get('subject', '')
            lesson_week_type = lesson.get('week_type', '')

            if (lesson_week_type == current_week_type or lesson_week_type == 'both') and \
               len(lesson_time) == 2 and \
               current_time.hour == lesson_time[0] and \
               current_time.minute == lesson_time[1] - 5:
                link = zoomlink_data.get(lesson_subject, "класрум")
                message_key = (day_name, lesson_subject, tuple(lesson_time))

                if message_key not in sent_messages or \
                   (current_time - sent_messages[message_key]) > timedelta(minutes=10):
                    message = (f"━━━━━━━━━━━━━━━━━━━━\n"
                               f"📚 Урок через 10 хвилин: *{lesson_subject}*\n"
                               f"🔗 Посилання на Zoom: [Перейти]({link})\n"
                               f"━━━━━━━━━━━━━━━━━━━━\n")
                    sent_message = bot.send_message(CHAT_ID, message, reply_to_message_id=4)
                    bot_message_ids.append((CHAT_ID, sent_message.message_id))
                    sent_messages[message_key] = current_time
    except Exception as e:
        bot.send_message(ADMIN_ID, f"Ошибка при отправке Zoom-ссылки: {e}")

# Основной цикл
if __name__ == '__main__':
    load_json_files()  # Загружаем JSON-файлы только один раз при старте

    while True:
        send_daily_schedule()
        clear_old_messages()
        send_zoom_links()
        time.sleep(60)
