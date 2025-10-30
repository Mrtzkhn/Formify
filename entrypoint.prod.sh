#this file to creae the some basic code gather in this 
#file , wherase wirte this code in docker file keep
#in this file and has some benefit for prod stage 
python manage.py collectstatic --noinput
python manage.py migrate
python -m gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3