# WLTraders Landing

Одностраничный лендинг двух связанных продуктов:

- **WLTraders** — open source P2P-платформа для трейдерских команд, мерчантов и процессинга;
- **Cortex** — коммерческий платёжный агрегатор с управляемым каскадом провайдеров.

По умолчанию открывается WLTraders. Режим Cortex доступен по `?mode=cascade`; выбор сохраняется локально и восстанавливается при обновлении страницы.

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

Скрипт сам заменит статический `location /` в действующем nginx-сайте на прокси к локальному сервису, проверит `nginx -t` и перезагрузит nginx. Если проверка не пройдёт, исходный конфиг восстанавливается из резервной копии.

Проверка и отчёт доступны через SSH:

```bash
curl -f http://127.0.0.1:8090/health
python3 /opt/wltraders-landing/analytics_report.py
```

База счётчиков находится в `/var/lib/wltraders-analytics/visitors.sqlite3`; она не затрагивается при `git pull`.

## Демо

WLTraders: [demo.wltraders.pro](https://demo.wltraders.pro/)

Cortex: [cascade.wltraders.pro](https://cascade.wltraders.pro/)

- Логин: `admin`
- Пароль: `password`

## Файлы

- `index.html` — разметка, стили и интерактивность.
- `analytics_server.py` — статический сервер и приватная аналитика.
- `analytics_report.py` — вывод счётчиков и последних посещений.
- `deploy/` — unit systemd и конфигурация nginx.
- `assets/screens/` — скриншоты интерфейса для карусели.
