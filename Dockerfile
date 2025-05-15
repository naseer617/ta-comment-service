FROM python:3.11-slim

WORKDIR /app

COPY comment-service/app ./app
COPY shared ./shared
COPY comment-service/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH="/app:/app/shared:$PYTHONPATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]