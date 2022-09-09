from setuptools import setup, find_packages

setup(name="my_very_best_mess_client",
      version="0.1.0",
      description="Mess Client Mess",
      author="Alexey Larin",
      author_email="larin_aleksey93@mail.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
