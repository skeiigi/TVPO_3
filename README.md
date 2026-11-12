# Практическая работа № 3 — CI/CD

Вариант из задания: **калькулятор ипотеки**. Программа рассчитывает аннуитетный ежемесячный платёж, общую выплату и переплату. Разработка ведётся локально; после `git push` GitLab запускает тесты и, если они прошли, обновляет приложение на Linux ВМ через GitLab Runner. Развёртывание идёт только из основной ветки.

## 1. Проверка программы локально

В папке проекта:

```powershell
python -m unittest discover -s tests -v
python app.py
```

Откройте `http://localhost:8000`. Например, для 100 000 ₽ под 12% на 1 год платёж составляет **8 884,88 ₽**. Остановить сервер: `Ctrl+C`.

## 2. Подготовка GitLab

Создайте пустой проект в GitLab.com. В папке `practical_3` выполните по одной команде, заменив адрес репозитория своим:

```powershell
git init -b main
git add .
git commit -m "Add mortgage calculator and CI/CD"
git remote add origin https://gitlab.com/ВАШ_ЛОГИН/ВАШ_ПРОЕКТ.git
git push -u origin main
```

Если Git попросит указать имя и почту, задайте их для этого репозитория через `git config --local user.name "Имя"` и `git config --local user.email "почта"`, затем повторите коммит. Не публикуйте токен runner в репозитории.

## 3. Подготовка Linux ВМ

ВМ TVPO работает на CentOS. Установите `python3`, `curl`, `git` и GitLab Runner по [официальной инструкции для RPM-систем](https://docs.gitlab.com/runner/install/linux-repository/) с помощью `dnf`. Системный пользователь runner — `gitlab-runner`. В GitLab откройте **Settings → CI/CD → Runners → Create project runner**, задайте тег `production-vm`, затем на ВМ зарегистрируйте runner по показанной GitLab команде с executor `shell`. При создании runner разрешите ему запускать задания основной ветки, если она защищена. После регистрации проверьте, что runner отображается как online. [Инструкция GitLab по регистрации](https://docs.gitlab.com/runner/register/).

На ВМ создайте папку и сервис. Файл `mortgage-calculator.service` из проекта скопируйте в `/etc/systemd/system/`:

```bash
sudo install -d -o gitlab-runner -g gitlab-runner /home/gitlab-runner/mortgage-calculator
sudo cp mortgage-calculator.service /etc/systemd/system/
sudo systemctl daemon-reload
```

Для разрешения runner перезапускать **только этот сервис** откройте `sudo visudo -f /etc/sudoers.d/mortgage-calculator` и добавьте строку:

```text
gitlab-runner ALL=(root) NOPASSWD: /usr/bin/systemctl restart mortgage-calculator.service
```

Проверьте расположение `systemctl` через `command -v systemctl`: если путь отличается от `/usr/bin/systemctl`, измените путь и в `deploy.sh`, и в правиле sudoers. Порт 8000 откройте в настройках сети ВМ только для доступа с вашего компьютера. Приложение учебное и работает по HTTP; не выставляйте его напрямую в интернет.

## 4. Запуск конвейера и демонстрация

Файл `.gitlab-ci.yml` задаёт два этапа: `unit_tests` и `deploy_production`. Оба выполняются runner на ВМ, поскольку у них тег `production-vm`. Deploy копирует текущий код в каталог сервиса, перезапускает его и проверяет `/health`. Если тесты не пройдут, этап deploy не запустится.

После push откройте **Build → Pipelines** в GitLab. Дождитесь зелёного статуса обоих заданий. На ВМ проверьте:

```bash
systemctl status mortgage-calculator.service
curl http://127.0.0.1:8000/health
```

В браузере с вашего компьютера откройте `http://АДРЕС_ВМ:8000`. Для демонстрации автоматического обновления измените заголовок в `app.py`, сделайте коммит и `git push`. После успешного pipeline обновите страницу ВМ: заголовок должен измениться. Для демонстрации защиты от ошибочного кода временно измените ожидаемое значение в одном тесте, отправьте коммит и покажите, что `unit_tests` красный, а deploy не запускался. Затем исправьте тест и снова отправьте коммит.

В отчёт удобно включить скриншоты работающего калькулятора, результата тестов, двух зелёных заданий pipeline и страницы ВМ до и после обновления. Сдачу в еКурсы выполняйте согласно требованиям преподавателя.

## Файлы проекта

- `mortgage.py` — расчёт и проверка входных данных;
- `app.py` — веб-форма и HTTP-сервер;
- `tests/test_mortgage.py` — осмысленные автоматические тесты;
- `.gitlab-ci.yml` — проверка и развёртывание после push;
- `deploy.sh` — копирование кода, перезапуск сервиса и проверка;
- `mortgage-calculator.service` — запуск приложения в Linux.

