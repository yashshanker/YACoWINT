FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

WORKDIR /app

# Setup & build
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY server ./server
COPY .env ./.env

ENV "APP_MODULE" "server.app:app"
