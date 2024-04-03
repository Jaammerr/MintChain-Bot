FROM python:3.11
LABEL authors="Jammer"

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt -qq update
COPY requirements.txt .

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ../.. .
CMD ["python", "./run.py"]
