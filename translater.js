const fs = require('fs');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// Проверка аргументов командной строки
if (process.argv.length < 3) {
    console.error('Ошибка: Не указан файл для перевода');
    console.log('Использование: node script.js filename.srt [from:to]');
    console.log('Пример: node script.js movie.srt en:fr - перевод с английского на французский');
    console.log('По умолчанию: en:ru - перевод с английского на русский');
    process.exit(1);
}

const srtFilePath = process.argv[2];
let translationDirection = 'en:ru'; // Направление перевода по умолчанию

// Проверка наличия аргумента с направлением перевода
if (process.argv.length >= 4) {
    const directionArg = process.argv[3];
    if (/^[a-z]{2}:[a-z]{2}$/.test(directionArg)) {
        translationDirection = directionArg;
    } else {
        console.error('Ошибка: Неверный формат направления перевода. Используйте формат "from:to", например "en:fr"');
        process.exit(1);
    }
}

const [fromLang, toLang] = translationDirection.split(':');

// Проверка существования файла
if (!fs.existsSync(srtFilePath)) {
    console.error(`Ошибка: Файл ${srtFilePath} не найден`);
    process.exit(1);
}

console.log(`Файл \x1b[1;33m${srtFilePath}\x1b[0m`);
console.log(`Направление перевода: \x1b[1;36m${fromLang} → ${toLang}\x1b[0m`);
console.log('Начинаю перевод...');

async function translateFile() {
    const startTime = Date.now(); // Засекаем время начала

    try {
        // Чтение исходного файла
        const original = fs.readFileSync(srtFilePath, 'utf8');

        // Создание массива строк
        const arrayOriginStrings = original.split(/\r?\n/);

        // Создание массива с нумерацией строк
        const numberedLines = arrayOriginStrings.map((line, index) => [index, line]);

        // Определение строк для перевода
        const arrayForTranslate = numberedLines.filter(([index, line]) => {
            const trimmedLine = line.trim();
            return trimmedLine &&
                !/^\d+$/.test(trimmedLine) &&
                !/^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$/.test(trimmedLine);
        });

        // Асинхронная функция для перевода текста
        async function translateText(text) {
            try {
                // Экранирование кавычек для командной строки
                const escapedText = text.replace(/"/g, '\\"');
                const command = `trans -brief -no-warn -from ${fromLang} -to ${toLang} "${escapedText}"`;

                const { stdout, stderr } = await execAsync(command);
                if (stderr) {
                    console.error(`Ошибка перевода: ${stderr}`);
                    return text;
                }
                return stdout.trim();
            } catch (error) {
                console.error(`Ошибка перевода текста: ${text}`, error.message);
                return text;
            }
        }

        // Асинхронный перевод всех строк
        const translationPromises = arrayForTranslate.map(async ([index, line]) => {
            const translated = await translateText(line);
            return { index, translated };
        });

        // Ожидание завершения всех переводов
        const translationResults = await Promise.all(translationPromises);

        // Обновление строк в numberedLines
        translationResults.forEach(({ index, translated }) => {
            numberedLines[index][1] = translated;
        });

        // Создание переведенного текста
        const arrayTransated = numberedLines.map(([index, line]) => line);
        const translatedText = arrayTransated.join('\n');

        // Переименование оригинального файла
        const newFilePath = srtFilePath + '_';
        fs.renameSync(srtFilePath, newFilePath);

        // Сохранение переведенного файла
        fs.writeFileSync(srtFilePath, translatedText, 'utf8');

        // Расчет времени выполнения
        const endTime = Date.now();
        const durationInSeconds = Math.round((endTime - startTime) / 1000);

        // Форматирование времени
        let durationString;
        if (durationInSeconds < 60) {
            durationString = `${durationInSeconds} сек`;
        } else {
            const minutes = Math.floor(durationInSeconds / 60);
            const seconds = durationInSeconds % 60;
            durationString = `${minutes} мин ${seconds} сек`;
        }

        // Обновление статуса в консоли
        process.stdout.write('\x1B[2A\x1B[2K'); // Перемещаем курсор на 2 строки вверх и очищаем
        console.log(`\x1b[1;32mПереведен за ${durationString}\x1b[0m`);

    } catch (error) {
        // Обновление статуса в консоли
        process.stdout.write('\x1B[2A\x1B[2K'); // Перемещаем курсор на 2 строки вверх и очищаем
        console.log(`\x1b[1;31mНе удалось перевести\x1b[0m`);
        console.error('Ошибка:', error.message);
        process.exit(1);
    }
}

// Запуск асинхронного процесса перевода
translateFile();