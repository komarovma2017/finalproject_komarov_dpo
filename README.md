# ValutaTrade Hub

Комплексная платформа для отслеживания и симуляции торговли валютами.

## Описание

ValutaTrade Hub позволяет пользователям:
- Регистрироваться и управлять виртуальным портфелем
- Совершать сделки по покупке/продаже валют
- Отслеживать актуальные курсы в реальном времени
- Получать данные из внешних API (CoinGecko, ExchangeRate-API)

## Архитектура

Проект состоит из двух основных сервисов:

1. **Core Service** - основное приложение с CLI интерфейсом
2. **Parser Service** - сервис обновления курсов валют

### Структура проекта

```
finalproject_mosyagin_group/
├── data/                      # Данные в JSON формате
│   ├── users.json            # Пользователи
│   ├── portfolios.json       # Портфели
│   ├── rates.json            # Кеш курсов
│   └── exchange_rates.json   # История курсов
├── valutatrade_hub/
│   ├── core/                 # Основная бизнес-логика
│   │   ├── currencies.py     # Иерархия валют
│   │   ├── exceptions.py     # Пользовательские исключения
│   │   ├── models.py         # Модели данных
│   │   ├── usecases.py       # Бизнес-логика
│   │   └── utils.py          # Вспомогательные функции
│   ├── infra/                # Инфраструктура
│   │   ├── settings.py       # Singleton настроек
│   │   └── database.py       # Singleton БД
│   ├── parser_service/       # Сервис парсинга
│   │   ├── config.py         # Конфигурация
│   │   ├── api_clients.py    # API клиенты
│   │   ├── updater.py        # Обновление курсов
│   │   ├── storage.py        # Хранилище
│   │   └── scheduler.py      # Планировщик
│   ├── cli/                  # CLI интерфейс
│   │   └── interface.py      # Команды
│   ├── logging_config.py     # Настройка логов
│   └── decorators.py         # Декораторы
├── main.py                   # Точка входа
├── pyproject.toml            # Конфигурация Poetry
├── Makefile                  # Команды для сборки
└── README.md                 # Документация
```

## Установка

### Требования

- Python 3.10+
- Poetry

### Шаги установки

1. Клонируйте репозиторий:
```bash
cd finalproject_mosyagin_group
```

2. Установите зависимости:
```bash
make install
```

3. (Опционально) Настройте API ключ для ExchangeRate-API:
```bash
export EXCHANGERATE_API_KEY="your-api-key-here"
```

Получить ключ можно на https://www.exchangerate-api.com/

## Использование

### Запуск приложения

```bash
make project
# или
poetry run python main.py
```

### Основные команды

#### Регистрация и вход

```bash
# Регистрация
poetry run python main.py register --username alice --password 1234

# Вход
poetry run python main.py login --username alice --password 1234
```

#### Управление портфелем

```bash
# Показать портфель
poetry run python main.py show-portfolio

# Показать в другой базовой валюте
poetry run python main.py show-portfolio --base EUR
```

#### Торговля

```bash
# Купить валюту
poetry run python main.py buy --currency BTC --amount 0.05

# Продать валюту
poetry run python main.py sell --currency BTC --amount 0.02
```

#### Курсы валют

```bash
# Получить курс
poetry run python main.py get-rate --from BTC --to USD

# Обновить курсы из внешних API
poetry run python main.py update-rates

# Показать кешированные курсы
poetry run python main.py show-rates

# Показать топ-3 криптовалюты
poetry run python main.py show-rates --top 3
```

#### Справка

```bash
poetry run python main.py help
```

## Поддерживаемые валюты

### Фиатные
- **USD** - US Dollar (United States)
- **EUR** - Euro (Eurozone)
- **GBP** - British Pound (United Kingdom)
- **RUB** - Russian Ruble (Russian Federation)

### Криптовалюты
- **BTC** - Bitcoin (SHA-256)
- **ETH** - Ethereum (Ethash)
- **SOL** - Solana (PoH)

## Кеш и TTL

Курсы валют кешируются в `data/rates.json` со сроком годности 5 минут (TTL).
Если курс устарел, система предложит выполнить `update-rates`.

## Parser Service

Parser Service обновляет курсы из двух источников:
- **CoinGecko** - для криптовалют
- **ExchangeRate-API** - для фиатных валют

### Обновление курсов

```bash
# Обновить все курсы
poetry run python main.py update-rates

# Обновить только из одного источника
poetry run python main.py update-rates --source coingecko
```

### API ключи

ExchangeRate-API требует ключ. Установите переменную окружения:
```bash
export EXCHANGERATE_API_KEY="your-key"
```

CoinGecko работает без ключа (с ограничениями по количеству запросов).

## Логирование

Все операции логируются в `logs/actions.log` с ротацией файлов:
- Максимальный размер: 10 MB
- Количество backup файлов: 5

Формат лога:
```
INFO 2025-10-09T12:05:22 BUY user='alice' currency='BTC' amount=0.0500 result=OK
```

## Разработка

### Проверка кода

```bash
# Проверка с ruff
make lint
```

### Сборка пакета

```bash
# Сборка
make build

# Публикация (требуется настройка PyPI)
make publish

# Установка из wheel
make package-install
```

### Очистка

```bash
make clean
```

## Технические детали

### Паттерны проектирования

1. **Singleton** - используется для `SettingsLoader` и `DatabaseManager`
2. **ABC (Abstract Base Class)** - иерархия валют и API клиентов
3. **Factory** - фабрика валют `get_currency()`
4. **Decorator** - `@log_action` для логирования операций

### Безопасность

- Пароли хешируются с использованием SHA-256 + соль
- Соль генерируется уникально для каждого пользователя
- Пароли никогда не хранятся в открытом виде

### Хранение данных

Данные хранятся в JSON файлах с атомарной записью (через временный файл).

### Обработка ошибок

Система использует пользовательские исключения:
- `InsufficientFundsError` - недостаточно средств
- `CurrencyNotFoundError` - неизвестная валюта
- `ApiRequestError` - ошибка API

## Требования к коду

- Соответствие PEP8 (проверка через ruff)
- Максимальная длина строки: 86 символов
- Docstrings для всех публичных функций и классов
- Логирование всех критических операций

## Лицензия

None

## Автор

Komarov_dpo

## Дополнительная информация

Для получения дополнительной информации о командах используйте:
```bash
poetry run python main.py help
```

Если возникли проблемы с API, проверьте логи в `logs/actions.log`.

