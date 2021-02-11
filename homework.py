import os
import time

import requests
import telegram
import logging
import json

from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    filename='main.log',
    filemode='w'
)

PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
API_URL = 'https://praktikum.yandex.ru/api/user_api/{}'
API_URL_METHOD = 'homework_statuses/'
TIME_SLEEP = 300
TIME_SLEEP_EXCEPTION = 5
TIMEOUT_GET = 1


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    result = {
        'rejected': 'К сожалению в работе нашлись ошибки.',
        'approved': 'Ревьюеру всё понравилось, '
        'можно приступать к следующему уроку.'
    }

    if homework_name is None or homework_status is None:
        message = 'Ошибка получения данных'
        logging.error(message)
        return message

    try:
        if result.get(homework_status):
            verdict = result.get(homework_status)
            message = f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
            logging.info(message)
            return message

    except KeyError:
        logging.error('result: key error.')


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())

    headers = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}',
    }
    params = {
        'from_date': current_timestamp,
        #'from_date': 0,
    }
    try:
        homework_statuses = requests.get(url=API_URL.format(API_URL_METHOD),
                                         params=params, headers=headers,
                                         timeout=TIMEOUT_GET)
        # homework_statuses.raise_for_status() - В настоящий момент не
        # пропускается PyTest, но необходим для исключения
        # requests.exceptions.HTTPError
        return homework_statuses.json()

    except json.JSONDecodeError as e:
        message = f'Вернулось не ожидаемое значение: {e}'
        logging.exception(message)

    except requests.ConnectionError as e:
        message = f'Ошибка соединения: network problem: {e}'
        logging.exception(message)

    except requests.exceptions.HTTPError as e:
        message = f'Вернулся не ожидаемый код состояния запроса: {e}'
        logging.exception(message)

    except requests.RequestException as e:
        message = f'Бот столкнулся с ошибкой: {e}'
        logging.exception(message)


def send_message(message, bot_client):
    logging.info('Отправлено сообщение в чат Telegram')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    message = 'Бот запущен'
    logging.debug(message)
    send_message(message, bot_client)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            homeworks = new_homework.get('homeworks')
            if homeworks:
                send_message(parse_homework_status(homeworks[0]), bot_client)
                logging.info('Сообщение было отправлено')
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(TIME_SLEEP)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.exception(message)
            send_message(message, bot_client)
            time.sleep(TIME_SLEEP_EXCEPTION)


if __name__ == '__main__':
    main()
