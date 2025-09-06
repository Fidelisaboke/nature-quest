@echo off
REM Simple script to run the Django server locally

IF NOT EXIST .env (
    echo ".env file not found. Please copy .env.example to .env and configure it."
    exit /b 1
)

REM Activate virtual environment if exists
IF EXIST venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
