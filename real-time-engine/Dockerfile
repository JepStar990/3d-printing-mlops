FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env.real-time .
COPY processor.py .

CMD ["python3", "processor.py"]
