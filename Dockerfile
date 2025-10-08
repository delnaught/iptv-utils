FROM python:alpine

ADD requirements.txt .
ADD generate.py .

RUN apk update --no-cache \
    && apk add --no-cache ffmpeg \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt
