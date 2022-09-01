# Лаунчер

import subprocess


def main():
    processes = []

    while True:
        action: str = input('Выберите действие: q - выход, '
                            's - запустить сервер и клиенты, k - запустим клиента, '
                            'x - закрыть все окна: ')

        if action == 'q':
            break

        elif action == 's':
            # Запускаем сервер
            processes.append(subprocess.Popen('python server.py',
                                              creationflags=subprocess.CREATE_NEW_CONSOLE))
        elif action == 'k':
            # Запускаем нужное количество клиентов
            clients_count = int(input('Введите количество тестовых клиентов для запуска: '))
            for i in range(clients_count):
                processes.append(subprocess.Popen(f'python client.py -n test{i + 1} -p 123456',
                                                  creationflags=subprocess.CREATE_NEW_CONSOLE))

        elif action == 'x':
            while processes:
                processes.pop().kill()


if __name__ == '__main__':
    main()
