FROM python:3.6.6-alpine
MAINTAINER asi@dbca.wa.gov.au


RUN apk update \
  && apk upgrade \
  && apk add --no-cache --virtual .build-deps postgresql-dev gcc python3-dev musl-dev \
  && apk add --no-cache libpq bash git
WORKDIR /usr/src/app
COPY manage.py requirements.txt gunicorn.ini ./
COPY recoup ./recoup
COPY scrooge ./scrooge
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py collectstatic --noinput
RUN apk del .build-deps

EXPOSE 8080
CMD ["gunicorn", "scrooge.wsgi", "--config", "gunicorn.ini"]
