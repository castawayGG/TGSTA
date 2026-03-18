# ⭐ TGSTA — Telegram Stars Purchase Bot

Телеграм-бот для оформления заявок на пополнение Telegram Stars.  
Принимает оплату в RUB через Telegram Payments, создаёт заказы и уведомляет пользователей об их статусе.

> **Важно:** исполнение заявок осуществляется оператором **вручную**. Автоматическая отправка Stars не реализована и не предусмотрена.

---

## Возможности

- **Меню**: Купить Stars / Мои заказы / Помощь / Правила & Оферта
- **Покупка**: выбор пакета → указание получателя → счёт в RUB → оплата
- **Мои заказы**: история последних N заказов с актуальными статусами
- **Очередь для оператора** (`/admin`): список оплаченных заказов, смена статуса, уведомления
- **Идемпотентность**: защита от двойного начисления по `telegram_payment_charge_id`
- **Хранение**: SQLite (по умолчанию) или PostgreSQL через `DATABASE_URL`
- **Миграции**: Alembic 2.0

---

## Требования

- Python 3.11+
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- Payment Provider Token (ЮKassa, CloudPayments и др.)
- VDS / VPS с доступом в интернет

---

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone https://github.com/castawayGG/TGSTA.git
cd TGSTA
```

### 2. Создать `.env`

```bash
cp .env.example .env
nano .env
```

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен бота от @BotFather |
| `PROVIDER_TOKEN` | Токен платёжного провайдера (ЮKassa и др.) |
| `ADMIN_IDS` | Telegram user_id администраторов (через запятую) |
| `PACKAGES_JSON` | Пакеты Stars в формате JSON |
| `DATABASE_URL` | URL базы данных (SQLite по умолчанию) |
| `SLA_TEXT` | Текст SLA, показываемый пользователю после оплаты |

**Формат `PACKAGES_JSON`:**
```json
[{"stars":100,"price_rub":199},{"stars":250,"price_rub":449},{"stars":500,"price_rub":849},{"stars":1000,"price_rub":1599}]
```

---

## Деплой: Docker Compose (рекомендуется)

### SQLite

```bash
docker compose --profile sqlite up -d --build
```

### PostgreSQL

Раскомментируйте в `.env` строки PostgreSQL, затем:

```bash
docker compose --profile postgres up -d --build
```

### Логи

```bash
docker compose logs -f
```

---

## Деплой: systemd (без Docker)

```bash
# Установить зависимости
sudo apt update && sudo apt install -y python3.11 python3.11-venv
cd /opt/tgsta
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .

# Применить миграции
alembic upgrade head
```

Создать `/etc/systemd/system/tgsta-bot.service`:

```ini
[Unit]
Description=TGSTA Telegram Stars Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/tgsta
EnvironmentFile=/opt/tgsta/.env
ExecStart=/opt/tgsta/.venv/bin/python -m bot.main
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tgsta-bot
journalctl -u tgsta-bot -f
```

---

## Миграции Alembic

```bash
alembic upgrade head                          # применить все
alembic revision --autogenerate -m "change"  # создать новую
alembic downgrade -1                         # откатить последнюю
```

---

## Получение токенов

### BOT_TOKEN
1. [@BotFather](https://t.me/BotFather) → `/newbot` → скопируйте токен

### PROVIDER_TOKEN (ЮKassa)
1. Зарегистрируйтесь на [ЮKassa](https://yookassa.ru) как самозанятый
2. [@BotFather](https://t.me/BotFather) → `/mybots` → бот → Payments → ЮKassa → скопируйте токен

### ADMIN_IDS
Узнать свой user_id: [@userinfobot](https://t.me/userinfobot)

---

## Статусы заказов

| Статус | Описание |
|---|---|
| `created` | Заказ создан |
| `awaiting_username` | Ожидание получателя |
| `invoice_sent` | Счёт выставлен |
| `paid` | Оплачен, ожидает оператора |
| `processing` | Оператор взял в работу |
| `completed` | Исполнен ✅ |
| `cancelled` | Отменён ❌ |
| `clarification_requested` | Требуется уточнение |

---

## Разработка и тесты

```bash
pip install -e ".[dev]"
pytest
ruff check .
black --check .
```

---

## Лицензия

MIT
