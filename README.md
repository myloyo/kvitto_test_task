![CI](https://github.com/myloyo/kvitto_test_task/actions/workflows/ci.yml/badge.svg)
# Kvitto Payments

API оплаты курсов: тарифы, создание платежа, статусы от банка.

## Слои

- `app/domain` — правила: деньги, промокод, статусы, исключения
- `app/application` — сценарии (создать платёж, сменить статус)
- `app/infrastructure` — база, репозитории, банк, HMAC
- `app/api` — HTTP: роуты и схемы

## Запуск

Python 3.11+, [Poetry](https://python-poetry.org/).

```bash
poetry env use python3.11
poetry install
copy .env.example .env
poetry run uvicorn app.main:app --reload
```

На Linux/macOS вместо `copy` используйте `cp .env.example .env`.

Виртуальное окружение создаётся в `.venv` внутри проекта (`poetry.toml`). Активация: `.venv\Scripts\activate` (Windows) или `source .venv/bin/activate` (Linux/macOS).

Документация: http://127.0.0.1:8000/docs  
Проверка: http://127.0.0.1:8000/health

## Тесты

```bash
poetry run pytest
```

## Примеры

Список тарифов:

```bash
curl http://127.0.0.1:8000/tariffs
```

Создать платёж (standard, промокод, рассрочка 3 месяца):

```bash
curl -X POST http://127.0.0.1:8000/payments ^
  -H "Content-Type: application/json" ^
  -H "Idempotency-Key: pay-1" ^
  -d "{\"tariff_id\":\"standard\",\"email\":\"a@b.c\",\"method\":\"installment\",\"installment_months\":3,\"promo_code\":\"kvitto10\"}"
```

Повтор с тем же `Idempotency-Key` вернёт тот же платёж и HTTP 200.

Получить платёж:

```bash
curl http://127.0.0.1:8000/payments/1
```

Вебхук банка:

```bash
curl -X POST http://127.0.0.1:8000/webhooks/bank ^
  -H "Content-Type: application/json" ^
  -d "{\"payment_id\":1,\"status\":\"succeeded\"}"
```

Запрещённый переход статуса: `409` и `{"error":"invalid_transition"}`.

Суммы в API и в базе — целые копейки: `19 900 ₽` → `1990000`. Промокод `KVITTO10` даёт −10%, регистр не важен.

Опционально: проверка подписи вебхука (`WEBHOOK_VERIFY_SIGNATURE=true`, заголовок `X-Signature` — HMAC-SHA256 тела с `WEBHOOK_SECRET`), фильтры `GET /payments?email=&status=`.
