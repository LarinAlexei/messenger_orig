import dis


# Метакласс для проверки соответствия сервера:


class ServerMarker(type):
    def __int__(cls, clsname, bases, clsdict):
        # Список методов, которые используются в функциях наших классов
        methods = []
        attrs = []  # Атрибуты, вызываемые функциями классов
        for func in clsdict:
            try:
                ret = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:  # Заполнение списка методами, используещиеся в классах
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # Заполнение список атрибутами, используещиеся в классах
                            attrs.append(i.argval)
                    if 'connect' in methods:
                        raise TypeError('Использование метода connect недопустимо в серверном классе')
                    # Если сокет не инициализировался SOCK_STREAM(TCP) AF_INET(IPv4), вызывается исключение
                    if not ('SOCK_STREAM' in attrs and 'AF_INET' in attrs):
                        raise TypeError('Некорректная инициализация сокета.')
                    # Вызываем конструктор предка:
                    super().__init__(clsname, bases, clsdict)

                # Метакласс для проверки клиента
                class ClientMaker(type):
                    def __init__(cls, clsname, bases, clsdict):
                        # Список методов, которые используются в классах:
                        methods = []
                        for func in clsdict:
                            try:
                                ret = dis.get_instructions(clsdict[func])
                                # Если не функция, то отлавливаем исключение
                            except TypeError:
                                pass
                            else:
                                for i in ret:
                                    if i.opname == 'LOAD_GLOBAL':
                                        if i.argval not in methods:
                                            methods.append(i.argval)
                        # Обнаружено использование недопустимого метода accept, listen, socket то исключение:
                        for command in ('accept', 'listen', 'socket'):
                            if command in methods:
                                raise TypeError('В классе обнаружено использование запрещённого метода')
                        # Вызов get_message или send_message из utils считаем корректным сокетом
                        if 'get_message' in methods or 'send_message' in methods:
                            pass
                        else:
                            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
                        super().__init__(clsname, bases, clsdict)
