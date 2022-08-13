import inspect
import sys
import logging
import logs.server_config_log
import traceback


def log(func_to_log):
    def log_saver(*args, **kwargs):
        logger_name = 'server' if 'server.py' in sys.argv[0] else 'client'
        LOGGER = logging.getLogger(logger_name)
        rt = func_to_log(*args, **kwargs)

        LOGGER.debug(f'Вызвана функция {func_to_log.__name__} с параметрами {args}, {kwargs}')
        LOGGER.debug(f'Функция {func_to_log.__name__}'
                     f' вызвана из этой функции {traceback.format_stack()[0].strip().split()[-1]}')

        return rt

    return log_saver()
