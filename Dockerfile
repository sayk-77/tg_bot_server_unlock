FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r src/requirements.txt
RUN pip install --no-cache-dir -r tg_bot/requirements.txt

CMD ["sh", "-c", "python src/server.py & python tg_bot/bot.py"]