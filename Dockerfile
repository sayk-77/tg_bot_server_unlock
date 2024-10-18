FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r src/requirements.txt
RUN pip install --no-cache-dir -r tg_bot/requirements.txt
RUN pip install supervisor

COPY supervisord.conf /etc/supervisord.conf

CMD ["supervisord", "-c", "/etc/supervisord.conf"]