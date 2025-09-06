#!/bin/sh
# Unified script to set up and run the Django server

if [ ! -f .env ]; then
  echo ".env file not found. Please copy .env.example to .env and configure it."
  exit 1
fi

if [ -d venv ]; then
  . venv/bin/activate
fi

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
