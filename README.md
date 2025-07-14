# 🚀 FastAPI Currency API

![Python](https://img.shields.io/badge/python-3.13.1+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.12+-blue.svg)
![Tests](https://img.shields.io/badge/tests-pytest-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

>⚠️ **Внимание:** Документация актуальна для [синхронной версии](
> https://github.com/Dev-AlexB/currency_exchange/tree/SyncRoutes_FakeBase).

## 📚 Содержание

- [Краткое описание](#-краткое-описание)
- [Функциональность проекта](#-функциональность-проекта)
- [Что реализовано в проекте](#-что-реализовано-в-проекте)
- [Документация](#-документация)
- [Установка и запуск](#-установка-и-запуск)
- [Структура проекта](#-структура-проекта)
- [Переменные окружения](#-переменные-окружения)
- [Тестирование](#-тестирование)
- [Примеры запросов](#-примеры-запросов)
- [Лицензия](#-лицензия)

## 📝 Краткое описание

RESTful API на FastAPI для расчета обменных операций с валютами с получением 
актуальных курсов валют с использованием внешнего источника 
[apilayer.com](https://apilayer.com/marketplace/currency_data-api).

## 🔧 Функциональность проекта

Основным функционалом является расчет обменных операций с валютами. Пользователь
направляет запрос с кодом обмениваемой валюты, ее количеством и кодом желаемой 
валюты, на которую происходит обмен. В качестве ответа пользователь получает 
количество желаемой валюты, рассчитанной по актуальному курсу, полученному из 
внешнего API. Также реализована возможность осуществить запрос на получение 
списка всех доступных кодов валют. Доступ к эндпоинтам возможен только после 
аутентификации пользователя и получения JWT-токена.

## 🧠 Что реализовано в проекте

- 🔐 **Регистрация и аутентификация пользователей**
  - Хеширование паролей с помощью `bcrypt`
  - JWT-токены (доступ)
  - Защищённые эндпоинты с зависимостями FastAPI

- 💱 **Получение актуальных курсов валют**
  - Подключение к внешнему API
  - Контроль ошибок внешнего API, с предоставлением пользователю кастомных 
сообщений об ошибках
  - ~~Асинхронные HTTP-запросы через `httpx`~~

- ⚙️ **Организованная архитектура**
  - Отделение логики, схем, ошибок, utils
  - Pydantic-схемы для валидации
  - Доступ к **фейковой** базе данных через сервис и репозиторий
  - Доступ к константам через файл конфигурации с использованием 
`pydantic.BaseSettings`
  - Кастомные ошибки и хендлеры
  - Логгирование всех ошибок в консоль

- 🧪 **Тестирование**
  - Покрытие `pytest` + ~~`httpx.AsyncClient`~~ `TestClient`
  - Unit-тестами покрыт весь основной функционал, в том числе сервисы, 
репозитории, схемы Pydantic, запросы к внешнему API, логика авторизации,
кастомные ошибки и хэндлеры
  - Интеграционное тестирование эндпоинтов
  - Использование фикстур 
  - Тестирование как успешных вызовов, так и ошибок
  - Использование параметризованных тестов
  - Моки зависимостей через `dependency_overrides` и `pytest-mock` 
  - В общей сложности 93 теста (покрытие 99% по pytest-cov)

- 🧩 **Автоматизация и стиль**
  - `pre-commit`, `black`, `flake8`, `isort`
  - Хранение конфигурации в окружении - `.env`

## 📘 Документация

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 📦 Установка и запуск

```bash
# Клонировать репозиторий
git clone https://github.com/Dev-AlexB/currency_exchange.git
cd currency_exchange

# Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate  # или .\.venv\Scripts\activate для Windows

# Установить зависимости
pip install -r requirements.txt

# Запуск приложения
uvicorn main:app --reload  # или просто запустить .\main.py
```

## 📁 Структура проекта

```bash
├── app
│   ├── api
│   │   ├── db                    # Работа с базой данных (фэйковой)
│   │   │   ├── database.py       
│   │   │   └── services.py
│   │   ├── endpoints             # Эндпоинты FastAPI
│   │   │   ├── currency.py
│   │   │   └── users.py
│   │   ├── errors                # Обработка ошибок и логгирование
│   │   │   ├── exceptions.py
│   │   │   ├── handlers.py
│   │   │   └── logger.py
│   │   ├── schemas               # Модели Pydantic
│   │   │   ├── currency.py
│   │   │   └── users.py
│   │   └── utils                 # Вспомогательные функции
│   │       └── external_api.py
│   └── core                      # Конфигурация, безопасность
│       ├── config.py
│       └── security.py
├── tests                         # Pytest тесты
│   ├── conftest.py
│   ├── test_database.py
│   ├── test_endpoints.py
│   ├── test_exceptions.py
│   ├── test_ext_api.py
│   ├── test_handlers.py
│   ├── test_schemas.py
│   ├── test_security.py
│   └── test_services.py
├── .env                          # Переменные окружения
├── README.md
├── env_template                  # Шаблон файла .env
├── main.py                       # Точка входа
├── pytest.ini                    # Настройки pytest
└── requirements.txt              # Зависимости
```

## 📌 Переменные окружения

Создайте `.env` на основе `env_template`, заполнив секретный ключ и API-ключ.
Первый можно сгенерировать, например, использовав Bash-команду (в том числе в 
Bash-терминале, устанавливающемся вместе с Git):
```bash
openssl rand -hex 32  
```
API-ключ можно получить зарегистрировавшись на сайте 
[apilayer.com](https://apilayer.com/marketplace/currency_data-api).
```env
JWT__SECRET_KEY='___'

CURRENCY__API_KEY='___'
```

## 🧪 Тестирование
Для запуска тестов используйте команду:
```bash
pytest
```

## 🔍 Примеры запросов

### Регистрация пользователя:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/auth/register/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "string",
  "email": "user@example.com",
  "password": "string"
}'
```

Пример ответа:
```json
{
  "message": "Пользователь string успешно создан.",
  "details": {
    "username": "string",
    "email": "user@example.com"
  }
}
```
### Аутентификация пользователя:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/auth/login/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password&username=admin&password=password&scope=&client_id=string&client_secret=string'
```

Пример ответа:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1MDMyODAyMX0.3K1JCv2wQ1DCubH3Iq1SFFFuszsQi0CJyJ_0AY7nuuA",
  "token_type": "bearer"
}
```

### Получить курс валют:

```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/currency/exchange/?from=USD&to=EUR&amount=1' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1MDMyODAyMX0.3K1JCv2wQ1DCubH3Iq1SFFFuszsQi0CJyJ_0AY7nuuA'
```

Пример ответа:
```json
{
  "from": "USD",
  "to": "EUR",
  "amount": 1,
  "result": 0.87159
}
```

### Получить список валют:

```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/currency/list/' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc1MDMyODAyMX0.3K1JCv2wQ1DCubH3Iq1SFFFuszsQi0CJyJ_0AY7nuuA'
```

Пример ответа:
```json
{
  "currencies": {
    "EUR": "Euro",
    "RUB": "Russian Ruble",
    "USD": "United States Dollar"
  }
}
```

## 📄 Лицензия

Этот проект лицензирован под [MIT License](LICENSE).