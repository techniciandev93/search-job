# Сравниваем вакансии программистов

Этот скрипт предназначен для поиска зарплаты по языкам программирования на ресурсах [superjob.ru](https://superjob.ru) и [hh.ru](https://hh.ru) используя их API

## Как установить

Python 3.8 должен быть уже установлен.
Затем используйте `pip` (или `pip3`, есть конфликт с Python2) для установки зависимостей:
```
pip install -r requirements.txt
```

Создайте файл `.env` в корневой директории проекта и добавьте переменную окружения:

```
SUPERJOB_TOKEN=YOUR_SUPERJOB_TOKEN
```
## Как запустить
Запустите скрипт, указав несколько языков программирования через пробел после ключа -l:
```
python main.py -l Python Java GO
```
По умолчанию произойдёт поиск по языку Python:
```
python main.py
```

По окончанию будут выведены таблицы со статистикой по Москве HeadHunter и SuperJob:
```
+SuperJob Moscow--------+------------------+---------------------+------------------+
| Язык программирования | Вакансий найдено | Вакансий обработано | Средняя зарплата |
+-----------------------+------------------+---------------------+------------------+
| Python                | 12               | 8                   | 76075            |
| Java                  | 3                | 2                   | 314000           |
+-----------------------+------------------+---------------------+------------------+
+HH Moscow--------------+------------------+---------------------+------------------+
| Язык программирования | Вакансий найдено | Вакансий обработано | Средняя зарплата |
+-----------------------+------------------+---------------------+------------------+
| Python                | 1792             | 394                 | 205215           |
| Java                  | 1710             | 298                 | 226290           |
+-----------------------+------------------+---------------------+------------------+
```

## Примечания

- Для работы скрипта необходимо иметь API-токен SuperJob [api.superjob.ru](https://api.superjob.ru/)


Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).