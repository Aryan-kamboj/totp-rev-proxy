FROM python:3.11-slim

WORKDIR /app

COPY main_app/requirements.txt ./main_app/

RUN pip install --no-cache-dir -r main_app/requirements.txt

COPY main_app/* ./main_app/

WORKDIR /app/main_app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

