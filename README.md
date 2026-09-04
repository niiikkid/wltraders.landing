# WLTraders Landing

Одностраничный лендинг WLTraders — open source P2P-платформы для трейдерских команд, мерчантов и процессинга.

## Локальный просмотр

Откройте `index.html` в браузере или запустите простой сервер:

```bash
python3 -m http.server 8080
```

После этого откройте `http://localhost:8080`.

## Учёт посещений

`analytics_server.py` отдаёт лендинг и ведёт SQLite-журнал документных запросов (`/` и `/index.html`).

- Уникальность определяется по IP за всё время: отдельные счётчики `humans` и `bots`.
- Боты распознаются по User-Agent; записи поисковых роботов и превью-сервисов не смешиваются с людьми.
- В журнал попадают время, IP, User-Agent, URL, Referer, язык браузера и переданные Cloudflare страна, город и часовой пояс.
- Процесс принимает трафик только на `127.0.0.1:8090`; наружу его публикует nginx.
- nginx берёт IP из `CF-Connecting-IP` только для сетей Cloudflare и передаёт его приложению как `X-Real-IP`.

На сервере после `git pull` запустите от root:

```bash
chmod +x deploy/install-analytics.sh
./deploy/install-analytics.sh
```

Затем добавьте директивы из `deploy/wltraders-analytics-nginx.conf` в действующий HTTPS server block для `wltraders.pro` и выполните:

```bash
nginx -t && systemctl reload nginx
```

Проверка и отчёт доступны через SSH:

```bash
curl -f http://127.0.0.1:8090/health
python3 /var/www/wltraders.landing/analytics_report.py
```

База счётчиков находится в `/var/lib/wltraders-analytics/visitors.sqlite3`; она не затрагивается при `git pull`.

## Демо

Рабочая демо-версия: [demo.wltraders.pro](https://demo.wltraders.pro/)

- Логин: `admin`
- Пароль: `password`

## Файлы

- `index.html` — разметка, стили и интерактивность.
- `analytics_server.py` — статический сервер и приватная аналитика.
- `analytics_report.py` — вывод счётчиков и последних посещений.
- `deploy/` — unit systemd и конфигурация nginx.
- `assets/screens/` — скриншоты интерфейса для карусели.
