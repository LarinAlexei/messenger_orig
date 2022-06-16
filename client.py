# Клиент
import argparse
import socket
import sys
import json
import threading
import time
import logging
import logs.client_config_log
from common.variables import *
from common.utils import get_message, send_message
from errors import ReqFieldMissingError, IncorrectDataRecivedError, NonDictInputError, ServerError
from decos import log

# Клиентский логер
CLIENT_LOGGER = logging.getLogger('client')


@log
def create_exit_message(account_name):
    return {
        ACTION: EXIT,
        TIME: time.time(),
        ACCOUNT_NAME: account_name
    }


@log
def message_from_server(sock, my_username):
    while True:
        try:
            message = get_message(sock)
            if ACTION in message and message[ACTION] == [MESSAGE] and SENDER in message and DESTINATION in message \
                    and MESSAGE_TEXT in message and message[DESTINATION] == my_username:
                print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                      f'\n{message[MESSAGE_TEXT]}')
                CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                   f'\n{message[MESSAGE_TEXT]}')
            else:
                CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
        except IncorrectDataRecivedError:
            CLIENT_LOGGER.error(f'Декодировать сообщение не удалось')
        except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
            CLIENT_LOGGER.critical(f'Потеря соединения')
            break


@log
def create_message(sock, account_name='Larin'):
    to_user = input('Получатель сообщения: ')
    message = input('Введите текст сообщения: ')
    message_dict = {
        ACTION: MESSAGE,
        SENDER: account_name,
        DESTINATION: to_user,
        TIME: time.time(),
        MESSAGE_TEXT: message
    }
    CLIENT_LOGGER.debug(f'Словарь сообщения сформирован: {message_dict}')
    try:
        send_message(sock, message_dict)
        CLIENT_LOGGER.info(f'Пользователю {to_user} отправленно сообщение')
    except Exception as e:
        print(e)
        CLIENT_LOGGER.critical('Потеря соединения')
        sys.exit(1)


def print_help():
    print('Команды')
    print('message - отправить сообщение')
    print('help - вывод подсказок по командам')
    print('exit - выход из программы')


@log
def user_interactive(sock, username):
    print_help()
    while True:
        command = input('Введите команду: ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'help':
            print_help()
        elif command == 'exit':
            send_message(sock, create_exit_message(username))
            print('Соединение завершено')
            CLIENT_LOGGER.info('Завершение работы по команде пользователя')
            time.sleep(0.5)
            break
        else:
            print('Команда была не распознана, попробуйте еще раз. help - вывод подсказок по командам')


@log
def create_presence(account_name='Larin'):
    out_data = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    CLIENT_LOGGER.info(f'Сообщение {PRESENCE} пользователю {account_name}')
    return out_data


@log
def process_ans(message):
    CLIENT_LOGGER.debug(f'Приветственное сообщение от сервера {message}')
    if RESPONSE in message:
        if message[RESPONSE] == 200:
            return '200 : OK'
        elif message[RESPONSE] == 400:
            raise ServerError(f'400 : {message[ERROR]}')
    raise ReqFieldMissingError(RESPONSE)


@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default=DEFAULT_IP_address, nargs='?')
    parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверка порта
    if not 1023 < server_port < 65536:
        CLIENT_LOGGER.critical(f'Запуск клиента с неправильным номером порта: {server_port},'
                               f'Допустимые адреса с 1024 по 65536. Клиент не запущен')
        sys.exit(1)

    # Проверка режима работы клиента
    if client_name not in ('listen', 'send'):
        CLIENT_LOGGER.critical(f'Недопустимы режим работы клиента {client_name},'
                               f'доступны режимы: listen и send')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    print('Сработал')
    server_address, server_port, client_name = arg_parser()
    print(client_name)
    if not client_name:
        client_name = input('Введите имя пользователя')
    CLIENT_LOGGER.info(f'Запущен клиент имеющий параметры адрес сервера: {server_address},'
                       f'и порт: {server_port}, Имя пользователя: {client_name}')

    # Создание сокета и обмен
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_message(transport, create_message(client_name))
        answer = process_ans(get_message(transport))
        CLIENT_LOGGER.info(f'Установлено соединение: {answer}')
        print(f'Установлено соединение')
    except json.JSONDecodeError:
        CLIENT_LOGGER.error('Не удачная попытка декодирования Json строки')
        sys.exit(1)
    except ServerError as error:
        CLIENT_LOGGER.error(f'Ошибка соединения: {error.text}')
        sys.exit(1)
    except ReqFieldMissingError as missing_error:
        CLIENT_LOGGER.error(f'Необходимые поля отсутствуют: {missing_error.missing_field}')
        sys.exit(1)
    except (ConnectionResetError, ConnectionError):
        CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {server_address}:{server_port},'
                               f'запрос на подключение отклонен')
        sys.exit(1)
    else:
        # Если соединение с сервером прошло успешно, то начинаем обмен с ним, в требуемом режиме
        # Цикл всей программы
        receiver = threading.Thread(target=message_from_server, args=(transport, client_name))
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=user_interactive, args=(transport, client_name))
        user_interface.daemon = True
        user_interface.start()
        CLIENT_LOGGER.debug('Запущены процессы')
        while True:
            # Режим: отправка сообщений
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
