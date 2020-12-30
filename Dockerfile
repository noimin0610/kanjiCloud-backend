FROM python:3.7

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
