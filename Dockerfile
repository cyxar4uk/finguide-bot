FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/db/finguide.db

RUN mkdir -p /app/db

# При первом запуске БД заполняется демо-данными из seed_data.py
CMD ["sh", "-c", "[ -f \"$DATABASE_PATH\" ] || python seed_data.py; python bot.py"]
