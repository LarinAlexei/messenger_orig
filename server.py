# Сервер


import sys
import select
import json
import socket
import logging

from virtualenv.report import LOGGER

import logs.server_config_log
from common.variables import *
from common.utils import get_message, send_message
from errors import IncorrectDataRecivedError, ReqFieldMissingError, NonDictInputError
import argparse
import time
from decos import log

# Серверный логер
SERVER_LOGGER = logging.getLogger('server')


@log
def process_client_msg(message, client, msg_list, clients, names):
    try:
        if not isinstance(message, dict):
            raise NonDictInputError

        conditions = ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message
        if conditions:
            if message[USER][ACCOUNT_NAME] not in names.keys():
                names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Такое имя уже существует'
                send_message(client, response)
                clients.remove(client)
                client.close()
            return
            # Если это сообщение, то добавляем его в очередь сообщений.
            # Ответ не требуется.
        elif ACTION in message and message[ACTION] == MESSAGE and \
                DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            msg_list.append(message)
            return
            # Если клиент выходит
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            clients.remove(names[message[ACCOUNT_NAME]])
            names[message[ACCOUNT_NAME]].close()
            del names[message[ACCOUNT_NAME]]
            return
        else:
            response = RESPONSE_400
            response[ERROR] = 'Некорректный запрос'
            send_message(client, response)
            return

    except NonDictInputError as err:
        SERVER_LOGGER.error(err)


@log
def process_message(message, names, listen_socks):
    if message[DESTINATION] in names and names[message[DESTINATION]] in listen_socks:
        send_message(names[message[DESTINATION]], message)
        SERVER_LOGGER.info(f'Отправлено от : {message[SENDER]}'
                           f'доставлено : {message[DESTINATION]}')
    elif message[DESTINATION] in names and names[message[DESTINATION]] not in listen_socks:
        raise ConnectionError
    else:
        SERVER_LOGGER.error(
            f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
            f'отправка сообщения невозможна.')


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    if not 1023 < listen_port < 65536:
        SERVER_LOGGER.critical(f'Запуск сервера с указанным портом {listen_port},'
                               f'допустимые адреса 1024 по 65535')
        sys.exit(1)

    return listen_address, listen_port


def main():
    # Загрузка параметров командной строки
    listen_ip, listen_port = arg_parser()

    # Подготавливаем сокет
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.bind((listen_ip, listen_port))
    transport.settimeout(0.5)

    # Список клиентов и очередь сообщений
    clients = []
    messages = []

    # Этот словарь, содержит имена пользователей и их сокеты
    names = dict()

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)
    SERVER_LOGGER.info('Сервер запущен и находится в режиме ожидания')

    while True:
        # Подключение
        try:
            client, client_address = transport.accept()
        except OSError as err:
            #    print(err.errno)  # The error number returns None because it's just a timeout
            pass
        else:
            SERVER_LOGGER.info(f'Установлено соединение с ПК {client_address}')
            clients.append(client)

        recv_data_lst = []
        send_data_lst = []

        # Проверяем наличие ждущих клиентов
        try:
            if clients:
                recv_data_lst, send_data_lst, err_lst = select.select(clients, clients, [], 0)
        except OSError:
            pass

        # принимаем сообщения и если оно не пустое,
        # кладём в словарь, если проходит ошибка, исключаем этого клиента
        if recv_data_lst:
            for client_with_message in recv_data_lst:
                try:
                    process_client_msg(get_message(client_with_message), messages,
                                       client_with_message, clients, names)
                except Exception:
                    SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                       f'отключился от сервера')
                    clients.remove(client_with_message)

        # Если есть сообщения то обрабатываем все сообщение
        for i in messages:
            try:
                process_message(i, names, send_data_lst)
            except Exception:
                SERVER_LOGGER.info(f'Связь с клиентом с именем {i[DESTINATION]} была потеряна')
                clients.remove(names[i[DESTINATION]])
                del names[i[DESTINATION]]
        messages.clear()


if __name__ == '__main__':
    main()
