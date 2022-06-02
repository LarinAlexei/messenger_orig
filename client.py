# Клиент

import socket
import sys
import json
import time
import logging
import logs.client_config_log
from common.variables import *
from common.utils import get_message, send_message
from errors import ReqFieldMissingError, IncorrectDataRecivedError, NonDictInputError

# Клиентский логер
CLIENT_LOGGER = logging.getLogger('client')


def create_presence(account_name='Larin'):
    out_data = {
        ACTION: PRESENCE,
        TIME: time.time(),
        USER: {
            ACCOUNT_NAME: account_name
        }
    }
    return out_data


def process_ans(msg):
    if RESPONSE in msg:
        if msg[RESPONSE] == 200:
            return '200 : OK'
        return f'400 : {msg[ERROR]}'
    raise ValueError


def main():
    try:
        server_address = sys.argv[1]
        server_port = int(sys.argv[2])
        if server_port < 1024 or server_port > 65535:
            raise ValueError
    except IndexError:
        CLIENT_LOGGER.info('Параметры сервера не указаны, но сервер запустится и применит все значения по умолчанию')
        server_address = DEFAULT_IP_address
        server_port = DEFAULT_PORT
    except ValueError:
        CLIENT_LOGGER.error(f'Запуска клиента с недопустимым номером: {server_port}.'
                            f'(номер должен быть от 1024 до 65535)')
        # print('Порт должен быть указан из диапазона от 1024 до 65535.')
        sys.exit(1)

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


if __name__ == '__main__':
    main()
