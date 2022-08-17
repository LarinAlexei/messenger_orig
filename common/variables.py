# Константы проекта
import logging

# Порт по умолчанию для сетевого взаимодействия
DEFAULT_PORT = 7777
# IP адрес по умолчанию для подключения клиента
DEFAULT_IP_address = '127.0.0.1'
# Максимальная очередь подключений
MAX_CONNECTIONS = 5
# Максимальная длина сообщения в байтах
MAX_PACKAGE_LENGTH = 1024
# Кодировка проекта
ENCODING = 'utf-8'
# База данных для хранения данных
SERVER_DATABASE = 'sqlite://server_base.db3'
# Текущий уровень логирования
LOGGING_LEVEL = logging.DEBUG
# Хранение данных сервера
SERVER_CONFIG = 'server_dist.ini'

# Описание протокола JIM:
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'sender'
DESTINATION = 'to'

# Прочие ключи, используемые в протоколе
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'

# Ответы:
# 202
RESPONSE_202 = {RESPONSE: 202,
                LIST_INFO:None
                }
# 400
RESPONSE_400 = {
    RESPONSE: 400,
    ERROR: None
}
