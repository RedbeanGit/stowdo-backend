FROM python:3.8-alpine3.15

WORKDIR /app

COPY requirements.txt /app
COPY stowdo /app

RUN \
 apk add --no-cache bash postgresql-libs jpeg-dev && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev zlib-dev g++ libffi-dev && \
 pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

EXPOSE 8000