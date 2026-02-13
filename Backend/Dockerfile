# Pin Python 3.11 to avoid building pydantic-core/PyMuPDF from source on 3.14
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 10000
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
