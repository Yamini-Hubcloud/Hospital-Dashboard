# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Copy all project files to container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir fastapi==0.135.1 uvicorn==0.23.2 gunicorn==21.2.0 pandas==2.1.1

# Expose port 10000 for Render
EXPOSE 10000

# Start FastAPI app with Gunicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:10000"]
