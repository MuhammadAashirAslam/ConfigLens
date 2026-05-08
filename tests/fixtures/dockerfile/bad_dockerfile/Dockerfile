# Non-compliant Dockerfile
FROM python:latest
WORKDIR /app

ENV DB_PASSWORD=SuperSecretPassword123

RUN apt-get update
RUN apt-get install -y curl

COPY . /app

CMD ["python", "app.py"]
