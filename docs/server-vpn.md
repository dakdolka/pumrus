# Смена VPN-подключения на сервере

Порядок составлен по `docker-compose.yaml`, коду бота и локальной копии
`deploy/sing-box/config.json`. Состояние работающего сервера нужно сверить перед
заменой: локальная копия не является источником актуальных параметров.

## Где используется ссылка

В конфигурации проекта цепочка такая:

`tg_bot → TG_PROXY → sing-box:1080 (SOCKS5) → VLESS/Reality → Telegram`.

Сервис `sing-box` использует образ `ghcr.io/sagernet/sing-box:v1.13.12`.
Каталог сервера `/etc/pumrus/sing-box` подключён в контейнер как
`/etc/sing-box:ro`; процесс читает конфигурацию из этого каталога через `-C`.
Healthcheck проверяет `/etc/sing-box/config.json`.

Новая ссылка `vless://…` задаёт параметры исходящего подключения в JSON.
В `TG_PROXY` хранится адрес SOCKS-прокси, а не VLESS-ссылка. Для указанной
схемы это `socks5://sing-box:1080`. При обычной смене VLESS-ссылки `TG_PROXY`,
входящий SOCKS-порт, правила маршрутизации и версию образа сохраняют.
Эта настройка сама по себе не направляет весь трафик сервера через VPN.

## 1. Сверить работающую конфигурацию и сделать копию

Подключиться к серверу и перейти в каталог проекта с рабочими Compose-файлами
и `.env`. Все команды ниже выполняются там, в одной Bash-сессии.
Использовать тот же набор `-f` / `--env-file` / `-p`, с которым запущен проект,
если он отличается от стандартного.

```bash
docker compose ps sing-box tg_bot
docker inspect "$(docker compose ps -q sing-box)" \
  --format '{{range .Mounts}}{{println .Source "->" .Destination}}{{end}}'
docker compose exec -T sing-box sing-box version
docker compose exec -T sing-box sing-box check -C /etc/sing-box

vpn_backup_dir="/etc/pumrus/vpn-backups/$(date -u +%Y%m%dT%H%M%SZ)"
sudo install -d -m 700 "$vpn_backup_dir"
sudo cp -a /etc/pumrus/sing-box "$vpn_backup_dir/"
vpn_candidate_dir=$(sudo mktemp -d /etc/pumrus/sing-box-candidate.XXXXXX)
sudo cp -a /etc/pumrus/sing-box/. "$vpn_candidate_dir/"
```

Если реальные mount, версия или структура отличаются, сначала адаптировать
порядок к ним. Если исходная проверка не проходит, разобраться с этой ошибкой
до замены ссылки. Копии и временные файлы хранить вне `/etc/pumrus/sing-box`:
дополнительный JSON внутри рабочего каталога может попасть в загрузку через `-C`.

## 2. Перенести параметры новой ссылки

Открыть копию актуального серверного файла:

```bash
sudoedit "$vpn_candidate_dir/config.json"
```

Для VLESS поверх TCP с Reality найти исходящий блок `type: "vless"`
(в локальной копии его `tag` — `vpn`) и перенести параметры ссылки:

| Часть `vless://UUID@HOST:PORT?…` | Поле исходящего блока sing-box |
| --- | --- |
| `UUID` | `uuid` |
| `HOST` | `server` |
| `PORT` | `server_port`, число |
| `flow` | `flow` |
| `sni` | `tls.server_name` |
| `fp` | `tls.utls.fingerprint` |
| `pbk` | `tls.reality.public_key` |
| `sid` | `tls.reality.short_id` |

Для `security=reality` должны быть включены `tls.enabled` и
`tls.reality.enabled`; при использовании fingerprint — `tls.utls.enabled`.
Параметры ссылки декодировать из URL-кодирования. Пустой или отсутствующий
`flow` не заменять старым значением; необязательные поля сверять с настройками
нового подключения. Часть после `#` — название профиля, в JSON она не нужна.

Эта таблица относится к TCP/Reality. Ссылку подписки `https://…`, другой
протокол, транспорт (`ws`, `grpc` и т. п.) или неизвестные параметры сначала
разобрать отдельно: простой замены полей из таблицы недостаточно.
Сохранять `tag` исходящего подключения, входящие подключения и маршруты.

Ссылку и JSON с реквизитами не добавлять в Git, команды терминала или публичные
логи. Локальный каталог `deploy/` исключён из Git и не монтируется данным Compose.

Поля сверены с документацией sing-box:
[VLESS](https://sing-box.sagernet.org/configuration/outbound/vless/),
[TLS и Reality](https://sing-box.sagernet.org/configuration/shared/tls/).
Окончательная проверка совместимости — бинарником используемого образа.

## 3. Проверить копию и установить

Проверить копию тем же образом, который указан для сервиса, без запуска VPN:

```bash
docker compose run --rm --no-deps \
  -v "$vpn_candidate_dir:/etc/sing-box:ro" \
  sing-box check -C /etc/sing-box
```

Продолжать только при коде завершения `0`. Проверка подтверждает допустимость
конфигурации, но ещё не доступность VPN. Установить изменённый файл и
перезапустить прокси, затем бот:

```bash
sudo install -o root -g root -m 600 \
  "$vpn_candidate_dir/config.json" /etc/pumrus/sing-box/config.json
docker compose restart --no-deps sing-box
docker compose ps sing-box
```

Дождаться `healthy`. Если контейнер перезапускается или остаётся `unhealthy`,
перейти к откату. После `healthy`:

```bash
docker compose restart --no-deps tg_bot
docker compose ps sing-box tg_bot
docker compose logs --since=2m --tail=80 sing-box tg_bot
```

Если менялся также `TG_PROXY` в `.env`, вместо перезапуска бота выполнить
`docker compose up -d --no-deps --force-recreate tg_bot`:
[restart не обновляет переменные окружения контейнера](https://docs.docker.com/reference/cli/docker/compose/restart/).

## 4. Проверить реальный запрос к Telegram

Проверить соединение из контейнера бота через его текущие настройки. Команда
не запускает второй polling-процесс и не выводит токен:

```bash
docker compose exec -T tg_bot python - <<'PY'
import asyncio
from main import create_bot

async def main():
    bot = create_bot()
    try:
        await asyncio.wait_for(bot.get_me(), timeout=30)
        print("Telegram getMe: OK")
    except Exception as exc:
        print("Telegram getMe: FAILED (" + type(exc).__name__ + ")")
        raise SystemExit(1)
    finally:
        await bot.session.close()

asyncio.run(main())
PY
```

Затем отправить боту `/start` и проверить ответ. Замена завершена, если
`sing-box` здоров, запрос `getMe` успешен и бот отвечает. Один статус
`healthy` недостаточен: healthcheck в Compose проверяет только конфигурацию.
При ошибке проверить DNS, доступность нового узла и параметры Reality;
если быстро восстановить связь не удалось — откатить.

## 5. Откат

В той же Bash-сессии восстановить сохранённый файл:

```bash
sudo cp -a "$vpn_backup_dir/sing-box/config.json" /etc/pumrus/sing-box/config.json
docker compose restart --no-deps sing-box
docker compose ps sing-box
```

После `healthy` перезапустить `tg_bot` и повторить проверку `getMe` и `/start`.
Если отдельно меняли `.env`, восстановить прежний `TG_PROXY` и пересоздать
контейнер бота. В новой сессии сначала задать `vpn_backup_dir` точным путём
нужной резервной копии.
