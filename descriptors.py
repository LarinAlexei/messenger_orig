import logging
import sys

logger = logging.getLogger('server')

# Инициализация логера
# Определение источника запуска
if sys.argv[0].find('client_dist') == -1:
    # Сервер
    logger = logging.getLogger('server_dist')
else:
    # Клиент
    logger = logging.getLogger('client_dist')


# Дескриптор для описания порта:
class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(
                f'Попытка запуска с указанием неподходящего порта {value}. Допустимы адреса с 1024 до 65535.')
            exit(1)

        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
