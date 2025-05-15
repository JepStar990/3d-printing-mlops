FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY .env.synthesizer .
COPY synthesizer.py .

RUN mkdir -p /app/data
VOLUME /app/data

CMD ["python3", "synthesizer.py"]
