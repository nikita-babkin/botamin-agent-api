# Деплой Botamin Booking API через Docker

## 1. Локальная проверка

Создайте `.env` и замените тестовый API-ключ:

```bash
cp .env.example .env
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100 api
curl http://127.0.0.1:8000/health
```

Бронирования сохраняются в Docker volume `botamin-api-data`.

## 2. Публикация в GitHub

```bash
git add Dockerfile compose.yaml .dockerignore DEPLOY_DOCKER.md
git commit -m "Add Docker deployment"
git push
```

Проверьте, что `.env` не отслеживается:

```bash
git ls-files .env
```

Команда не должна ничего вывести.

## 3. Подготовка Ubuntu VPS

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

Переподключитесь к VPS и проверьте:

```bash
docker version
docker compose version
```

## 4. Клонирование проекта

```bash
sudo mkdir -p /opt/botamin-api
sudo chown "$USER":"$USER" /opt/botamin-api
git clone https://github.com/USERNAME/botamin-agent-api.git /opt/botamin-api
cd /opt/botamin-api
```

## 5. Настройка секрета

```bash
cp .env.example .env
openssl rand -hex 32
nano .env
chmod 600 .env
```

Файл `.env` должен содержать сгенерированный ключ:

```env
BOTAMIN_API_KEY=replace_with_generated_value
```

## 6. Сборка и запуск

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100 api
```

Контейнер должен перейти в состояние `healthy`.

## 7. Открытие порта

```bash
sudo ufw allow OpenSSH
sudo ufw allow 8000/tcp
sudo ufw enable
sudo ufw status
```

В firewall панели VPS-провайдера также разрешите входящий TCP-порт `8000`.
Docker может обходить часть правил UFW, поэтому внешний firewall провайдера
является предпочтительным местом ограничения доступа.

## 8. Проверка

На VPS:

```bash
curl http://127.0.0.1:8000/health
```

С локального компьютера:

```bash
curl http://PUBLIC_IP:8000/health
```

Защищённый endpoint:

```bash
curl -X POST http://PUBLIC_IP:8000/available-slots \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"date_mode":"nearest","period":"any"}'
```

## 9. Подключение ElevenLabs

- `POST http://PUBLIC_IP:8000/available-slots`
- `POST http://PUBLIC_IP:8000/book-meeting`

В оба webhook-запроса добавьте секретный заголовок `X-API-Key`.

Обычный HTTP не шифрует API-ключ и контактные данные. Для публичной
эксплуатации добавьте HTTPS reverse proxy и замените публикацию порта в
`compose.yaml` на `127.0.0.1:8000:8000`.

## 10. Обновление версии

После отправки изменений в GitHub выполните на VPS:

```bash
cd /opt/botamin-api
git pull --ff-only
docker compose up -d --build
docker compose ps
docker compose logs --tail=50 api
curl http://127.0.0.1:8000/health
```

Постоянный volume с бронированиями при обновлении сохраняется.

## 11. Управление

```bash
docker compose restart api
docker compose stop
docker compose start
docker compose logs -f api
```
