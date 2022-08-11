# Клиент
import argparse
import socket
import sys
import json
import time
import logging
import logs.client_config_log
from common.variables import *
from common.utils import get_message, send_message
from errors import ReqFieldMissingError, IncorrectDataRecivedError, NonDictInputError
from decos import log

# Клиентский логер
CLIENT_LOGGER = logging.getLogger('client')


@log
def message_from_server(message):
    if ACTION in message and message[ACTION] == MESSAGE and SENDER in message and MESSAGE_TEXT in message:
        print(f'Получили сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        CLIENT_LOGGER.info(f'Получили сообщение от пользователя {message[SENDER]}:\n{message[MESSAGE_TEXT]}')
    else:
        CLIENT_LOGGER.error(f'Полили не корректное сообщение с сервера: {message}')


@log
def create_message(sock, account_name='Larin'):
    message = input('Введите сообщение для отправки или команду \'!q\' для завершения работы:')
    if message == '!q':
        sock.close()
        CLIENT_LOGGER.info('Завершение работы по команде пользователя')
        print('Благодарим за использование нашего сервиса!')
        sys.exit(0)
    message_dict = {
        ACTION: MESSAGE,
        TIME: time.time(),
        ACCOUNT_NAME: account_name,
        MESSAGE_TEXT: message
    }
    CLIENT_LOGGER.debug(f'Словарь сообщения сформирован: {message_dict}')
    return message_dict


@log
def create_presence(account_name='Larin'):
    out_data = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.info(f'Сгенерирован запрос о присутствии клиента {account_name}')
    return out_data


@log
def process_ans(msg):
    try:
        if not isinstance(msg, dict):
            raise NonDictInputError

        if RESPONSE in msg:
            if msg[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {msg[ERROR]}'
    except NonDictInputError as err:
        CLIENT_LOGGER.error(err)


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_address, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default='listen', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_mode = namespace.mode

    # проверка порта
    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(f'Запуск клиента с неправильным номером порта: {server_port},'
                               f'Допустимые адреса с 1024 по 65536. Клиент не запущен')
        sys.exit(1)

    # Проверка режима работы клиента
    if client_mode not in ('listen', 'send'):
        CLIENT_LOGGER.critical(f'Недопустимы режим работы клиента {client_mode},'
                               f'доступны режимы: listen и send')
        sys.exit(1)

    return server_address, server_port, client_mode


def main():
    server_address, server_port, client_mode = arg_parser()
    CLIENT_LOGGER.info(f'Запущен клиент имеющий параметры адрес сервера: {server_address},'
                       f'и порт: {server_port}, режим работы: {client_mode}')

    # Создание сокета и обмен
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        CLIENT_LOGGER.info(f'Удаленное подключение к серверу {server_address}:{server_port}')
        msg_to_server = create_presence()
        send_message(transport, msg_to_server)
        answer = process_ans(get_message(transport))
        CLIENT_LOGGER.info(f'Принято от сервера {answer}')
        print(answer)
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удачная попытка декодирования Json строки')
    except ConnectionRefusedError:
        CLIENT_LOGGER.critical(f'Неудачная попытка подключения к серверу {server_address}:{server_port}'
                               f'компюьтер не разрешил подключение')
    except ReqFieldMissingError as missing_err:
        CLIENT_LOGGER.error(f'Отсутствует необходимое поле'
                            f'{missing_err.missing_field}')
    else:
        # Если соединение с сервером прошло успешно, то начинаем обмен с ним, в требуемом режиме
        # Цикл всей программы
        if client_mode == 'send':
            print('Режим: отправка сообщений')
        else:
            print('Режим: прием сообщений')
        while True:
            # Режим: отправка сообщений
            if client_mode == 'send':
                try:
                    send_message(transport, create_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно')
                    sys.exit(1)

            # Режим: прием сообщений
            if client_mode == 'listen':
                try:
                    message_from_server(get_message(transport))
                except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                    CLIENT_LOGGER.error(f'Соединение с сервером {server_address} было потеряно')
                    sys.exit(1)


if __name__ == '__main__':
    main()
