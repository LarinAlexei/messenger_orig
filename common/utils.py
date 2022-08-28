# Утилиты приложения

import sys
import json
from common.variables import MAX_PACKAGE_LENGTH, ENCODING
from common.decos import log
from errors import IncorrectDataRecivedError, NonDictInputError
sys.path.append('../')


@log
def get_message(client):
    encoded_response = client.recv(MAX_PACKAGE_LENGTH)
    json_response = encoded_response.decode(ENCODING)
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@log
def send_message(sock, message):
    if not isinstance(message, dict):
        raise NonDictInputError
    js_message = json.dumps(message)
    encoded_message = js_message.encode(ENCODING)
    sock.send(encoded_message)
