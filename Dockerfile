# Use an official Python base image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY ./app ./app

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port if needed (FastAPI default is 8000)
EXPOSE 8000

# Start the app using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
