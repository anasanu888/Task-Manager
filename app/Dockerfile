FROM python:3.11-slim

WORKDIR /app

# system deps for redis client (none required), keep image small
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./ 
COPY templates ./templates
COPY static ./static

ENV FLASK_ENV=production
EXPOSE 5000

CMD ["python", "app.py"]
