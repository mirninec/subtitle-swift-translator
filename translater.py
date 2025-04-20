import sys
import os
import re
import subprocess
import time
from typing import List, Tuple

# ANSI-коды для цветного вывода в консоль
class Colors:
    YELLOW = "\033[1;33m"
    CYAN = "\033[1;36m"
    GREEN = "\033[1;32m"
    RED = "\033[1;31m"
    WHITE = "\033[1;37m"
    RESET = "\033[0m"

# Проверка аргументов командной строки
if len(sys.argv) < 2:
    print(f"{Colors.RED}Ошибка: Не указан входной файл{Colors.RESET}")
    print("Использование: python translate_srt.py filename.srt [from:to]")
    print("Пример: python translate_srt.py movie.srt en:fr - перевод с английского на французский")
    print("По умолчанию: en:ru - перевод с английского на русский")
    sys.exit(1)

srt_file_path = sys.argv[1]
translation_direction = "en:ru"  # Направление перевода по умолчанию

# Проверка аргумента направления перевода
if len(sys.argv) >= 3:
    direction_arg = sys.argv[2]
    if not re.match(r"^[a-z]{2}:[a-z]{2}$", direction_arg):
        print(f"{Colors.RED}Ошибка: Неверный формат направления перевода. Используйте формат 'from:to', например 'en:fr'{Colors.RESET}")
        sys.exit(1)
    translation_direction = direction_arg

from_lang, to_lang = translation_direction.split(":")

# Проверка существования файла
if not os.path.exists(srt_file_path):
    print(f"{Colors.RED}Ошибка: Файл {srt_file_path} не найден{Colors.RESET}")
    sys.exit(1)

print(f"Файл: {Colors.YELLOW}{srt_file_path}{Colors.RESET}")
print(f"Направление перевода: {Colors.CYAN}{from_lang} → {to_lang}{Colors.RESET}")
print("Начинаю перевод...")
# Вывод начальной белой полосы прогресса (100 символов)
print(f"{Colors.WHITE}{'█' * 100}{Colors.RESET}")

def translate_text(text: str) -> str:
    """Перевод текста с использованием утилиты 'trans'."""
    try:
        # Экранирование кавычек для безопасного выполнения команды
        escaped_text = text.replace('"', '\\"')
        command = f'trans -brief -no-warn -from {from_lang} -to {to_lang} "{escaped_text}"'
        
        # Выполнение команды и захват вывода
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Ошибка перевода: {e.stderr}{Colors.RESET}")
        return text
    except Exception as e:
        print(f"{Colors.RED}Ошибка перевода текста '{text}': {str(e)}{Colors.RESET}")
        return text

def translate_file():
    """Основная функция для обработки и перевода файла .srt."""
    start_time = time.time()  # Засекаем время начала

    try:
        # Чтение исходного файла
        with open(srt_file_path, "r", encoding="utf-8") as f:
            original = f.read()

        # Разделение на строки
        lines = original.splitlines()

        # Создание списка кортежей (индекс, строка)
        numbered_lines: List[Tuple[int, str]] = [(i, line) for i, line in enumerate(lines)]

        # Фильтрация строк, которые нужно перевести
        lines_to_translate = [
            (index, line)
            for index, line in numbered_lines
            if line.strip()
            and not re.match(r"^\d+$", line.strip())
            and not re.match(r"^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$", line.strip())
        ]

        total_lines = len(lines_to_translate)
        translated_lines = []

        # Перевод каждой строки с обновлением прогресс-бара
        for i, (index, line) in enumerate(lines_to_translate, 1):
            translated = translate_text(line)
            translated_lines.append((index, translated))
            
            # Вычисление прогресса
            progress = i / total_lines
            green_blocks = int(progress * 100)
            white_blocks = 100 - green_blocks
            
            # Обновление прогресс-бара (перемещение в начало строки)
            print(f"\033[1A\033[2K", end="")  # Подняться на 1 строку и очистить
            print(f"{Colors.GREEN}{'█' * green_blocks}{Colors.WHITE}{'█' * white_blocks}{Colors.RESET}")

        # Обновление исходных строк переведенным текстом
        for index, translated in translated_lines:
            numbered_lines[index] = (index, translated)

        # Создание переведенного текста
        translated_text = "\n".join(line for _, line in numbered_lines)

        # Переименование исходного файла
        backup_path = srt_file_path + "_"
        os.rename(srt_file_path, backup_path)

        # Сохранение переведенного файла
        with open(srt_file_path, "w", encoding="utf-8") as f:
            f.write(translated_text)

        # Расчет времени выполнения
        duration_seconds = round(time.time() - start_time)
        if duration_seconds < 60:
            duration_str = f"{duration_seconds} сек"
        else:
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration_str = f"{minutes} мин {seconds} сек"

        # Замена прогресс-бара сообщением об успешном завершении
        print(f"\033[1A\033[2K", end="")  # Подняться на 1 строку и очистить
        print(f"{Colors.GREEN}Переведено за {duration_str}{Colors.RESET}")

    except Exception as e:
        # Обновление статуса в консоли
        print(f"\033[1A\033[2K", end="")  # Подняться на 1 строку и очистить
        print(f"{Colors.RED}Не удалось перевести{Colors.RESET}")
        print(f"Ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    translate_file()


"""
Описание скрипта:

Этот скрипт предназначен для перевода текста в файлах субтитров формата .srt с одного языка на другой с использованием утилиты командной строки `trans`. Скрипт сохраняет структуру субтитров, переводя только текстовые строки, оставляя нетронутыми номера субтитров и временные метки. Исходный файл сохраняется с суффиксом `_1` (например, `movie.srt_1`), а переведенный текст записывается в файл с исходным именем.

### Основные функции:
1. **Проверка входных данных**: Скрипт принимает путь к файлу .srt и, опционально, направление перевода в формате `from:to` (например, `en:fr`). По умолчанию используется перевод с английского на русский (`en:ru`).
2. **Фильтрация строк**: Переводятся только текстовые строки, исключая пустые строки, номера субтитров и временные метки.
3. **Перевод**: Используется утилита `trans` для перевода каждой строки. Ошибки перевода логируются, и в случае сбоя сохраняется исходный текст.
4. **Прогресс-бар**: Во время перевода отображается шкала из 100 символов, которая начинается белой и постепенно становится зеленой по мере обработки строк.
5. **Сохранение результата**: После завершения перевода исходный файл переименовывается, а переведенный текст сохраняется. Прогресс-бар заменяется сообщением о времени выполнения (например, "Переведено за 3 сек").
6. **Обработка ошибок**: При возникновении ошибок (например, файл не найден или сбой перевода) выводится сообщение об ошибке, и процесс завершается.

### Использование:
1. **Убедитесь, что утилита `trans` установлена**:
   Установите `translate-shell` с помощью команды:
   ```bash
   sudo apt install translate-shell  # Для Ubuntu/Debian
"""
