# Практическая работа № 3. CI/CD с GitHub Actions и TVPO — пошаговая заметка

В исходном задании используется GitLab CI/CD. В этой работе вместо GitLab применяется **GitHub Actions**, потому что GitLab.com требует дополнительную проверку аккаунта, а локальный GitLab слишком тяжёлый для виртуальной машины TVPO. Смысл работы сохраняется: после отправки кода автоматически запускаются тесты, и только успешно проверенная версия разворачивается на CentOS.

Рабочая папка на Windows:

```text
D:\учеба\7 semester\Технологии внедрения программного обеспечения\Lab3
```

Репозиторий:

```text
https://github.com/skeiigi/TVPO_3
```

В виртуальной машине используется системный Python 3.9. Его не обновляй и не удаляй: эта версия нужна для предыдущей практической работы.

## Что получилось

Схема работы следующая:

```text
Windows: Lab3
    ↓ git push
GitHub: skeiigi/TVPO_3
    ↓ GitHub Actions запускает unittest
успешный CI
    ↓ TVPO проверяет GitHub раз в 60 секунд
CentOS: загрузка новой версии и перезапуск сервиса
    ↓
http://127.0.0.1:8000/health → ok
```

GitHub не получает пароль от виртуальной машины. TVPO сама читает открытый репозиторий и забирает только тот коммит, для которого GitHub Actions завершился успешно.

## Часть 1. Состав проекта

Основные файлы:

- `app.py` — веб-приложение ипотечного калькулятора;
- `mortgage.py` — функция расчёта ежемесячного платежа;
- `tests/test_mortgage.py` — модульные тесты;
- `.github/workflows/ci-cd.yml` — проверка проекта в GitHub Actions;
- `deploy.sh` — копирование приложения и перезапуск сервиса;
- `mortgage-calculator.service` — пользовательский сервис приложения;
- `github-deploy.sh` — проверка последнего успешного запуска CI и загрузка версии;
- `tvpo3-deploy.service` — одноразовый запуск сценария развёртывания;
- `tvpo3-deploy.timer` — автоматический запуск проверки раз в минуту.

Перед отправкой изменений проверь проект в PowerShell:

```powershell
cd "D:\учеба\7 semester\Технологии внедрения программного обеспечения\Lab3"
python -m unittest discover -s tests -v
```

Ожидаемый результат:

```text
Ran 3 tests
OK
```

Тесты проверяют обычный расчёт аннуитетного платежа, нулевую процентную ставку и отклонение неправильных значений.

## Часть 2. Автоматическая проверка в GitHub Actions

Файл `.github/workflows/ci-cd.yml` содержит два задания:

1. `Unit tests` загружает репозиторий и запускает все тесты;
2. `Ready for TVPO deployment` выполняется только после успешных тестов и помечает коммит как готовый к развёртыванию.

Проверка запускается автоматически при каждом `push` в ветку `main`. Её также можно запустить вручную на странице GitHub: `Actions` → `CI/CD` → `Run workflow`.

Для отправки изменений:

```powershell
git status
git add -- .
git diff --cached
git commit -m "Описание изменения"
git push origin main
```

На GitHub открой репозиторий `TVPO_3`, затем вкладку `Actions`. Зелёная галочка возле запуска `CI/CD` означает, что оба задания выполнены. Красный крест означает, что новая версия не будет установлена на TVPO.

## Часть 3. Приложение как сервис CentOS

Приложение работает от отдельного пользователя `gitlab-runner`, но GitLab Runner для нового варианта не нужен. Имя пользователя оставлено, потому что сервис и каталог уже были безопасно подготовлены без прав `root`.

Файлы приложения находятся здесь:

```text
/home/gitlab-runner/mortgage-calculator
```

Файл пользовательского сервиса:

```text
/home/gitlab-runner/.config/systemd/user/mortgage-calculator.service
```

Для проверки сервиса в терминале TVPO от имени `root` выполни:

```bash
uid=$(id -u gitlab-runner)
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid systemctl --user status mortgage-calculator.service
curl http://127.0.0.1:8000/health
```

В статусе должно быть `active (running)`, а последняя команда должна вывести `ok`.

## Часть 4. Автоматическое развёртывание на TVPO

В TVPO установлены сценарий и таймер:

```text
/home/gitlab-runner/github-deploy.sh
/home/gitlab-runner/.config/systemd/user/tvpo3-deploy.service
/home/gitlab-runner/.config/systemd/user/tvpo3-deploy.timer
```

Алгоритм `github-deploy.sh`:

1. Получить идентификатор последнего коммита ветки `main` через GitHub API.
2. Сравнить его с уже развёрнутым коммитом.
3. Проверить итог соответствующего запуска GitHub Actions.
4. Если CI ещё идёт или завершился с ошибкой — ничего не менять.
5. Если CI успешен — клонировать репозиторий или обновить существующий клон.
6. Запустить `deploy.sh`.
7. Перезапустить ипотечный калькулятор и проверить адрес `/health`.
8. Запомнить идентификатор успешно развёрнутого коммита.

Проверь таймер:

```bash
uid=$(id -u gitlab-runner)
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid systemctl --user status tvpo3-deploy.timer
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid systemctl --user list-timers
```

Состояние таймера должно быть `active (waiting)`. Проверка выполняется примерно раз в 60 секунд, поэтому после зелёного CI развёртывание может начаться не мгновенно.

Чтобы запустить проверку немедленно:

```bash
uid=$(id -u gitlab-runner)
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid systemctl --user start tvpo3-deploy.service
```

Посмотреть журнал последних запусков:

```bash
uid=$(id -u gitlab-runner)
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid journalctl --user -u tvpo3-deploy.service -n 30 --no-pager
```

Показать идентификатор установленной версии:

```bash
cat /home/gitlab-runner/.tvpo3-deployed-sha
```

Он должен совпадать с последним успешным коммитом ветки `main` на GitHub.

## Часть 5. Как продемонстрировать работу

### 1. Успешный сценарий

На Windows внеси небольшое правильное изменение, например дополни `README.md`, затем выполни:

```powershell
cd "D:\учеба\7 semester\Технологии внедрения программного обеспечения\Lab3"
python -m unittest discover -s tests -v
git add -- README.md
git commit -m "Update project description"
git push origin main
```

После этого:

1. Покажи новый коммит в GitHub.
2. Открой вкладку `Actions` и дождись зелёной галочки.
3. Подожди до 60 секунд или запусти `tvpo3-deploy.service` вручную.
4. Покажи журнал развёртывания.
5. Выполни `curl http://127.0.0.1:8000/health` и покажи `ok`.

### 2. Защита от ошибочной версии

Для безопасной демонстрации не ломай рабочее приложение. Создай временный тест с заведомо неверным ожиданием, отправь коммит и покажи красный запуск GitHub Actions. TVPO увидит результат `failure` и не будет разворачивать этот коммит. Затем исправь или откати тест и снова отправь изменения.

Перед демонстрацией обязательно убедись, что последний коммит с рабочей версией уже сохранён на GitHub.

## Часть 6. Открытие приложения с Windows

Приложение слушает порт `8000` внутри TVPO. Безопасный способ открыть его с Windows — SSH-туннель через настроенный порт `2222`:

```powershell
ssh -N -L 8002:127.0.0.1:8000 -p 2222 user@127.0.0.1
```

Не закрывай это окно PowerShell, пока работаешь с приложением. Затем открой в браузере:

```text
http://127.0.0.1:8002
```

Для проверки введи, например:

- сумма кредита — `3000000`;
- ставка — `12`;
- срок — `20` лет.

Ожидаемый ежемесячный платёж — примерно `33032.58`.

## Если что-то не работает

### GitHub Actions показывает ошибку

Открой красный запуск, выбери задание `Unit tests` и прочитай первую строку ошибки. Локально повтори ту же проверку:

```powershell
python -m unittest discover -s tests -v
```

Исправь ошибку, создай новый коммит и снова выполни `git push`.

### Таймер включён, но версия не обновляется

Сначала проверь GitHub Actions: развёртываются только успешные запуски. Затем выполни:

```bash
uid=$(id -u gitlab-runner)
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid systemctl --user start tvpo3-deploy.service
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid journalctl --user -u tvpo3-deploy.service -n 30 --no-pager
```

Если написано `pending`, GitHub Actions ещё не закончил работу. Если написано `failure`, тесты не прошли.

### Сервис приложения не запускается

Проверь журнал:

```bash
uid=$(id -u gitlab-runner)
runuser -u gitlab-runner -- env XDG_RUNTIME_DIR=/run/user/$uid journalctl --user -u mortgage-calculator.service -n 30 --no-pager
```

Убедись, что Python остался версии 3.9:

```bash
python3 --version
```

### В браузере не открывается `localhost:8000`

`localhost` на Windows и `localhost` внутри TVPO — разные компьютеры. Используй SSH-туннель и адрес `http://127.0.0.1:8002`. Также проверь, что окно с командой `ssh -N ...` остаётся открытым.

## Итоговая проверка

Работа выполнена, если одновременно выполняются все условия:

1. Локально проходят три модульных теста.
2. Код находится в `https://github.com/skeiigi/TVPO_3`.
3. Последний запуск `CI/CD` на GitHub зелёный.
4. `tvpo3-deploy.timer` имеет состояние `active (waiting)`.
5. `mortgage-calculator.service` имеет состояние `active (running)`.
6. `curl http://127.0.0.1:8000/health` выводит `ok`.
7. Идентификатор в `.tvpo3-deployed-sha` совпадает с последним успешным коммитом `main`.

