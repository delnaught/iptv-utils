FROM python:alpine

ADD requirements.txt .
ADD generate.py .

RUN apk update --no-cache \
    && apk add --no-cache libgit2 \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt