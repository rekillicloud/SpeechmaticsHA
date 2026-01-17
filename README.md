# Speechmatics STT для Home Assistant

Кастомный компонент STT (Speech-to-Text) для Home Assistant, использующий Speechmatics Real-Time API.

## Описание

Этот компонент интегрирует облачный сервис Speechmatics STT в пайплайн голосового помощника Home Assistant. Компонент поддерживает стриминг аудио в реальном времени и возвращает финальные транскрипты для передачи в LLM компонент.

## Требования

- Home Assistant 2024.x или выше
- API ключ от Speechmatics (получить можно на [speechmatics.com](https://www.speechmatics.com))
- Python пакет `speechmatics-rt` (устанавливается автоматически)

## Установка

### Способ 1: Через HACS (рекомендуется)

**Важно:** Если вы получаете ошибку `The version 4dfecc5 for this integration can not be used with HACS`, см. [HACS_INSTALLATION.md](HACS_INSTALLATION.md) для решения проблемы.

1. Убедитесь, что у вас установлен HACS
2. Создайте GitHub репозиторий и загрузите код
3. Создайте релиз с тегом `v1.0.0` (соответствует версии в manifest.json)
4. В HACS: **Интеграции** → **⋮** → **Custom repositories**
5. Добавьте URL вашего GitHub репозитория, категория: **Integration**
6. Установите интеграцию через HACS
7. Перезапустите Home Assistant

### Способ 2: Ручная установка (без HACS)

1. Скопируйте папку `custom_components/speechmatics_stt` в директорию `custom_components` вашего Home Assistant
2. Перезапустите Home Assistant
3. Перейдите в **Настройки** → **Устройства и службы** → **Добавить интеграцию**
4. Найдите "Speechmatics STT" и следуйте инструкциям
5. Введите API ключ и настройте параметры

### Способ 3: Через YAML

Добавьте в `configuration.yaml`:

```yaml
stt:
  - platform: speechmatics_stt
    api_key: !secret speechmatics_api_key
    language: ru
    operating_point: enhanced
    max_delay: 0.8
```

И добавьте в `secrets.yaml`:

```yaml
speechmatics_api_key: ваш_api_ключ
```

## Конфигурация

### Параметры

- **api_key** (обязательный): API ключ от Speechmatics
- **language** (опционально, по умолчанию: `en`): Код языка для транскрипции
  - Поддерживаемые языки: en, ru, de, fr, es, it, pt, pl, tr, nl, cs, ar, zh, ja, hi, th, vi, ko
- **operating_point** (опционально, по умолчанию: `enhanced`): Режим работы
  - `enhanced`: Лучшая точность, больше задержка
  - `standard`: Меньшая задержка, немного ниже точность
- **max_delay** (опционально, по умолчанию: `0.8`): Максимальная задержка перед отправкой финального транскрипта (в секундах, от 0.1 до 5.0)

### Примеры конфигурации

#### Русский язык с улучшенной точностью:
```yaml
stt:
  - platform: speechmatics_stt
    api_key: !secret speechmatics_api_key
    language: ru
    operating_point: enhanced
    max_delay: 1.0
```

#### Английский язык с минимальной задержкой:
```yaml
stt:
  - platform: speechmatics_stt
    api_key: !secret speechmatics_api_key
    language: en
    operating_point: standard
    max_delay: 0.5
```

## Интеграция в Assist Pipeline

После установки компонента:

1. Перейдите в **Настройки** → **Голосовые помощники** → **Assist**
2. Выберите или создайте пайплайн
3. В разделе **STT** выберите "Speechmatics STT"
4. Настройте LLM и TTS компоненты (если еще не настроены)
5. Сохраните конфигурацию

Теперь пайплайн будет работать следующим образом:
**Микрофон → Speechmatics STT → LLM → TTS → Воспроизведение**

## Поддерживаемые форматы аудио

- **Форматы**: WAV, OGG
- **Кодеки**: PCM
- **Частоты дискретизации**: 16000 Hz, 44100 Hz
- **Каналы**: Mono (1 канал)
- **Битрейт**: 16-bit

## Обработка ошибок

Компонент автоматически обрабатывает:
- Таймауты соединения
- Ошибки сети
- Невалидный API ключ
- Ошибки от Speechmatics API

При критических ошибках entity переходит в состояние `unavailable`.

## Логирование

Для отладки включите логирование в `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.speechmatics_stt: debug
```

## Устранение неполадок

### Компонент не появляется в списке интеграций
- Убедитесь, что папка находится в `custom_components/speechmatics_stt`
- Проверьте, что `manifest.json` корректен
- Перезапустите Home Assistant

### Ошибка "Invalid API key"
- Проверьте правильность API ключа
- Убедитесь, что ключ активен в вашем аккаунте Speechmatics

### Нет транскрипции
- Проверьте логи на наличие ошибок
- Убедитесь, что формат аудио поддерживается
- Проверьте сетевое соединение с Speechmatics API

### Большая задержка
- Попробуйте уменьшить `max_delay`
- Используйте `operating_point: standard` вместо `enhanced`

## Лицензия

Этот компонент использует Speechmatics Python SDK, который имеет свою лицензию. Проверьте лицензионные условия на [github.com/speechmatics/speechmatics-python-sdk](https://github.com/speechmatics/speechmatics-python-sdk).

## Поддержка

При возникновении проблем:
1. Проверьте логи Home Assistant
2. Убедитесь, что все зависимости установлены
3. Проверьте документацию Speechmatics API
