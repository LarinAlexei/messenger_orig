# Сервер


import select
import sys
import socket
import logging
# import logs.server_log_config
from common.variables import *
from common.utils import get_message, send_message
# from errors import IncorrectDataRecivedError, ReqFieldMissingError, NonDictInputError
from decos import log
import argparse
from descriptors import Port
from metaclasses import ServerMaker

# Инициализация серверного логгера
SERVER_LOGGER = logging.getLogger('server')


# парсер аргументов командной строки
@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=DEFAULT_PORT, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return listen_address, listen_port


# Классы сервера
class Server(metaclass=ServerMaker):
    port = Port()

    def __init__(self, listen_address, listen_port):
        # Параметры подключения
        self.addr = listen_address
        self.port = listen_port

        # Список клиентов
        self.clients = []

        # Сообщения на отправке
        self.messages = []

        # Словарь, содержащий сопоставленные имена и сокеты
        self.names = dict()

        self.sock = None

    def init_socket(self):  # Инициализация сокета
        # Сохраняем событие
        SERVER_LOGGER.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.addr}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        # Выполняем подготовку сокета
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)
        # Слушаем сокет
        self.sock = transport
        self.sock.listen()

    def main_loop(self):
        # Инициализацию сокета
        self.init_socket()

        # Основной цикл программы
        while True:
            # Подключение
            try:
                client, client_address = self.sock.accept()
            except OSError as err:
                pass
            else:
                SERVER_LOGGER.info(f'Установлено соединение с ПК {client_address}')
                print(f'Установлено соединение с ПК {client_address}')
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем наличие клиентов
            try:
                if self.clients:
                    recv_data_lst, send_data_lst, err_lst = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass

            # Принимаем сообщения и если там есть информация,
            # кладём в словарь, если ошибка, удаляем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    print('клиент', client_with_message)
                    try:
                        self.process_client_msg(get_message(client_with_message), client_with_message)
                    except:
                        SERVER_LOGGER.info(f'Клиент {client_with_message.getpeername()} '
                                           f'отключился от сервера.')
                        self.clients.remove(client_with_message)

            # Если есть сообщения, то обрабатываем каждое из сообщенияй
            for msg in self.messages:
                try:
                    print('Вызов self.process_message: ', msg)
                    self.process_message(msg, send_data_lst)
                    print('Вызова self.process_message выполнен успешно!')
                except:
                    SERVER_LOGGER.info(f'Связь с клиентом с именем {msg[DESTINATION]} была потеряна')
                    self.clients.remove(self.names[msg[DESTINATION]])
                    del self.names[msg[DESTINATION]]
            self.messages.clear()

    def process_message(self, message, listen_socks):
        print('сработала ф-ия process_message ')
        if message[DESTINATION] in self.names and self.names[message[DESTINATION]] in listen_socks:
            send_message(self.names[message[DESTINATION]], message)
            SERVER_LOGGER.info(f'Отправлено сообщение пользователю {message[DESTINATION]} '
                               f'от пользователя {message[SENDER]}.')
        elif message[DESTINATION] in self.names and self.names[message[DESTINATION]] not in listen_socks:
            raise ConnectionError
        else:
            SERVER_LOGGER.error(
                f'Пользователь {message[DESTINATION]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')

    def process_client_msg(self, message, client):
        """
        Функция обеспечивает обработку сообщений от клиентов.
        :param message: словарь
        :param client: идентификатор клиента (имя)
        :return:
        """
        SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаемм
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message and USER in message:
            # Если такой пользователь ещё не зарегистрирован, регистрируем,
            # иначе отправляем отказ.
            if message[USER][ACCOUNT_NAME] not in self.names.keys():
                self.names[message[USER][ACCOUNT_NAME]] = client
                send_message(client, RESPONSE_200)
            else:
                response = RESPONSE_400
                response[ERROR] = 'Такое имя уже существует'
                send_message(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений.
        elif ACTION in message and message[ACTION] == MESSAGE and DESTINATION in message and TIME in message \
                and SENDER in message and MESSAGE_TEXT in message:
            self.messages.append(message)
            return
        # Когда клиент вышел
        elif ACTION in message and message[ACTION] == EXIT and ACCOUNT_NAME in message:
            self.clients.remove(self.names[ACCOUNT_NAME])
            self.names[ACCOUNT_NAME].close()
            del self.names[ACCOUNT_NAME]
            return
        # Иначе Bad request
        else:
            response = RESPONSE_400
            response[ERROR] = 'Запрос некорректен.'
            send_message(client, response)
            return


def main():
    """
    Функция получает параметры командной строки, которые были переданы при запуске и
    создает с ними экземпляр класса сервера.
    Далее функция запускает метод main_loop, отвечающий за инициализацию сокета.
    """
    listen_address, listen_port = arg_parser()
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
