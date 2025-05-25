FROM python:3.11-slim

WORKDIR /app

COPY auth_app/requirements.txt ./auth_app/

RUN pip install --no-cache-dir -r auth_app/requirements.txt

COPY auth_app/* ./auth_app/
COPY auth_app/templates ./auth_app/templates

WORKDIR /app/auth_app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]

