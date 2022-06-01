# Сервер


import sys
import json
import socket
from common.variables import *
from common.utils import get_message, send_message


def process_client_msg(msg):
    print('сработал')
    print(ACTION, msg)
    conditions = ACTION in msg and msg[ACTION] == PRESENCE \
        and TIME in msg and USER in msg \
        and msg[USER][ACCOUNT_NAME] == 'Larin'
    # Если True, то отдаем 200 код.
    if conditions:
        return {RESPONSE: 200}
    return {
        RESPONSE: 400,
        ERROR: 'Bad request',
    }


def main():
    print('сработал')
    # Получаем порт или устанавливаем значение по умолчанию
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = DEFAULT_PORT
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('Вы не указали номер порта после параметра - \'p\'!')

    # Получаем ip или устанаваливаем значение по умолчанию
    try:
        if '-a' in sys.argv:
            listen_ip = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_ip = ''
    except IndexError:
        print('После параметра -a необходимо указать адрес, '
              'который будет слушать сервер.')


    # Готовим сокет
    transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    transport.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    transport.bind((listen_ip, listen_port))

    # Слушаем порт
    transport.listen(MAX_CONNECTIONS)

    while True:
        client, client_address = transport.accept()
        try:
            # Получаем сообщение от клиента из функции, созданной в utils
            msg_from_client = get_message(client)
            print(msg_from_client)
            # Готовим ответ клиенту
            response = process_client_msg(msg_from_client)
            # Отправляем ответ клиенту и закрываем сокет
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Принято некорректное сообщение от клиента!')
            client.close()


if __name__ == '__main__':
    main()
