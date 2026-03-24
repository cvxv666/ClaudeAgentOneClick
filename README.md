![Claude Server Kit](docs/images/social-preview.png)

# Claude Server Kit

[![CI](https://github.com/doffskiii/claude-server-kit/actions/workflows/test-setup.yml/badge.svg)](https://github.com/doffskiii/claude-server-kit/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-6e1cff.svg)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-6e1cff.svg)](https://claude.ai)

> **TL;DR для агентов:** `git clone https://github.com/doffskiii/claude-server-kit.git && cd claude-server-kit && bash setup.sh && bash configure.sh && claude`

Превращаем VPS в персонального AI-ассистента с памятью, Telegram-ботом и кучей суперсил.

Две недели ежедневных итераций, упакованные в один репозиторий. Клонишь, запускаешь `setup.sh`, и получаешь агента, который помнит всё, управляет задачами, расшифровывает голосовые и общается с тобой в Telegram.

> Подробная серия постов, где разобран каждый компонент: [Курс молодого AI билдера](https://t.me/yshlfe/264)

![Architecture](docs/images/architecture.png)

---

## Оглавление

- [Чо внутри](#чо-внутри)
- [Быстрый старт](#быстрый-старт)
- [Что нужно для запуска](#что-нужно-для-запуска)
- [Настройка кредов](#настройка-кредов)
- [Структура репозитория](#структура-репозитория)
- [Brain MCP — 20 инструментов](#brain-mcp--20-инструментов)
- [Takopi (Telegram-бот)](#takopi-telegram-бот)
- [Конвенции хранилища](#конвенции-хранилища)
- [Под капотом](#под-капотом)
- [Создание скиллов](#создание-скиллов)
- [Авто-память](#авто-память)
- [Мониторинг](#мониторинг)
- [Бэкапы](#бэкапы)
- [Библиотекарь](#библиотекарь)

---

## Чо внутри

- **Brain MCP** — 20 инструментов для работы с памятью: поиск (обычный + по смыслу), запись, дашборд, транскрибация аудио, календарь, мониторинг сервера
- **Vault** — Obsidian-хранилище с git-синком, мета-тегами, двусторонними ссылками и контекстным файлом в каждой папке
- **Семантический поиск** — находит документы по смыслу, а не только по словам. ONNX модель, работает на CPU
- **Whisper** — OpenAI-совместимый сервер транскрибации. Короткие аудио обрабатываются локально, длинные летят на Groq API
- **Takopi** — Telegram-бот для общения с агентом с телефона. Голосовые, файлы, мультисессии
- **Мониторинг** — алерты в Telegram когда CPU/RAM/диск на пределе или процесс упал
- **Библиотекарь** — еженедельный автономный аудит хранилища: находит сироток, битые ссылки, устаревшие файлы
- **Dual-Channel Ask** — вопросы одновременно в VS Code и Telegram. Кто первый ответил, тот и молодец
- **Context7** — актуальная документация по любой библиотеке по запросу
- **Скиллы** — расширяемая система команд для повторяющихся задач
- **Эскалирующие напоминалки** — крон-ремайндеры, которые становятся настойчивее с каждым уровнем
- **Интерактивный онбординг** — агент сам проведёт новичка по всем шагам, без чтения документации

## Быстрый старт

```bash
# 1. Клонируем
git clone https://github.com/doffskiii/claude-server-kit.git
cd claude-server-kit

# 2. Ставим всё (uv, Node.js, PM2, Brain, vault, ML модели)
bash setup.sh

# 3. Настраиваем креды (интерактивный визард)
bash configure.sh

# 4. Запускаем Claude Code и пишем "привет"
claude
```

![Onboarding Flow](docs/images/onboarding-flow.png)

Агент сам поймёт, что это первый запуск, и запустит **интерактивный онбординг**: познакомится, расскажет что умеет, настроит Telegram, голосовые, бэкапы, безопасность. Просто отвечай на вопросы.

## Что нужно для запуска

- Ubuntu 20.04+ (или аналогичный Linux)
- 2+ GB RAM (4+ GB если хотите Whisper + эмбеддинги)
- Git, интернет
- `setup.sh` установит всё остальное: uv, Python 3.12+, Node.js, PM2, ffmpeg

## Настройка кредов

Можно через визард `bash configure.sh`, а можно руками:

**Takopi (Telegram-бот)** — нужен для общения с телефона
```bash
uv tool install takopi && takopi
```

**Groq API (опционально)** — ускоряет транскрибацию длинных аудио
```bash
echo '{"api_key":"gsk_..."}' > ~/.groq-api-key.json && chmod 600 ~/.groq-api-key.json
```

**Git-бэкап хранилища (опционально)** — пушит vault в приватный репо каждые 5 минут
```bash
cd ~/vault && git remote add origin git@github.com:you/vault-private.git
```

**Шифрованный бэкап (опционально)** — ежедневный полный бэкап с GPG
```bash
echo 'your-passphrase' > ~/.backup-passphrase && chmod 600 ~/.backup-passphrase
```

Все чувствительные файлы — `chmod 600` и в `.gitignore`.

<details>
<summary><b>Структура репозитория</b></summary>

```
claude-server-kit/
├── brain/                    # Brain MCP сервер (Python, FastMCP)
│   ├── src/brain/
│   │   ├── server.py         # 20 MCP инструментов
│   │   ├── config.py         # Конфигурация (env-driven)
│   │   ├── whisper_server.py # OpenAI-compatible Whisper API
│   │   ├── vault/            # Операции с хранилищем
│   │   ├── calendar/         # Календарь (SQLite)
│   │   └── server_tools/     # Мониторинг сервера
│   ├── scripts/              # Утилиты
│   └── ecosystem.config.cjs  # PM2 конфигурация
│
├── librarian/                # Автономный аудит хранилища
│   ├── SYSTEM.md             # Системный промпт агента
│   ├── CHECKLIST.md          # 10-секционный чеклист
│   └── run.sh                # Cron entry point
│
├── vault-template/           # Пустое хранилище с контекстными файлами
│   ├── dashboard.md          # Дашборд задач
│   ├── inbox/                # Входящие идеи
│   ├── conversations/        # Записи сессий
│   ├── decisions/            # Лог решений
│   ├── knowledge/            # Знания (проекты, личное, обучение)
│   ├── retro/                # Ретроспективы
│   └── templates/            # Шаблоны Obsidian
│
├── templates/                # Шаблоны конфигов Claude Code
│   ├── CLAUDE.md             # Инструкции агента (THE BRAIN)
│   ├── mcp.json              # Регистрация MCP серверов
│   ├── settings.json         # Конфигурация permissions
│   └── memory/MEMORY.md      # Бутстрап авто-памяти
│
├── scripts/                  # Серверная автоматизация
│   ├── backup.sh             # Шифрованный бэкап (GPG AES-256)
│   ├── git-push-all.sh       # Ежедневный пуш кода на GitHub
│   ├── calendar-sync.py      # Синхронизация календаря (hourly)
│   └── reminders/            # Эскалирующие напоминалки
│
├── skills/                   # Пример скиллов Claude Code
│   ├── onboarding/SKILL.md   # Интерактивный онбординг
│   ├── track/SKILL.md        # Умный роутинг задач
│   └── reflect/SKILL.md      # Дневная рефлексия
│
├── setup.sh                  # Установка в одну команду
├── configure.sh              # Интерактивный визард кредов
└── .gitignore
```

</details>

<details>
<summary><b>Brain MCP — 20 инструментов</b></summary>

**Хранилище:** `search_vault` (полнотекстовый поиск) / `semantic_search` (поиск по смыслу) / `read_vault` / `write_vault` (с авто-мета и git-синком) / `list_vault` / `update_dashboard` (безопасное обновление, никогда не перезаписывает)

**Ингест:** `ingest_audio` (аудио в текст, локально или через Groq) / `ingest_document` (PDF/текст с авто-чанкингом)

**Календарь:** `get_today` (текущая дата + граница дня в 03:00 + неделя) / `add_calendar_event` / `list_calendar_events` / `remove_calendar_event` / `update_calendar_event` / `queue_calendar_sync`

**Telegram:** `send_telegram_question` (неблокирующий) / `check_telegram_answer` (поллинг) / `cancel_telegram_question` / `ask_via_telegram` (блокирующий, legacy)

**Сервер:** `get_server_status` (CPU/RAM/диск/PM2) / `get_server_map` (карта сервисов)

</details>

## Takopi (Telegram-бот)

[Takopi](https://github.com/miilv/takopi) — open-source мост между Telegram и AI-агентами.

- Мульти-движок: Claude Code, Codex, OpenCode, DeepSeek
- Транскрибация голосовых (роутит на Brain Whisper)
- Передача файлов, мультисессии, стриминг
- Dual-channel Q&A сервер на порту 9877
- Установка: `uv tool install -U takopi`

## Конвенции хранилища

- **Контекстные файлы** — в каждой папке есть `FOLDER_NAME.md`, который индексирует содержимое
- **Фронтматтер** — все файлы имеют YAML метаданные: title, tags, created, source
- **Двусторонние ссылки** — если A ссылается на B, то B обязан ссылаться на A
- **Дашборд** — только через `update_dashboard()`, никогда через `write_vault("dashboard.md")`
- **Решения** — значимые решения записываются в `decisions/YYYY-MM-DD_slug.md`
- **Записи сессий** — после работы в VS Code записываем в `conversations/YYYY-MM-DD_slug.md`
- **Граница дня в 03:00** — для полуночников: логический день заканчивается в 3 утра, не в полночь

<details>
<summary><b>Под капотом</b></summary>

**Debounced Git Sync** — несколько записей за 30 секунд собираются в один коммит. Fire-and-forget, не блокирует ответ.

**Инкрементальные эмбеддинги** — при записи документа пересчитываются только его эмбеддинги. Полный ребилд индекса не нужен.

**Thread-Safe ONNX** — глобальный лок предотвращает конкурентный доступ к модели эмбеддингов. Безопасно для параллельных тул-коллов.

**Fail-Safe Calendar Sync** — события привязаны к таск-системам через `source_type` + `source_id`. Часовой крон проверяет завершённость задач перед удалением событий.

**Эскалирующие напоминалки** — 4 уровня: подробная статистика -> простой тычок -> последний шанс -> авто-выполнение. Маркер-файлы предотвращают повторный запуск.

**Безопасность путей** — все vault-пути валидируются от directory traversal и symlink-атак. `.env`, `.ssh`, токены заблокированы от ингеста.

</details>

## Создание скиллов

Скиллы — это файлы с инструкциями, которые расширяют возможности агента:

```
~/.claude/skills/my-skill/
├── SKILL.md      # Инструкции + триггеры
└── scripts/      # Вспомогательные скрипты (опционально)
```

Смотри `skills/onboarding/SKILL.md` для примера, `skills/track/SKILL.md` и `skills/reflect/SKILL.md` для боевых скиллов.

## Авто-память

Claude Code хранит знания между сессиями в `~/.claude/projects/<project>/memory/`:

- `MEMORY.md` — ключевые правила, всегда загружается в контекст (держи до 200 строк)
- Топик-файлы (`whisper.md`, `trello.md`) — детальные знания по доменам, подгружаются по необходимости
- Claude обновляет эти файлы сам по мере работы

## Мониторинг

Brain Monitor (PM2 демон) шлёт алерты в Telegram когда:
- CPU > 80% три проверки подряд
- Свободная RAM < 1 GB
- Диск > 85%
- Любой PM2 процесс упал

Кулдаун 30 минут между одинаковыми алертами.

## Бэкапы

Три слоя:
1. **Git-синк хранилища** (каждые 5 мин) — непрерывный бэкап знаний
2. **Git-пуш кода** (ежедневно) — все репозитории на GitHub
3. **Шифрованный бэкап** (ежедневно) — GPG AES-256 -> облако

## Библиотекарь

Еженедельный автономный агент, который аудитит хранилище:
- Пропущенные контекстные файлы, сироты, битые ссылки
- Устаревшие записи, нарушения двусторонних ссылок
- Проблемы с фронтматтером, скоринг свежести
- Шлёт сжатый отчёт в Telegram

Крон: `0 4 * * 1 bash ~/librarian/run.sh` (понедельник, 4 утра).

<details>
<summary><b>Environment Variables</b></summary>

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `BRAIN_VAULT_PATH` | `~/vault` | Путь к Obsidian хранилищу |
| `TAKOPI_CONFIG` | `~/.takopi/takopi.toml` | Конфиг Takopi |
| `GROQ_KEY_FILE` | `~/.groq-api-key.json` | API ключ Groq для длинных аудио |

</details>

## Credits

- [Takopi](https://github.com/miilv/takopi) by banteg — Telegram-мост для AI-агентов
- [FastMCP](https://github.com/jlowin/fastmcp) — легковесный MCP фреймворк
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2 Whisper
- [Obsidian](https://obsidian.md) — управление знаниями
- [sentence-transformers](https://www.sbert.net/) — мультиязычные эмбеддинги

## License

MIT

---

Понравилось? Поставь звёздочку — это помогает другим найти проект!
