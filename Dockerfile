# syntax=docker/dockerfile:1
FROM python:3.10
WORKDIR /sidus_task

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
