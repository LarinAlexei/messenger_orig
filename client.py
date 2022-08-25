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
from metaclasses import ClientMaker

# Клиентский логер
CLIENT_LOGGER = logging.getLogger('client')


# Класс взаимодействует с пользователем, формирует и отправляет ему сообщения
class ClientSender(threading.Thread, metaclass=ClientMaker):

    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def create_exit_message(self):
        """
        Функция создает словарь с сообщение о выходе
        """
        return {
            ACTION: EXIT,
            TIME: time.time(),
            ACCOUNT_NAME: self.account_name,
        }

    def create_message(self):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер.
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            ACTION: MESSAGE,
            SENDER: self.account_name,
            DESTINATION: to_user,
            TIME: time.time(),
            MESSAGE_TEXT: message
        }
        CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        try:
            send_message(self.sock, message_dict)
            CLIENT_LOGGER.info(f'Отправлено сообщение для пользователя {to_user}')
        except Exception as e:
            print(e)
            CLIENT_LOGGER.critical('Потеряно соединение с сервером.')
            sys.exit(1)

    def run(self):
        """
        Функция взаимодействия с пользователем,
        запрашивает команды, отправляет сообщения
        """
        # 1. покажем справку
        self.print_help()

        # 2. предлагаем пользователю ввести команду
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()  # параметры для метода будут установлены в __init__
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                send_message(self.sock, self.create_exit_message())
                print('Завершение соединения.')
                CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - '
                      'вывести поддерживаемые команды.')

    @staticmethod
    def print_help():
        """Функция выводящяя справку по использованию"""
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')


# Класс обеспечивает получение сообщений с сервера
class ClientReader(threading.Thread, metaclass=ClientMaker):

    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    def run(self):
        """
        Основной цикл приемки сообщений
        """
        while True:
            try:
                message = get_message(self.sock)
                if ACTION in message and message[ACTION] == MESSAGE and \
                        SENDER in message and DESTINATION in message \
                        and MESSAGE_TEXT in message and message[DESTINATION] == self.account_name:
                    print(f'\nПолучено сообщение от пользователя {message[SENDER]}:'
                          f'\n{message[MESSAGE_TEXT]}')
                    CLIENT_LOGGER.info(f'Получено сообщение от пользователя {message[SENDER]}:'
                                       f'\n{message[MESSAGE_TEXT]}')
                else:
                    CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')
            except IncorrectDataRecivedError:
                CLIENT_LOGGER.error(f'Не удалось декодировать полученное сообщение.')
            except (OSError, ConnectionError, ConnectionAbortedError,
                    ConnectionResetError, json.JSONDecodeError):
                CLIENT_LOGGER.critical(f'Потеряно соединение с сервером.')
                break

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
    print('Клиентский модуль.')
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
        send_message(transport, create_presence(client_name))
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
        receiver = ClientReader(client_name, transport)
        receiver.daemon = True
        receiver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = ClientSender(client_name, transport)
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
