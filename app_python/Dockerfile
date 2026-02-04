FROM python:3.13-slim

RUN useradd -m -u 1000 appuser

USER appuser

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
