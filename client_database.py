from sqlalchemy import create_engine, Table, Column, Integer, String, Text, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
from common.variables import *
import datetime


# Класс базы данных сервера
class ClientDatabase:  # Отображение известных нам пользователей
    class KnownUsers:
        def __int__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:  # История сообщений
        def __int__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        def __int__(self, contact):
            self.id = None
            self.name = contact

    def __int__(self, name):  # Конструктор класса
        # Создаём движок базы данных, поскольку разрешено несколько клиентов одновременно,
        # каждый должен иметь свою БД.
        # Поскольку клиент мультипоточный, то необходимо отключить проверки на подключения
        # с разных потоков, иначе sqlite3.ProgrammingError
        self.database_engine = create_engine(f'sqlite:///client_{name}.db3',
                                             echo=False,
                                             pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        # Создаем MetaData объект
        self.metadata = MetaData()

        # Создание таблицу с известными пользователями
        users = Table('known_users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )

        # Создание таблицы с историей сообщений клиентов
        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('from_user', String),
                        Column('to_user', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )

        # Создание таблицы контактов
        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        # Создание таблицы
        self.metadata.create_all(self.database_engine)

        # Создание отображений
        mapper(self.KnownUsers, users)
        mapper(self.MessageHistory, history)
        mapper(self.Contacts, contacts)

        # Создание сессии
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session

        # Очищаем таблицу контактов, потому что при запуске мы их подгружаем из сервера
        self.session.query(self.Contacts).delete()
        self.session.commit()

    # Функция добавления контактов
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # Функция удаления контактов
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    # Функция добавления известных пользователей
    # Пользователей получаем только с сервера, поэтому таблица очищается
    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    # Функция сохраняющая сообщения
    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    # Функция возвращает контакты
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    # Функция возвращает список известных пользователей
    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    # Функция проверяет наличие пользователя в таблице известных пользователей
    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    # Функция проверяет наличие пользователя в Контактах
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    # Функция возвращает историю сообщений
    def get_history(self, from_who=None, to_who=None):
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(from_user=to_who)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]


# отладка
if __name__ == '__main__':
    test_db = ClientDatabase('test1')
    for i in ['test3', 'test4', 'test5']:
        test_db.add_contact(i)
    test_db.add_contact('test4')
    test_db.add_users('test1', 'test2', 'test3', 'test4', 'test5')
    test_db.save_message('test1', 'test2',
                         f'Привет! Я тестовое сообщение от {datetime.datetime.now()}!')
    test_db.save_message('test2', 'test1',
                         f'Привет! Я второе тестовое сообщение от {datetime.datetime.now()}!')
    print(test_db.get_contacts())
    print(test_db.get_users())
    print(test_db.check_user('test1'))
    print(test_db.check_user('test32'))
    print(test_db.get_history('test5'))
    print(test_db.get_history(to_who='test5'))
    print(test_db.get_history('test2'))
    test_db.del_contact('test3')
    print(test_db.get_contacts())
