# VideoDating — продуктовая карта (Miro)

**Артефакты для заказчика и разработчиков:**

| Файл | Назначение |
|------|------------|
| [Miro-доска](https://miro.com/app/board/uXjVH9Gr3u0=/) | Интерактивная карта: экраны, воронка, развилки |
| `VideoDating-Developer-Spec.docx` | Текстовое ТЗ для backend / frontend |
| `generate_developer_spec_docx.py` | Пересборка DOCX после правок |

```bash
python3 docs/generate_developer_spec_docx.py
```

---

## Скрипты обслуживания доски

| Скрипт | Назначение |
|--------|------------|
| `miro_populate_board.py` | Первичное заполнение фреймами |
| `miro_update_board.py` | Добавление фреймов (Anna path, wireframes…) |
| `miro_fix_alignment.py` | Выравнивание стикеров по сетке 2 колонки |
| `miro_font32_board.py` | Единый размер шрифта 32 |
| `miro_complete_promises.py` | Закрытие пробелов обещаний заказчику |
| `generate_developer_spec_docx.py` | Сборка DOCX для разработчиков |

**Устаревшие** (не запускать на живой доске): `miro_polish_board.py`, `miro_relayout_board.py`, `miro_normalize_board.py`.

### Канонический пайплайн после правок

```bash
export MIRO_ACCESS_TOKEN="ваш_токен"
export MIRO_BOARD_ID="uXjVH9Gr3u0="
python3 docs/miro_complete_promises.py   # пробелы обещаний
python3 docs/miro_fix_alignment.py     # сетка 2 колонки
python3 docs/miro_font32_board.py      # единый шрифт 32
python3 docs/generate_developer_spec_docx.py
```

---

## API-токен (если нужно обновить доску)

1. https://developers.miro.com/ → **My apps** → Create app
2. Permissions: `boards:read`, `boards:write`
3. **Get access token** → скопировать
4. Не коммитьте токен в git; после работы — отозвать

```bash
export MIRO_ACCESS_TOKEN="..."
export MIRO_BOARD_ID="uXjVH9Gr3u0="
python3 docs/miro_populate_board.py   # только для новой доски
```

Dry-run:

```bash
export MIRO_DRY_RUN=1
python3 docs/miro_populate_board.py
```

---

## Структура доски

| Фрейм | Содержание |
|-------|------------|
| 0. Сайт ≠ Приложение | Лендинг vs мобильное app |
| 1. User Flow | Воронка 10 шагов |
| 1.2 Гостевой режим | Лимиты, edge cases |
| 1.3–1.4 Регистрация | Модерация, доступы |
| 1.5 Структура БД | Поля для фильтрации |
| 2. Лайки и мэтчи | Корзина, лимиты |
| 2.2 Чаты | Кружки, архивация |
| 2.3 WebRTC | Оплата, запись |
| 3. Модерация | Pipeline + score |
| 4. ЛК и рейтинги | 4 критерия |
| 5. Лендинг | Секции сайта |
| Путь Анны | Сценарий от скачивания до свидания |
| Wireframes | Ключевые экраны app |
| 6–7. Поставка | Этапы реализации |

После правок: **Fit to screen** в Miro.
