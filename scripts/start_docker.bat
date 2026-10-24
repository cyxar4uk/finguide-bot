@echo off
cd /d "%~dp0.."
chcp 65001 >nul
title FinGuide Bot - Docker Launcher

echo.
echo ╔════════════════════════════════════════╗
echo ║   FinGuide Bot - Запуск через Docker   ║
echo ╚════════════════════════════════════════╝
echo.

REM Проверка наличия Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Docker не найден!
    echo Установите Docker Desktop с https://www.docker.com/
    pause
    exit /b 1
)

REM Проверка наличия .env файла
if not exist ".env" (
    echo [ОШИБКА] Файл .env не найден!
    echo Создайте файл .env на основе .env.example
    pause
    exit /b 1
)

echo [INFO] Запуск FinGuide Bot через Docker...
echo.

REM Запуск через docker-compose
docker-compose up -d

if errorlevel 1 (
    echo [ОШИБКА] Не удалось запустить контейнер
    pause
    exit /b 1
)

echo.
echo [OK] Бот успешно запущен в Docker!
echo.
echo Команды управления:
echo   docker-compose logs -f          - Просмотр логов
echo   docker-compose stop             - Остановить бота
echo   docker-compose restart          - Перезапустить бота
echo   docker-compose down             - Остановить и удалить контейнер
echo.
pause
