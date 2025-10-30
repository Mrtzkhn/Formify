#create_file

1. .env.local
2. .env.prod

after pull the project create this two file in the root of the project, the place manage.py exist and fill this file with this item :

1. .env.local:
   DEBUG=True
   DJANGO_SECRET_KEY='dev-insecure-key-change-me
   DJANGO_ALLOWED_HOSTS=localhost

   -->database setting
   DJANGO_DB_ENGINE=django.db.backends.sqlite3
   DJANGO_DB_NAME=db.sqlite3

2. .env.prod:
   DEBUG=False
   DJANGO_SECRET_KEY='dev-insecure-key-change-me'
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

   -->database setting
   DJANGO_DB_ENGINE=django.db.backends.sqlite3
   DJANGO_DB_NAME=db.sqlite3

## Start Project with Docker

> by this code docker image create
> `docker compose build`

> by this code docker execute container by this image
> `docker compose up -d`

after run this code you can see the project in this address:

> http://localhot
> htttp://127.0.0.1
