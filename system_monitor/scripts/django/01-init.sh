#!/bin/bash


python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input
gunicorn system_monitor.wsgi -b 0.0.0.0:8000 -w 4
