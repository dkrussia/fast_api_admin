Конфигурация поднимается из файла "PROJECT_FOLDER/.env.$**SERVER_MODE**"    
По умолчанию **SERVER_MODE**=local

Запуск сервера:  
    1. Скопировать ".env.example" в ".env.local"    
    2. Отредактировать строку подключения к Database.  
Выполнить команды:

    alembic upgrade head
    uvicorn app.main:app --reload --port 5000
........................................................................   
Команды для alembic.

    - alembic revision -m "comment"
    
Решение проблемы с установкой pymssql  
Скачать и установить из файла .whl  
Для примера   `pymssql-2.1.5-cp39-cp39-win_amd64.whl`
  
#####Приложение admin
1. Определить entities согласно образцу.