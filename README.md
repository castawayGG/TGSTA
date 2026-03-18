# TGSTA — Telegram Stars Payment Bot

Telegram-бот для приёма оплат в **рублях** (через Telegram Payments) и ведения очереди заявок на **пополнение Telegram Stars** пользователю в полуавтоматическом режиме.

> ⚠️ **Важно:** Stars зачисляются **вручную администратором** после получения оплаты. Бот не отправляет Stars автоматически — только принимает платёж, ведёт очередь заявок и уведомляет пользователей.

---

## Возможности

- 🛒 **Меню покупки** — выбор пакета Stars, ввод @username получателя
- 💳 **Оплата в рублях** через Telegram Payments (ЮKassa, CloudPayments, и др.)
- 📋 **«Мои заказы»** — история заказов с ID, пакетом, суммой, статусом и датами
- 🔔 **Уведомления** — пользователь получает уведомления при каждом изменении статуса
- 🔧 **Админ-панель** — очередь заказов, смена статусов, комментарии, запрос уточнений
- 🗄 **SQLite** (по умолчанию) или **PostgreSQL** через `DATABASE_URL`
- 🐳 **Docker** + **docker-compose** для простого деплоя

---

## Статусы заказа

| Статус | Описание |
|--------|----------|
| `awaiting_payment` | Ожидает оплаты |
| `paid` | Оплачен, ожидает обработки администратором |
| `processing` | Взят администратором в работу |
| `needs_info` | Требуется уточнение от пользователя |
| `done` | Исполнен ✅ |
| `canceled` | Отменён ❌ |

---

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone https://github.com/castawayGG/TGSTA.git
cd TGSTA
cp .env.example .env
```

Отредактируйте `.env`:

```env
BOT_TOKEN=your_bot_token          # от @BotFather
PROVIDER_TOKEN=your_provider_token # от @BotFather → Payments
ADMIN_IDS=123456789               # ваш Telegram user_id
```

### 2. Запуск локально (Python)

```bash
# Создайте виртуальное окружение
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows

# Установите зависимости
pip install -e ".[dev]"

# Создайте директорию для базы данных
mkdir -p data

# Примените миграции
alembic upgrade head

# Запустите бота
python -m app.bot
```

### 3. Запуск через Docker (SQLite)

```bash
# Соберите и запустите
docker compose --profile sqlite up -d --build

# Просмотр логов
docker compose logs -f bot-sqlite
```

### 4. Запуск через Docker (PostgreSQL)

Добавьте в `.env`:
```env
DATABASE_URL=postgresql+asyncpg://tgsta:changeme@postgres:5432/tgsta
POSTGRES_PASSWORD=changeme
```

```bash
docker compose --profile with-postgres up -d --build
```

---

## Деплой на VDS (systemd)

### 1. Установка зависимостей

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv git
```

### 2. Создание пользователя и клонирование

```bash
sudo useradd -m -s /bin/bash tgsta
sudo su - tgsta
git clone https://github.com/castawayGG/TGSTA.git
cd TGSTA
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e "."
cp .env.example .env
nano .env                          # заполните BOT_TOKEN, PROVIDER_TOKEN, ADMIN_IDS
mkdir -p data
alembic upgrade head
```

### 3. systemd unit

Создайте `/etc/systemd/system/tgsta.service`:

```ini
[Unit]
Description=TGSTA Telegram Stars Bot
After=network.target

[Service]
Type=simple
User=tgsta
WorkingDirectory=/home/tgsta/TGSTA
Environment=PATH=/home/tgsta/TGSTA/.venv/bin
ExecStart=/home/tgsta/TGSTA/.venv/bin/python -m app.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgsta
sudo systemctl start tgsta
sudo systemctl status tgsta
```

---

## Конфигурация (.env)

| Переменная | Обязательна | Описание |
|-----------|-------------|----------|
| `BOT_TOKEN` | ✅ | Токен бота от @BotFather |
| `PROVIDER_TOKEN` | ✅ | Токен провайдера оплаты (Payments в @BotFather) |
| `ADMIN_IDS` | ✅ | Telegram user ID администраторов через запятую |
| `DATABASE_URL` | ❌ | DSN для PostgreSQL. По умолчанию: SQLite `./data/app.db` |
| `CURRENCY` | ❌ | Валюта (по умолчанию `RUB`) |
| `PACKAGES_JSON` | ❌ | JSON-массив пакетов (см. ниже) |
| `ORDER_SLA_TEXT` | ❌ | Текст о сроках исполнения |
| `SUPPORT_CONTACT` | ❌ | Контакт поддержки (e.g. `@support`) |
| `TERMS_URL` | ❌ | URL оферты |
| `TERMS_TEXT` | ❌ | Текст оферты (имеет приоритет над `TERMS_URL`) |

### Настройка пакетов

```env
PACKAGES_JSON=[
  {"stars":100,"price":19900,"label":"100 ⭐"},
  {"stars":250,"price":44900,"label":"250 ⭐"},
  {"stars":500,"price":84900,"label":"500 ⭐"},
  {"stars":1000,"price":159900,"label":"1000 ⭐"}
]
```

- `stars` — количество Stars в пакете
- `price` — цена в **копейках** (19900 = 199 ₽)
- `label` — отображаемое название

---

## Получение токена провайдера

1. Откройте [@BotFather](https://t.me/BotFather)
2. Выберите вашего бота → **Payments** → подключите провайдера (ЮKassa, CloudPayments, и др.)
3. Скопируйте полученный `PROVIDER_TOKEN` в `.env`

Для тестирования используйте тестовый токен от `@BotFather` (Payments → Test).

---

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Запуск и главное меню |
| `/help` | Помощь |
| `/orders` | Мои заказы |
| `/admin` | Панель администратора (только для `ADMIN_IDS`) |

---

## Разработка

### Запуск тестов

```bash
pytest -v
```

### Линтинг

```bash
ruff check .
black --check .
mypy app/
```

### pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

### Alembic: создание новой миграции

```bash
alembic revision --autogenerate -m "your_change"
alembic upgrade head
```

---

## Структура проекта

```
TGSTA/
├── app/
│   ├── bot.py              # Точка входа
│   ├── config.py           # Конфигурация из .env
│   ├── database.py         # SQLAlchemy engine, session
│   ├── models.py           # ORM модели (User, Order)
│   ├── handlers/
│   │   ├── common.py       # /start, /help, правила
│   │   ├── purchase.py     # Флоу покупки
│   │   ├── payments.py     # pre_checkout + successful_payment
│   │   ├── orders.py       # «Мои заказы»
│   │   └── admin.py        # Админ-панель
│   ├── keyboards/
│   │   ├── main_menu.py    # Reply/inline клавиатуры
│   │   └── admin.py        # Кнопки управления заказами
│   └── utils/
│       └── validators.py   # Валидация username, парсинг PACKAGES_JSON
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial.py  # Начальная миграция
├── tests/
│   ├── test_validators.py  # Тесты валидации
│   └── test_config.py      # Тесты парсинга пакетов
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Лицензия

MIT