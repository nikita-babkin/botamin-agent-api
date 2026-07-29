# Деплой Botamin API через Nginx и Certbot

Production URL:

```text
https://botamin-151-243-3-142.nip.io
```

FastAPI запускается в Docker и публикуется только на `127.0.0.1:8000`.
Nginx принимает публичный HTTP/HTTPS-трафик и проксирует его в FastAPI.

## Запуск API

```bash
cd /opt/botamin-api
cp .env.example .env
nano .env
chmod 600 .env
docker compose -f compose.nginx.yaml up -d --build
curl http://127.0.0.1:8000/health
```

## Bootstrap Nginx

```bash
sudo mkdir -p /var/www/certbot
sudo cp deploy/nginx/botamin-api-http.conf /etc/nginx/sites-available/botamin-api
sudo ln -sfn /etc/nginx/sites-available/botamin-api /etc/nginx/sites-enabled/botamin-api
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## Сертификат

```bash
sudo certbot certonly \
  --webroot \
  --webroot-path /var/www/certbot \
  --domain botamin-151-243-3-142.nip.io \
  --agree-tos \
  --register-unsafely-without-email \
  --no-eff-email
```

## Включение HTTPS

```bash
sudo cp deploy/nginx/botamin-api-https.conf /etc/nginx/sites-available/botamin-api
sudo nginx -t
sudo systemctl reload nginx
curl https://botamin-151-243-3-142.nip.io/health
```

## Автопродление

```bash
sudo certbot renew --dry-run
sudo systemctl enable --now certbot.timer
```

Deploy hook `/etc/letsencrypt/renewal-hooks/deploy/reload-nginx`:

```sh
#!/bin/sh
systemctl reload nginx
```

## Обновление приложения

```bash
cd /opt/botamin-api
git pull --ff-only
docker compose -f compose.nginx.yaml up -d --build
curl https://botamin-151-243-3-142.nip.io/health
```
