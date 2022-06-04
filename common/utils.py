# Утилиты приложения

import json
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from decos import logs


@logs
def get_message(client):
    # Принимаем сообщение в байтах
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    # Проводим валидацию данных и если все ок, то возвращаем словарь
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        if isinstance(json_response, str):
            response = json.loads(json_response)  # из строки получаем словарь
            if isinstance(response, dict):
                return response  # возвращаем словарь
            raise ValueError
        raise ValueError
    raise ValueError


@logs
def send_message(sock, message):
    if not isinstance(message, dict):
        raise TypeError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
