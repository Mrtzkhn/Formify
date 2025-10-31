#!/usr/bin/env bash
set -e

python manage.py makemigrations --noinput
python manage.py migrate --noinput
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application