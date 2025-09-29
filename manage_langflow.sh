#!/bin/bash

# Скрипт для управления Langflow
# Автор: MIA Team
# Версия: 1.0

set -e

LANGFLOW_PORT=7860
LANGFLOW_HOST="0.0.0.0"
PID_FILE="/tmp/langflow.pid"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Langflow Management Script${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Проверка виртуального окружения
check_venv() {
    if [ ! -d ".venv" ]; then
        print_error "Виртуальное окружение .venv не найдено"
        exit 1
    fi
    
    source .venv/bin/activate
    
    if ! command -v langflow &> /dev/null; then
        print_error "Langflow не найден в виртуальном окружении"
        exit 1
    fi
}

# Проверка статуса Langflow
check_status() {
    if curl -s "http://localhost:$LANGFLOW_PORT" &> /dev/null; then
        print_status "Langflow работает на http://localhost:$LANGFLOW_PORT"
        return 0
    else
        print_warning "Langflow не отвечает на http://localhost:$LANGFLOW_PORT"
        return 1
    fi
}

# Запуск Langflow
start_langflow() {
    if check_status &> /dev/null; then
        print_warning "Langflow уже запущен"
        return 0
    fi
    
    print_status "Запуск Langflow..."
    
    # Запускаем в фоне и сохраняем PID
    nohup langflow run --host $LANGFLOW_HOST --port $LANGFLOW_PORT > langflow.log 2>&1 &
    echo $! > $PID_FILE
    
    # Ждем запуска
    sleep 5
    
    if check_status; then
        print_status "Langflow успешно запущен!"
        print_status "Откройте в браузере: http://localhost:$LANGFLOW_PORT"
        print_status "Логи: langflow.log"
        print_status "PID: $(cat $PID_FILE)"
    else
        print_error "Не удалось запустить Langflow"
        exit 1
    fi
}

# Остановка Langflow
stop_langflow() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat $PID_FILE)
        if ps -p $PID > /dev/null 2>&1; then
            print_status "Остановка Langflow (PID: $PID)..."
            kill $PID
            rm -f $PID_FILE
            print_status "Langflow остановлен"
        else
            print_warning "Процесс Langflow не найден"
            rm -f $PID_FILE
        fi
    else
        print_warning "PID файл не найден"
    fi
    
    # Дополнительная проверка и принудительная остановка
    PIDS=$(ps aux | grep "langflow run" | grep -v grep | awk '{print $2}')
    if [ ! -z "$PIDS" ]; then
        print_warning "Найдены дополнительные процессы Langflow, останавливаю..."
        echo $PIDS | xargs kill -9
        print_status "Все процессы Langflow остановлены"
    fi
}

# Перезапуск Langflow
restart_langflow() {
    print_status "Перезапуск Langflow..."
    stop_langflow
    sleep 2
    start_langflow
}

# Показать логи
show_logs() {
    if [ -f "langflow.log" ]; then
        print_status "Последние 20 строк логов Langflow:"
        echo "----------------------------------------"
        tail -20 langflow.log
    else
        print_warning "Файл логов langflow.log не найден"
    fi
}

# Показать информацию о системе
show_info() {
    print_header
    echo ""
    print_status "Информация о системе:"
    echo "  Python: $(python --version)"
    echo "  Langflow: $(langflow --version)"
    echo "  Виртуальное окружение: $(pwd)/.venv"
    echo ""
    
    if check_status; then
        print_status "Статус: Работает"
        if [ -f "$PID_FILE" ]; then
            echo "  PID: $(cat $PID_FILE)"
        fi
        echo "  URL: http://localhost:$LANGFLOW_PORT"
    else
        print_warning "Статус: Не работает"
    fi
    
    echo ""
    print_status "Использование памяти:"
    ps aux | grep "langflow run" | grep -v grep | awk '{print "  PID: " $2 "  MEM: " $6 " KB"}'
}

# Показать справку
show_help() {
    print_header
    echo ""
    echo "Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  start     - Запустить Langflow"
    echo "  stop      - Остановить Langflow"
    echo "  restart   - Перезапустить Langflow"
    echo "  status    - Показать статус"
    echo "  logs      - Показать логи"
    echo "  info      - Показать информацию о системе"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 stop"
}

# Основная логика
main() {
    case "${1:-help}" in
        start)
            check_venv
            start_langflow
            ;;
        stop)
            stop_langflow
            ;;
        restart)
            check_venv
            restart_langflow
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs
            ;;
        info)
            check_venv
            show_info
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

# Запуск основной функции
main "$@"

