# HTTPS для Botamin Booking API

`docker compose` автоматически объединяет `compose.yaml` и
`compose.override.yaml`. Caddy принимает публичные запросы на портах 80/443 и
передаёт их FastAPI-контейнеру `api:8000`.

## Переменные окружения

В серверном `.env` должны быть:

```env
BOTAMIN_API_KEY=replace_with_secure_api_key
PUBLIC_IP=91.218.112.192
```

Если `PUBLIC_IP` не указан, Compose использует `91.218.112.192`.

## Обновление на VPS

```bash
cd /opt/botamin-api
git pull --ff-only
docker compose config
docker compose pull caddy
docker compose up -d --build
docker compose ps
docker compose logs --tail=200 caddy
```

## Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

Откройте TCP 80 и 443 также в firewall панели VPS-провайдера. После успешной
проверки HTTPS закройте публичный TCP 8000 в панели провайдера и UFW:

```bash
sudo ufw delete allow 8000/tcp
```

## Проверка

```bash
curl -v https://91.218.112.192/health
```

Проверка защищённого endpoint:

```bash
curl -X POST https://91.218.112.192/available-slots \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"date_mode":"nearest","period":"any"}'
```

## ElevenLabs

- `POST https://91.218.112.192/available-slots`
- `POST https://91.218.112.192/book-meeting`

Порт `8000` в URL ElevenLabs не указывается. В оба инструмента добавляется
секретный заголовок `X-API-Key`.

## Диагностика

```bash
docker compose ps
docker compose logs --tail=200 caddy
docker compose logs --tail=100 api
sudo ss -lntp | grep -E ':80|:443'
```

Сертификаты Caddy хранятся в постоянном volume `botamin-caddy-data`, поэтому
не теряются при пересоздании контейнера. IP-сертификат использует ACME profile
`shortlived` и должен автоматически продлеваться Caddy.
