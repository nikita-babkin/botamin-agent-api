# Botamin Booking API

> Актуальный production-деплой использует HTTPS через Caddy. См. DEPLOY_HTTPS.md.

API календарной логики для голосового агента Botamin.

## Возможности

- возвращает ровно два доступных слота;
- не назначает встречи на сегодня и выходные;
- разрешает начало встречи с 09:00 до 17:00 МСК;
- защищает рабочие endpoints API-ключом;
- сохраняет встречи в `data/bookings.jsonl`;
- отклоняет повторное бронирование занятого слота.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export BOTAMIN_API_KEY=test-secret
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Проверка:

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/available-slots \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-secret" \
  -d '{"date_mode":"nearest","period":"any"}'
```

Swagger UI доступен по адресу `http://127.0.0.1:8000/docs`.

## Тесты

```bash
pytest -v
```

## Деплой на VPS

1. Клонируйте репозиторий в `/opt/botamin-api`.
2. Создайте `.venv` и установите `requirements.txt`.
3. Создайте `/etc/botamin-api.env` с `BOTAMIN_API_KEY`.
4. Проверьте пользователя и группу в `deploy/botamin-api.service`.
5. Установите и запустите сервис:

```bash
sudo cp deploy/botamin-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now botamin-api
sudo ufw allow 8000/tcp
```

После этого API доступен по `http://PUBLIC_IP:8000`.

Для ElevenLabs используются:

- `POST http://PUBLIC_IP:8000/available-slots`
- `POST http://PUBLIC_IP:8000/book-meeting`

В оба webhook-запроса добавьте секретный заголовок `X-API-Key`.
