import os
import time

import requests
import telegram
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log',
    filemode='w'
)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name is None or homework_status is None:
        message = 'Ошибка получения данных'
        logging.error(message)
        return message

    if homework_status == 'reviewing':
        message = f'Работа {homework_name} взята в ревью'
        logging.info(message)
        return message

    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
    message = f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    logging.info(message)
    return message


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())

    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
    }
    try:
        homework_statuses = requests.get(url=API_URL, params=params,
                                         headers=headers, timeout=1)
        return homework_statuses.json()

    except Exception as e:
        message = f'Ошибка: {e}'
        logging.error(message)


def send_message(message, bot_client):
    logging.info('Отправлено сообщение в чат Telegram')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    message = 'Бот запущен'
    logging.info(message)
    send_message(message, bot_client)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_client)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(300)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(message)
            send_message(message, bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
