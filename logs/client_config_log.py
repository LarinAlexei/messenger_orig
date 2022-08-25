import logging

# Создадим логер с именем 'client'
logger = logging.getLogger('client')

# Форматирование
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
# Создаем файловый обработчик логирования
su = logging.FileHandler('logs/client.log', encoding='utf-8')
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
