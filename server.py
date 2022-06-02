# Сервер


import sys
import json
import socket
import logging
import logs.server_config_log
from common.variables import *
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError, ReqFieldMissingError, NonDictInputError

# Серверный логер
SERVER_LOGGER = logging.getLogger('server')


def process_client_msg(msg):
    try:
        if not isinstance(msg, dict):
            raise NonDictInputError

        conditions = ACTION in msg and msg[ACTION] == PRESENCE and TIME in msg and USER in msg \
                     and msg[USER][ACCOUNT_NAME] == 'Larin'
        # Если верно(True) то код 200
        if conditions:
            return {RESPONSE: 200}
        return {
            RESPONSE: 400,
            ERROR: 'Bad request',
        }
    except NonDictInputError as err:
        SERVER_LOGGER.error(err)


# print('сработал')
# print(ACTION, msg)
# conditions = ACTION in msg and msg[ACTION] == PRESENCE \
# and TIME in msg and USER in msg \
# and msg[USER][ACCOUNT_NAME] == 'Larin'
# Если True, то отдаем 200 код.
# if conditions:
# return {RESPONSE: 200}
# return {
# RESPONSE: 400,
# ERROR: 'Bad request',
# }


def main():
    print('Сработало')
    # Получаем порт
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('Вы не указали номер порта после параметра - \'p\'!')

    # Получаем ip или устанавливаем уго по умолчанию
    try:
        if '-a' in sys.argv:
            listen_ip = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_ip = ''
    except IndexError:
        print('После параметра \'-a\' нужно указать IP или сервер не запустится')

    # сокет
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((listen_ip, listen_port))

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)
    SERVER_LOGGER.info('Сервер запущен успешно')

    while True:
        client, client_address = transport.accept()
        try:
            # Получаем сообщение от клиента из функции, созданной в utils
            msg_from_client = get_message(client)
            account_name_client = msg_from_client['user']['account_name']  # Получаем имя клиента
            print(msg_from_client)
            # Готовим ответ клиенту
            response = process_client_msg(msg_from_client)
            # Отправляем ответ клиенту и закрываем сокет
            send_message(client, response)
            SERVER_LOGGER.info(f'Ответ клиенту {account_name_client}')
            client.close()
        except json.JSONDecodeError:
            SERVER_LOGGER.error(f'Декодирование json строки не выполнено {account_name_client} - {client_address}')
            client.close()
        except IncorrectDataRecivedError:
            SERVER_LOGGER.error(f'Клиент {account_name_client} передал не корретные данные,'
                                f'Он будет отключен от сервера')
            client.close()


if __name__ == '__main__':
    main()
