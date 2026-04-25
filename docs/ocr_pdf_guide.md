# Как оцифровать PDF в текст (OCR System)

## Быстрый старт

```bash
# Установка
pip install -e .

# Базовая команда (все страницы, качество medium)
ocr-extract-pdf document.pdf

# Сохранить в файл
ocr-extract-pdf document.pdf --output text.txt
```

## Качество и скорость

| Качество | `--quality` | Scale | Скорость | Точность |
|---------|------------|-------|---------|---------|
| **High** | `high` | 2.0x | медленно | ★★★★★ |
| **Medium** (default) | `medium` | 1.5x | умеренно | ★★★★☆ |
| **Low** | `low` | 1.0x | быстро | ★★★☆☆ |

**Примеры:**
```bash
# Максимальное качество для важного документа
ocr-extract-pdf book.pdf --quality high --output book.txt

# Быстрая предпросмотр 10-страничной главы
ocr-extract-pdf book.pdf --pages 1-10 --quality low --jobs 4 --output draft.txt

# Баланс: книга 200 стр. за приемлемое время
ocr-extract-pdf book.pdf --quality medium --jobs 4 --output full.txt
```

## Параллельная обработка

```bash
# Использовать 4 потока (ускоряет на 10-15%)
ocr-extract-pdf book.pdf --jobs 4

# Авто: количество ядер CPU
ocr-extract-pdf book.pdf --jobs 0
```

**Важно:** Параллелизм эффективен для документов >10 страниц. Для коротких файлов (`--jobs 1` быстрее).

## Выбор страниц

```bash
# Конкретные страницы
ocr-extract-pdf doc.pdf --pages 1,3,5

# Диапазон
ocr-extract-pdf doc.pdf --pages 1-10

# Смешанный список
ocr-extract-pdf doc.pdf --pages 1-5,8,10-15

# Все (по умолчанию)
ocr-extract-pdf doc.pdf          # или --pages all
```

## Языки и режимы

```bash
# Русский язык (старые тексты с Ѣ, І, Ѳ)
ocr-extract-pdf book.pdf --languages ru-RU --quality high

# Мультиязычный документ
ocr-extract-pdf doc.pdf --languages en-US,fr-FR,de-DE

# Быстрый режим (менее точный, но быстрее)
ocr-extract-pdf doc.pdf --level fast

# Рукопись (iOS 16+/macOS 13+)
ocr-extract-pdf drawing.pdf --handwriting
```

**Важно:** Для старых книг (XIX век) **всегда используйте `--no-correction` выключено** (по умолчанию). Language correction критически важен для преобразования ſ→s, Ѣ→е и т.д.

## Сохранение и вывод

```bash
# Сохранить в файл
ocr-extract-pdf doc.pdf --output result.txt

# Показать confidence для каждой страницы
ocr-extract-pdf doc.pdf --confidence

# Кастомный разделитель между страницами
ocr-extract-pdf doc.pdf --separator "\n\n==========\n\n"
```

## Примеры реальных сценариев

### 1. Оцифровка старой книги (1879, кириллица)
```bash
ocr-extract-pdf "Русскія_Сказки_1879.pdf" \
  --quality high \
  --languages ru-RU \
  --output=russian_fairy_tales.txt \
  --jobs 4
```
*Примечание: Без `--no-correction`, иначе текст нечитаем.*

### 2. Быстрый просмотр многостраничного PDF (100+ стр.)
```bash
ocr-extract-pdf manual.pdf \
  --quality low \
  --jobs 0 \
  --output draft.txt
```
*За 5-10 минут получите черновик для поиска по тексту.*

### 3. Точное извлечение короткого документа
```bash
ocr-extract-pdf contract.pdf \
  --quality high \
  --level accurate \
  --confidence \
  --output contract.txt
```

### 4. Извлечение только нужных глав
```bash
ocr-extract-pdf novel.pdf --pages 1-50,100-150 --output part1.txt
ocr-extract-pdf novel.pdf --pages 151-300 --output part2.txt
```

## Ограничения и требования

### Обязательно
- **macOS** (Vision framework — часть macOS/iOS)
- **PyObjC**: `pip install pyobjc-framework-Vision pyobjc-framework-CoreML`
- Для PDF: также `pyobjc-framework-Quartz`

### Известные проблемы
1. **Старая кириллица** (XIX век): Vision путает устаревшие буквы. Language correction помогает, но не идеально.
2. **Сложные макеты** (колонки, таблицы): Текст извлекается, но структура может теряться.
3. **Фоновые изображения/водяные знаки**: Могут интерферировать.
4. **Горизонтальный текст**: Не поддерживается (только вертикальная разметка).

### When not to use
- Сканированные документы с плохим качеством (размытые, наклоненные) → предварительная обработка нужна
- Многостраничные научные статьи с формулами → Vision не распознает LaTeX/math
- PDF с защитой/закрытым содержимым → нужно разблокировать вручную

## Формат вывода

По умолчанию текст страниц объединяется через двойной перевод строки (`\n\n`). Можно изменить:

```bash
# Разделитель "--- PAGE N ---"
ocr-extract-pdf doc.pdf --separator "\n--- PAGE ---\n"

# Без разделителей (просто склеить)
ocr-extract-pdf doc.pdf --separator ""
```

С флагом `--confidence` в начало каждой страницы добавляется строка:
```
--- Page 1 [98.45%] ---
<text>
```

## Советы

1. **Always preview first:** Пробуйте 1-3 страницы перед полной обработкой:
   ```bash
   ocr-extract-pdf bigbook.pdf --pages 1-3 --quality high
   ```

2. **Cache PDF handling:** Система кэширует открытый PDF, так что повторные запуски быстрее.

3. **Memory:** Очень большие PDF (>500 стр.) при `--quality high` могут потреблять много RAM. Используйте `--quality low` или разбивайте на части.

4. **Combine with grep:** После оцифровки быстро ищите:
   ```bash
   ocr-extract-pdf book.pdf | grep -i "ważny fraza"
   ```

5. **Batch processing:**
   ```bash
   for f in *.pdf; do
     ocr-extract-pdf "$f" --quality medium --jobs 2 --output "${f%.pdf}.txt"
   done
   ```

## Требования к системе

| Компонент | Минимум | Рекомендуется |
|-----------|---------|--------------|
| macOS | 10.15 (Catalina) | 13.0+ (Ventura) |
| CPU | 4 ядра | 8+ ядер |
| RAM | 8 GB | 16+ GB |
| Python | 3.9 | 3.11+ |

## Дальше

- Полная документация: `README.md`
- Архитектура: `docs/architecture.md` (если есть)
- Тесты: `pytest ocr_system/tests/`
- Отчёт по оптимизациям: `PERFORMANCE_OPTIMIZATION_REPORT.md`

**Точность** зависит от:
- Качества сканирования (resolution ≥300 DPI рекомендуется)
- Чистоты шрифта (анти-алиасинг helpful)
- Языка (английский лучше всего, старые языки — сложнее)
- Использования `--quality high` и `--no-correction` off

Удачи в оцифровке!
