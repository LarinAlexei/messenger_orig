# import inspect
import sys
import logging
import logs.server_config_log
import logs.client_config_log

# import traceback

# определение источника запуска
if sys.argv[0].find('client_dist') == -1:
    # или сервер
    logger = logging.getLogger('server_dist')
else:
    # или клиент
    logger = logging.getLogger('client_dist')


def log(func_log):
    def saver_log(*args, **kwargs):
        logger.debug(f'Была вызвана функция {func_log.__name__} c параметрами {args}, {kwargs}'
                     f'Вызываем из модуля {func_log.__module__}')
        ret = func_log(*args, **kwargs)
        return ret
    return saver_log
