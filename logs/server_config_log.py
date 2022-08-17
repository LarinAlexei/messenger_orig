import logging
from logging.handlers import TimedRotatingFileHandler


# Сщздадим логер с именем 'server'
logger = logging.getLogger('server')

# Создадим форматирование
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
su = TimedRotatingFileHandler('logs/server.log', when='D', interval=1, backupCount=5)

su.setLevel(logging.DEBUG)
su.setFormatter(formatter)
# новый обработчик событий
logger.addHandler(su)
logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    # Создадим потоковый обработчик
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)
    logger.info('Тест')
    logger.critical('critical error')
